# SLZ Agent — Subagent CLI

A tiny, dependency-free CLI that turns the project's AI API keys into
callable **subagents** for coding work: code review, patch generation,
architecture questions, test writing, doc drafting — anything.

It talks to the OpenAI-compatible gateway at `https://api.aeramc.su/v1`
(configured in `agent/.keys.json`, git-ignored) and lets you pick the model
per task:

| Model | Use for |
|---|---|
| `deepseek/deepseek-v4-pro-0813` | fast, cheap bulk work — drafts, refactors, tests |
| `claude-opus-5` | high-quality implementation and code review |
| `claude-opus-5-thinking` | hard reasoning — architecture, debugging, tricky domain logic |

## Setup

```bash
cp agent/.keys.example.json agent/.keys.json   # paste your keys into the array
```

Keys are read from `agent/.keys.json` (git-ignored). Multiple keys are used
as a pool: the CLI fails over to the next key on auth/rate-limit/5xx errors.

## Usage

```bash
# One-shot question with optional repo files injected as context
node agent/subagent.mjs --model claude-opus-5-thinking \
  --prompt "Review docker-compose.yml for the backend healthcheck." \
  --context erp/docker-compose.yml

# System prompt (persona) + prompt from a file
node agent/subagent.mjs --model claude-opus-5 \
  --system agent/skills/reviewer.md \
  --prompt-file /tmp/task.txt \
  --context erp/backend/config/settings/dev.py

# Write the reply to a file (e.g. a generated patch, then apply manually)
node agent/subagent.mjs --model deepseek/deepseek-v4-pro-0813 \
  --prompt "Write the code for X." --out /tmp/x.patch

# Raw JSON (usage tokens, finish reason, model actually used)
node agent/subagent.mjs --model claude-opus-5 --json --prompt "hi"
```

Flags:

- `--model <id>` — model to call (default `deepseek/deepseek-v4-pro-0813`)
- `--prompt <text>` — user message
- `--prompt-file <path>` — read the user message from a file (mutually exclusive with `--prompt`)
- `--system <text|path>` — system prompt; a path is read from disk
- `--context <paths...>` — repo files to inject into the user message as
  `=== file: path ===` blocks (relative to repo root, or absolute)
- `--max-tokens <n>` — default 4096
- `--temp <n>` — temperature, default 0.3
- `--json` — print the full raw response (content + usage + model)
- `--out <path>` — write only the assistant text to a file
- `--timeout <ms>` — default 300000 (thinking models can be slow)

Exit code: 0 on success, 1 if every key/model attempt failed.