# Contributing

## Reviewing a record

Every file in `knowledge/papers/` has a `review_status` of `draft` or `reviewed`. Drafts were produced by Claude from the PubMed abstract and may be wrong.

1. Open the paper by its DOI or PubMed ID.
2. Check every field in the YAML against the paper. Fix anything wrong. Remove anything the paper does not actually say.
3. Set `review_status: reviewed` and put your GitHub handle in `reviewed_by`.
4. Run `python knowledge/build_index.py` and commit the regenerated `INDEX.md` and `ALTERATIONS.md`.
5. Open a pull request titled `Review PMID <id>`.

## Adding a paper

```bash
python extract/extract_paper.py <pmid>
```

This writes `knowledge/papers/<pmid>.yaml` as a draft. Review it as above before or after opening the pull request. Papers with no abstract on PubMed need the record written by hand from the full text.

## Monitor and lookup scripts

Keep them dependency-light and runnable without an API key. Summaries are the only thing that should require `ANTHROPIC_API_KEY`.

## Scope

JGCT first. Adult granulosa cell tumor and other sex cord-stromal tumors are in scope when a paper or sample set bears on JGCT biology or treatment.
