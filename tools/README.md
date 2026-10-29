# tools/

All scripts run with `python3` from the repository root. Dependencies: `pyyaml`, `jsonschema` (both preinstalled on the runner).

| Script | Purpose |
|---|---|
| `ledger.py` | SQLite ledger at `state/ledger.sqlite` of every source item (found / processed / unreachable / skipped). `add`, `set`, `get`, `list`, `stats`, `search`. Never open the DB directly. `search` matches titles and notes only (not authors). |
| `fetch.py` | Structured-API fetcher. `discover-pubmed`, `discover-epmc` load hits into the ledger with a title-keyword priority. `abstract <pmid>...` prints verbatim PubMed metadata and abstract. `fulltext <pmid>` prints open-access full text (Europe PMC, falling back to NCBI PMC efetch) and caches XML in `state/cache/` (gitignored). `cites <pmid> --dir citing|refs` adds citing/cited PMIDs to the ledger. |
| `mkrecord.py` | Library: `rec(...)` writes a `pmid-<id>.yaml` record; `rec_url(...)` writes a `url-<sha1[:12]>.yaml` record for non-PMID sources. Sets `retrieved_on` to today and `review_status: draft`. Typical use: write a throwaway batch script outside the repo that imports it. |
| `validate.py` | Schema validation plus project rules: file stem matches source, confidence ceilings per tier (abstract-only peer_reviewed <= 3, model_assisted_fetch <= 3, etc.), confidence 5 requires full_text, `conflicts_with` targets exist and are reciprocal. Exit 1 on errors. |
| `check_meta.py` | Cross-checks every pmid record's DOI, year, and title against PubMed esummary. Run after writing records. |
| `build_index.py` | Regenerates `knowledge/INDEX.md` and the ledger snapshot section of `sources/INDEX.md` (below the `<!-- LEDGER-SNAPSHOT -->` marker; text above it is hand-maintained). |

## Typical run

```
python3 tools/ledger.py stats
python3 tools/ledger.py list --status found --limit 40
python3 tools/fetch.py abstract <pmids>
python3 tools/fetch.py fulltext <pmid>
# write records via mkrecord.rec in a scratch script
python3 tools/ledger.py set pmid:<n> --status processed --record pmid-<n>
python3 tools/validate.py && python3 tools/check_meta.py
python3 tools/build_index.py
```

## Known limitations / ideas

- `fetch.py` priority scoring is keyword-based and noisy; consider using PubMed publication types and MeSH.
- `ledger.py search` cannot search by author; add an `authors` column when next touching discovery.
- No conference-abstract or non-US trial-registry fetchers yet.
