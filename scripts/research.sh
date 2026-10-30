#!/usr/bin/env bash
# Launch one research run. Claude Code does the work: branch, commits, pushes, pull request.
# This script prepares the environment, runs it with retry and session resume, and as a last
# resort pushes any work an interrupted run left behind.
#
# Required env: ANTHROPIC_API_KEY, GH_TOKEN
# Optional env: MAX_BUDGET_USD (default 40), CLAUDE_MODEL (default claude-opus-5-5),
#               RETRY_BUDGET_USD (resume once with this cap after the main cap is hit),
#               MAX_ATTEMPTS (default 6), RETRY_DELAYS (default 120,300,600,900,1800 seconds)
set -euo pipefail
cd "$(dirname "$0")/.."

BUDGET="${MAX_BUDGET_USD:-40}"
MODEL="${CLAUDE_MODEL:-claude-opus-5-5}"
TODAY=$(date -u +%Y-%m-%d)
TRANSCRIPT_DIR="${RUNNER_TEMP:-/tmp}/transcript"
OUT="${TRANSCRIPT_DIR}/run.jsonl"
mkdir -p "${TRANSCRIPT_DIR}"
: > "${OUT}"
echo "== research run $(date -u +%Y-%m-%d) on ${MODEL}, budget \$${BUDGET}"

# An open research pull request is not a reason to skip: the agent reads its branch and continues on it.
open_pr=$(gh api "repos/{owner}/{repo}/pulls?state=open&per_page=50" --jq '[.[] | select(.head.ref | startswith("research/"))] | .[0] | select(. != null) | "#\(.number) \(.head.ref)"' 2>/dev/null || true)
[ -n "${open_pr}" ] && echo "Open research pull request ${open_pr}: the agent will continue on that branch."

# If a previous run pushed a research/* branch but could not open its pull request, open it now and exit.
# The branch's own run report is the body. No research is repeated.
orphan=$(gh api "repos/{owner}/{repo}/branches?per_page=100" --jq '[.[] | select(.name | startswith("research/"))] | sort_by(.name) | last | .name // empty' 2>/dev/null || true)
has_pr=""
[ -n "${orphan}" ] && has_pr=$(gh api "repos/{owner}/{repo}/pulls?state=all&head={owner}:${orphan}&per_page=1" --jq '.[0].number // empty' 2>/dev/null || true)
if [ -n "${orphan}" ] && [ -z "${has_pr}" ] && [ "${orphan}" != "research/${TODAY}" ]; then
  echo "Found research branch ${orphan} without a pull request. Opening one."
  git fetch origin "${orphan}"
  report="state/runs/${orphan#research/}.md"
  body="$(git show "origin/${orphan}:${report}" 2>/dev/null || echo "Run report missing from the branch.")"
  gh api -X POST "repos/{owner}/{repo}/labels" -f name=research-sweep -f color=0E8A16 -f description="Automated knowledge base sweep" >/dev/null 2>&1 || true
  pr_json=$(gh api -X POST "repos/{owner}/{repo}/pulls" -f title="Research run ${orphan#research/}" -f head="${orphan}" -f base=main -f body="${body}")
  pr_num=$(printf '%s' "${pr_json}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["number"])')
  gh api -X POST "repos/{owner}/{repo}/issues/${pr_num}/labels" -f "labels[]=research-sweep" >/dev/null || true
  gh api -X POST "repos/{owner}/{repo}/pulls/${pr_num}/requested_reviewers" -f "reviewers[]=mrcloudchase" >/dev/null || true
  echo "Opened pull request #${pr_num} for ${orphan}. Review and merge it, then trigger the next run."
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

# The stream has no user turn: a headless run's only user input is the prompt. Print it so the log is complete.
sed 's/^/< /' prompts/research.md
echo

# Run with retry and session resume. See scripts/run_claude.py for the policy.
set +e
python3 scripts/run_claude.py \
  --prompt-file prompts/research.md \
  --budget "${BUDGET}" \
  --retry-budget "${RETRY_BUDGET_USD:-0}" \
  --transcript-dir "${TRANSCRIPT_DIR}" \
  --model "${MODEL}" \
  --max-attempts "${MAX_ATTEMPTS:-6}" \
  --delays "${RETRY_DELAYS:-120,300,600,900,1800}"
code=$?
set -e

# Last resort: if the agent left uncommitted or unpushed work, push it so nothing is lost.
branch="research/${TODAY}"
if [ -n "$(git status --porcelain)" ]; then
  echo "== uncommitted work found after the run; committing it as a safety net"
  git checkout -q -B "${branch}" 2>/dev/null || true
  git add -A
  git commit -q -m "Safety net: uncommitted work left by an interrupted run on ${TODAY}" || true
fi
if git rev-parse --verify -q "${branch}" >/dev/null; then
  if ! git diff --quiet "${branch}" "origin/${branch}" 2>/dev/null; then
    echo "== pushing ${branch}"
    git push -u origin "${branch}" || true
  fi
fi

# Render the same transcript as Markdown for the workflow artifact.
{ sed 's/^/< /' prompts/research.md; echo; python3 scripts/stream_filter.py --markdown < "${OUT}"; } > "${TRANSCRIPT_DIR}/transcript.md" || true
echo "== claude exited ${code}; transcript in ${TRANSCRIPT_DIR}"
exit "${code}"
