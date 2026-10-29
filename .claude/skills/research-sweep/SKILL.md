---
name: research-sweep
description: The fixed monthly procedure for building and updating the JGCT knowledge base. Follow it in order every run.
---

# Research sweep

You run this procedure every time. Same steps, same order. The repository is your memory; the ledger is your to-do list.

## 0. Orient (read only, no fetching)

1. `python3 tools/ledger.py status` for counts, then `python3 tools/ledger.py triage` so every PubMed item has a title and a priority, then `python3 tools/ledger.py next --limit 30` to see what is up. Do not open the raw JSON files; they are far too large to read.
2. Read `knowledge/INDEX.md` and the two most recent files in `state/runs/`. Note what the last run left unfinished and any "Suggested changes".
3. Read `sources/index.md`. Note any source marked `verify on first run` that has not been verified.
4. Decide the plan for this run and write it as the first section of `state/runs/<today>.md` before doing anything else. If the run dies, the report still says what was intended.

## 1. Discover (cheap, structured APIs first)

Goal: make the backlog complete, not to process it yet.

1. `python3 tools/monitor/monitor.py --dry-run` for new PubMed papers and ClinicalTrials.gov trials.
2. `python3 tools/europepmc.py search '"juvenile granulosa cell tumor" OR "juvenile granulosa cell tumour"'` and the same with `SRC:PPR` for preprints.
3. For every source in `sources/index.md` of type `sweep`, follow its "how to query" note. Society abstract sites: search their abstract archive for the phrase. Registries and organizations: fetch the listed pages and look for publications or updates newer than the ledger's last visit.
4. Citation chasing: for each record with `confidence >= 4` added in the last run, use Europe PMC's citations endpoint to find papers that cite it. Add unseen ones to the backlog.
5. Add every new source ID to `state/backlog.json` with `python3 tools/ledger.py add <source_type> <source_id> <url> [--tier T] [--needs-index-approval]`.

Off-index domains: do not fetch. Add to the backlog with `--needs-index-approval` and move on.

## 2. Process (the expensive part)

Work the backlog in the order `tools/ledger.py next` gives, and stop when the validator-safe budget is reached (see step 4). Triage sets priority 1 for reviews, cohorts, registries, guidelines and genomic studies, 2 for other papers, 3 for preprints, abstracts and database entries, 4 for case reports, 5 for organization pages. Within a priority, newest first.

For each item:

1. `python3 tools/ledger.py start <source_id>`.
2. Fetch the source. PubMed items: `python3 tools/extract/extract_paper.py <pmid>` writes a draft from the abstract; then try `python3 tools/europepmc.py fulltext <pmid>` and, if full text exists, read it and improve the record. Set `confidence` to 5 only if you read the full text. Non-PubMed items: WebFetch, then write the YAML by hand per the schema.
3. Cross-reference: if the record reports a gene alteration, check `knowledge/ALTERATIONS.md` for existing entries and set `conflicts_with` where numbers disagree materially.
4. `python3 tools/ledger.py done <source_id> --record <file>` or `python3 tools/ledger.py unreachable <source_id> --reason "<why>"`.

Never write a record for a source you did not retrieve in this run.

## 3. Refresh generated data

Once per run, not per item:

1. `python3 tools/genomics/gct_lookup.py` to refresh the public cBioPortal and CIViC snapshot.
2. If the snapshot changed materially (new samples, new pediatric cases), note it in the run report.

## 4. Finish (budget-safe: start this with at least 15 percent of budget left)

1. `python3 tools/validate.py`. Fix every error. A run that fails validation is rejected by the script.
2. `python3 tools/build_index.py`.
3. Rewrite `knowledge/SUMMARY.md`: a narrative overview of JGCT biology, presentation, diagnosis, staging, treatment, outcomes, and open questions. Every sentence that states a fact cites one or more record IDs in brackets, like `[pmid-35031544]`. Where sources conflict, say so and cite both. Keep it under 2,000 words.
4. Complete `state/runs/<today>.md` with the template below.

## Run report template

```markdown
# Research sweep <YYYY-MM-DD>

## Plan
<what this run intended to do, written at the start>

## Added (<n> records)
| Record | Tier | Confidence | One line |
|---|---|---|---|
<rows, lowest confidence first so the reviewer sees the shaky ones at the top>

## Updated (<n> records)
<same table>

## Unreachable (<n>)
| Source | Reason |

## Needs index approval (<n>)
| URL | Why it looks credible | Suggested tier |

## Conflicts noted
<each conflict in one sentence with both record IDs>

## Backlog remaining
pending <n>, by priority: <counts>

## Budget
Approximate spend and whether the run stopped on budget or on an empty backlog.

## Suggested changes
<anything about the procedure, schema, index, or rubric that should change, as proposals; do not change them yourself>
```
