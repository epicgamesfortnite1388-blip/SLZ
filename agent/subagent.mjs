#!/usr/bin/env node
/**
 * subagent.mjs — call the project's AI gateway with a chosen model + repo
 * context, usable as a coding subagent. See agent/README.md.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve, isAbsolute, join } from "node:path";

const REPO_ROOT = resolve(import.meta.dirname, "..");
const DEFAULT_MODEL = "deepseek/deepseek-v4-pro-0813";

function usage() {
  console.error(`Usage: node agent/subagent.mjs [flags]
  --model <id>          model id (default ${DEFAULT_MODEL})
  --prompt <text>       user message
  --prompt-file <path>  read user message from file
  --system <text|path>  system prompt (path if it exists on disk)
  --context <paths...>  repo files to inject as context
  --max-tokens <n>      default 4096
  --temp <n>            default 0.3
  --json                print full raw response
  --out <path>          write assistant text to file
  --timeout <ms>        default 300000`);
  process.exit(2);
}

const args = process.argv.slice(2);
const opts = { model: DEFAULT_MODEL, maxTokens: 4096, temp: 0.3, timeoutMs: 300000, json: false };
const ctx = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  const next = () => args[++i];
  switch (a) {
    case "--model": opts.model = next(); break;
    case "--prompt": opts.prompt = next(); break;
    case "--prompt-file": opts.promptFile = next(); break;
    case "--system": opts.system = next(); break;
    case "--context": while (args[i + 1] && !args[i + 1].startsWith("--")) ctx.push(next()); break;
    case "--max-tokens": opts.maxTokens = Number(next()); break;
    case "--temp": opts.temp = Number(next()); break;
    case "--json": opts.json = true; break;
    case "--out": opts.out = next(); break;
    case "--timeout": opts.timeoutMs = Number(next()); break;
    case "-h": case "--help": usage(); break;
    default:
      console.error(`unknown flag: ${a}`); usage();
  }
}

if (!opts.prompt && !opts.promptFile) { console.error("error: --prompt or --prompt-file is required"); usage(); }

// ---- config ----
let cfg;
try {
  cfg = JSON.parse(readFileSync(resolve(import.meta.dirname, ".keys.json"), "utf8"));
} catch {
  console.error("error: agent/.keys.json missing — cp agent/.keys.example.json agent/.keys.json and paste your keys");
  process.exit(1);
}
const baseUrl = (cfg.base_url || "https://api.aeramc.su/v1").replace(/\/+$/, "");
const keys = (cfg.keys || []).filter(Boolean);
if (!keys.length) { console.error("error: no keys in agent/.keys.json"); process.exit(1); }

// ---- assemble messages ----
let userMsg = opts.promptFile ? readFileSync(opts.promptFile, "utf8") : opts.prompt;

if (ctx.length) {
  const blocks = [];
  for (const p of ctx) {
    const abs = isAbsolute(p) ? p : join(REPO_ROOT, p);
    let text;
    try {
      text = readFileSync(abs, "utf8");
    } catch (e) {
      blocks.push(`=== file: ${p} ===\n(UNREADABLE: ${e.message})`);
      continue;
    }
    if (text.length > 30000) text = text.slice(0, 30000) + "\n…[truncated]";
    blocks.push(`=== file: ${p} ===\n${text}`);
  }
  userMsg += `\n\n--- Repo context ---\n${blocks.join("\n\n")}`;
}

let systemMsg = opts.system;
if (systemMsg) {
  try { systemMsg = readFileSync(systemMsg, "utf8"); } catch { /* it's inline text */ }
}

const messages = [];
if (systemMsg) messages.push({ role: "system", content: systemMsg });
messages.push({ role: "user", content: userMsg });

// ---- call with key failover ----
async function call(key) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), opts.timeoutMs);
  const started = Date.now();
  try {
    const res = await fetch(`${baseUrl}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
      body: JSON.stringify({
        model: opts.model,
        messages,
        max_tokens: opts.maxTokens,
        temperature: opts.temp,
      }),
      signal: ctrl.signal,
    });
    const text = await res.text();
    let json;
    try { json = JSON.parse(text); } catch { json = null; }
    return { status: res.status, latencyMs: Date.now() - started, json, text };
  } finally {
    clearTimeout(t);
  }
}

function mask(k) { return k.length <= 8 ? "****" : `${k.slice(0, 6)}…${k.slice(-4)}`; }

let lastErr = null;
for (const key of keys) {
  let r;
  try {
    r = await call(key);
  } catch (e) {
    lastErr = e; console.error(`[subagent] key ${mask(key)} errored: ${e.message}`); continue;
  }
  if (r.status >= 200 && r.status < 300) {
    const content = r.json?.choices?.[0]?.message?.content ?? "";
    if (opts.json) {
      console.log(JSON.stringify({
        model: opts.model,
        key: mask(key),
        latencyMs: r.latencyMs,
        usage: r.json?.usage ?? null,
        finish_reason: r.json?.choices?.[0]?.finish_reason ?? null,
        content,
      }, null, 2));
    } else if (opts.out) {
      writeFileSync(opts.out, content);
      console.error(`[subagent] wrote ${content.length} chars to ${opts.out}`);
    } else {
      process.stdout.write(content.endsWith("\n") ? content : content + "\n");
    }
    process.exit(0);
  }
  lastErr = new Error(`HTTP ${r.status}: ${r.json?.error?.message || r.text.slice(0, 300)}`);
  console.error(`[subagent] key ${mask(key)} failed: HTTP ${r.status} — ${r.json?.error?.message || r.text.slice(0, 200)}`);
}
console.error(`[subagent] all keys failed for model ${opts.model}: ${lastErr?.message}`);
process.exit(1);