# jgct-ai

A knowledge base on juvenile granulosa cell tumor (JGCT), built from nothing and kept current by a headless Claude Code run that receives the same prompt once a month, reads this repository as its memory, does the next slice of research, and opens a pull request for human review.

JGCT is a rare ovarian sex cord-stromal tumor of children and young women. What is known about it is scattered across a few hundred papers, conference abstracts, registries, guidelines, and databases. This repository exists to pull that together into one honest, sourced place.

> **Disclaimer:** Nothing here is medical advice. Records describe what sources report. Every AI-written record is a draft until a human has checked it against its source.

## How it works

The repository starts with four things and nothing else:

| File | What it is |
|---|---|
| `prompts/research.md` | The task. Never changes. |
| `CLAUDE.md` | What the project is and how to work. Never changes between runs. |
| `knowledge/schema/record.schema.json` | The shape of a record. |
| `scripts/research.sh` and `.github/workflows/research.yml` | The monthly launcher. |

On the first of each month the workflow runs the launcher. The launcher starts Claude Code with the prompt and a dollar cap. Claude Code reads what is already here, finds and reads sources, writes records, builds the indexes it needs to orient next time, writes whatever tools it needs and keeps them in `tools/`, and then creates a branch, commits, pushes, and opens a pull request requesting review from the maintainer. Main is protected. Merging is the review.

The first run starts from an empty base and builds. Every later run extends. The repository grows like memory.

## Running it by hand

Trigger the `Research run` workflow under Actions with a dollar cap. Or locally:

```bash
export ANTHROPIC_API_KEY=... GH_TOKEN=...
MAX_BUDGET_USD=10 scripts/research.sh
```

## Reviewing a run

Open the pull request. The body is the run's own report: what it added, with its confidence in each record, lowest first; what it could not reach; where the literature disagrees; what it suggests changing. Open sources, fix what is wrong, merge. Suggested changes to `CLAUDE.md` or the schema are yours to make by a normal commit; the run cannot edit them.

## Licenses

Code is MIT. Knowledge base content under `knowledge/` is CC BY 4.0.

## Why

My daughter is seven and is being treated for JGCT. See [awesome-cancer-ai](https://github.com/mrcloudchase/awesome-cancer-ai) for the wider map of AI against cancer.
