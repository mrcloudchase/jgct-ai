# tools/

All scripts run with `python3` from the repository root. Dependencies: `pyyaml`, `jsonschema` (both preinstalled on the runner).

| Script | Purpose |
|---|---|
| `fulltext.py` | **Full text, the only basis for a record.** `locate <id>...` prints one JSON line per id (PMCID, OA flags, Unpaywall OA URLs). `get <id> [--url URL] [--accept]` tries PMC XML (Europe PMC, then NCBI efetch), then Unpaywall OA PDFs/pages, then the DOI landing page; saves plain text to `state/cache/fulltext/<stem>.txt` and prints `FULLTEXT_SOURCE` (the value for the record's `full_text_source`). PDFs via `pypdf` (`pip install --user pypdf`). Run with `python3 -I`. Known blocks (2026-10-30): Elsevier/linkinghub, Wiley pdfdirect, AACR, OUP, ASCO and the PMC website return 403 or a redirect stub to scripts; Europe PMC fullTextXML returns 500 and NCBI efetch has no body for non-OA PMC articles. |
| `ledger.py` | SQLite ledger (connect timeout 60 s, so several agents can write concurrently) at `state/ledger.sqlite` of every source item (found / processed / needs_full_text / unreachable / skipped). `add`, `set`, `get`, `list`, `stats`, `search`. Never open the DB directly. `search` matches titles and notes only (not authors). |
| `fetch.py` | Structured-API fetcher. `discover-pubmed`, `discover-epmc` load hits into the ledger with a title-keyword priority. `abstract <pmid>...` prints verbatim PubMed metadata and abstract. `fulltext <pmid>` prints open-access full text (Europe PMC, falling back to NCBI PMC efetch) and caches XML in `state/cache/` (gitignored). `cites <pmid> --dir citing|refs` adds citing/cited PMIDs to the ledger. |
| `mkrecord.py` | Library: `write(**fields)` fills defaults (source_url, tier peer_reviewed, retrieved_on today, draft), orders keys as in the schema, validates, and writes `knowledge/records/<source_type>-<source_id>.yaml`. `full_text_source` is required. Use from a scratch script outside the repo. |
| `validate.py` | Schema validation plus project rules: file stem matches source, `conflicts_with` and `overlaps_with` targets exist and are reciprocal, `tumor_site` key present, PMC `full_text_source` matches `pmcid`, the record's ledger item is `processed`. Exit 1 on errors. |
| `check_meta.py` | Cross-checks every pmid record's DOI, year, and title against PubMed esummary. Run after writing records. |
| `openalex_discover.py` | OpenAlex discovery: `fetch '<search>' <out.jsonl> [filter]` pages /works and reconstructs abstracts verbatim from `abstract_inverted_index`; `compare <out.jsonl> .` lists items whose PMID/DOI is not in the ledger. Set `OPENALEX_MAILTO`. Run with `python3 -I`. |
| `cbio_grct_scan.py`, `cbio_grct_detail.py` | cBioPortal public API: scan all studies for samples labelled granulosa (OncoTree GRCT, cancer type text), then pull clinical data and mutations for one study. Output in `state/cache/cbio/`. GENIE instance needs login (HTTP 401). |
| `epmc_supplement_grep.py` | Fetch a congress-supplement full text from Europe PMC (fallback NCBI) and print each abstract-sized unit matching a regex (default JGCT terms), verbatim. For conference abstracts. |
| `build_index.py` | Regenerates `knowledge/INDEX.md` (with tumor site column; automatically splits into `knowledge/index/<study_type>.md` topic indexes once it would pass ~300 lines) and the ledger snapshot section of `sources/INDEX.md` (below the `<!-- LEDGER-SNAPSHOT -->` marker; text above it is hand-maintained). |

## Typical run

```
python3 tools/ledger.py stats
python3 tools/ledger.py list --status found --limit 40
python3 -I tools/fulltext.py get pmid:<n>     # then read state/cache/fulltext/pmid-<n>.txt in full
# write the record via mkrecord.write in a scratch script
python3 tools/ledger.py set pmid:<n> --status processed --record pmid-<n>
python3 tools/validate.py && python3 tools/check_meta.py
python3 tools/build_index.py
```

## Known limitations / ideas

- `fetch.py` priority scoring is keyword-based and noisy; consider using PubMed publication types and MeSH.
- `ledger.py search` cannot search by author; add an `authors` column when next touching discovery.
- Conference abstracts: `epmc_supplement_grep.py` plus OpenAlex; ESPE abstracts are on abstracts.eurospe.org. Non-US trial registries (EU CTR/CTIS, ISRCTN, JRCT, ChiCTR) were probed by curl on 2026-10-30 but there is no fetcher yet.
