# jgct-ai

Open knowledge base, literature monitor and genomic lookup tools for juvenile granulosa cell tumor (JGCT), built with AI.

JGCT is a rare ovarian sex cord-stromal tumor that occurs mostly in children and young women. Fewer than 450 papers mention it. The largest molecular study covers 31 tumors. There is no public dataset to train a model on, so this project does the thing AI is actually good at today for a rare disease: reading everything, structuring it, and keeping watch.

> **Disclaimer:** Nothing in this repository is medical advice. The genomic lookups generate hypotheses for discussion with a treating oncologist, not treatment recommendations. Every AI-extracted record is marked as a draft until a human has checked it against the source paper.

## What is here

| Part | Directory | What it does |
|---|---|---|
| Knowledge base | `knowledge/` | One YAML record per paper, in a fixed schema, with a review status. `build_index.py` renders them into `INDEX.md` and `ALTERATIONS.md`. |
| Literature monitor | `monitor/` | Weekly GitHub Action that queries PubMed and ClinicalTrials.gov for new JGCT papers and trials, summarizes them with Claude, and opens an issue. |
| Genomic lookup | `genomics/` | Pulls every granulosa cell tumor sample in public cBioPortal studies, separates adult-type from likely juvenile-type using the FOXL2 C134W marker, and annotates recurrent JGCT genes against CIViC. |
| Extractor | `extract/` | Turns a PubMed ID into a draft knowledge record using Claude structured outputs. |

## Quick start

```bash
pip install -r requirements.txt

# Genomic lookup: no API key needed, hits public cBioPortal and CIViC
python genomics/gct_lookup.py

# Literature monitor, dry run (no issue, no summaries unless ANTHROPIC_API_KEY is set)
python monitor/monitor.py --dry-run --backfill 5

# Draft a knowledge record for one paper (needs ANTHROPIC_API_KEY)
python extract/extract_paper.py 35031544

# Rebuild the index after adding or reviewing records
python knowledge/build_index.py
```

## Known JGCT biology, in one paragraph

Unlike adult granulosa cell tumor, which carries the FOXL2 p.C134W mutation in about 97 percent of cases, JGCT does not. Reported recurrent alterations include KMT2C truncating mutations, SWI/SNF chromatin remodeling genes, hotspot AKT1 in-frame duplications, DICER1 mutations, TERT rearrangements with CLPTM1L or DROSHA in about 13 percent, GNAS hotspot mutations, and IDH1 R132 in the setting of Ollier disease or Maffucci syndrome. Genome-wide methylation cleanly separates juvenile from adult tumors. See `knowledge/ALTERATIONS.md` for the sourced table.

## Contributing

Reviewing AI-drafted records against their source papers is the most valuable contribution. See `CONTRIBUTING.md`.

## Licenses

Code is MIT. Knowledge base content under `knowledge/` is CC BY 4.0. Source abstracts remain the property of their publishers and are not redistributed beyond what PubMed makes public.

## Why

My daughter is seven and is being treated for JGCT. See [awesome-cancer-ai](https://github.com/mrcloudchase/awesome-cancer-ai) for the wider map of AI tools against cancer.
