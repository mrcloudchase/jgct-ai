#!/usr/bin/env bash
# Run one research sweep: branch, run Claude Code headless with the fixed prompt, validate, commit, open a PR.
# The model never runs git. This script owns every git and gh call.
#
# Required env: ANTHROPIC_API_KEY, GH_TOKEN (in Actions: github.token)
# Optional env: MAX_BUDGET_USD (default 40), CLAUDE_MODEL (default claude-opus-5-5), DRY_RUN=1 (no push, no PR)
set -euo pipefail

cd "$(dirname "$0")/.."
TODAY=$(date -u +%Y-%m-%d)
BRANCH="research/${TODAY}"
BUDGET="${MAX_BUDGET_USD:-40}"
MODEL="${CLAUDE_MODEL:-claude-opus-5-5}"
REPORT="state/runs/${TODAY}.md"

echo "== research sweep ${TODAY} on ${MODEL}, budget \$${BUDGET}"

# 1. Refuse to run if a previous sweep PR is still open. Two open sweeps would conflict.
if [ "${DRY_RUN:-0}" != "1" ]; then
  open_pr=$(gh pr list --state open --label research-sweep --json number --jq '.[0].number // empty')
  if [ -n "${open_pr}" ]; then
    echo "Sweep PR #${open_pr} is still open. Review and merge it before the next sweep. Exiting."
    gh pr comment "${open_pr}" --body "The scheduled sweep for ${TODAY} was skipped because this pull request is still open."
    exit 0
  fi
fi

# 2. Fresh branch from main.
git fetch origin main
git checkout -B "${BRANCH}" origin/main
git config user.name "jgct-ai research sweep"
git config user.email "actions@users.noreply.github.com"

# 3. Run Claude Code with the fixed prompt. Permissions come from .claude/settings.json.
mkdir -p state/runs
set +e
claude -p "$(cat prompts/research.md)" \
  --model "${MODEL}" \
  --max-budget-usd "${BUDGET}" \
  --permission-mode acceptEdits \
  --output-format json \
  > "state/runs/${TODAY}.claude.json"
claude_exit=$?
set -e
echo "== claude exited ${claude_exit}"
python3 - <<PY
import json, pathlib
p = pathlib.Path("state/runs/${TODAY}.claude.json")
try:
    d = json.loads(p.read_text())
    print("cost_usd:", d.get("total_cost_usd"), "turns:", d.get("num_turns"), "subtype:", d.get("subtype"))
except Exception as e:
    print("could not parse claude output:", e)
PY

# 4. The model must not have touched git.
if ! git diff --quiet HEAD -- .git 2>/dev/null; then :; fi
if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
  echo "Branch moved during the run; the model ran git. Discarding."
  exit 1
fi

# 5. Validate and rebuild. A sweep that fails validation does not become a PR.
python3 tools/validate.py
python3 tools/build_index.py

# 6. Anything to commit?
rm -f "state/runs/${TODAY}.claude.json"
if git diff --quiet && [ -z "$(git status --porcelain)" ]; then
  echo "No changes produced. Nothing to commit."
  exit 0
fi
if [ ! -f "${REPORT}" ]; then
  echo "Run report ${REPORT} missing; writing a minimal one."
  printf '# Research sweep %s\n\nThe run ended without writing its report. Changes below are unreviewed.\n' "${TODAY}" > "${REPORT}"
fi

git add -A
git commit -q -m "Research sweep ${TODAY}"

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "DRY_RUN: committed on ${BRANCH}, not pushing."
  exit 0
fi

# 7. Push and open the PR with the run report as the body.
git push -u origin "${BRANCH}"
gh label create research-sweep --description "Automated knowledge base sweep" --color 0E8A16 2>/dev/null || true
gh pr create \
  --base main \
  --head "${BRANCH}" \
  --title "Research sweep ${TODAY}" \
  --label research-sweep \
  --body-file "${REPORT}"
echo "== done"
