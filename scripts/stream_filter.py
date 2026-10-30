#!/usr/bin/env python3
"""Render Claude Code's stream-json output as a human-readable transcript. Nothing is truncated.

Usage:
  claude -p ... --output-format stream-json --verbose | python3 scripts/stream_filter.py            # Actions log
  python3 scripts/stream_filter.py --markdown < raw.jsonl > transcript.md                           # Markdown with <details>

Layout (log mode):
  == init: model · permission mode · version · cwd         session start; the tool list sits in a collapsed group
  ── turn 12 · 00:14:33 · in 1.2k out 80 cache 0.9k · Σ in 120k out 9k
  ~ thinking                                               when the model exposes it
  > assistant text
  ▸ |_ Bash: python3 tools/ledger.py stats → 4 lines       one collapsed group per tool call; inside: the full
       |    command: ...                                     input, then the full result nested under it
       |    |_ result (Bash) 4 lines
       |         found 1919
  == result: success · cost $… · turns … · duration …      per-model usage, denials, final text

Tool errors and permission denials are also raised as ::warning:: annotations so they appear in the run summary.
A tool call is printed when its result arrives, so that groups never nest (the Actions log cannot nest groups).
"""
from __future__ import annotations

import json
import signal
import sys
import time

signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # exit quietly if the reader closes, e.g. `| head`

MARKDOWN = "--markdown" in sys.argv[1:]
ARG = "  |    "
RES = "  |    |_ "
RESBODY = "  |         "

t0 = time.time()
turn = 0
tot = {"in": 0, "out": 0, "cr": 0, "cw": 0}
pending_calls: dict[str, dict] = {}   # tool_use_id -> {"name", "input", "turn"}
call_order: list[str] = []


def out(s: str = "") -> None:
    print(s, flush=True)


def k(n: int | None) -> str:
    n = n or 0
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def elapsed() -> str:
    s = int(time.time() - t0)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def lines_of(text) -> list[str]:
    if text is None:
        return []
    if not isinstance(text, str):
        text = json.dumps(text, indent=2, ensure_ascii=False)
    return text.splitlines() or [""]


def block(text, prefix: str) -> None:
    for line in lines_of(text):
        out(prefix + line)


def content_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "text":
            parts.append(c.get("text", ""))
        elif isinstance(c, dict):
            parts.append(json.dumps(c, ensure_ascii=False))
        else:
            parts.append(str(c))
    return "\n".join(parts)


def summary(name: str, inp) -> str:
    """One line that says what a tool call did, for the collapsed group title."""
    if not isinstance(inp, dict):
        return f"{name}: {json.dumps(inp, ensure_ascii=False)}"
    if name == "Bash":
        cmd = (inp.get("command") or "").strip()
        first = cmd.splitlines()[0] if cmd else ""
        more = f" (+{len(cmd.splitlines()) - 1} lines)" if len(cmd.splitlines()) > 1 else ""
        return f"Bash: {first}{more}"
    if name == "Read":
        return f"Read {inp.get('file_path', '')}"
    if name == "Write":
        return f"Write {inp.get('file_path', '')} ← {len(lines_of(inp.get('content', '')))} lines"
    if name == "Edit":
        o, n = inp.get("old_string", ""), inp.get("new_string", "")
        return f"Edit {inp.get('file_path', '')}: {len(lines_of(o))} → {len(lines_of(n))} lines"
    if name == "WebFetch":
        return f"WebFetch {inp.get('url', '')}"
    if name == "WebSearch":
        return f"WebSearch {inp.get('query', '')}"
    if name in ("Glob", "Grep"):
        return f"{name} {inp.get('pattern', '')} {inp.get('path', '') or ''}".rstrip()
    if name == "Agent":
        return f"Agent: {inp.get('description', '')}"
    return f"{name}: {json.dumps(inp, ensure_ascii=False)}"


def group_start(title: str) -> None:
    if MARKDOWN:
        out(f"<details><summary><code>|_ {title}</code></summary>\n\n```text")
    else:
        out(f"::group::  |_ {title}")


def group_end() -> None:
    if MARKDOWN:
        out("```\n\n</details>")
    else:
        out("::endgroup::")


def warn(msg: str) -> None:
    if MARKDOWN:
        out(f"> **Warning:** {msg}")
    else:
        out(f"::warning::{msg}")


def render_call(tid: str, result_block: dict | None) -> None:
    """Print a tool call with its result, as one flat group."""
    call = pending_calls.pop(tid, None)
    if call is None:
        name, inp = "?", {}
    else:
        name, inp = call["name"], call["input"]
    body = content_text(result_block.get("content")) if result_block else ""
    n_lines = len(lines_of(body)) if body else 0
    err = bool(result_block and result_block.get("is_error"))
    title = f"{summary(name, inp)} → {n_lines} lines" if result_block else f"{summary(name, inp)} → (no result)"
    if err:
        title += "  ERROR"
    group_start(title)
    if isinstance(inp, dict):
        for key, v in inp.items():
            if isinstance(v, str) and "\n" in v:
                out(f"{ARG}{key}:")
                block(v, ARG + "    ")
            else:
                out(f"{ARG}{key}: {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}")
    else:
        block(inp, ARG)
    if result_block is not None:
        out(f"{RES}result ({name}) {n_lines} lines{'  ERROR' if err else ''}")
        block(body, RESBODY)
    group_end()
    if err:
        warn(f"tool error in {summary(name, inp)}: {lines_of(body)[0] if body else ''}")


def handle_init(e: dict) -> None:
    out(f"== init: {e.get('model')} · {e.get('permissionMode')} · claude_code {e.get('claude_code_version', '')} · session {e.get('session_id')}")
    out(f"   cwd {e.get('cwd')}")
    group_start(f"tools available ({len(e.get('tools') or [])})")
    block("\n".join(e.get("tools") or []), ARG)
    group_end()


def handle_assistant(e: dict) -> None:
    global turn
    msg = e.get("message", {})
    u = msg.get("usage") or {}
    if u:
        turn += 1
        tot["in"] += u.get("input_tokens", 0) or 0
        tot["out"] += u.get("output_tokens", 0) or 0
        tot["cr"] += u.get("cache_read_input_tokens", 0) or 0
        tot["cw"] += u.get("cache_creation_input_tokens", 0) or 0
        out("")
        out(f"── turn {turn} · {elapsed()} · in {k(u.get('input_tokens'))} out {k(u.get('output_tokens'))} "
            f"cache {k(u.get('cache_read_input_tokens'))} · Σ in {k(tot['in'])} out {k(tot['out'])} cache {k(tot['cr'])}"
            f"{' · stop=' + str(msg.get('stop_reason')) if msg.get('stop_reason') and msg.get('stop_reason') != 'tool_use' else ''}")
    for b in msg.get("content", []):
        t = b.get("type")
        if t == "thinking":
            txt = b.get("thinking") or ""
            block(txt, "~ ") if txt.strip() else out("~ (thinking occurred; text not exposed by the model)")
        elif t == "redacted_thinking":
            out("~ (redacted thinking)")
        elif t == "text":
            block(b.get("text", ""), "> ")
        elif t == "tool_use":
            tid = b.get("id", "")
            pending_calls[tid] = {"name": b.get("name", ""), "input": b.get("input", {})}
            call_order.append(tid)
        else:
            out(f"  ?? content block {t}")
            block(b, ARG)


def handle_user(e: dict) -> None:
    content = e.get("message", {}).get("content", [])
    if isinstance(content, str):
        block(content, "< ")
        return
    for b in content:
        if isinstance(b, dict) and b.get("type") == "tool_result":
            render_call(b.get("tool_use_id", ""), b)
        elif isinstance(b, dict) and b.get("type") == "text":
            block(b.get("text", ""), "< ")
        else:
            out("  ?? user block")
            block(b, ARG)


def handle_result(e: dict) -> None:
    for tid in list(call_order):
        if tid in pending_calls:
            render_call(tid, None)
    out("")
    out(f"== result: {e.get('subtype')} · cost ${e.get('total_cost_usd')} · turns {e.get('num_turns')} · "
        f"duration {(e.get('duration_ms') or 0) / 1000:.0f}s (api {(e.get('duration_api_ms') or 0) / 1000:.0f}s) · is_error {e.get('is_error')}")
    for model, mu in (e.get("modelUsage") or {}).items():
        out(f"   model {model}: in {k(mu.get('inputTokens'))} out {k(mu.get('outputTokens'))} "
            f"cache_read {k(mu.get('cacheReadInputTokens'))} cache_write {k(mu.get('cacheCreationInputTokens'))} · ${mu.get('costUSD')}")
    denials = e.get("permission_denials") or []
    if denials:
        out(f"   permission denials: {len(denials)}")
        for d in denials:
            out(f"     - {summary(d.get('tool_name', '?'), d.get('tool_input'))}")
            block(d.get("tool_input"), "         | ")
            warn(f"permission denied: {summary(d.get('tool_name', '?'), d.get('tool_input'))}")
    if e.get("result"):
        out("   final text:")
        block(e["result"], "   | ")


def main() -> None:
    for raw in sys.stdin:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            out(line)
            continue
        t = e.get("type")
        if t == "system" and e.get("subtype") == "init":
            handle_init(e)
        elif t == "system":
            out(f"== system {e.get('subtype')}")
            block({a: b for a, b in e.items() if a not in ("type", "subtype")}, "   | ")
        elif t == "assistant":
            handle_assistant(e)
        elif t == "user":
            handle_user(e)
        elif t == "result":
            handle_result(e)
        else:
            out(f"?? {t}")
            block(e, "   | ")


if __name__ == "__main__":
    main()
