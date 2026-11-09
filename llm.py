"""One logged client for every generator and judge call.

Rules (docs/model-access.md): every call carries an explicit model ID, system
prompt, max_tokens and sampling policy; every request and response is written to
disk; a cost ledger enforces a hard cap. Three providers:

  anthropic   Anthropic SDK. Claude 5.5 models reject temperature/top_p, so the
              sampling policy for Claude is "provider default" and is recorded as
              such. Refusals are data in this benchmark, so the server-side
              fallbacks parameter is deliberately NOT used: a refusal comes back
              as stop_reason="refusal" and is logged.
  openrouter  OpenAI-compatible endpoint for GPT, Gemini, Qwen, DeepSeek, Llama.
  mock        Deterministic fake text, no network, zero cost. Lets the pipeline
              run end to end before any key exists.

Identical requests are cached on disk by key, so a crashed or budget-stopped run
resumes without paying twice. Failed requests are not cached and retry next run.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# USD per 1M tokens (input, output). Anthropic list prices, Nov 2026.
PRICES_PER_M = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-fable-5-1": (10.00, 50.00),
}
# Used only when an OpenRouter response omits its cost field.
DEFAULT_PRICE = (2.00, 8.00)


class BudgetExceeded(RuntimeError):
    pass


MAX_ATTEMPTS = 8  # per request, on 429 / 5xx / connection errors


class _Throttle:
    """Per-model spacing between requests, switched on by the first 429.

    OpenRouter limits new accounts to 20 requests per minute per model (seen 9 Nov 2026 on
    openai/gpt-5.5); the judge stages fire fast calls from several workers and hit it at once.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._interval: dict[str, float] = {}
        self._next_ok: dict[str, float] = {}

    def wait(self, model: str) -> None:
        with self._lock:
            iv = self._interval.get(model)
            if not iv:
                return
            now = time.time()
            t = max(now, self._next_ok.get(model, now))
            self._next_ok[model] = t + iv
        if t > time.time():
            time.sleep(t - time.time())

    def slow_down(self, model: str, rpm: float) -> float:
        with self._lock:
            iv = max(self._interval.get(model, 0.0), 60.0 / rpm)
            self._interval[model] = iv
            return iv


def _retry_after(exc) -> Optional[float]:
    try:
        v = exc.response.headers.get("retry-after")
        return float(v) if v else None
    except Exception:  # noqa: BLE001
        return None


@dataclass(frozen=True)
class ModelSpec:
    provider: str  # anthropic | openrouter | mock
    model: str     # exact model id as the provider names it
    family: str    # anthropic | openai | google | alibaba | deepseek | meta | mock (self-preference checks)

    @property
    def key(self) -> str:
        return f"{self.provider}:{self.model}"


@dataclass
class Result:
    id: str
    provider: str
    model: str
    timestamp: str
    text: str
    stop_reason: str
    refused: bool            # hard refusal signalled by the provider
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_s: float
    cached: bool = False
    error: Optional[str] = None


class LLM:
    def __init__(self, run_dir: Path | str, budget_usd: float, mock: bool = False):
        self.run_dir = Path(run_dir)
        self.raw_dir = self.run_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.run_dir / "ledger.jsonl"
        self.budget_usd = budget_usd
        self.mock = mock
        self._lock = threading.Lock()
        self._spent = self._load_spent()
        self._anthropic = None
        self._openrouter = None
        self._throttle = _Throttle()

    # ---- ledger -----------------------------------------------------------
    def _load_spent(self) -> float:
        if not self.ledger_path.exists():
            return 0.0
        total = 0.0
        with self.ledger_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    total += float(json.loads(line).get("cost_usd", 0.0))
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
        return total

    @property
    def spent_usd(self) -> float:
        return self._spent

    def _record(self, res: Result, tag: str) -> None:
        with self._lock:
            self._spent += res.cost_usd
            with self.ledger_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": res.id, "tag": tag, "provider": res.provider, "model": res.model,
                    "in": res.input_tokens, "out": res.output_tokens, "cost_usd": res.cost_usd,
                    "latency_s": res.latency_s, "ts": res.timestamp, "error": res.error,
                }) + "\n")

    def _check_budget(self) -> None:
        if self._spent >= self.budget_usd:
            raise BudgetExceeded(f"spent ${self._spent:.2f} of ${self.budget_usd:.2f} cap")

    # ---- clients ----------------------------------------------------------
    def _get_anthropic(self):
        if self._anthropic is None:
            import anthropic
            self._anthropic = anthropic.Anthropic(max_retries=3, timeout=180.0)
        return self._anthropic

    def _get_openrouter(self):
        if self._openrouter is None:
            from openai import OpenAI
            key = os.environ.get("OPENROUTER_API_KEY", "").strip()
            if not key:
                raise RuntimeError("OPENROUTER_API_KEY not set")
            self._openrouter = OpenAI(
                base_url="https://openrouter.ai/api/v1", api_key=key, max_retries=1, timeout=180.0,  # retries live in _call_openrouter
            )
        return self._openrouter

    # ---- the one entry point ----------------------------------------------
    def call(
        self,
        spec: ModelSpec,
        system: str,
        user: str,
        *,
        max_tokens: int = 4000,
        temperature: Optional[float] = None,
        effort: Optional[str] = None,
        key: Optional[str] = None,
        tag: str = "",
    ) -> Result:
        """Send one request. `key` makes the call idempotent across runs (disk cache)."""
        cache_key = key or f"{spec.key}|{system}|{user}|{max_tokens}|{temperature}|{effort}"
        rid = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:20]
        raw_path = self.raw_dir / f"{rid}.json"
        if raw_path.exists():
            saved = json.loads(raw_path.read_text(encoding="utf-8"))
            res = Result(**saved["result"])
            res.cached = True
            return res

        self._check_budget()
        provider = "mock" if self.mock else spec.provider
        request = {
            "provider": provider, "model": spec.model, "system": system, "user": user,
            "max_tokens": max_tokens, "temperature": temperature, "effort": effort, "tag": tag, "key": key,
        }
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        t0 = time.time()
        raw = None
        error = None
        try:
            if provider == "mock":
                fields, raw = self._call_mock(spec, system, user)
            elif provider == "anthropic":
                fields, raw = self._call_anthropic(spec, system, user, max_tokens, effort)
            elif provider == "openrouter":
                fields, raw = self._call_openrouter(spec, system, user, max_tokens, temperature, effort)
            else:
                raise ValueError(f"unknown provider {provider!r}")
        except BudgetExceeded:
            raise
        except Exception as e:  # noqa: BLE001 - logged; the pipeline continues
            error = f"{type(e).__name__}: {e}"
            fields = dict(text="", stop_reason="error", refused=False, input_tokens=0, output_tokens=0, cost_usd=0.0)

        res = Result(
            id=rid, provider=provider, model=spec.model, timestamp=ts,
            latency_s=round(time.time() - t0, 3), error=error, **fields,
        )
        self._record(res, tag)
        if error is None:
            raw_path.write_text(
                json.dumps({"request": request, "result": asdict(res), "raw": raw}, ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
        return res

    # ---- providers --------------------------------------------------------
    def _call_anthropic(self, spec: ModelSpec, system: str, user: str, max_tokens: int, effort: Optional[str]):
        client = self._get_anthropic()
        kwargs = dict(model=spec.model, max_tokens=max_tokens, system=system,
                      messages=[{"role": "user", "content": user}])
        if effort and effort != "none":
            kwargs["output_config"] = {"effort": effort}
        r = client.messages.create(**kwargs)
        text = "".join(b.text for b in r.content if b.type == "text")
        u = r.usage
        p_in, p_out = PRICES_PER_M.get(spec.model, DEFAULT_PRICE)
        cache_w = getattr(u, "cache_creation_input_tokens", 0) or 0
        cache_r = getattr(u, "cache_read_input_tokens", 0) or 0
        cost = (u.input_tokens * p_in + u.output_tokens * p_out + cache_w * p_in * 1.25 + cache_r * p_in * 0.1) / 1e6
        fields = dict(
            text=text,
            stop_reason=r.stop_reason or "",
            refused=(r.stop_reason == "refusal"),
            input_tokens=u.input_tokens + cache_w + cache_r,
            output_tokens=u.output_tokens,
            cost_usd=round(cost, 6),
        )
        return fields, r.to_dict()

    def _call_openrouter(self, spec: ModelSpec, system: str, user: str, max_tokens: int, temperature: Optional[float],
                         effort: Optional[str] = None):
        client = self._get_openrouter()
        extra_body: dict = {"usage": {"include": True}}
        if effort == "none":  # mechanical tasks (the damager): no thinking at all
            extra_body["reasoning"] = {"enabled": False}
        elif effort:  # OpenRouter normalises reasoning effort across OpenAI, Google, DeepSeek and Qwen
            extra_body["reasoning"] = {"effort": effort}
        kwargs = dict(
            model=spec.model,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            extra_body=extra_body,
            extra_headers={"X-Title": "roast-bench"},
        )
        if temperature is not None:
            kwargs["temperature"] = temperature
        import openai

        for attempt in range(MAX_ATTEMPTS):
            self._throttle.wait(spec.model)
            try:
                r = client.chat.completions.create(**kwargs)
                break
            except openai.RateLimitError as e:
                m = re.search(r"(\d+)\s+requests per minute", str(e))
                rpm = float(m.group(1)) if m else 20.0
                iv = self._throttle.slow_down(spec.model, rpm * 0.8)
                if attempt == MAX_ATTEMPTS - 1:
                    raise
                delay = _retry_after(e) or min(60.0, 5.0 * 2 ** attempt)
                print(f"429 on {spec.model}: spacing requests {iv:.1f}s, retry in {delay:.0f}s", flush=True)
                time.sleep(delay + random.uniform(0, 1))
            except (openai.APIConnectionError, openai.APITimeoutError, openai.InternalServerError) as e:
                if attempt == MAX_ATTEMPTS - 1:
                    raise
                delay = min(60.0, 3.0 * 2 ** attempt)
                print(f"{type(e).__name__} on {spec.model}: retry in {delay:.0f}s", flush=True)
                time.sleep(delay + random.uniform(0, 1))
        choice = r.choices[0] if r.choices else None
        text = (choice.message.content or "") if choice else ""
        finish = (choice.finish_reason or "") if choice else "no_choice"
        u = r.usage
        in_tok = int(getattr(u, "prompt_tokens", 0) or 0)
        out_tok = int(getattr(u, "completion_tokens", 0) or 0)
        cost = None
        if u is not None:
            extra = getattr(u, "model_extra", None) or {}
            cost = extra.get("cost", getattr(u, "cost", None))
        if cost is None:
            p_in, p_out = DEFAULT_PRICE
            cost = (in_tok * p_in + out_tok * p_out) / 1e6
        if finish == "length" and not text.strip():
            # reasoning ate the whole max_tokens budget: an error (retried on resume), not a roast
            raise RuntimeError(f"length: no visible text after {max_tokens} tokens")
        refused = finish == "content_filter" or text.strip() == ""
        fields = dict(text=text, stop_reason=finish, refused=refused, input_tokens=in_tok,
                      output_tokens=out_tok, cost_usd=round(float(cost), 6))
        return fields, r.model_dump()

    def _call_mock(self, spec: ModelSpec, system: str, user: str):
        """Deterministic fake. Echoes a few prompt words so masking and the swap test have something to chew on."""
        h = int(hashlib.sha256((spec.model + "\x00" + user).encode("utf-8")).hexdigest(), 16)
        # Judge prompts: return something parseable so the downstream stages can be tested.
        if "Answer with the number only" in user:
            text = str(1 + h % 5)
            return dict(text=text, stop_reason="end_turn", refused=False, input_tokens=len(user.split()),
                        output_tokens=1, cost_usd=0.0), None
        if "Answer with a single letter" in user:
            text = "AB"[h % 2]
            return dict(text=text, stop_reason="end_turn", refused=False, input_tokens=len(user.split()),
                        output_tokens=1, cost_usd=0.0), None
        if "Return a JSON array" in user:
            v = ["supported", "contradicted", "absent"][h % 3]
            text = ('[{"claim": "mock claim about a date", "verdict": "supported"}, '
                    f'{{"claim": "mock claim about a number", "verdict": "{v}"}}]')
            return dict(text=text, stop_reason="end_turn", refused=False, input_tokens=len(user.split()),
                        output_tokens=30, cost_usd=0.0), None
        if h % 41 == 0:
            text = "I'd rather not write that. Can I help with something else?"
            refused = True
        else:
            words = [w.strip(".,;:()[]\"'") for w in user.replace("\n", " ").split(" ")]
            words = [w for w in words if len(w) > 3][:400] or ["thing"]
            pick = [words[(h >> (i * 7)) % len(words)] for i in range(6)]
            zh = "螺蛳" in user or "吐槽" in user or "锐评" in user
            if zh:
                text = f"[mock {spec.model}] 说到{pick[0]}，{pick[1]}这事儿，{pick[2]}。（停一拍）{pick[3]}。说实话也没什么恶意。"
            else:
                text = (
                    f"[mock {spec.model}] Let's talk about {pick[0]}. {pick[1]} and {pick[2]}, which is {pick[3]}. "
                    f"It is like a clown at a funeral insisting everyone lighten up. No offense, though."
                )
            refused = False
        n_in = len(user.split()) + len(system.split())
        fields = dict(text=text, stop_reason="end_turn", refused=refused, input_tokens=n_in,
                      output_tokens=len(text.split()), cost_usd=0.0)
        return fields, None


__all__ = ["LLM", "ModelSpec", "Result", "BudgetExceeded", "PRICES_PER_M"]
