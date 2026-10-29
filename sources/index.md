# Source index

Every place the research sweep is allowed to look. Add a row when you discover a credible source. Rows marked `verify on first run` were added from knowledge of the organization, not from a fetched page; confirm the URL and update the row.

Types: `api` (structured, query with a tool), `sweep` (search or browse each run), `reference` (fetch when a record needs it).

## Literature

| Source | Type | Tier | Domain | How to query | Notes |
|---|---|---|---|---|---|
| PubMed | api | peer_reviewed | eutils.ncbi.nlm.nih.gov, pubmed.ncbi.nlm.nih.gov | `tools/monitor/monitor.py`, `tools/extract/extract_paper.py` | 429 hits as of 2026-10-29 for the phrase query |
| PubMed Central | api | peer_reviewed | pmc.ncbi.nlm.nih.gov | via `tools/europepmc.py fulltext` | Open access full text |
| Europe PMC | api | peer_reviewed, preprint | www.ebi.ac.uk, europepmc.org | `tools/europepmc.py search`, `SRC:PPR` for preprints | Broader than PubMed; has citation endpoints. Phrase search returned 633 hits on 2026-10-29 (vs 429 PubMed) because it matches full text; default `--limit` is 100, pass `--limit 1000`. For abstracts, `rest/search?query=EXT_ID:<pmid> AND SRC:MED&resultType=core&format=json` works when pubmed.ncbi.nlm.nih.gov serves a cookie wall |
| OpenAlex | api | peer_reviewed | api.openalex.org | `GET /works?search=...` | 250M works; use for citation chasing and non-indexed journals |
| Semantic Scholar | api | peer_reviewed | api.semanticscholar.org | `GET /graph/v1/paper/search?query=...` | Rate limited without key |
| bioRxiv, medRxiv | api | preprint | api.biorxiv.org, www.biorxiv.org, www.medrxiv.org | details endpoint by date range, filter title and abstract | |
| DOI resolver | reference | varies | doi.org | fetch to find the publisher page | |
| Major publishers (full text) | reference | peer_reviewed | www.nature.com, link.springer.com, onlinelibrary.wiley.com, www.sciencedirect.com, journals.lww.com, academic.oup.com, www.mdpi.com, www.frontiersin.org, journals.plos.org, bmcjournals.biomedcentral.com, aacrjournals.org, ascopubs.org, www.thieme-connect.com, www.karger.com, www.tandfonline.com, www.cambridge.org, jamanetwork.com, www.nejm.org, www.thelancet.com | fetch the DOI landing page; many are paywalled | Record `unreachable` with reason `paywall` when blocked |

## Conference abstracts

| Source | Type | Tier | Domain | How to query | Notes |
|---|---|---|---|---|---|
| ASCO Meeting Library | sweep | conference_abstract | meetings.asco.org, ascopubs.org | search "juvenile granulosa" in the abstract archive | verify on first run |
| AACR | sweep | conference_abstract | aacrjournals.org | Cancer Research supplement abstracts | verify on first run |
| SIOP (International Society of Paediatric Oncology) | sweep | conference_abstract | siop-online.org | annual congress abstracts, published in Pediatric Blood & Cancer supplements | verify on first run |
| ESGO | sweep | conference_abstract | esgo.org, ijgc.bmj.com | IJGC supplement abstracts | verify on first run |
| ISPOG / IGCS | sweep | conference_abstract | igcs.org | congress abstracts | verify on first run |
| ESPE / Pediatric Endocrine Society | sweep | conference_abstract | www.eurospe.org, pedsendo.org | JGCT often presents as precocious puberty; endocrine meetings carry case series | verify on first run |

## Registries and consortia

| Source | Type | Tier | Domain | How to query | Notes |
|---|---|---|---|---|---|
| International Ovarian and Testicular Stromal Tumor Registry | sweep | registry | www.ppbregistry.org, www.childrensmn.org | publications page; NCT01970696 | Children's Minnesota; enrolling since 2011. Checked 2026-10-29: the ppbregistry.org home page describes only the International PPB/DICER1 Registry (Children's Minnesota) and does not mention OTST or JGCT; no publications page found there. Try `/accelerate-research/` or childrensmn.org next run |
| German Registry for Rare Pediatric Tumors (STEP) | reference | registry | find via PubMed | NCT05773651 on ClinicalTrials.gov | Added 2026-10-29. Largest prospective pediatric JGCT cohort (113 patients, pmid-40272823); part of EXPeRT/PARTNER |
| Pediatric Cancer Data Commons | sweep | registry | commons.cri.uchicago.edu, portal.pedscommons.org | consortium pages for germ cell and rare tumors | |
| AACR Project GENIE | api | database | genie.cbioportal.org | cBioPortal API, OncoTree `grct` | login required for the GENIE instance |
| Childhood Cancer Data Initiative | sweep | registry | ccdi.cancer.gov, moleculartargets.ccdi.cancer.gov | Molecular Targets Platform search | |
| Kids First DRC | sweep | registry | kidsfirstdrc.org, portal.kidsfirstdrc.org | | controlled access for genomic data |

## Trials

| Source | Type | Tier | Domain | How to query | Notes |
|---|---|---|---|---|---|
| ClinicalTrials.gov | api | database | clinicaltrials.gov | `tools/monitor/monitor.py` | |
| EU Clinical Trials Register | sweep | database | www.clinicaltrialsregister.eu, euclinicaltrials.eu | search "granulosa" | |
| ISRCTN | sweep | database | www.isrctn.com | search "granulosa" | |
| WHO ICTRP | sweep | database | trialsearch.who.int | search "granulosa cell" | aggregates national registries |

## Genomic and clinical evidence databases

| Source | Type | Tier | Domain | How to query | Notes |
|---|---|---|---|---|---|
| cBioPortal | api | database | www.cbioportal.org | `tools/genomics/gct_lookup.py` | 87 granulosa cell tumor samples across 8 public studies as of 2026-10-29 |
| CIViC | api | database | civicdb.org | GraphQL, in `tools/genomics/gct_lookup.py` | |
| OncoKB | api | database | www.oncokb.org | annotator with academic token | token not yet configured |
| COSMIC | reference | database | cancer.sanger.ac.uk | search by gene | registration required for downloads |
| ClinVar | reference | database | www.ncbi.nlm.nih.gov | variant lookup | |

## Guidelines and classification

| Source | Type | Tier | Domain | How to query | Notes |
|---|---|---|---|---|---|
| WHO Classification of Tumours, Female Genital Tumours | reference | guideline | tumourclassification.iarc.who.int | | subscription for full text |
| NCCN Ovarian Cancer guideline | reference | guideline | www.nccn.org | sex cord-stromal section | free registration |
| ESMO | reference | guideline | www.esmo.org | rare ovarian tumours guidance | |
| Children's Oncology Group | reference | guideline | childrensoncologygroup.org | rare tumor protocols | |
| EXPeRT (European rare pediatric tumors group) | reference | guideline | | published in European Journal of Cancer and Pediatric Blood & Cancer | find via PubMed. SCST consensus 2021 is PMID 33760357; European standard clinical practice recommendations 2026 is PMID 42504512 |

## Organizations

| Source | Type | Tier | Domain | How to query | Notes |
|---|---|---|---|---|---|
| NORD | reference | organization | rarediseases.org | rare disease report | |
| Orphanet | reference | organization | www.orpha.net | ORPHA entry for JGCT | |
| Granulosa Cell Tumor Research Foundation | sweep | organization | gctrf.org | funded research list | verify on first run. Tried 2026-10-29: home page returned no readable content; still unverified |
| St. Jude Cloud PeCan | reference | database | pecan.stjude.cloud, www.stjude.cloud | variant knowledgebase | |

## Out of scope

Patient forums, Facebook groups, Inspire, Reddit, personal blogs. Never fetched, never cited.
