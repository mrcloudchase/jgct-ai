# Analyses

The maintenance agent's own analyses across the records: a patient-level dataset of published JGCT cases and pooled descriptive tables from the cohort studies. Unreviewed, not a source, not medical advice. The [protocol](protocol.md) states inclusion, deduplication, statistics and why no treatment effect is estimated.

| File | What |
|---|---|
| [protocol.md](protocol.md) | Rules for everything in this directory |
| [published-cases.md](published-cases.md) | Descriptive analysis of the patient-level dataset (generated) |
| [pooled-cohorts.md](pooled-cohorts.md) | Cohort-by-cohort tables with pooled proportions (generated) |
| [data/published-cases.csv](data/published-cases.csv) | The dataset, one row per patient, with the record it comes from (generated) |
| [data/cohorts.yaml](data/cohorts.yaml) | Study-level counts with overlap groups (hand-maintained) |

Generated files are rebuilt by `python3 tools/patients.py export && python3 tools/analyze.py`.
