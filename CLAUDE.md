# jgct-ai

This repository is a comprehensive, centralized knowledge base on juvenile granulosa cell tumor (JGCT), a rare ovarian sex cord-stromal tumor of children and young women. It is built and maintained by a headless Claude Code run that receives the same prompt every month, reads this repository as its memory, does the next slice of research, and leaves the repository in a state the next run can read. Every change goes to a pull request for human review. You never merge, never push, and never run git.

## Layout

| Path | What it is | You may |
|---|---|---|
| `knowledge/records/*.yaml` | One record per source, in the schema below | create, update drafts |
| `knowledge/schema/record.schema.json` | The record schema | read only |
| `knowledge/INDEX.md`, `knowledge/ALTERATIONS.md`, `knowledge/TREATMENTS.md` | Generated from records by `tools/build_index.py` | regenerate, never hand-edit |
| `knowledge/SUMMARY.md` | Your synthesized narrative overview of JGCT, with citations to record IDs | rewrite each run |
| `sources/index.md` | Every place worth checking, how to query it, its tier | add sources, update notes |
| `sources/credibility.md` | How to rate a source and resolve conflicts | read only |
| `state/ledger.json` | Every source ID you have processed, with status and date | append and update |
| `state/backlog.json` | Source IDs discovered but not yet processed | add and remove |
| `state/runs/YYYY-MM-DD.md` | Your run report, used verbatim as the pull request body | write once per run |
| `tools/` | Scripts that fetch, extract, validate, and build | run with `python3` |
| `.claude/skills/research-sweep/SKILL.md` | The step-by-step procedure for a run | follow it |

## Record schema, in short

Every record is one source: a paper, preprint, conference abstract, guideline, registry report, organization page, or database entry. File name is `<source_type>-<source_id>.yaml`, for example `pmid-35031544.yaml`, `doi-10.1101-2024.11.01.621087.yaml` (slashes become dashes), `abstract-asco-2024-5567.yaml`, `url-<sha1 of url, first 12 chars>.yaml`.

Required fields: `source_id`, `source_type`, `source_tier`, `source_url`, `retrieved_on`, `title`, `year`, `study_type`, `key_findings`, `relevance_to_jgct`, `review_status`, `confidence`.

`review_status` is always `draft` when you write it. Only a human sets `reviewed`. Never change a record whose `review_status` is `reviewed` except to add a `superseded_by` or `conflicts_with` note.

`confidence` is your own 1 to 5 rating of how sure you are the record faithfully reflects the source. Use 5 only when you read the full text. Set `extraction_method` on every record: `full_text`, `verbatim_abstract` (from `tools/europepmc.py abstract` or the extractor), `model_assisted_fetch` (WebFetch paraphrase, cap confidence at 3), or `manual`.

Prefer verbatim text. WebFetch returns a model's paraphrase of a page, not the page. For PubMed items always use `tools/europepmc.py abstract` first and WebFetch only for sources that have no structured API.

The full schema is `knowledge/schema/record.schema.json`. The validator enforces it.

## Rules

1. **Read before you research.** Start with `python3 tools/ledger.py status` and `python3 tools/ledger.py next --limit 30`, then `knowledge/INDEX.md` and the last two files in `state/runs/`. Never open `state/ledger.json` or `state/backlog.json` directly; they are tens of thousands of tokens and the ledger tool answers every question about them. Do not re-process a source whose ledger status is `done` unless a newer version exists.
2. **Only cite what you fetched.** Every claim in a record traces to text you actually retrieved. If you could not fetch a source, ledger it as `unreachable` with the reason. Never write a record from memory of a paper.
3. **Source tiers are not optional.** Rate every record per `sources/credibility.md`. A conference abstract is `conference_abstract`, not `peer_reviewed`, even if it later became a paper.
4. **Conflicts are recorded, not resolved.** If two sources disagree, note it in both records' `conflicts_with` and say so in `SUMMARY.md`. Do not pick a winner.
5. **Stay in the source index.** Fetch only domains listed in `sources/index.md`. When you find a credible source elsewhere, add it to `state/backlog.json` with `"needs_index_approval": true` and list it in the run report. The permission settings will block fetches outside the index anyway.
6. **Never scrape patient communities or personal stories.** Forums, social media, and support groups are out of scope.
7. **No medical advice.** Records describe what sources report. `SUMMARY.md` synthesizes the literature and says so. Nothing in this repository recommends treatment for any person.
8. **Budget awareness.** You have a turn and dollar cap. Prefer finishing fewer records well over starting many. Write the ledger and run report before you are out of budget, not after.
9. **No git.** The surrounding script commits and opens the pull request. If you run `git`, the run is discarded.
10. **Determinism over cleverness.** Same prompt, same procedure, every run. The repository is your memory. If something about the procedure should change, say so in the run report under "Suggested changes" rather than improvising.

## Tools you can run

```
python3 tools/monitor/monitor.py --dry-run     # new PubMed papers and trials since last state
python3 tools/genomics/gct_lookup.py           # refresh public cBioPortal and CIViC data for granulosa cell tumor
python3 tools/extract/extract_paper.py <pmid>  # draft a record from a PubMed abstract via Claude
python3 tools/europepmc.py search "<query>"    # Europe PMC search, broader than PubMed, includes preprints; default limit 1000
python3 tools/europepmc.py abstract <pmid>...  # verbatim abstracts in batches; prefer this over WebFetch of PubMed pages
python3 tools/europepmc.py fulltext <id>       # open access full text when available
python3 tools/validate.py                      # validate every record against the schema; must pass before you finish
python3 tools/build_index.py                   # regenerate INDEX.md, ALTERATIONS.md, TREATMENTS.md
python3 tools/ledger.py status                 # counts by status; run this first
python3 tools/ledger.py next --limit N         # highest-priority pending items with titles
python3 tools/ledger.py triage                 # batch-fetch titles and publication types from PubMed, set priorities
python3 tools/ledger.py add|start|done|unreachable|skip ...   # update one item; never edit the JSON by hand
```

For sources without a tool, use WebFetch on the URL and write the record by hand with `tools/ledger.py` to log it.

## Finishing a run

In this order, always:

1. `python3 tools/validate.py` and fix every error.
2. `python3 tools/build_index.py`.
3. Update `knowledge/SUMMARY.md` if any record changed.
4. Write `state/runs/<today>.md` using the template in the skill. It is the pull request body.
