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
| `knowledge/README.md` | Narrative synthesis of what the base says about JGCT, in two parts. Rewritten whenever records change. See "The knowledge README" below. |
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
6. Open the branch and the pull request before any research. See the next section.

## Branch, commits, and pull request

You can be interrupted at any moment by an API outage, a spend limit, or a runner timeout. Work so that an interruption loses nothing.

- **Up front.** After writing the plan, create `research/<today>` from `main`, commit the plan, push, and open a draft pull request to `main` titled `Research run <today>`, labeled `research-sweep`, with the plan as its body. If the branch or pull request already exists for today, you are resuming: check it out, read `git log`, and continue from the last commit.
- **As you work.** Commit and push after every batch: a set of records, a tool, an index rebuild. Never leave more than about fifteen minutes of work uncommitted.
- **Commit messages are your memory.** Write each one as if you will forget everything the moment it is written and a stranger must continue from it: what was done, the ledger counts now, and the next step. Example:

  ```
  Add 6 records from the DICER1 citation chase

  Ledger: 78 processed, 1,913 found. All six validated. Next: the three cached
  open-access full texts (pmid-39773640, pmid-37324278, pmid-37796616), then
  rebuild the indexes.
  ```

- **Finishing.** Complete the run report, put it in the pull request body, mark the pull request ready for review, and request `mrcloudchase` as reviewer. Use `gh pr create`, `gh pr edit`, and `gh pr ready`; if one fails, use the REST API through `gh api`. Never merge, never approve, never push to main.
- **When resumed.** The launcher may restart you with a note that you were interrupted. Re-read `state/runs/<today>.md` and `git log`, confirm the working tree matches, and carry on. Do not redo committed work.

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

Tiering decisions already made, so runs stay consistent: a ClinicalTrials.gov or other trial registry entry is `database`. A disease registry's own report, such as a STEP or International Ovarian and Testicular Stromal Tumor Registry paper, is `registry` even when it appears in a peer-reviewed journal. An NCI PDQ summary is `organization`; it is expert-written but not peer-reviewed in the journal sense. Set `tumor_site` on every record: `ovary`, `testis`, `both`, `other`, or null when the source does not say.

Rules that do not bend:

- **Only cite what you fetched this run.** A record is written from text you retrieved. Never from memory of a paper.
- **Copy numbers, never compute them.** "4 of 31" stays `4/31`. A case report is `n_jgct_patients: 1`.
- **Conflicts are recorded, not resolved.** When sources disagree, link them in both records' `conflicts_with` and say so in the summary.
- **Confidence is yours to rate** from 1 to 5. Use 5 only after reading full text. Say in `extraction_method` how you got the text.
- **`review_status` is always `draft` when you write it.** Only a human sets `reviewed`. Never change a reviewed record except to add `conflicts_with` or `superseded_by`.
- **Patient communities, forums, social media, and personal stories are never sources.**
- **No medical advice.** Records say what sources report. The summary synthesizes literature and says so. Nothing here recommends treatment for any person.
- **Retractions stay in the base** with `retracted: true` so nobody re-adds them.

## The knowledge README

`knowledge/README.md` renders when anyone opens the `knowledge/` folder on GitHub. It has exactly two parts, in this order, each under 2,500 words:

1. **For clinicians and researchers.** Technical synthesis: epidemiology, presentation, pathology, molecular biology, staging, treatment, outcomes, prognostic factors, open questions. Every factual sentence cites one or more record IDs in brackets, like `[pmid-40272823]`. Where sources conflict, say so and cite both.
2. **For parents and patients.** The same knowledge in plain language for someone with no medical training who has just heard the words "juvenile granulosa cell tumor." Define every term the first time it is used. Keep sentences short. Every factual sentence still cites record IDs, so a parent can hand the paragraph to a doctor. Say clearly what is well established, what is uncertain, and what is unknown. It must not tell anyone what to do; it points to the questions worth asking a care team. It does not soften bad findings and does not dramatize them.

Both parts open with one sentence saying the text is a synthesis of recorded sources, not medical advice, and that all records are drafts until a human reviews them.

## How to work within a run

You have a dollar cap set by the launcher. Prefer finishing fewer records well over starting many. Process sources in order of value: large series, genomic studies, guidelines, and registry reports first; then reviews; then preprints and abstracts; then case reports, newest first; then organization pages.

Build tools when a task will recur. A fetcher, a ledger query, a validator, an index builder. Put them in `tools/`, document them in `tools/README.md`, and run them with `python3`. Earlier runs' tools are yours to improve.

Keep the ledger and indexes current as you go, not at the end, and commit as you go. A run that stops early must leave a consistent, pushed state.

## How to finish

Start finishing with at least fifteen percent of the budget left. In this order:

1. Validate every record against the schema with your validator. Fix every error.
2. Rebuild `knowledge/INDEX.md` and `sources/INDEX.md`.
3. Rewrite `knowledge/README.md` if any record changed.
4. Complete `state/runs/<today>.md`: plan, what was added and updated with tier and confidence (lowest confidence first), what was unreachable and why, conflicts noted, what remains in the backlog, approximate spend, and suggested changes to this file or the schema that you may not make yourself.
5. Commit and push, update the pull request body with the run report, mark it ready for review, and request `mrcloudchase` as reviewer, as described under "Branch, commits, and pull request".

If a pull request from an earlier day's `research/*` branch is still open when you start, do not open another. Comment on it that this run was skipped and stop.
