# Maintainer review, 2026-10-31

An independent check of this knowledge base against the public record, done for the maintainer
outside the monthly run. Method: the public JGCT literature was re-enumerated from scratch (PubMed,
Europe PMC, OpenAlex, Semantic Scholar, Crossref, DOAJ, J-STAGE, CiNii, SciELO, ClinicalTrials.gov,
cBioPortal, CIViC, Orphanet, PDQ, educational and patient sites), about 45 open-access full texts and
the abstracts of the paywalled landmark papers were read, and only then was the repository compared
with that picture. This file is for the next run and for the maintainer; it is not a record.

## Verdict

- **Coverage of what can be read legally and automatically is complete.** Every open-access article
  with JGCT in its title (42 of 42 found independently) is already a record, and 53 of the 65
  open-access articles that mention JGCT five or more times are records. The 12 that are not are
  listed below; all are peripheral (adult GCT, SLCT, SCCOHT, yolk sac tumour).
- **Records are accurate.** Ten records whose sources were read independently in full (OTST 2025,
  STEP 2025, Bessière 2015, the stage IC meta-analysis, the 5-case molecular study, the 2025
  management flowchart paper, MAD2L1BP, McCune-Albright, the 2026 European recommendations, the
  testicular systematic review) matched their sources in every number checked. One nit:
  `pmid-34286167` labels the stage IC2 as "intra-operative rupture"; the paper classifies rupture
  found at surgery as IC2 without saying when it happened.
- **The base knows things the independent sweep missed**, notably the 2026 European Standard
  Clinical Practice recommendations (pmid-42504512, found via Unpaywall in the Padua repository),
  the five-guideline comparison (pmid-36980387) and the recurrence survival analysis
  (pmid-40815979).
- **The summaries lacked a gist.** Both were accurate and fully cited but opened straight into
  detail. A "The gist" section now opens each one, and CLAUDE.md asks for it to be kept.
- **Topics do not exist yet.** `knowledge/topics/` holds only the README, and the site's Topics page
  is a placeholder. CLAUDE.md lists topics as a thing that must always be true. The next run should
  write them; `prompts/research.md` now names topics explicitly. Subjects the records already
  support: stage and chemotherapy decisions (IC1 vs IC2/IC3); mitotic index as a prognostic factor;
  testicular JGCT; AKT1, GNAS and the other drivers; syndromic associations (Ollier/Maffucci,
  McCune-Albright, DICER1, MAD2L1BP); differential diagnosis (SCCOHT, SLCT, adult GCT); markers and
  follow-up; relapse and salvage; JGCT in pregnancy and in adults; endocrine aftermath (central
  precocious puberty, fertility).
- **The largest gap is paywalled full text**, as the run reports say: 859 items, including Young
  1984 (125 cases), Zaloudek 1982, Lawrence 1985, Vassal 1988, Calaminus 1997, Schneider 2003,
  Kalfa 2006 (GNAS), Kao 2015 (70 testicular cases), EXPeRT/PARTNER 2021, MITO-9 2021,
  Vougiouklakis 2022 (31-tumour genomics), Collins 2023 (testicular monosomy 10), Marino 2025
  (Monza, 30 patients), Boyraz 2026 (anaplastic JGCT, TP53 and MYC). No automated route exists;
  a person with library access is the only way in.

## Source families not yet in `sources/INDEX.md`

The catalogue covers the major indexes, trial registries, cBioPortal, PDQ, GeneReviews and
conference supplements. These were not catalogued or were only touched in passing:

| Family | How to query | What it holds |
|---|---|---|
| Semantic Scholar bulk search | `https://api.semanticscholar.org/graph/v1/paper/search/bulk?query="juvenile granulosa"&fields=title,year,externalIds,openAccessPdf,venue` | 664 items on 2026-10-31; 173 not in PubMed/Europe PMC (regional journals, abstracts, Spanish, Portuguese, Chinese, Japanese, Persian, Russian, Indonesian, Korean items; many with OA PDF links). See `2026-10-31-leads-outside-pubmed-epmc.tsv`. |
| Crossref | `https://api.crossref.org/works?query.bibliographic="juvenile granulosa"&rows=1000` | Mostly duplicates; two 1990s abstracts (liver-directed therapy, ABMT) not elsewhere. |
| DOAJ | `https://doaj.org/api/search/articles/"juvenile granulosa"` | 78 items; about 20 not in the ledger, all small OA journals (usable full text). |
| J-STAGE, CiNii (Japan) | `https://api.jstage.jst.go.jp/searchapi/do?service=3&text=juvenile granulosa`; `https://cir.nii.ac.jp/opensearch/all?q=...&format=json` | Japanese case reports with English abstracts, some OA PDFs. |
| SciELO (Latin America) | `https://search.scielo.org/?q="juvenile granulosa"&output=ris` | Spanish and Portuguese reports (Chile, Brazil, Venezuela). |
| CNKI / Wanfang (China) | no API; titles surface via OpenAlex and Semantic Scholar | Chinese series (e.g. 18-case 2026 series pmid-42706059) exist only as English abstracts. |
| Educational sites | PathologyOutlines (ovary `ovarytumorgctjuv`, testis `testisgranulosajuvenile`), Radiopaedia, MyPathologyReport (patient-facing pathology explainer, updated 2026-04), Wikipedia | Not records (secondary), but useful cross-checks and the places families actually land; PathologyOutlines and Radiopaedia block scripts (429/406), so read by hand. |
| Registries' own sites | OTST Registry (otstregistry.org, Children's Minnesota), International PPB/DICER1 Registry, STEP (raretumors-children.eu), TESST group | Enrolment information for families; current contact points. |
| Patient communities | GCT Survivor Sisters (closed Facebook group, open to parents of JGCT patients), Inspire ovarian cancer community, Ovarian Cancer Research Alliance support page | There is no JGCT-specific charity; this is what exists. |
| ESPE abstracts | abstracts.eurospe.org | Paediatric endocrinology case abstracts (precocious puberty). |
| Theses | OATD, BASE, ProQuest (metadata only) | Not yet searched. |
| WHO Classification (Blue Books, 5th ed.) | not public | The defining text for JGCT; cite via reviews that quote it. |

## Open-access texts not yet records (JGCT mentioned 5+ times)

| PMC | year | title |
|---|---|---|
| PMC10545264 | 2021 | A case report of ovarian granulosa cell tumor in patient with polycystic ovarian syndrome. |
| PMC11196119 | 2024 | A Comparison of Diagnostic and Immunohistochemical Workup and Literature Review Capabilities of Online Artificial Intelligence... |
| PMC12119149 | 2025 | Delayed Diagnosis of Adult Granulosa Cell Tumor: Emphasizing the Importance of Comprehensive Ovarian Mass Evaluation |
| PMC12289768 | 2025 | A molecular and immunohistochemical study of 37 cases of ovarian Sertoli-Leydig cell tumor. |
| PMC13199555 | 2026 | Clinicopathological and molecular characteristics of small cell carcinoma of the ovary, hypercalcemic type |
| PMC13375443 | 2026 | Pregnancy-Associated Small Cell Carcinoma of the Ovary, Hypercalcaemic Type Initially Misdiagnosed as Granulosa Cell Tumour |
| PMC13671097 | 2026 | Multidisciplinary Management of a Giant Ovarian Sertoli-Leydig Cell Tumor Presenting With Isosexual Precocious Puberty |
| PMC4434146 | 2014 | Yolk sac tumor of the ovary in a young girl with tuberous sclerosis: A case report and review of the literature |
| PMC6421921 | 2019 | Extragonadal yolk sac tumor following congenital buccal mature cystic teratoma. |
| PMC7103096 | 2017 | ESPR 2017 abstracts (contains JGCT abstracts) |
| PMC7535776 | 2020 | Adult granulosa cell tumors of bilateral ovaries with pure cystic presentation |
| PMC8052061 | 2021 | Disseminated ovarian granulosa cell tumor after laparoscopic surgery: Two case reports. |

Most are differential-diagnosis material (SCCOHT misdiagnosed as JGCT, SLCT with follicular pattern);
the two SCCOHT papers and the SLCT series are worth records for the differential-diagnosis topic.

## Readability notes for the two audiences

- The home page, the "How to read this site" box and the About page are clear. The gist sections
  now give both readers the picture in a minute.
- The clinician summary is long (about 2,800 words) and reads as a catalogue of what each source
  says. That is by design (nothing synthesized beyond the sources), but once topic articles exist the
  summary can shrink and point into them.
- Family text cites every sentence with bracketed IDs. The brackets are the price of traceability;
  the site could render them smaller or as superscripts so the prose reads more easily.
- "Not yet read" is a 12,000-word list. A short head note saying what the biggest unread items are,
  and how a reader with library access can help, would make it useful rather than daunting.
- Nothing on the site yet tells a family where the registries and communities are (table above).

## Compliance note

`tools/fulltext.py` reads non-open-access PMC article pages with a browser user agent and backs off
on reCAPTCHA. That is reading pages NCBI serves to any reader, not bulk download, but it is a
judgement call the maintainer should make knowingly; the agent cannot. Elsevier and other
publisher captchas were not circumvented.

## Actions taken on 2026-10-31 (same review session, PR 18)

- `knowledge/topics/`: 14 topic articles written from the records (list in `knowledge/topics/README.md`); every cited ID checked against `knowledge/records/`.
- `knowledge/summary/`: both summaries rewritten as the gist followed by short sections, each ending with a link to its topic article.
- `site/build.py`: relative `.md` links in topics and summaries now render as page links; citations render as small superscripts; the home page lists the topics.
- `sources/INDEX.md`: the source families in the table above were added to the hand-maintained catalogue; 29 leads not already in the ledger were loaded as `found`.
- `knowledge/records/pmid-34286167.yaml`: stage wording made consistent with the paper's own classification.

## Abstract tier (same day, maintainer decision)

The maintainer asked that paywalled sources at least contribute their abstracts. Done as follows:

- Schema: `evidence_basis` (full_text | abstract); abstract records have `abstract_source` and no `full_text_source`. Ledger status `abstract_only`.
- 169 records withdrawn on 2026-10-30 restored from git history as abstract records; 200 new abstract records written from PubMed, Semantic Scholar and Crossref abstracts (`tools/mkabstract.py`), covering every `needs_full_text` item whose abstract speaks about JGCT; three complete meeting abstracts recorded as full text. 98 JGCT-titled items have no abstract anywhere and stay `needs_full_text`; 29 items skipped as passing mentions.
- Site: every citation of an abstract record carries a dagger; source pages, the sources list, home, about, footer and the "Not yet read in full" page show the split.
- Topics and summaries cite the abstract-only landmarks (Young 1984, Zaloudek 1982, Plantaz 1992, Calaminus 1997, MAKEI 2003, Kiel 2003, Kalfa 2006/2007, TGM-95, MITO-9, TGM13, Vougiouklakis 2022, Boyraz 2022/2026, Collins 2023, Baillard 2021, ESGO-SIOPE 2020, EXPeRT 2021) and say in words when a claim rests on an abstract.
