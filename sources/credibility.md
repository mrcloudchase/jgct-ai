# Credibility rubric

Every record carries a `source_tier`. Pick the lowest tier that honestly describes the source. When in doubt, go lower.

| Tier | What qualifies | Typical confidence ceiling |
|---|---|---|
| `peer_reviewed` | Article in a journal with editorial peer review, indexed in PubMed or Europe PMC | 5 with full text, 3 with abstract only |
| `guideline` | NCCN, ESMO, COG, SIOP, WHO classification, national society guidance | 5 |
| `registry` | Report from a disease registry or consortium (OTST Registry, PCDC, GENIE) | 4 |
| `preprint` | bioRxiv, medRxiv, Research Square, SSRN | 3 |
| `conference_abstract` | ASCO, AACR, SIOP, ESGO, ISPOG, or similar meeting abstracts | 3 |
| `database` | CIViC, OncoKB, COSMIC, cBioPortal, ClinicalTrials.gov entries | 4 |
| `organization` | Foundation, hospital, or rare disease organization pages | 2 |
| `other` | Anything else credible but unclassified | 2 |

## Rules

1. **A source is what it is at retrieval time.** An abstract that later became a paper gets a second record for the paper. Link them with `superseded_by`.
2. **Sample size is recorded, never inflated.** A case report is `n_jgct_patients: 1`. A series that mentions JGCT among other tumors records only the JGCT count. If the count is not stated, leave it null.
3. **Frequencies are copied, not computed.** If the source says "4 of 31," write `4/31`. If it says "13 percent," write `13%`. Do not convert.
4. **Claims about treatment efficacy need the denominator.** "Responded to carboplatin" from a single case is a case observation, recorded under `treatments` with `outcome` and nothing more.
5. **Conflicts are recorded in both records.** If source A reports FOXL2 absent in JGCT and source B reports it present in 2 of 10, both records get `conflicts_with` pointing at the other, and the summary says the literature disagrees.
6. **Retraction and correction check.** For `peer_reviewed`, note any retraction or erratum visible on PubMed. A retracted paper stays in the base with `retracted: true` so nobody re-adds it.
7. **Non-English sources** are in scope. Record the language. Confidence ceiling 3 unless you read the full text in that language.
8. **Predatory or unknown journals.** If the journal is not indexed in PubMed, Europe PMC, or DOAJ, tier it `other` and say why in `notes`.
9. **Never cite memory.** If you know a fact but cannot retrieve a source for it this run, it does not go in a record. Put it in the run report under "Suggested changes" as a lead.
10. **Patient communities, forums, and social media are never sources.**
