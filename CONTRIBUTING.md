# Contributing

## Reviewing a sweep pull request

This is the most valuable contribution. Each `research/YYYY-MM-DD` pull request is one month of automated research.

1. Read the run report in the PR body. Start with the lowest-confidence additions.
2. For each record, open `source_url` and check every field against the source. Fix mistakes in the branch. Delete anything the source does not say.
3. Check the "Needs index approval" list. If a source is credible, add it to `sources/index.md` and the matching `WebFetch(domain:...)` line in `.claude/settings.json`.
4. Read "Suggested changes" and open issues for any you agree with.
5. Merge.

## Marking a record as verified

Set `review_status: reviewed`, `reviewed_by: <your handle>`, `reviewed_on: <date>`. Sweeps never edit a reviewed record except to add `conflicts_with` or `superseded_by`.

## Adding a source by hand

```bash
python3 tools/ledger.py add pmid 12345678 https://pubmed.ncbi.nlm.nih.gov/12345678/ --tier peer_reviewed
```

The next sweep will process it. To process it now with your own key, run `python3 tools/extract/extract_paper.py 12345678`, review the draft, and open a PR.

## Changing the procedure

`CLAUDE.md`, the skill, the rubric, the schema, and the script are deliberately not editable by the sweep. Change them by pull request like any code.

## Scope

JGCT first. Adult granulosa cell tumor and other sex cord-stromal tumors are in scope when they bear on JGCT biology or treatment. Patient communities and personal stories are never sources.
