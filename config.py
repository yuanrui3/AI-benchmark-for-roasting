"""Arms, models, languages and prompts for the preflight.

Everything that decides what gets generated lives here, so a run is reproducible
from this file plus targets.jsonl. Edit here, not in generate.py.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from llm import ModelSpec

load_dotenv()

ROOT = Path(__file__).resolve().parent
SKILL_PATH = ROOT / ".claude" / "skills" / "roast-anything" / "SKILL.md"

LANGS = ["en", "zh"]
SAMPLES = 2            # samples per (arm, target, lang)
GEN_MAX_TOKENS = 8000  # roasts are short; the headroom is for models that think before writing (billed by use, not by cap).
                       # Qwen3.8-max spent more than 4000 thinking tokens on one Chinese roast in the smoke run.

# OpenRouter ids are checked against https://openrouter.ai/api/v1/models before a real run
# (generate.py --list-models shows candidates). Fix them here if the check fails.
MODELS: dict[str, ModelSpec] = {
    "opus": ModelSpec("anthropic", "claude-opus-5-5", "anthropic"),
    "sonnet": ModelSpec("anthropic", "claude-sonnet-5-5", "anthropic"),
    "haiku": ModelSpec("anthropic", "claude-haiku-5-5", "anthropic"),
    # checked against https://openrouter.ai/api/v1/models on 9 Nov 2026; dated snapshots preferred for reproducibility
    "gpt": ModelSpec("openrouter", "openai/gpt-5.5", "openai"),
    "gemini": ModelSpec("openrouter", "google/gemini-3.1-pro-preview", "google"),
    "deepseek": ModelSpec("openrouter", "deepseek/deepseek-v4-pro-0813", "deepseek"),
    "qwen": ModelSpec("openrouter", "qwen/qwen3.8-max-0902", "alibaba"),
}

# Roles that are a prompt condition rather than a measured model (the two controls, the damager) move to
# this model when their own provider's key is missing. Measured arms never fall back: they are skipped.
FALLBACK_MODEL = "deepseek"
DAMAGER_MODEL = "haiku"

# kind: plain   = roast prompt, model's own knowledge
#       facts   = roast prompt + fact sheet (isolates the value of facts from the value of the skill)
#       skill   = SKILL.md as system prompt + fact sheet (the specialist arm)
#       bland   = polite critique, no jokes (funniness floor)
#       generic = roast of the category, no target (specificity floor)
#       frame   = agent-action framing (owner, 9 Nov 2026): roast the practice ("wearing Crocs out of the house"),
#                 aim at the people doing it, not the object. Same system prompt as plain; needs target.practice.
#   Model-size ladder (11 Nov 2026): plain and frame on Sonnet 5.5 and Haiku 5.5 next to Opus 5.5. A benchmark that
#   cannot order Opus above Haiku on the same prompt is not measuring anything; the ladder is the cheapest validity check.
ARMS: list[dict] = [
    {"name": "plain-opus", "kind": "plain", "model": "opus"},
    {"name": "plain-sonnet", "kind": "plain", "model": "sonnet"},
    {"name": "plain-haiku", "kind": "plain", "model": "haiku"},
    {"name": "plain-gpt", "kind": "plain", "model": "gpt"},
    {"name": "plain-gemini", "kind": "plain", "model": "gemini"},
    {"name": "plain-deepseek", "kind": "plain", "model": "deepseek"},
    {"name": "plain-qwen", "kind": "plain", "model": "qwen"},
    {"name": "facts-opus", "kind": "facts", "model": "opus"},
    {"name": "skill-opus", "kind": "skill", "model": "opus"},
    {"name": "frame-opus", "kind": "frame", "model": "opus"},
    {"name": "frame-sonnet", "kind": "frame", "model": "sonnet"},
    {"name": "frame-haiku", "kind": "frame", "model": "haiku"},
    {"name": "frame-gpt", "kind": "frame", "model": "gpt"},
    {"name": "frame-gemini", "kind": "frame", "model": "gemini"},
    {"name": "frame-deepseek", "kind": "frame", "model": "deepseek"},
    {"name": "frame-qwen", "kind": "frame", "model": "qwen"},
    {"name": "control-bland", "kind": "bland", "model": "sonnet", "fallback": True},
    {"name": "control-generic", "kind": "generic", "model": "sonnet", "fallback": True},
]

LENGTH = {"en": "80 to 150 words", "zh": "120到250字"}

# Judges. Rule: a judge from a different family than the generator, or self-preference is measured
# and reported (analyze.py does the latter, so both families judge everything).
JUDGES: dict[str, str] = {        # judge name -> MODELS key
    "judge-sonnet": "sonnet",
    "judge-gpt": "gpt",
    "judge-deepseek": "deepseek",   # about a fifth of GPT-5.5's price per call; it also generates (plain-deepseek), so
                                    # analyze.py's self-preference column is the check on it
    "judge-opus": "opus",           # twice Sonnet's price and the generator of most arms (self-preference check applies);
                                    # on request only: name it with --judges, the default judge set leaves it out
}
ON_REQUEST_JUDGES = {"judge-opus"}
JUDGE_EFFORT = "low"        # classification tasks: swap test, truth, agency, devices
PAIR_JUDGE_EFFORT = "low"   # comparative tasks: damage tests, pair judging (position-tied answers at low effort on Sonnet)
JUDGE_MAX_TOKENS = 8000  # thinking tokens count toward this; answers are a few tokens. DeepSeek V4 Pro spent
                         # more than 2000 on most truth checks and more than 4000 on a few swap tests at effort=low.
# The truth check is a fact-check against a supplied sheet, so one judge is enough: the first usable one here.
TRUTH_JUDGE_ORDER = ["judge-sonnet", "judge-deepseek", "judge-gpt"]
# Sentence labelling (agency.py) is cheap work: the cheapest adequate judge first.
AGENCY_JUDGE_ORDER = ["judge-deepseek", "judge-sonnet", "judge-gpt"]

_KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "openrouter": "OPENROUTER_API_KEY"}


def has_key(provider: str) -> bool:
    """A provider is usable when its key is set and it is not parked in DISABLED_PROVIDERS (.env, comma list).
    Parking is for a key that exists but has no credit: every arm, judge and fallback then skips it cleanly
    instead of failing call by call."""
    if provider == "mock":
        return True
    parked = {p.strip() for p in os.environ.get("DISABLED_PROVIDERS", "").split(",") if p.strip()}
    if provider in parked:
        return False
    return bool(os.environ.get(_KEY_ENV.get(provider, ""), "").strip())


def usable_arms(mock: bool = False) -> list[dict]:
    """ARMS whose provider key exists (all of them under --mock). Measured arms without a key are dropped and
    printed; arms flagged fallback=True (the controls) move to FALLBACK_MODEL instead. Items record the model used."""
    if mock:
        return [dict(a) for a in ARMS]
    keep, dropped, moved = [], [], []
    for a in ARMS:
        if has_key(MODELS[a["model"]].provider):
            keep.append(dict(a))
        elif a.get("fallback") and has_key(MODELS[FALLBACK_MODEL].provider):
            keep.append({**a, "model": FALLBACK_MODEL})
            moved.append(a["name"])
        else:
            dropped.append(a["name"])
    if dropped:
        print(f"no key for provider; skipping arms: {dropped}")
    if moved:
        print(f"no key for provider; arms running on {MODELS[FALLBACK_MODEL].model} instead: {moved}")
    return keep


def damager_spec(mock: bool = False) -> ModelSpec:
    """The model that writes damaged variants: DAMAGER_MODEL, or FALLBACK_MODEL when its key is missing."""
    spec = MODELS[DAMAGER_MODEL]
    if mock or has_key(spec.provider):
        return spec
    fb = MODELS[FALLBACK_MODEL]
    print(f"no key for {spec.provider}; damager runs on {fb.model}")
    return fb


def _first_usable(order: list[str], mock: bool) -> list[str]:
    usable = usable_judges(mock)
    for j in order:
        if j in usable:
            return [j]
    return usable[:1]


def truth_judges(mock: bool = False) -> list[str]:
    return _first_usable(TRUTH_JUDGE_ORDER, mock)


def agency_judges(mock: bool = False) -> list[str]:
    return _first_usable(AGENCY_JUDGE_ORDER, mock)


def usable_judges(mock: bool = False) -> list[str]:
    """The default judge set: every judge whose key exists, minus the on-request ones (pass --judges to use those)."""
    if mock:
        return [j for j in JUDGES if j not in ON_REQUEST_JUDGES]
    keep = [j for j, m in JUDGES.items() if has_key(MODELS[m].provider) and j not in ON_REQUEST_JUDGES]
    dropped = [j for j in JUDGES if j not in keep and j not in ON_REQUEST_JUDGES]
    if dropped:
        print(f"no key for provider; skipping judges: {dropped}")
    return keep


def _facts_block(target: dict, lang: str) -> str:
    lines = "\n".join(f"{i + 1}. {f}" for i, f in enumerate(target["facts"]))
    if lang == "zh":
        return f"以下是关于{target_name(target, lang)}的事实清单（已核实）：\n{lines}"
    return f"Fact sheet for {target_name(target, lang)} (verified):\n{lines}"


def target_name(target: dict, lang: str) -> str:
    if lang == "zh":
        return target.get("name_zh") or target["name"]
    return target["name"]


def target_label(target: dict, lang: str) -> str:
    """Name plus a disambiguating gloss for the prompt, e.g. 'Papyrus (the typeface)'. In the smoke run three of
    four plain arms roasted the Undertale skeleton. Masking uses name and aliases, never the gloss."""
    name = target_name(target, lang)
    gloss = target.get("gloss_zh" if lang == "zh" else "gloss")
    if not gloss:
        return name
    return f"{name}（{gloss}）" if lang == "zh" else f"{name} ({gloss})"


def practice_text(target: dict, lang: str) -> str:
    """The target as someone doing something ('wearing Crocs out of the house'). Falls back to a generic phrasing
    when targets.jsonl has no practice yet, so a frame arm never silently roasts the object."""
    p = target.get("practice_zh" if lang == "zh" else "practice")
    if p:
        return p
    label = target_label(target, lang)
    return f"有人在用{label}" if lang == "zh" else f"people who go in for {label}"


def category_name(target: dict, lang: str) -> str:
    if lang == "zh":
        return target.get("category_zh") or target["category"]
    return target["category"]


def build_prompt(arm: dict, target: dict, lang: str) -> tuple[str, str]:
    """Return (system, user) for one generation."""
    kind = arm["kind"]
    name = target_name(target, lang)
    label = target_label(target, lang)
    cat = category_name(target, lang)
    n = LENGTH[lang]

    if kind == "skill":
        skill = SKILL_PATH.read_text(encoding="utf-8")
        addendum = (
            "\n\n## Benchmark mode\n"
            "You cannot search the web. The fact sheet in the user message replaces your search step: "
            "use those facts plus common knowledge, and invent no specifics. Output only the roast as "
            "performable lines. No Sources list, no preamble, no commentary. "
            + ("Write in English." if lang == "en" else "用中文写。")
        )
        system = skill + addendum
        if lang == "zh":
            user = f"{_facts_block(target, lang)}\n\n目标：{label}。写一段{n}的吐槽。"
        else:
            user = f"{_facts_block(target, lang)}\n\nTarget: {label}. Write a roast of {n}."
        return system, user

    if lang == "zh":
        system = "你是一位脱口秀编剧，写的是现场表演的段子。只输出段子正文，不要标题，不要解释。"
        if kind == "plain":
            user = f"写一段吐槽{label}的段子，{n}。要具体到{name}本身：换成别的东西也成立的吐槽算失败。"
        elif kind == "facts":
            user = (f"{_facts_block(target, lang)}\n\n写一段吐槽{label}的段子，{n}。"
                    f"可以用上面的事实，不要编造别的具体细节。要具体到{name}本身。")
        elif kind == "bland":
            system = "你是一位写产品评测的作者。只输出正文。"
            user = f"客观、礼貌地评价一下{label}，{n}。说优点也说不足，语气平和，不开玩笑，不讽刺。"
        elif kind == "generic":
            user = f"写一段吐槽“{cat}”这一类东西的段子，{n}。针对这一整类，不要单独点名其中任何一个。"
        elif kind == "frame":
            practice = practice_text(target, lang)
            user = (f"写一段吐槽“{practice}”的段子，{n}。矛头对准干这件事的人：他们是谁、图什么、落得什么下场。"
                    f"不要只形容{name}本身。要具体到{name}：换成别的东西也成立的吐槽算失败。")
        else:
            raise ValueError(kind)
        return system, user

    system = "You are a stand-up comedy writer. Output only the roast itself: no title, no explanation."
    if kind == "plain":
        user = (f"Write a roast of {label}, {n}. Be specific to {name}: a roast that would work just as well "
                f"for something else is a failure.")
    elif kind == "facts":
        user = (f"{_facts_block(target, lang)}\n\nWrite a roast of {label}, {n}. You may use the facts above; "
                f"invent no other specifics. Be specific to {name}.")
    elif kind == "bland":
        system = "You write balanced product reviews. Output only the review text."
        user = (f"Write a polite, balanced critique of {label}, {n}. Mention strengths and weaknesses in a calm "
                f"tone. No jokes, no sarcasm.")
    elif kind == "generic":
        user = (f"Write a roast of {cat} as a category, {n}. Aim at the whole category; do not single out or "
                f"name any particular one.")
    elif kind == "frame":
        practice = practice_text(target, lang)
        user = (f"Write a roast of {practice}, {n}. Aim at the people doing it: who they are, what they are after, "
                f"what it gets them. Do not describe {name} as an object. Be specific to {name}: a roast that would "
                f"work just as well for something else is a failure.")
    else:
        raise ValueError(kind)
    return system, user
