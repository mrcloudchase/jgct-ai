#!/usr/bin/env python3
"""Turn Claude Code's stream-json output into readable log lines as they arrive.

Reads JSON lines on stdin, prints assistant text, tool calls, and tool result sizes to stdout,
and prints a cost and turn summary when the final result event arrives. Lines that are not JSON pass through.
"""
import json
import sys


def main() -> None:
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            print(line, flush=True)
            continue
        t = e.get("type")
        if t == "assistant":
            for b in e.get("message", {}).get("content", []):
                if b.get("type") == "text" and b["text"].strip():
                    print(b["text"].strip(), flush=True)
                elif b.get("type") == "tool_use":
                    inp = b.get("input", {})
                    if b["name"] == "Bash":
                        detail = inp.get("command", "")
                    elif b["name"] in ("Read", "Write", "Edit"):
                        detail = inp.get("file_path", "")
                    elif b["name"] in ("WebFetch", "WebSearch"):
                        detail = inp.get("url") or inp.get("query", "")
                    else:
                        detail = json.dumps(inp)
                    print(f"> {b['name']}: {str(detail)[:200]}", flush=True)
        elif t == "user":
            for b in e.get("message", {}).get("content", []):
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    content = b.get("content")
                    size = len(content) if isinstance(content, str) else sum(len(c.get("text", "")) for c in content or [] if isinstance(c, dict))
                    flag = " (error)" if b.get("is_error") else ""
                    print(f"  < result {size} chars{flag}", flush=True)
        elif t == "result":
            print(f"== result: {e.get('subtype')}, cost ${e.get('total_cost_usd')}, turns {e.get('num_turns')}", flush=True)
            for d in (e.get("permission_denials") or [])[:10]:
                print(f"  denied: {d.get('tool_name')} {str(d.get('tool_input'))[:140]}", flush=True)
        elif t == "system" and e.get("subtype") == "init":
            print(f"== session {e.get('session_id')} model {e.get('model')}", flush=True)


if __name__ == "__main__":
    main()
