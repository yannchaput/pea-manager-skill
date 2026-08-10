# PEA Management — Project Instructions

## Model configuration (LiteLLM proxy)

All subagents use `claude-qwen3.6-plus-no-thinking` (set via `CLAUDE_CODE_SUBAGENT_MODEL` in `~/.claude/settings.json`). This model has `supports_reasoning: false` in the LiteLLM config to bypass the thinking-mode bug (see below). All models route through a local LiteLLM proxy at `http://localhost:4000` configured in `/home/yann/litellm/config.yaml`.

### Thinking-mode bug

The global `supports_reasoning: true` in LiteLLM causes OpenCode-provided models (DeepSeek v4 Pro/Flash, Qwen 3.6 Plus) to allocate all `max_tokens` to `reasoning_content`, producing empty `content` in the final text block. The proxy rejects this with:
```
API Error: 400 — Invalid assistant message: content or tool_calls must be set
```

**Root cause:** LiteLLM's adapter (`transformation.py:723-768`) converts Anthropic `thinking` param to OpenAI `reasoning_effort` for non-Claude models — `budget_tokens ≥ 10000` maps to `reasoning_effort: "high"`. DeepSeek/Qwen models already have native chain-of-thought; adding explicit `reasoning_effort` amplifies the thinking ratio to the point where the entire token budget is consumed by reasoning. With complex subagent prompts (~10-15K token system message + tools + skill loads) the model "thinks" extensively and produces zero visible content.

The problem only manifests on complex tasks — simple prompts produce short reasoning chains that leave room for content.

**Symptoms:** The task notification shows the agent made tool calls and has thinking blocks (~50-60K chars), but the text block is 0 chars. Simple tasks often pass; complex tasks (large data + skill loads) trigger it reliably.

**Fix: Strip `reasoning_effort` via `additional_drop_params`** (preferred)

DeepSeek/Qwen models produce reasoning natively without `reasoning_effort`. The fix is to strip the problematic parameter from requests while keeping `supports_reasoning: true` (so reasoning_content in responses is still propagated):

```yaml
# In /home/yann/litellm/config.yaml
- model_name: claude-deepseek-v4-flash
  litellm_params:
    model: openai/deepseek-v4-flash
    ...
    drop_params: true
    additional_drop_params:
      - reasoning_effort  # model has native reasoning — don't force aggressive allocation
```

This lets the model self-manage its thinking/content balance. The model still produces reasoning_content (shown in <think> blocks) without starving content.

**Fallback: Per-model `supports_reasoning: false`** (disables thinking entirely)

The `claude-qwen3.6-plus-no-thinking` variant exists as a fallback for models that don't need thinking at all, or when native reasoning allocation is still problematic:
```yaml
- model_name: claude-qwen3.6-plus-no-thinking
  litellm_params:
    model: dashscope/qwen3.6-plus
    api_base: https://opencode.ai/zen/go/v1
    api_key: "sk-..."
    drop_params: true
    supports_reasoning: false
```
Agents currently use `claude-deepseek-v4-flash` as the default subagent model via `CLAUDE_CODE_SUBAGENT_MODEL`.

## Parallel subagent safety

- **Shared `/tmp/pea_ohlcv.json` causes silent data corruption** when parallel `pea-price-analyst` agents run — each overwrites the file while others read it. The agent definition now mandates ticker-unique paths (`/tmp/pea_ohlcv_AI.PA.json`). Never revert to a shared path.
- The `compute_indicators.py` script supports `-i <path>` for arbitrary input files. 6mo of daily data (~127 bars) is insufficient for SMA200 — agents should extend to 1y (255 bars) when SMA200 is needed.
