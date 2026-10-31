# Protocol for the analyses

This directory holds the maintenance agent's own analyses of the records in `knowledge/records/`. The knowledge base never combines a number from one record with a number from another; this directory is the one place where that happens, under the rules below. Nothing here is a source, nothing here has been checked by a human against the papers, and nothing here is medical advice. The maintainer judges it in pull-request review like everything else.

## Questions

1. What do the published JGCT cases, taken together, look like: age, presentation, stage, treatment, outcome, relapse timing, syndromes, pregnancy? (`published-cases.md`)
2. What do the larger cohorts and registries report for the same quantities, and what do they add up to when cohorts that share patients are counted once? (`pooled-cohorts.md`)
3. Can the records answer whether adjuvant chemotherapy changes relapse at stage IC? (No; the reasons are stated, and the source figures are shown side by side without pooling.)

## Inclusion

- **Patient-level dataset.** Every record whose `evidence_basis` is `full_text` and whose study type is a case report or a series small enough for the source to describe patients individually, plus complete meeting abstracts recorded as full text. One row per JGCT patient the source describes, with the fields of the `patients` item in `knowledge/schema/record.schema.json`. Values are copied from the record, which copied them from the paper; a field the source does not state is left null, never inferred. Patients whose tumor the source itself calls mixed (gynandroblastoma, Sertoli-Leydig components) or reclassifies after review are not entered. Patients whose juvenile classification the source leaves uncertain (adult-type morphology, no immunohistochemistry at adult age) are entered with the note `classification uncertain` and excluded from the tables, listed separately.
- **Cohort table** (`data/cohorts.yaml`). Series and registries of ten or more JGCT patients, and the registries' testicular arms, with the counts their record states: n, stage I, followed, relapses, deaths of disease, chemotherapy, mitotic-index events, lymphadenectomy and node positivity. Abstract-based records are included and marked.

## Deduplication

- Patients: two records that report the same patient are linked by `overlaps_with`; when both carry patient rows, the rows of the lower-ranked record (url below doi below pmid) are dropped. The dropped records are named in the report.
- Cohorts: every cohort row carries a `group`; cohorts in one group share patients (STEP and the MAKEI and Kiel cohorts; the three OTST reports; TGM-95 paper and abstract; two Fudan series; pooled reviews of published cases). One row per group, marked `primary`, enters a pooled figure. The others are shown for the record.
- The published-cases dataset and the cohort table are never added to each other: most case reports are also inside the published-case reviews and some are inside the registries.

## Statistics

Proportions with Wilson 95% confidence intervals per cohort. Where at least three primary cohorts report the same numerator and denominator, a crude pooled proportion and a DerSimonian-Laird random-effects pooled proportion on the logit scale with I². No regression, no survival analysis (follow-up is reported too unevenly), no subgroup comparison between treated and untreated patients.

## Why no treatment effect is estimated

Every source that reports chemotherapy at stage IC gave it to the patients judged at higher risk (preoperative rupture, malignant ascites, high mitotic index) and observed the rest; the registries say so. Stage IC itself meant different things before and after FIGO 2014 and in the Wollner system used by the French series. Follow-up differs by years. Pooling such groups would give a confounded estimate with a falsely narrow interval. The raw figures of each source are shown side by side so a reader can see what exists; the conclusion that no study has shown an effect, and none was designed to, is itself the finding.

## Biases

Published cases over-represent the unusual: adult-age tumors, syndromes, pregnancies, rare presentations, relapses and deaths. Follow-up in case reports is often months. Cohorts from referral centers and consultation files (the 1984 series) differ from population registries (SEER). Older cohorts predate the mitotic-index threshold and modern staging. The tables describe the literature as it is, not the disease.

## Reproducing

```
python3 tools/patients.py export     # analyses/data/published-cases.csv from the records
python3 tools/analyze.py             # analyses/published-cases.md and analyses/pooled-cohorts.md
```

Rows are added by writing `patients` into records (see `tools/patients.py merge`) and cohort counts by editing `data/cohorts.yaml`; both are re-run on every maintenance run so the reports follow the records.
