# Published JGCT cases: a patient-level dataset and descriptive analysis

**What this is.** The maintenance agent's own analysis of the patient-level rows extracted into the records of this knowledge base. It is not a source, has not been checked by a human, and is not medical advice. Read [the protocol](protocol.md) first: it states what was included, how duplicates were removed, and why no treatment effect is estimated. Every row traces to a record; the dataset is `data/published-cases.csv`.

**Dataset.** 156 patient rows from 118 records (full-text case reports, small series and complete meeting abstracts). 2 rows from 2 records were dropped as duplicate reports of the same patients (url-d9e99f99c3cf, url-f1a86961fa15). 5 rows whose juvenile classification the source itself leaves uncertain were set aside (doi-10.17352_ijsrhc.000044, doi-10.32677_ijcr.v10i2.4357, pmid-30123871, pmid-38513413, url-a3c143927c76). Analysed: **149 patients** (133 ovarian, 16 testicular) from 111 records.

**Verification.** The `source_check` column says what each row was checked against and when. 143 of 156 rows were re-read against the paper's own text by the agent after extraction, with corrections and the reason for every judgement call written into `notes`. 13 rows from 5 records could not be re-checked because no full text could be fetched this run (doi-10.15296_ijwhr.2013.12, doi-10.22037_irjps.v9i1.35714, url-991aeae8d365, url-a3204c897af7, url-d9e99f99c3cf). No row has been checked by a human.

**Biases to keep in mind.** These are published cases: unusual presentations, syndromes, pregnancies, relapses and adult-age tumors are over-represented, and follow-up is short or missing in many. Proportions below describe the published literature, not the disease. The registry cohorts in [pooled-cohorts.md](pooled-cohorts.md) are the better guide to frequencies.

## Ovarian cases

### Age

Age stated for 104 of 133: median 13.0 years (range 0.20 to 65). 
18 and over: 28. 8 to 17: 34. age not stated: 29. under 8: 42.

### Presentation by age group

Denominators are patients in each age group with any presentation recorded.

| feature | under 8 | 8 to 17 | 18 and over |
|---|---|---|---|
| precocious puberty | 34/40 (85%) | 4/33 (12%) | 0/25 (0%) |
| virilization | 2/40 (5%) | 5/33 (15%) | 4/25 (16%) |
| abdominal pain | 6/40 (15%) | 9/33 (27%) | 10/25 (40%) |
| abdominal mass or distension | 24/40 (60%) | 19/33 (58%) | 14/25 (56%) |
| menstrual change | 0/40 (0%) | 15/33 (45%) | 2/25 (8%) |
| torsion | 4/40 (10%) | 2/33 (6%) | 2/25 (8%) |
| rupture or hemoperitoneum | 1/40 (2%) | 1/33 (3%) | 4/25 (16%) |
| ascites | 6/40 (15%) | 6/33 (18%) | 8/25 (32%) |
| pregnancy | 0/40 (0%) | 0/33 (0%) | 6/25 (24%) |
| incidental | 0/40 (0%) | 2/33 (6%) | 2/25 (8%) |

### Stage at diagnosis (as the source states it)

| stage | patients |
|---|---|
| I | 7 |
| IA | 46 |
| IC | 13 |
| IC1 | 2 |
| IC2 | 7 |
| IC3 | 1 |
| II | 1 |
| IIIA | 2 |
| IIIB | 2 |
| IIIC | 4 |
| not stated | 48 |

Among 85 staged patients, 76/85 (89%) were stage I (Wilson 95% CI 81 to 94%); the registries report about four in five. Published cases over-represent advanced disease.

### Treatment

Surgery: unilateral salpingo-oophorectomy 50; unknown 32; oophorectomy 21; other 16; cystectomy or enucleation 6; radical 5; cystectomy then completion 3.

| stage group | patients | adjuvant chemotherapy | no adjuvant chemotherapy | not stated |
|---|---|---|---|---|
| IA/IB | 46 | 3 | 37 | 3 |
| IC (any) | 23 | 10 | 3 | 8 |
| I, substage not stated | 7 | 1 | 4 | 2 |
| II to IV | 9 | 4 | 2 | 2 |
| not stated | 48 | 4 | 25 | 19 |

### Outcome by stage

| stage group | patients | NED | alive with disease | died of disease | died, other cause | unknown | relapsed | median follow-up, months |
|---|---|---|---|---|---|---|---|---|
| IA/IB | 46 | 39 | 0 | 3 | 0 | 4 | 5 | 18 (n=24) |
| IC (any) | 23 | 21 | 2 | 0 | 0 | 0 | 3 | 14 (n=10) |
| I, substage not stated | 7 | 5 | 0 | 1 | 0 | 1 | 1 | 48 (n=2) |
| II to IV | 9 | 3 | 0 | 3 | 0 | 3 | 4 | 6 (n=5) |
| not stated | 48 | 19 | 0 | 2 | 1 | 26 | 2 | 7 (n=13) |

Among 99 ovarian patients with a stated outcome, 9/99 (9%) died of disease (Wilson 95% CI 5 to 16%). Short follow-up in many NED rows makes this a lower bound on relapse and death.

### Timing of relapse

15 ovarian patients relapsed; timing is stated for 11: median 9 months (range 1 to 60); 9 of 11 within 24 months. The late ones: 60 months (pmid-32341591); 48 months (pmid-36748172).

### Stage IC: adjuvant chemotherapy and relapse, counted but not compared

Of 23 stage IC patients, 10 received adjuvant chemotherapy (1 relapsed, 0 with unknown outcome) and 3 did not (0 relapsed, 0 unknown); the rest do not state chemotherapy. These counts are not a comparison: patients who received chemotherapy were selected for it, follow-up differs, rupture timing and substage are often missing, and the numbers are tiny. See the protocol for why no effect is estimated.

### Mitotic index

A count per 10 high-power fields and a relapse status are both stated for only 12 ovarian patients: 0 of 1 with 20 or more relapsed, 1 of 11 below 20. Too few to say anything; the registries (STEP, OTST, Kiel) are the evidence here, see pooled-cohorts.md.

### Syndromes recorded

Donohue syndrome (pmid-25153212); Ollier disease (pmid-28144098); Ollier disease (pmid-30581564); Ollier disease (pmid-32030011); McCune-Albright syndrome (mosaic GNAS R201C) (pmid-34286167); neurofibromatosis type 1 (clinical) (pmid-35848651); Ollier disease; 47,XXX (pmid-35968204); Ollier disease (shared somatic IDH1 R132C) (pmid-37324278); xeroderma pigmentosum group C (pmid-37567969); Ollier disease (pmid-37840846); DICER1 syndrome (germline frameshift) (pmid-40076617); xeroderma pigmentosum (group not stated) (pmid-41035579); DICER1 syndrome (germline c.556delT) (url-1c23e1dc296b); DICER1 syndrome (germline splice deletion); thyroid carcinoma at 11 (url-1c23e1dc296b). 14 of 133 ovarian cases, a published-case rate that overstates the true frequency.

### Pregnancy-associated cases

8 cases: age 26, stage IA, NED (doi-10.18203_2320-1770.ijrcog20200395); age not stated, stage IA, NED (doi-10.5350_semb2013470410); age 19, stage IC2, NED (doi-10.59692_jogeca.v36i1.90); age not stated, stage I, DOD (pmid-18205951); age 24, stage not stated, NED (pmid-25484595); age 33, stage IIIB, NED (pmid-36992983); age 28, stage IC2, NED (pmid-37426562); age 28, stage IA, NED (pmid-41797949).

## Testicular cases

16 boys; age stated for 16, median 0.1 months (range 0.0 to 5 months). Surgery: orchiectomy 10; testis sparing 3; unknown 2; other 1. Outcomes: NED 10, unknown 6; no relapse, metastasis or death in any row; chemotherapy in none.

## Records contributing patients

[doi-10.14260_jemds_2018_676], [doi-10.15296_ijwhr.2013.12], [doi-10.15406_jpnc.2015.03.00113], [doi-10.17352_ijrro.000039], [doi-10.18203_2320-1770.ijrcog20175037], [doi-10.18203_2320-1770.ijrcog20200395], [doi-10.18203_2320-1770.ijrcog20240811], [doi-10.18203_2320-1770.ijrcog20251260], [doi-10.18535_jmscr_v8i4.28], [doi-10.18544_ep-01.16.01.1664], [doi-10.21203_rs.3.rs-9115875_v1], [doi-10.22037_irjps.v9i1.35714], [doi-10.28982_josam.636136], [doi-10.29333_ejgm_82225], [doi-10.31083_j.ejgo.2020.02.4938], [doi-10.32677_ijcr.v9i8.4077], [doi-10.3329_mediscope.v1i1.21636], [doi-10.36948_ijfmr.2026.v08i02.76511], [doi-10.37549_ar1663], [doi-10.37549_ar2293], [doi-10.38029_babcockuniv.med.j..v7i2.560], [doi-10.4103_0971-9903.189530], [doi-10.4103_2096-2924.255993], [doi-10.4103_cjhr.cjhr_39_20], [doi-10.4103_tofj.tofj_8_17], [doi-10.4236_jct.2013.48165], [doi-10.4236_ojanes.2015.512044], [doi-10.51288_00810113], [doi-10.5152_etd.2017.17016], [doi-10.5180_jsgoe.32.285], [doi-10.5281_zenodo.7960981], [doi-10.5350_semb2013470410], [doi-10.5455_2320-1770.ijrcog20141259], [doi-10.56951_medicinus.v33i3.66], [doi-10.59692_jogeca.v36i1.90], [pmid-18205951], [pmid-21526089], [pmid-22511424], [pmid-23008780], [pmid-23024526], [pmid-23217189], [pmid-23424695], [pmid-23565375], [pmid-23776871], [pmid-23801894], [pmid-24155044], [pmid-24198925], [pmid-24371683], [pmid-24455600], [pmid-24596770], [pmid-24783102], [pmid-24959454], [pmid-25153212], [pmid-25484595], [pmid-25788847], [pmid-26327951], [pmid-26500075], [pmid-27047664], [pmid-27057263], [pmid-27843515], [pmid-28123736], [pmid-28144098], [pmid-28331810], [pmid-28652991], [pmid-29546931], [pmid-29923976], [pmid-30547828], [pmid-30581564], [pmid-31582893], [pmid-31871849], [pmid-32030011], [pmid-32341591], [pmid-33201299], [pmid-33241170], [pmid-33362514], [pmid-33849266], [pmid-34285730], [pmid-34286167], [pmid-34306284], [pmid-34411449], [pmid-34487069], [pmid-34728912], [pmid-35371651], [pmid-35848651], [pmid-35968204], [pmid-36112066], [pmid-36247268], [pmid-36647328], [pmid-36748172], [pmid-36992983], [pmid-37324278], [pmid-37426562], [pmid-37483405], [pmid-37567969], [pmid-37840846], [pmid-38646138], [pmid-39161564], [pmid-39877787], [pmid-40076617], [pmid-40847681], [pmid-41035579], [pmid-41112815], [pmid-41797949], [pmid-42927143], [url-1c23e1dc296b], [url-3730726ce1a3], [url-6e9d1ea4030e], [url-7878f52277db], [url-991aeae8d365], [url-a3204c897af7], [url-e7696d5604e8]
