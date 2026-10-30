#!/usr/bin/env python3
"""Render Claude Code's stream-json output as a structured, untruncated log.

Reads JSON lines on stdin. Nothing is cut. Layout:

  == init ...                      session start: model, tools, permission mode
  < user input                     the prompt (printed by the launcher; the stream itself has no user turn)
  ~ thinking text                  assistant thinking (when the model exposes it)
  > assistant text                 what the agent says
  |_ Name #id                      a tool call, with its full input beneath
  |    key: value
  |    |_ result (Name)            the tool result the agent saw, nested under its call, in full
  |         line
  [usage in=.. out=.. cache_read=.. cache_write=..]   per-turn tokens
  == result ...                    cost, turns, duration, per-model usage, permission denials
  ?? type                          any other event, as JSON
"""
import json
import sys

CALL = "  |_ "
ARG = "  |    "
RES = "  |    |_ "
RESBODY = "  |         "
tool_names: dict[str, str] = {}
pending_usage: list[str] = []


def flush_usage() -> None:
    """Print the previous turn's usage line after that turn's tool results, not between call and result."""
    while pending_usage:
        out(pending_usage.pop(0))


def out(s: str = "") -> None:
    print(s, flush=True)


def block(text, prefix=ARG) -> None:
    """Print text with every line prefixed. Accepts str, list, dict, or None."""
    if text is None:
        return
    if not isinstance(text, str):
        text = json.dumps(text, indent=2, ensure_ascii=False)
    for line in text.splitlines() or [""]:
        out(prefix + line)


def content_text(content) -> str:
    """Tool result content is a string or a list of content blocks."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for c in content:
        if isinstance(c, dict):
            if c.get("type") == "text":
                parts.append(c.get("text", ""))
            else:
                parts.append(json.dumps(c, ensure_ascii=False))
        else:
            parts.append(str(c))
    return "\n".join(parts)


def handle_init(e: dict) -> None:
    out(f"== init: session {e.get('session_id')}  model {e.get('model')}  permission_mode {e.get('permissionMode')}  "
        f"claude_code {e.get('claude_code_version', '')}")
    out(f"   cwd {e.get('cwd')}")
    out(f"   tools {', '.join(e.get('tools') or [])}")


def handle_assistant(e: dict) -> None:
    flush_usage()
    msg = e.get("message", {})
    for b in msg.get("content", []):
        t = b.get("type")
        if t == "thinking":
            txt = b.get("thinking") or ""
            if txt.strip():
                block(txt, prefix="~ ")
            else:
                out("~ (thinking occurred; text not exposed by the model)")
        elif t == "redacted_thinking":
            out("~ (redacted thinking)")
        elif t == "text":
            block(b.get("text", ""), prefix="> ")
        elif t == "tool_use":
            tool_names[b.get("id", "")] = b.get("name", "")
            out(f"{CALL}{b.get('name')} #{b.get('id')}")
            inp = b.get("input", {})
            if isinstance(inp, dict):
                for k, v in inp.items():
                    if isinstance(v, str) and "\n" in v:
                        out(f"{ARG}{k}:")
                        block(v, prefix=ARG + "    ")
                    else:
                        out(f"{ARG}{k}: {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}")
            else:
                block(inp, prefix=ARG)
        else:
            out(f"  ?? content block {t}")
            block(b)
    u = msg.get("usage") or {}
    if u:
        pending_usage.append(
            f"  [usage in={u.get('input_tokens', 0)} out={u.get('output_tokens', 0)} "
            f"cache_read={u.get('cache_read_input_tokens', 0)} cache_write={u.get('cache_creation_input_tokens', 0)}"
            f"{'  stop=' + str(msg.get('stop_reason')) if msg.get('stop_reason') else ''}]")


def handle_user(e: dict) -> None:
    msg = e.get("message", {})
    content = msg.get("content", [])
    if isinstance(content, str):
        block(content, prefix="< ")
        return
    for b in content:
        if not isinstance(b, dict):
            block(str(b), prefix="< ")
            continue
        if b.get("type") == "tool_result":
            tid = b.get("tool_use_id", "")
            name = tool_names.get(tid, "")
            flag = "  ERROR" if b.get("is_error") else ""
            out(f"{RES}result ({name}) #{tid}{flag}")
            block(content_text(b.get("content")), prefix=RESBODY)
        elif b.get("type") == "text":
            block(b.get("text", ""), prefix="< ")
        else:
            out(f"  ?? user block {b.get('type')}")
            block(b)


def handle_result(e: dict) -> None:
    flush_usage()
    out(f"== result: {e.get('subtype')}  cost ${e.get('total_cost_usd')}  turns {e.get('num_turns')}  "
        f"duration {e.get('duration_ms', 0) / 1000:.0f}s (api {e.get('duration_api_ms', 0) / 1000:.0f}s)  is_error {e.get('is_error')}")
    u = e.get("usage") or {}
    if u:
        out(f"   usage in={u.get('input_tokens', 0)} out={u.get('output_tokens', 0)} "
            f"cache_read={u.get('cache_read_input_tokens', 0)} cache_write={u.get('cache_creation_input_tokens', 0)}")
    for model, mu in (e.get("modelUsage") or {}).items():
        out(f"   model {model}: in={mu.get('inputTokens')} out={mu.get('outputTokens')} "
            f"cache_read={mu.get('cacheReadInputTokens')} cache_write={mu.get('cacheCreationInputTokens')} cost ${mu.get('costUSD')}")
    denials = e.get("permission_denials") or []
    if denials:
        out(f"   permission denials: {len(denials)}")
        for d in denials:
            out(f"     - {d.get('tool_name')} #{d.get('tool_use_id', '')}")
            block(d.get("tool_input"), prefix="         | ")
    if e.get("result"):
        out("   final text:")
        block(e["result"], prefix="   | ")


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
            block({k: v for k, v in e.items() if k not in ("type", "subtype")}, prefix="   | ")
        elif t == "assistant":
            handle_assistant(e)
        elif t == "user":
            handle_user(e)
        elif t == "result":
            handle_result(e)
        else:
            out(f"?? {t}")
            block(e, prefix="   | ")


if __name__ == "__main__":
    main()
