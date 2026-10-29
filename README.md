# jgct-ai

A comprehensive, centralized knowledge base on juvenile granulosa cell tumor (JGCT), built and kept current by a headless Claude Code run that receives the same prompt every month, reads this repository as its memory, does the next slice of research, and opens a pull request for human review.

JGCT is a rare ovarian sex cord-stromal tumor that occurs mostly in children and young women. A few hundred papers mention it. The largest molecular study covers 31 tumors. Knowledge about it is scattered across journals, conference abstracts, registries, guidelines, and databases that nobody has pulled together. This repository pulls it together.

> **Disclaimer:** Nothing here is medical advice. Records describe what sources report. The genomic lookups generate hypotheses for discussion with a treating oncologist. Every AI-written record is a draft until a human has checked it against its source.

## How it works

```
monthly cron ──▶ scripts/research.sh ──▶ claude -p prompts/research.md ──▶ edits knowledge/ and state/
                       │                                                            │
                       └── validate, build indexes, commit, open PR ◀───────────────┘
                                                │
                                     human review and merge to main
```

- **The prompt never changes.** It is `prompts/research.md`: research all sources on JGCT, organize them into this knowledge base, take into account what is already here.
- **The repository is the memory.** `state/ledger.json` records every source processed. `state/backlog.json` is the to-do list. `state/runs/` holds each run's report. `knowledge/` is the base itself.
- **The procedure is a skill.** `.claude/skills/research-sweep/SKILL.md` is the step-by-step method. `CLAUDE.md` holds the standing rules. `sources/index.md` says where to look. `sources/credibility.md` says how to rate what it finds.
- **The script owns git.** The model cannot run git or gh. The script validates every record against the schema, rebuilds the generated indexes, commits to a dated branch, and opens one pull request whose body is the run report.
- **Humans own main.** Branch protection requires a pull request and a reviewer. Merging is the review.
- **Starting from empty works.** The first runs work through the backlog until it is empty. Later runs find only what is new. Same prompt, same procedure.

## Layout

| Path | Contents |
|---|---|
| `knowledge/records/` | One YAML record per source, in `knowledge/schema/record.schema.json` |
| `knowledge/INDEX.md`, `ALTERATIONS.md`, `TREATMENTS.md` | Generated from records |
| `knowledge/SUMMARY.md` | Narrative synthesis, rewritten each run, every fact cited to a record |
| `sources/` | Source index and credibility rubric |
| `state/` | Ledger, backlog, run reports |
| `tools/` | Monitor, Europe PMC, genomic lookup, extractor, validator, ledger, index builder |
| `scripts/research.sh` | The sweep runner |
| `prompts/research.md` | The fixed prompt |
| `.claude/` | Settings with the domain allow-list, and the research-sweep skill |

## Running it

**In GitHub Actions.** Add an `ANTHROPIC_API_KEY` repository secret. The `Research sweep` workflow runs on the first of each month and can be triggered by hand with a dollar cap and model choice. The `Literature monitor` workflow runs weekly, costs almost nothing, and opens an issue when something new appears.

**Locally.**

```bash
pip install -r requirements.txt
npm install -g @anthropic-ai/claude-code
export ANTHROPIC_API_KEY=...
DRY_RUN=1 MAX_BUDGET_USD=5 scripts/research.sh   # commits to a local branch, no push, no PR
```

**Tools on their own.** No API key needed for any of these.

```bash
python3 tools/genomics/gct_lookup.py               # public cBioPortal and CIViC snapshot
python3 tools/monitor/monitor.py --dry-run         # new PubMed papers and trials
python3 tools/europepmc.py search '"juvenile granulosa cell tumor"' --preprints
python3 tools/ledger.py status
python3 tools/validate.py && python3 tools/build_index.py
```

## Reviewing a sweep

Open the pull request. The body ranks additions by confidence, lowest first. For each record, open the source and check the fields. Fix anything wrong in the branch. Merge when satisfied. To mark a record as human-verified, set `review_status: reviewed` and `reviewed_by`; a sweep will never edit it again except to link conflicts.

## Licenses

Code is MIT. Knowledge base content under `knowledge/` is CC BY 4.0.

## Why

My daughter is seven and is being treated for JGCT. See [awesome-cancer-ai](https://github.com/mrcloudchase/awesome-cancer-ai) for the wider map of AI against cancer.
