#!/usr/bin/env python3
"""Run Claude Code headless with retry and session resume.

Usage: python3 scripts/run_claude.py --prompt-file prompts/research.md --budget 40 --transcript-dir DIR [options]

Each attempt streams Claude Code's stream-json through scripts/stream_filter.py to stdout and appends the raw
events to <transcript-dir>/run.jsonl. After an attempt ends, the result event decides what happens next:

  success                 done, exit 0
  error_max_budget_usd    the cap was hit; resume once with --retry-budget if given, else exit 2
  anything else, or no result event at all (process died, API never answered)
                          wait, then resume the same session with a short continuation prompt

Resuming keeps the agent's full context: the session lives on this machine for the life of the job.
Exit code: 0 success, 2 stopped on budget, 3 attempts exhausted.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

RESUME_PROMPT = (
    "You were interrupted and this session has been resumed. Re-read state/runs/<today>.md and `git log` on your "
    "research branch, confirm the working tree matches the last commit, and carry on from there. Do not redo "
    "committed work. Follow CLAUDE.md, including committing and pushing as you go."
)


def log(msg: str) -> None:
    print(msg, flush=True)


def settings_lists(path: str) -> tuple[list[str], list[str]]:
    d = json.loads(Path(path).read_text())["permissions"]
    return d.get("allow", []), d.get("deny", [])


def attempt(n: int, prompt: str, sid: str | None, budget: float, args, allowed, denied) -> tuple[str, str]:
    """Run one attempt. Returns (session_id, result_subtype)."""
    part = Path(args.transcript_dir) / f"attempt-{n}.jsonl"
    cmd = ["claude", "-p", prompt, "--model", args.model, "--max-budget-usd", str(budget),
           "--settings", args.settings, "--permission-mode", "acceptEdits",
           "--output-format", "stream-json", "--verbose"]
    if sid:
        cmd += ["--resume", sid]
    if allowed:
        cmd += ["--allowedTools", *allowed]
    if denied:
        cmd += ["--disallowedTools", *denied]
    log(f"== attempt {n}" + (f" (resuming session {sid})" if sid else "") + f" · cap ${budget}")
    filt = subprocess.Popen([sys.executable, "scripts/stream_filter.py"], stdin=subprocess.PIPE, text=True)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    new_sid, subtype = sid or "", ""
    with part.open("w") as raw, Path(args.transcript_dir, "run.jsonl").open("a") as combined:
        assert proc.stdout is not None and filt.stdin is not None
        for line in proc.stdout:
            raw.write(line)
            combined.write(line)
            try:
                filt.stdin.write(line)
                filt.stdin.flush()
            except BrokenPipeError:
                pass
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "system" and e.get("subtype") == "init":
                new_sid = e.get("session_id", new_sid)
            elif e.get("type") == "result":
                subtype = e.get("subtype", "")
    code = proc.wait()
    try:
        filt.stdin.close()
    except Exception:
        pass
    filt.wait()
    if not subtype:
        subtype = "no_result_event"
    log(f"== attempt {n} ended: {subtype} (exit {code})")
    return new_sid, subtype


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--retry-budget", type=float, default=0.0, help="resume once with this cap after the main cap is hit")
    ap.add_argument("--transcript-dir", required=True)
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--settings", default=".claude/settings.json")
    ap.add_argument("--max-attempts", type=int, default=6)
    ap.add_argument("--delays", default="120,300,600,900,1800", help="seconds to wait before each retry")
    args = ap.parse_args()

    Path(args.transcript_dir).mkdir(parents=True, exist_ok=True)
    allowed, denied = settings_lists(args.settings)
    delays = [int(x) for x in args.delays.split(",") if x.strip()]
    prompt = Path(args.prompt_file).read_text()
    sid: str | None = None
    budget = args.budget
    budget_retry_used = False

    for n in range(1, args.max_attempts + 1):
        sid, subtype = attempt(n, prompt if n == 1 else RESUME_PROMPT, sid, budget, args, allowed, denied)
        if subtype == "success":
            return 0
        if subtype == "error_max_budget_usd":
            if args.retry_budget > 0 and not budget_retry_used:
                budget_retry_used = True
                budget = args.retry_budget
                log(f"== budget cap reached; resuming once with a fresh cap of ${budget}")
                continue
            log("== budget cap reached; not retrying (set RETRY_BUDGET_USD to allow one more attempt)")
            return 2
        if n == args.max_attempts:
            break
        wait = delays[min(n - 1, len(delays) - 1)] if delays else 60
        log(f"== attempt {n} did not finish ({subtype}); waiting {wait}s before resuming")
        time.sleep(wait)
    log("== attempts exhausted")
    return 3


if __name__ == "__main__":
    sys.exit(main())
