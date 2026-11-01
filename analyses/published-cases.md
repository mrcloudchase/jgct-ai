# Published JGCT cases: a patient-level dataset and descriptive analysis

**What this is.** The maintenance agent's own analysis of the patient-level rows extracted into the records of this knowledge base. It is not a source, has not been checked by a human, and is not medical advice. Read [the protocol](protocol.md) first: it states what was included, how duplicates were removed, and why no treatment effect is estimated. Every row traces to a record; the dataset is `data/published-cases.csv`.

**Dataset.** 199 patient rows from 153 records (full-text case reports, small series and complete meeting abstracts); 25 further rows on 21 abstract-only records are kept in the dataset but not analysed. 2 rows from 2 records were dropped as duplicate reports of the same patients (url-d9e99f99c3cf, url-f1a86961fa15). 6 rows whose juvenile classification the source itself leaves uncertain were set aside (doi-10.17352_ijsrhc.000044, doi-10.32677_ijcr.v10i2.4357, doi-10.5505_aot.2012.33042, pmid-30123871, pmid-38513413, url-a3c143927c76). Analysed: **191 patients** (170 ovarian, 21 testicular) from 145 records.

**Biases to keep in mind.** These are published cases: unusual presentations, syndromes, pregnancies, relapses and adult-age tumors are over-represented, and follow-up is short or missing in many. Proportions below describe the published literature, not the disease. The registry cohorts in [pooled-cohorts.md](pooled-cohorts.md) are the better guide to frequencies.

## Ovarian cases

### Age

Age stated for 148 of 170: median 10.0 years (range 0.20 to 66). 
18 and over: 33. 8 to 17: 48. age not stated: 22. under 8: 67.

### Presentation by age group

Denominators are patients in each age group with any presentation recorded.

| feature | under 8 | 8 to 17 | 18 and over |
|---|---|---|---|
| precocious puberty | 52/64 (81%) | 5/45 (11%) | 0/27 (0%) |
| virilization | 4/64 (6%) | 5/45 (11%) | 5/27 (19%) |
| abdominal pain | 13/64 (20%) | 16/45 (36%) | 11/27 (41%) |
| abdominal mass or distension | 33/64 (52%) | 27/45 (60%) | 14/27 (52%) |
| menstrual change | 1/64 (2%) | 18/45 (40%) | 3/27 (11%) |
| torsion | 5/64 (8%) | 3/45 (7%) | 2/27 (7%) |
| rupture or hemoperitoneum | 3/64 (5%) | 2/45 (4%) | 4/27 (15%) |
| ascites | 9/64 (14%) | 9/45 (20%) | 9/27 (33%) |
| pregnancy | 0/64 (0%) | 1/45 (2%) | 6/27 (22%) |
| incidental | 0/64 (0%) | 2/45 (4%) | 2/27 (7%) |

### Stage at diagnosis (as the source states it)

| stage | patients |
|---|---|
| I | 9 |
| IA | 52 |
| IC | 17 |
| IC1 | 2 |
| IC2 | 8 |
| IC3 | 1 |
| II | 1 |
| III | 1 |
| IIIA | 2 |
| IIIB | 2 |
| IIIC | 4 |
| IV | 1 |
| not stated | 70 |

Among 100 staged patients, 89/100 (89%) were stage I (Wilson 95% CI 81 to 94%); the registries report about four in five. Published cases over-represent advanced disease.

### Treatment

Surgery: unilateral salpingo-oophorectomy 63; unknown 43; oophorectomy 26; other 20; cystectomy or enucleation 8; radical 6; cystectomy then completion 4.

| stage group | patients | adjuvant chemotherapy | no adjuvant chemotherapy | not stated |
|---|---|---|---|---|
| IA/IB | 52 | 3 | 42 | 4 |
| IC (any) | 28 | 14 | 4 | 8 |
| I, substage not stated | 9 | 1 | 6 | 2 |
| II to IV | 11 | 6 | 2 | 2 |
| not stated | 70 | 5 | 27 | 36 |

### Outcome by stage

| stage group | patients | NED | alive with disease | died of disease | died, other cause | unknown | relapsed | median follow-up, months |
|---|---|---|---|---|---|---|---|---|
| IA/IB | 52 | 45 | 0 | 3 | 0 | 4 | 5 | 21 (n=31) |
| IC (any) | 28 | 26 | 2 | 0 | 0 | 0 | 4 | 16 (n=13) |
| I, substage not stated | 9 | 7 | 0 | 1 | 0 | 1 | 1 | 42 (n=4) |
| II to IV | 11 | 4 | 0 | 4 | 0 | 3 | 4 | 5 (n=6) |
| not stated | 70 | 22 | 1 | 3 | 1 | 43 | 4 | 6 (n=16) |

Among 119 ovarian patients with a stated outcome, 11/119 (9%) died of disease (Wilson 95% CI 5 to 16%). Short follow-up in many NED rows makes this a lower bound on relapse and death.

### Timing of relapse

18 ovarian patients relapsed; timing is stated for 14: median 9 months (range 1 to 60); 11 of 14 within 24 months. The late ones: 60 months (doi-10.52768_2766-7820_1964); 60 months (pmid-32341591); 48 months (pmid-36748172).

### Stage IC: adjuvant chemotherapy and relapse, counted but not compared

Of 28 stage IC patients, 14 received adjuvant chemotherapy (2 relapsed, 0 with unknown outcome) and 4 did not (0 relapsed, 0 unknown); the rest do not state chemotherapy. These counts are not a comparison: patients who received chemotherapy were selected for it, follow-up differs, rupture timing and substage are often missing, and the numbers are tiny. See the protocol for why no effect is estimated.

### Mitotic index

A count per 10 high-power fields and a relapse status are both stated for only 14 ovarian patients: 1 of 2 with 20 or more relapsed, 1 of 12 below 20. Too few to say anything; the registries (STEP, OTST, Kiel) are the evidence here, see pooled-cohorts.md.

### Syndromes recorded

Maffucci syndrome (doi-10.11164_jjsps.24.2_472_2); Donohue syndrome (pmid-25153212); Ollier disease (pmid-28144098); Ollier disease (pmid-30581564); Ollier disease (pmid-32030011); McCune-Albright syndrome (mosaic GNAS R201C) (pmid-34286167); neurofibromatosis type 1 (clinical) (pmid-35848651); Ollier disease; 47,XXX (pmid-35968204); Ollier disease (shared somatic IDH1 R132C) (pmid-37324278); xeroderma pigmentosum group C (pmid-37567969); Ollier disease (pmid-37840846); DICER1 syndrome (germline frameshift) (pmid-40076617); xeroderma pigmentosum (group not stated) (pmid-41035579); McCune-Albright syndrome (GNAS p.R201H) (url-08fbb6ac79f2); DICER1 syndrome (germline c.556delT) (url-1c23e1dc296b); DICER1 syndrome (germline splice deletion); thyroid carcinoma at 11 (url-1c23e1dc296b); Maffucci syndrome (url-71fabf45e585); Ollier disease (enchondromatosis) (url-bf94bf8a0b06). 18 of 170 ovarian cases, a published-case rate that overstates the true frequency.

### Pregnancy-associated cases

8 cases: age 26, stage IA, NED (doi-10.18203_2320-1770.ijrcog20200395); age 17, stage IA, NED (doi-10.5350_semb2013470410); age 19, stage IC2, NED (doi-10.59692_jogeca.v36i1.90); age not stated, stage I, DOD (pmid-18205951); age 24, stage not stated, NED (pmid-25484595); age 33, stage IIIB, NED (pmid-36992983); age 28, stage IC2, NED (pmid-37426562); age 28, stage IA, NED (pmid-41797949).

## Testicular cases

21 boys; age stated for 21, median 0.1 months (range 0.0 to 5 months). Surgery: orchiectomy 15; testis sparing 3; unknown 2; other 1. Outcomes: NED 13, unknown 8; no relapse, metastasis or death in any row; chemotherapy in none.

## Records contributing patients

[doi-10.11164_jjsps.22.6_1102], [doi-10.11164_jjsps.23.6_1133_1], [doi-10.11164_jjsps.24.2_472_2], [doi-10.11164_jjsps.26.5_987], [doi-10.11164_jjsps.29.6_1141], [doi-10.11164_jjsps.44.1_7], [doi-10.11164_jjsps.52.6_1241], [doi-10.11437_sanpunosinpo1949.41.783], [doi-10.14260_jemds_2018_676], [doi-10.1515_sjecr-2017-0016], [doi-10.15296_ijwhr.2013.12], [doi-10.15406_jpnc.2015.03.00113], [doi-10.17116_repro20212705148], [doi-10.17352_ijrro.000039], [doi-10.18203_2320-1770.ijrcog20175037], [doi-10.18203_2320-1770.ijrcog20200395], [doi-10.18203_2320-1770.ijrcog20240811], [doi-10.18203_2320-1770.ijrcog20251260], [doi-10.18535_jmscr_v8i4.28], [doi-10.18544_ep-01.16.01.1664], [doi-10.21203_rs.3.rs-143384_v1], [doi-10.21203_rs.3.rs-9115875_v1], [doi-10.21474_ijar01_14578], [doi-10.22037_irjps.v9i1.35714], [doi-10.28982_josam.636136], [doi-10.29333_ejgm_82225], [doi-10.31083_j.ejgo.2020.02.4938], [doi-10.3126_njog.v6i2.6764], [doi-10.32677_ijcr.v9i8.4077], [doi-10.3329_mediscope.v1i1.21636], [doi-10.33425_2689-1093.1008], [doi-10.36948_ijfmr.2026.v08i02.76511], [doi-10.37549_ar1663], [doi-10.37549_ar2293], [doi-10.38029_babcockuniv.med.j..v7i2.560], [doi-10.4067_s0717-75262015000300009], [doi-10.4067_s0717-95022010000200023], [doi-10.4103_0971-9903.189530], [doi-10.4103_2096-2924.255993], [doi-10.4103_cjhr.cjhr_39_20], [doi-10.4103_tofj.tofj_8_17], [doi-10.4172_2157-2518.1000i101], [doi-10.4236_jct.2013.48165], [doi-10.4236_ojanes.2015.512044], [doi-10.4236_ojped.2023.132019], [doi-10.51288_00810113], [doi-10.5152_etd.2017.17016], [doi-10.5180_jsgoe.32.285], [doi-10.52611_confluencia.2026.1821], [doi-10.52768_2766-7820_1964], [doi-10.5281_zenodo.6564246], [doi-10.5281_zenodo.7960981], [doi-10.5350_semb2013470410], [doi-10.54265_ucdu5860], [doi-10.5455_2320-1770.ijrcog20141259], [doi-10.56951_medicinus.v33i3.66], [doi-10.5712_rbmfc1(2)136], [doi-10.57291_jsgo.44.2_161], [doi-10.5795_jjscc.31.74], [doi-10.5795_jjscc.33.14], [doi-10.5935_2965-1980.2022v1n3a25], [doi-10.59692_jogeca.v36i1.90], [doi-10.62954_t96nbw45], [doi-10.83129_toubkal-6511], [pmid-18205951], [pmid-21526089], [pmid-22511424], [pmid-23008780], [pmid-23024526], [pmid-23217189], [pmid-23424695], [pmid-23565375], [pmid-23776871], [pmid-23801894], [pmid-24155044], [pmid-24198925], [pmid-24371683], [pmid-24455600], [pmid-24596770], [pmid-24783102], [pmid-24959454], [pmid-25153212], [pmid-25484595], [pmid-25788847], [pmid-26327951], [pmid-26500075], [pmid-27042471], [pmid-27047664], [pmid-27057263], [pmid-27843515], [pmid-28123736], [pmid-28144098], [pmid-28331810], [pmid-28652991], [pmid-29546931], [pmid-29923976], [pmid-30547828], [pmid-30581564], [pmid-31582893], [pmid-31871849], [pmid-32030011], [pmid-32341591], [pmid-33201299], [pmid-33241170], [pmid-33362514], [pmid-33849266], [pmid-34285730], [pmid-34286167], [pmid-34306284], [pmid-34411449], [pmid-34487069], [pmid-34728912], [pmid-35371651], [pmid-35848651], [pmid-35968204], [pmid-36112066], [pmid-36247268], [pmid-36647328], [pmid-36748172], [pmid-36992983], [pmid-37324278], [pmid-37426562], [pmid-37483405], [pmid-37567969], [pmid-37840846], [pmid-38646138], [pmid-39161564], [pmid-39877787], [pmid-40076617], [pmid-40269311], [pmid-40847681], [pmid-41035579], [pmid-41112815], [pmid-41797949], [pmid-42927143], [url-08fbb6ac79f2], [url-1c23e1dc296b], [url-3730726ce1a3], [url-6e9d1ea4030e], [url-71fabf45e585], [url-7878f52277db], [url-991aeae8d365], [url-a3204c897af7], [url-bf94bf8a0b06], [url-e7696d5604e8]
