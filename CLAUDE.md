# jgct-ai

## What this project is

This repository is a knowledge base on juvenile granulosa cell tumor (JGCT), a rare ovarian sex cord-stromal tumor of children and young women. It is built and maintained by you, running headless once a month with the same prompt every time. The repository is your memory. Each run reads the whole repository, then looks for everything else that exists about JGCT, reads all of it in full, and updates the repository. The first run starts from an empty base. Run two hundred maintains a full one. There is no special first-run mode; an empty repository simply means discovery starts at zero.

You manage the schema, the knowledge base, and the indexes yourself. The only fixed things are the prompt, this file, the launcher, the workflow, and the permissions.

Everything you produce goes to a pull request that a human reviews and merges. You never merge. Main is protected and requires an approving review from the maintainer, mrcloudchase.

## Who this is for

A parent whose seven-year-old daughter is being treated for JGCT, the clinicians treating her, and every family and researcher who comes after. The base should be the most complete, best-sourced, most honest single place to learn what is known about JGCT. Honest means every claim traces to a source you actually read, every source carries its credibility tier, and disagreements in the literature are recorded rather than resolved.

## Layout

You own everything below except the files marked fixed. Create what does not exist yet.

| Path | Purpose |
|---|---|
| `prompts/research.md` | The prompt you receive. Fixed. |
| `CLAUDE.md` | This file. Fixed. |
| `knowledge/schema/record.schema.json` | The record schema. Yours to evolve; see "Schema" below. Every record validates against the current schema. |
| `knowledge/records/<source_type>-<source_id>.yaml` | One record per source. |
| `knowledge/INDEX.md` | Index of the knowledge base: one line per record. When it passes about 300 lines, split it into topic indexes under `knowledge/index/` and make `INDEX.md` an index of those. |
| `knowledge/README.md` | Narrative synthesis of what the base says about JGCT, in two parts. Rewritten whenever records change. See "The knowledge README" below. |
| `sources/INDEX.md` | Index of every source: where it is, how to query it, its tier, when you last checked it, what you found. This is yours to build and keep the best it can be. |
| `sources/PENDING_FULL_TEXT.md` | Every source you know about but have not read in full, with its verbatim abstract if one exists, why the full text was not obtained, and when you last tried. Regenerated from the ledger. |
| `state/` | Your ledger of every source item found, processed, unreachable, or skipped, in whatever format you choose, plus `state/runs/<date>.md`, one run report per run. |
| `tools/` | Scripts you write to fetch, extract, validate, and index. Reuse and improve what earlier runs left; do not rewrite from scratch. Keep `tools/README.md` current so the next run knows what exists. |
| `scripts/`, `.github/`, `.claude/` | The launcher, workflow, and permissions. Fixed. |

## How to orient at the start of a run

Read the repository in full before anything else. Every run, every file: the run reports, the schema, every record, every index, the knowledge README, the source index, the pending list, the tools and their README. Query the ledger through your tool rather than opening a binary file, but read everything it tells you. You are allowed to skim nothing. If the repository has grown past what fits in your context, read it in parts, with sub-agents if needed, but every file is read every run. Only when you know everything the repository already holds do you go looking for what it does not.

Then:

1. Write the plan for this run as the first section of `state/runs/<today>.md`. If the run dies, the report still says what was intended.
2. Open the branch and the pull request before any research. See the next section.

## Schema

The schema is yours. Change it when the knowledge demands it: a field that keeps ending up in `notes`, a study type that does not fit, a structure a new kind of source needs. Every change follows the same procedure in the same run: update the schema, update the validator, migrate every existing record so the whole base validates, rebuild the indexes, and explain the change and the reason in the run report. A run never leaves records on two versions of the schema.

Whatever shape the schema takes, every record must always carry: what the source is and where it lives, where its full text was read from, what it says, how it relates to JGCT, which records it conflicts with, and a `review_status` that you only ever set to `draft`. There is no field for your confidence and there never will be. The human reviewer judges.

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

Prefer structured APIs over web pages, and verbatim text over paraphrase. Note that the built-in web fetch returns a summary of a page, not the page; for anything you will cite, get the actual text through an API or a script. Chase citations in both directions from the strongest records.

**Read everything in full.** A record exists only for a source whose full text you read start to finish this run: the whole paper, the whole guideline, the whole registry report, the whole abstract when the source is itself an abstract. Never write a record from an abstract of a paper, a summary, a citing paper's description, or memory. Get full text through Europe PMC, PubMed Central, Unpaywall, publisher open-access pages, author manuscripts, and preprint versions, in that order of preference. When none of those yields the full text, the source goes in `sources/PENDING_FULL_TEXT.md` with its abstract and the reason, and you try again on every later run, because papers become open access over time. Record what you read it from in `full_text_source`.

## How to describe sources

Every record carries a `source_tier`. It says what kind of source this is, so a reader can weigh it. It is a description, not a score. Pick the lowest tier that honestly describes the source.

| Tier | Qualifies |
|---|---|
| `peer_reviewed` | Journal article with editorial peer review |
| `guideline` | Professional society or consortium recommendations |
| `registry` | Disease registry or consortium report |
| `database` | Curated clinical or genomic database entry |
| `preprint` | Preprint server |
| `conference_abstract` | Meeting abstract, read in full |
| `organization` | Foundation, hospital, or rare disease organization page |
| `other` | Credible but unclassified |

You do not rate your own confidence in a record, and no field exists for it. The human reviewer judges. Your job is to make judging easy: cite exactly what you read, copy numbers verbatim, keep `notes` factual, and link conflicts.

Tiering decisions already made, so runs stay consistent: a ClinicalTrials.gov or other trial registry entry is `database`. A disease registry's own report, such as a STEP or International Ovarian and Testicular Stromal Tumor Registry paper, is `registry` even when it appears in a peer-reviewed journal. An NCI PDQ summary is `organization`; it is expert-written but not peer-reviewed in the journal sense. Set `tumor_site` on every record: `ovary`, `testis`, `both`, `other`, or null when the source does not say.

Rules that do not bend:

- **Only cite what you read in full this run.** A record is written from the complete text you retrieved. Never from an abstract, a summary, or memory.
- **Copy numbers, never compute them.** "4 of 31" stays `4/31`. A case report is `n_jgct_patients: 1`.
- **Conflicts are recorded, not resolved.** When sources disagree, link them in both records' `conflicts_with` and say so in the summary.
- **`review_status` is always `draft` when you write it.** Only a human sets `reviewed`. Never change a reviewed record except to add `conflicts_with` or `superseded_by`.
- **Patient communities, forums, social media, and personal stories are never sources.**
- **No medical advice.** Records say what sources report. The summary synthesizes literature and says so. Nothing here recommends treatment for any person.
- **Retractions stay in the base** with `retracted: true` so nobody re-adds them.

## The knowledge README

`knowledge/README.md` renders when anyone opens the `knowledge/` folder on GitHub. It has exactly two parts, in this order, each under 2,500 words:

1. **For clinicians and researchers.** Technical synthesis: epidemiology, presentation, pathology, molecular biology, staging, treatment, outcomes, prognostic factors, open questions. Every factual sentence cites one or more record IDs in brackets, like `[pmid-40272823]`. Where sources conflict, say so and cite both.
2. **For parents and patients.** The same knowledge in plain language for someone with no medical training who has just heard the words "juvenile granulosa cell tumor." Define every term the first time it is used. Keep sentences short. Every factual sentence still cites record IDs, so a parent can hand the paragraph to a doctor. Say clearly what is well established, what is uncertain, and what is unknown. It must not tell anyone what to do; it points to the questions worth asking a care team. It does not soften bad findings and does not dramatize them.

Both parts open with one sentence saying the text is a synthesis of sources read in full, not medical advice, and that all records are drafts until a human reviews them.

## How to work within a run

You have a dollar cap set by the launcher. Prefer finishing fewer records well over starting many. Process sources in order of value: large series, genomic studies, guidelines, and registry reports first; then reviews; then preprints and abstracts; then case reports, newest first; then organization pages.

Build tools when a task will recur. A fetcher, a ledger query, a validator, an index builder. Put them in `tools/`, document them in `tools/README.md`, and run them with `python3`. Earlier runs' tools are yours to improve.

Keep the ledger and indexes current as you go, not at the end, and commit as you go. A run that stops early must leave a consistent, pushed state.

**Migration.** If records exist that were written from abstracts, or that carry fields the schema no longer has, bring the base into line before adding new records: re-read each such source in full and rewrite its record with `full_text_source`, or, when the full text cannot be obtained, remove the record, keep its abstract in the ledger, and list it in `sources/PENDING_FULL_TEXT.md`. Update your validator and index builder to the current schema first. Say in the run report what was promoted and what was moved to pending.

## How to finish

Start finishing with at least fifteen percent of the budget left. In this order:

1. Validate every record against the schema with your validator. Fix every error.
2. Rebuild `knowledge/INDEX.md`, `sources/INDEX.md`, and `sources/PENDING_FULL_TEXT.md`.
3. Rewrite `knowledge/README.md` if any record changed.
4. Complete `state/runs/<today>.md`: plan, what was added and updated with tier and full-text source, what could not be read in full and why, conflicts noted, any schema change and why, what remains in the backlog, approximate spend, and suggested changes to this file that you may not make yourself.
5. Commit and push, update the pull request body with the run report, mark it ready for review, and request `mrcloudchase` as reviewer, as described under "Branch, commits, and pull request".

If a pull request from an earlier day's `research/*` branch is still open when you start, do not open another. Comment on it that this run was skipped and stop.
