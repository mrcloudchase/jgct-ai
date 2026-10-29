# jgct-ai

## What this project is

This repository is a knowledge base on juvenile granulosa cell tumor (JGCT), a rare ovarian sex cord-stromal tumor of children and young women. It is built and maintained by you, running headless once a month with the same prompt every time. The repository is your memory. Each run reads what earlier runs left, does the next slice of work, and leaves the repository in a state the next run can read. The first run starts from an empty base. Run two hundred maintains a full one. There is no special first-run mode; an empty ledger simply means discovery starts at zero.

Everything you produce goes to a pull request that a human reviews and merges. You never merge. Main is protected and requires an approving review from the maintainer, mrcloudchase.

## Who this is for

A parent whose seven-year-old daughter is being treated for JGCT, the clinicians treating her, and every family and researcher who comes after. The base should be the most complete, best-sourced, most honest single place to learn what is known about JGCT. Honest means every claim traces to a source you actually read, every source carries its credibility tier, and disagreements in the literature are recorded rather than resolved.

## Layout

You own everything below except the files marked fixed. Create what does not exist yet.

| Path | Purpose |
|---|---|
| `prompts/research.md` | The prompt you receive. Fixed. |
| `CLAUDE.md` | This file. Fixed. |
| `knowledge/schema/record.schema.json` | The record schema. Fixed. Every record validates against it. |
| `knowledge/records/<source_type>-<source_id>.yaml` | One record per source. |
| `knowledge/INDEX.md` | Index of the knowledge base: one line per record. When it passes about 300 lines, split it into topic indexes under `knowledge/index/` and make `INDEX.md` an index of those. |
| `knowledge/SUMMARY.md` | Narrative synthesis of what the base says about JGCT, under 2,500 words, every factual sentence citing record IDs in brackets. Rewritten whenever records change. |
| `sources/INDEX.md` | Index of every source: where it is, how to query it, its tier, when you last checked it, what you found. This is yours to build and keep the best it can be. |
| `state/` | Your ledger of every source item found, processed, unreachable, or skipped, in whatever format you choose, plus `state/runs/<date>.md`, one run report per run. |
| `tools/` | Scripts you write to fetch, extract, validate, and index. Reuse and improve what earlier runs left; do not rewrite from scratch. Keep `tools/README.md` current so the next run knows what exists. |
| `scripts/`, `.github/`, `.claude/` | The launcher, workflow, and permissions. Fixed. |

## How to orient at the start of a run

1. Read the two most recent files in `state/runs/`. They say what the last run did, what it left unfinished, and what it suggested.
2. Read `knowledge/INDEX.md` and `sources/INDEX.md`. Never read every record. Open a record only when you need to update or cross-reference it.
3. Query your ledger with the tool you wrote for it. Never open the raw ledger file; it will not fit in context once the base is large.
4. Read `tools/README.md` and reuse the tools.
5. Write the plan for this run as the first section of `state/runs/<today>.md` before doing anything else. If the run dies, the report still says what was intended.

## How to find sources

JGCT knowledge is scattered. PubMed holds a few hundred papers. Europe PMC, OpenAlex, and Semantic Scholar hold more, including preprints and citations. Conference abstracts from oncology, gynecologic oncology, pediatric oncology, pathology, and pediatric endocrinology meetings are often never published as papers. Disease registries and consortia publish reports. Guideline bodies publish management recommendations. Genomic databases hold sequenced samples. Rare disease organizations maintain summaries. Trial registries in several countries list studies. Non-English literature exists.

Prefer structured APIs over web pages, and verbatim text over paraphrase. Note that the built-in web fetch returns a summary of a page, not the page; for anything you will cite, get the actual text through an API or a script. Chase citations in both directions from the strongest records. When a source is behind a paywall, record it as unreachable with the reason rather than guessing its contents.

## How to judge sources

Every record carries a `source_tier`. Pick the lowest tier that honestly describes the source.

| Tier | Qualifies | Confidence ceiling |
|---|---|---|
| `peer_reviewed` | Journal article with editorial peer review | 5 with full text, 3 with abstract only |
| `guideline` | Professional society or consortium recommendations | 5 |
| `registry` | Disease registry or consortium report | 4 |
| `database` | Curated clinical or genomic database entry | 4 |
| `preprint` | Preprint server | 3 |
| `conference_abstract` | Meeting abstract | 3 |
| `organization` | Foundation, hospital, or rare disease organization page | 2 |
| `other` | Credible but unclassified | 2 |

Rules that do not bend:

- **Only cite what you fetched this run.** A record is written from text you retrieved. Never from memory of a paper.
- **Copy numbers, never compute them.** "4 of 31" stays `4/31`. A case report is `n_jgct_patients: 1`.
- **Conflicts are recorded, not resolved.** When sources disagree, link them in both records' `conflicts_with` and say so in the summary.
- **Confidence is yours to rate** from 1 to 5. Use 5 only after reading full text. Say in `extraction_method` how you got the text.
- **`review_status` is always `draft` when you write it.** Only a human sets `reviewed`. Never change a reviewed record except to add `conflicts_with` or `superseded_by`.
- **Patient communities, forums, social media, and personal stories are never sources.**
- **No medical advice.** Records say what sources report. The summary synthesizes literature and says so. Nothing here recommends treatment for any person.
- **Retractions stay in the base** with `retracted: true` so nobody re-adds them.

## How to work within a run

You have a dollar cap set by the launcher. Prefer finishing fewer records well over starting many. Process sources in order of value: large series, genomic studies, guidelines, and registry reports first; then reviews; then preprints and abstracts; then case reports, newest first; then organization pages.

Build tools when a task will recur. A fetcher, a ledger query, a validator, an index builder. Put them in `tools/`, document them in `tools/README.md`, and run them with `python3`. Earlier runs' tools are yours to improve.

Keep the ledger and indexes current as you go, not at the end. A run that stops early must leave a consistent state.

## How to finish

Start finishing with at least fifteen percent of the budget left. In this order:

1. Validate every record against the schema with your validator. Fix every error.
2. Rebuild `knowledge/INDEX.md` and `sources/INDEX.md`.
3. Rewrite `knowledge/SUMMARY.md` if any record changed.
4. Complete `state/runs/<today>.md`: plan, what was added and updated with tier and confidence (lowest confidence first), what was unreachable and why, conflicts noted, what remains in the backlog, approximate spend, and suggested changes to this file or the schema that you may not make yourself.
5. Create a branch named `research/<today>`, commit everything with a clear message, push it, and open a pull request to `main` with the run report as the body, the label `research-sweep`, and `mrcloudchase` requested as reviewer. Use `gh pr create`; if it fails, use the REST API through `gh api`. Never merge, never approve, never push to main.

If a sweep pull request is already open when you start, do not open another. Comment on it that this run was skipped and stop.
