# Calling models from Claude Code (tested 9 Nov 2026)

## From a claude.ai cloud session

- **Reachable**: only `api.anthropic.com`.
- **Blocked** (403 policy denial from the egress proxy): OpenAI, OpenRouter, Gemini, DeepSeek, DashScope (Qwen), Moonshot, Zhipu, Together, Groq, Mistral, xAI, Hugging Face, Ollama.
- **Claude Code CLI** 2.1.319 is installed, and `claude -p` runs on the owner's plan login.

| Model alias | Result | First-call cost | Note |
|---|---|---|---|
| haiku | claude-haiku-5-5 | $0.003 | Repeat calls ≈ $0.0003 once cached. Named the target despite being told not to (2 of 2). |
| sonnet | claude-sonnet-5-5 | $0.056 | Wrote the same Comic Sans joke as Opus. |
| opus | claude-opus-5-5 | $0.112 | |
| fable | (none) | n/a | "Out of usage credits" on the plan at test time. |

- **Hidden context.** Even with a custom system prompt, no tools, no MCP, no skills and no settings, about 13,900 tokens of hidden context reach the model on every call (prompt caching makes repeats cheap). `--bare` would strip it, but it requires `ANTHROPIC_API_KEY`, and authentication failed here without one.
- **No sampling control.** There is no temperature setting in `claude -p`.

## From the owner's machine

1. **Direct API scripts.** This is the right route for scored runs: fixed system prompt, temperature and seed policy, full request/response logs.
   - Anthropic SDK with an API key.
   - Any OpenAI-compatible endpoint (OpenAI, OpenRouter, DashScope, DeepSeek, a local Ollama or vLLM server).
2. **`claude -p --bare`** with an API key: a cleaner headless Claude call.
3. **PAL MCP (formerly Zen MCP).** Lets Claude Code consult Gemini, OpenAI, OpenRouter, Ollama and others; its `clink` tool hands work to Gemini CLI, Codex CLI or Qwen Code. Good for second opinions, wrong for measurement because it adds its own prompts. [PAL MCP](https://lobehub.com/mcp/beehiveinnovations-pal-mcp-server)
4. **Gateways via `ANTHROPIC_BASE_URL`** (LiteLLM and similar). These change which model drives Claude Code itself, not which models are under test. Anthropic doesn't support routing Claude Code to non-Claude models. [Claude Code docs: LLM gateways](https://code.claude.com/docs/en/llm-gateway.md)
5. **Subagents.** The `model` field takes `sonnet`, `opus`, `haiku`, `fable`, a full Claude model ID, or `inherit`. Claude only, and with the agent harness on top.

## Rules for the benchmark

- Every generator and judge call goes through one logged client with an explicit model ID, system prompt, temperature and max tokens.
- Judges come from a different family than the generator they are judging, or self-preference is measured and reported.
- Record the date and model ID with every output. Aliases move.
