"""Verify the API keys in .env without spending anything meaningful.

Anthropic: lists models (free) then sends a 5-token Haiku request (~$0.0001) to prove billing works.
OpenRouter: reads the key's own status endpoint (free), which reports credit limit and usage.
Run: uv run python check_keys.py
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def check_anthropic() -> bool:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        print("ANTHROPIC_API_KEY: missing")
        return False
    import anthropic

    client = anthropic.Anthropic(api_key=key)
    try:
        models = [m.id for m in client.models.list()]
    except anthropic.AuthenticationError:
        print("ANTHROPIC_API_KEY: rejected (wrong or revoked key)")
        return False
    except anthropic.APIStatusError as e:
        print(f"ANTHROPIC_API_KEY: API error {e.status_code}: {e.message}")
        return False
    try:
        r = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=5,
            messages=[{"role": "user", "content": "Say ok."}],
        )
        text = "".join(b.text for b in r.content if b.type == "text")
        print(f"ANTHROPIC_API_KEY: ok. {len(models)} models visible; Haiku replied {text!r}")
        return True
    except anthropic.PermissionDeniedError as e:
        print(f"ANTHROPIC_API_KEY: key valid but request refused (billing/credits?): {e.message}")
    except anthropic.BadRequestError as e:
        print(f"ANTHROPIC_API_KEY: key valid but request rejected: {e.message}")
    except anthropic.APIStatusError as e:
        print(f"ANTHROPIC_API_KEY: key valid but API error {e.status_code}: {e.message}")
    return False


def check_openrouter() -> bool:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        print("OPENROUTER_API_KEY: missing")
        return False
    import httpx2 as httpx  # the anthropic/openai SDKs ship httpx2

    r = httpx.get(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {key}"},
        timeout=20,
    )
    if r.status_code == 401:
        print("OPENROUTER_API_KEY: rejected (wrong or revoked key)")
        return False
    if r.status_code != 200:
        print(f"OPENROUTER_API_KEY: status {r.status_code}: {r.text[:200]}")
        return False
    data = r.json().get("data", {})
    limit = data.get("limit")
    usage = data.get("usage")
    remaining = data.get("limit_remaining")
    print(
        f"OPENROUTER_API_KEY: ok. usage so far ${usage}, limit {limit if limit is not None else 'none set'}, "
        f"remaining {remaining if remaining is not None else 'n/a'}"
    )
    return True


if __name__ == "__main__":
    ok_a = check_anthropic()
    ok_o = check_openrouter()
    if ok_a and ok_o:
        print("Both keys work. Real runs can start.")
        sys.exit(0)
    if ok_a:
        print("Anthropic only: Claude arms and judges will run; other model families will be skipped.")
        sys.exit(0)
    if ok_o:
        print("OpenRouter only: GPT, Gemini, DeepSeek and Qwen arms and the GPT judge will run; the Claude arms are "
              "skipped, and the controls and the damager run on config.FALLBACK_MODEL.")
        sys.exit(0)
    print("No usable key yet. The pipeline will run in mock mode.")
    sys.exit(1)
