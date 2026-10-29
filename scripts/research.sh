#!/usr/bin/env bash
# Launch one research run. Claude Code does the work, including branch, commit, push and pull request.
# This script only prepares the environment and starts it.
#
# Required env: ANTHROPIC_API_KEY, GH_TOKEN
# Optional env: MAX_BUDGET_USD (default 40), CLAUDE_MODEL (default claude-opus-5-5)
set -euo pipefail
cd "$(dirname "$0")/.."

BUDGET="${MAX_BUDGET_USD:-40}"
MODEL="${CLAUDE_MODEL:-claude-opus-5-5}"
echo "== research run $(date -u +%Y-%m-%d) on ${MODEL}, budget \$${BUDGET}"

# Skip if a sweep PR is still open: review it first. Cheaper to check here than to spend a turn on it.
open_pr=$(gh api "repos/{owner}/{repo}/pulls?state=open&per_page=50" --jq '[.[] | select(.labels[].name == "research-sweep")] | .[0].number // empty' 2>/dev/null || true)
if [ -n "${open_pr}" ]; then
  echo "Sweep PR #${open_pr} is still open. Review and merge it before the next run. Exiting."
  gh api -X POST "repos/{owner}/{repo}/issues/${open_pr}/comments" -f body="The scheduled research run for $(date -u +%Y-%m-%d) was skipped because this pull request is still open." >/dev/null || true
  exit 0
fi

git fetch origin main
git checkout -q main
git reset -q --hard origin/main
git config user.name "Claude (jgct-ai research)"
git config user.email "claude-jgct-ai@users.noreply.github.com"
gh api -X POST "repos/{owner}/{repo}/labels" -f name=research-sweep -f color=0E8A16 -f description="Automated knowledge base sweep" >/dev/null 2>&1 || true

# Mark the checkout as trusted so project settings load without the warning. The flags below apply them regardless.
python3 - <<'PY'
import json, os, pathlib
p = pathlib.Path.home() / ".claude.json"
d = json.loads(p.read_text()) if p.exists() else {}
d.setdefault("projects", {}).setdefault(os.getcwd(), {})["hasTrustDialogAccepted"] = True
p.write_text(json.dumps(d))
PY

mapfile -t ALLOWED < <(python3 -c 'import json; [print(r) for r in json.load(open(".claude/settings.json"))["permissions"]["allow"]]')
mapfile -t DENIED  < <(python3 -c 'import json; [print(r) for r in json.load(open(".claude/settings.json"))["permissions"]["deny"]]')
OUT="$(mktemp -t research-XXXXXX.jsonl)"

# Stream every event to the log as it happens; keep the raw stream for the summary.
set +e
set -o pipefail
claude -p "$(cat prompts/research.md)" \
  --model "${MODEL}" \
  --max-budget-usd "${BUDGET}" \
  --settings .claude/settings.json \
  --allowedTools "${ALLOWED[@]}" \
  --disallowedTools "${DENIED[@]}" \
  --permission-mode acceptEdits \
  --output-format stream-json \
  --verbose \
  | tee "${OUT}" \
  | python3 scripts/stream_filter.py
code=$?
set -e

echo "== claude exited ${code}"
exit "${code}"
