#!/usr/bin/env python3
"""Build the analyses/ reports from the published-cases dataset and the cohort table.

  python3 tools/analyze.py          # writes analyses/published-cases.md and analyses/pooled-cohorts.md

Inputs: analyses/data/published-cases.csv (from tools/patients.py export) and analyses/data/cohorts.yaml.
Everything here combines numbers across records, which the knowledge base itself never does; the
protocol in analyses/protocol.md states the rules, and every table names its sources. Nothing in the
output is a source: it is the maintenance agent's own analysis of the records, unreviewed.
"""
import csv, math, os, statistics
from collections import Counter, defaultdict
import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
AN = os.path.join(ROOT, "analyses")
CASES = os.path.join(AN, "data", "published-cases.csv")
COHORTS = os.path.join(AN, "data", "cohorts.yaml")
PREFER = {"pmid": 0, "doi": 1, "url": 2}


def wilson(e, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = e / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def pct(e, n):
    return f"{e}/{n} ({100 * e / n:.0f}%)" if n else "0/0"


def ci_str(e, n):
    lo, hi = wilson(e, n)
    return f"{100 * lo:.0f} to {100 * hi:.0f}%"


def dl_pool(pairs):
    """DerSimonian-Laird random-effects pooled proportion on the logit scale. pairs = [(events, n), ...]."""
    ys, vs = [], []
    for e, n in pairs:
        a, b = e + 0.5, n - e + 0.5
        ys.append(math.log(a / b)); vs.append(1 / a + 1 / b)
    w = [1 / v for v in vs]
    yf = sum(wi * yi for wi, yi in zip(w, ys)) / sum(w)
    q = sum(wi * (yi - yf) ** 2 for wi, yi in zip(w, ys))
    k = len(pairs)
    c = sum(w) - sum(wi * wi for wi in w) / sum(w)
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    ws = [1 / (v + tau2) for v in vs]
    y = sum(wi * yi for wi, yi in zip(ws, ys)) / sum(ws)
    se = math.sqrt(1 / sum(ws))
    inv = lambda t: 1 / (1 + math.exp(-t))
    i2 = max(0.0, (q - (k - 1)) / q) if q > 0 else 0.0
    return inv(y), inv(y - 1.96 * se), inv(y + 1.96 * se), i2, tau2


def load_cases():
    rows = list(csv.DictReader(open(CASES)))
    for r in rows:
        for k in ("age_years", "mitoses_per_10hpf", "tumor_size_cm", "relapse_months", "follow_up_months"):
            r[k] = float(r[k]) if r[k] not in ("", None) else None
        r["relapse"] = {"True": True, "False": False}.get(r["relapse"])
        r["presentation"] = [p for p in r["presentation"].split(";") if p]
        r["overlaps"] = [o for o in r["overlaps_with"].split(";") if o]
    return rows


def dedupe(rows):
    """Drop a record's patients when it overlaps a record that also has patients and ranks higher
    (pmid over doi over url, then the longer record). Returns kept rows and the dropped record stems."""
    with_pat = {r["record"] for r in rows}
    dropped = set()
    for stem in sorted(with_pat):
        for other in {o for r in rows if r["record"] == stem for o in r["overlaps"]}:
            if other in with_pat and other != stem:
                a = (PREFER.get(stem.split("-")[0], 9), stem); b = (PREFER.get(other.split("-")[0], 9), other)
                dropped.add(stem if a > b else other)
    return [r for r in rows if r["record"] not in dropped], sorted(dropped)


def fmt_age(r):
    return f"{r['age_years']:.0f}" if r["age_years"] is not None else "not stated"


def age_group(a):
    if a is None:
        return "age not stated"
    return "under 8" if a < 8 else ("8 to 17" if a < 18 else "18 and over")


def stage_group(s):
    if not s:
        return "not stated"
    if s in ("IA", "IB"):
        return "IA/IB"
    if s.startswith("IC"):
        return "IC (any)"
    if s == "I":
        return "I, substage not stated"
    return "II to IV"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def cases_report():
    all_rows = load_cases()
    rows, dropped = dedupe(all_rows)
    uncertain = [r for r in rows if "classification uncertain" in (r["notes"] or "")]
    rows = [r for r in rows if r not in uncertain]
    ov = [r for r in rows if r["site"] == "ovary"]
    te = [r for r in rows if r["site"] == "testis"]
    recs = sorted({r["record"] for r in rows})
    out = []
    out.append("# Published JGCT cases: a patient-level dataset and descriptive analysis\n")
    out.append("**What this is.** The maintenance agent's own analysis of the patient-level rows extracted into the records of this knowledge base. It is not a source, has not been checked by a human, and is not medical advice. Read [the protocol](protocol.md) first: it states what was included, how duplicates were removed, and why no treatment effect is estimated. Every row traces to a record; the dataset is `data/published-cases.csv`.\n")
    out.append(f"**Dataset.** {len(all_rows)} patient rows from {len({r['record'] for r in all_rows})} records (full-text case reports, small series and complete meeting abstracts). {sum(1 for r in all_rows if r['record'] in dropped)} rows from {len(dropped)} records were dropped as duplicate reports of the same patients ({', '.join(dropped)}). {len(uncertain)} rows whose juvenile classification the source itself leaves uncertain were set aside ({', '.join(sorted({r['record'] for r in uncertain}))}). Analysed: **{len(rows)} patients** ({len(ov)} ovarian, {len(te)} testicular) from {len(recs)} records.\n")
    out.append("**Biases to keep in mind.** These are published cases: unusual presentations, syndromes, pregnancies, relapses and adult-age tumors are over-represented, and follow-up is short or missing in many. Proportions below describe the published literature, not the disease. The registry cohorts in [pooled-cohorts.md](pooled-cohorts.md) are the better guide to frequencies.\n")

    # ovary: age and presentation
    out.append("## Ovarian cases\n")
    ages = [r["age_years"] for r in ov if r["age_years"] is not None]
    out.append(f"### Age\n\nAge stated for {len(ages)} of {len(ov)}: median {statistics.median(ages):.1f} years (range {min(ages):.2f} to {max(ages):.0f}). ")
    ag = Counter(age_group(r["age_years"]) for r in ov)
    out.append(" ".join(f"{k}: {v}." for k, v in sorted(ag.items())) + "\n")
    out.append("### Presentation by age group\n")
    feats = ["precocious_puberty", "virilization", "abdominal_pain", "abdominal_mass_or_distension", "menstrual_change", "torsion", "rupture_or_hemoperitoneum", "ascites", "pregnancy", "incidental"]
    groups = ["under 8", "8 to 17", "18 and over"]
    trs = []
    for f in feats:
        cells = []
        for g in groups:
            sub = [r for r in ov if age_group(r["age_years"]) == g and r["presentation"]]
            cells.append(pct(sum(1 for r in sub if f in r["presentation"]), len(sub)))
        trs.append([f.replace("_", " ")] + cells)
    out.append("Denominators are patients in each age group with any presentation recorded.\n\n" + table(["feature"] + groups, trs) + "\n")

    # stage
    out.append("### Stage at diagnosis (as the source states it)\n")
    sc = Counter(r["stage"] or "not stated" for r in ov)
    out.append(table(["stage", "patients"], sorted(sc.items(), key=lambda x: (x[0] == "not stated", x[0]))) + "\n")
    staged = [r for r in ov if r["stage"]]
    s1 = sum(1 for r in staged if r["stage"].startswith("I") and not r["stage"].startswith("II") and not r["stage"].startswith("IV"))
    out.append(f"Among {len(staged)} staged patients, {pct(s1, len(staged))} were stage I (Wilson 95% CI {ci_str(s1, len(staged))}); the registries report about four in five. Published cases over-represent advanced disease.\n")

    # treatment
    out.append("### Treatment\n")
    sg = Counter(r["surgery"] or "unknown" for r in ov)
    out.append("Surgery: " + "; ".join(f"{k.replace('_', ' ')} {v}" for k, v in sg.most_common()) + ".\n")
    trs = []
    for g in ["IA/IB", "IC (any)", "I, substage not stated", "II to IV", "not stated"]:
        sub = [r for r in ov if stage_group(r["stage"]) == g]
        known = [r for r in sub if r["chemotherapy"]]
        chemo = [r for r in known if r["chemo_setting"] in ("adjuvant", "neoadjuvant")]
        none = [r for r in known if r["chemotherapy"] == "none" or r["chemo_setting"] == "none"]
        trs.append([g, len(sub), len(chemo), len(none), len(sub) - len(known)])
    out.append(table(["stage group", "patients", "adjuvant chemotherapy", "no adjuvant chemotherapy", "not stated"], trs) + "\n")

    # outcomes
    out.append("### Outcome by stage\n")
    trs = []
    for g in ["IA/IB", "IC (any)", "I, substage not stated", "II to IV", "not stated"]:
        sub = [r for r in ov if stage_group(r["stage"]) == g]
        oc = Counter(r["outcome"] for r in sub)
        fu = [r["follow_up_months"] for r in sub if r["follow_up_months"] is not None]
        rel = [r for r in sub if r["relapse"] is True]
        trs.append([g, len(sub), oc.get("NED", 0), oc.get("AWD", 0), oc.get("DOD", 0), oc.get("died_other", 0), oc.get("unknown", 0), len(rel),
                    f"{statistics.median(fu):.0f} (n={len(fu)})" if fu else "none"])
    out.append(table(["stage group", "patients", "NED", "alive with disease", "died of disease", "died, other cause", "unknown", "relapsed", "median follow-up, months"], trs) + "\n")
    known_oc = [r for r in ov if r["outcome"] != "unknown"]
    dod = sum(1 for r in known_oc if r["outcome"] == "DOD")
    out.append(f"Among {len(known_oc)} ovarian patients with a stated outcome, {pct(dod, len(known_oc))} died of disease (Wilson 95% CI {ci_str(dod, len(known_oc))}). Short follow-up in many NED rows makes this a lower bound on relapse and death.\n")

    # relapse timing
    rel = [r for r in ov if r["relapse"] is True]
    rm = [r["relapse_months"] for r in rel if r["relapse_months"] is not None]
    if rm:
        out.append(f"### Timing of relapse\n\n{len(rel)} ovarian patients relapsed; timing is stated for {len(rm)}: median {statistics.median(rm):.0f} months (range {min(rm):.0f} to {max(rm):.0f}); {sum(1 for m in rm if m <= 24)} of {len(rm)} within 24 months. The late ones: " +
                   "; ".join(f"{r['relapse_months']:.0f} months ({r['record']})" for r in sorted(rel, key=lambda r: -(r['relapse_months'] or 0)) if r["relapse_months"] and r["relapse_months"] > 24) + ".\n")

    # stage IC: what the dataset shows, no estimate
    ic = [r for r in ov if stage_group(r["stage"]) == "IC (any)"]
    ic_chemo = [r for r in ic if r["chemo_setting"] in ("adjuvant", "neoadjuvant")]
    ic_none = [r for r in ic if r["chemotherapy"] == "none" or r["chemo_setting"] == "none"]
    out.append("### Stage IC: adjuvant chemotherapy and relapse, counted but not compared\n")
    out.append(f"Of {len(ic)} stage IC patients, {len(ic_chemo)} received adjuvant chemotherapy ({sum(1 for r in ic_chemo if r['relapse'] is True)} relapsed, {sum(1 for r in ic_chemo if r['outcome']=='unknown')} with unknown outcome) and {len(ic_none)} did not ({sum(1 for r in ic_none if r['relapse'] is True)} relapsed, {sum(1 for r in ic_none if r['outcome']=='unknown')} unknown); the rest do not state chemotherapy. These counts are not a comparison: patients who received chemotherapy were selected for it, follow-up differs, rupture timing and substage are often missing, and the numbers are tiny. See the protocol for why no effect is estimated.\n")

    # mitotic index
    mi = [r for r in ov if r["mitoses_per_10hpf"] is not None and r["relapse"] is not None]
    if mi:
        hi = [r for r in mi if r["mitoses_per_10hpf"] >= 20]; lo = [r for r in mi if r["mitoses_per_10hpf"] < 20]
        out.append(f"### Mitotic index\n\nA count per 10 high-power fields and a relapse status are both stated for only {len(mi)} ovarian patients: {sum(1 for r in hi if r['relapse'])} of {len(hi)} with 20 or more relapsed, {sum(1 for r in lo if r['relapse'])} of {len(lo)} below 20. Too few to say anything; the registries (STEP, OTST, Kiel) are the evidence here, see pooled-cohorts.md.\n")

    # syndromes and pregnancy
    syn = [r for r in ov if r["syndrome"]]
    out.append("### Syndromes recorded\n\n" + "; ".join(f"{r['syndrome']} ({r['record']})" for r in syn) + f". {len(syn)} of {len(ov)} ovarian cases, a published-case rate that overstates the true frequency.\n")
    preg = [r for r in ov if "pregnancy" in r["presentation"]]
    out.append(f"### Pregnancy-associated cases\n\n{len(preg)} cases: " + "; ".join(f"age {fmt_age(r)}, stage {r['stage'] or 'not stated'}, {r['outcome']} ({r['record']})" for r in preg) + ".\n")

    # testis
    out.append("## Testicular cases\n")
    tages = [r["age_years"] for r in te if r["age_years"] is not None]
    toc = Counter(r["outcome"] for r in te)
    tsg = Counter(r["surgery"] or "unknown" for r in te)
    out.append(f"{len(te)} boys; age stated for {len(tages)}, median {statistics.median(tages) * 12:.1f} months (range {min(tages) * 12:.1f} to {max(tages) * 12:.0f} months). Surgery: " + "; ".join(f"{k.replace('_', ' ')} {v}" for k, v in tsg.most_common()) + f". Outcomes: NED {toc.get('NED', 0)}, unknown {toc.get('unknown', 0)}; no relapse, metastasis or death in any row; chemotherapy in none.\n")

    # records list
    out.append("## Records contributing patients\n\n" + ", ".join(f"[{s}]" for s in recs) + "\n")
    open(os.path.join(AN, "published-cases.md"), "w").write("\n".join(out))
    return len(rows)


def cohorts_report():
    coh = yaml.safe_load(open(COHORTS))
    out = ["# Pooled descriptive tables from the cohort studies\n",
           "**What this is.** Study-level counts copied from the records of the larger JGCT series and registries, shown side by side, with a crude pooled proportion and a random-effects pooled proportion (DerSimonian-Laird on the logit scale) where at least three non-overlapping cohorts report the same thing. It is the maintenance agent's own analysis, unreviewed, and not a source. Rows marked † rest on abstracts only. Overlapping cohorts (the same registry reported more than once, the same hospital at two dates, pooled reviews of published cases) are shown but only the row marked primary enters a pooled figure. See [the protocol](protocol.md).\n"]
    ov = [c for c in coh if c["site"] == "ovary"]
    te = [c for c in coh if c["site"] == "testis"]

    def mark(c):
        return c["label"] + (" †" if c["evidence_basis"] == "abstract" else "") + ("" if c.get("primary") else " (overlaps, not pooled)")

    # stage I
    out.append("## Proportion stage I at diagnosis (ovary)\n")
    rows = [c for c in ov if c.get("stage_I") is not None and c.get("n")]
    trs = [[mark(c), c["n"], pct(c["stage_I"], c["n"]), ci_str(c["stage_I"], c["n"])] for c in rows]
    out.append(table(["cohort", "n", "stage I", "95% CI"], trs))
    prim = [(c["stage_I"], c["n"]) for c in rows if c.get("primary")]
    if len(prim) >= 3:
        e = sum(p[0] for p in prim); n = sum(p[1] for p in prim)
        p, lo, hi, i2, _ = dl_pool(prim)
        out.append(f"\nCrude pooled, primary cohorts only: {pct(e, n)}. Random-effects pooled: {100 * p:.0f}% (95% CI {100 * lo:.0f} to {100 * hi:.0f}%), I² = {100 * i2:.0f}%. OTST reports 81% without a count and is not in the pool.\n")

    # relapse
    out.append("## Proportion relapsing (ovary, any stage, as each cohort defines follow-up)\n")
    rows = [c for c in ov if c.get("relapses") is not None and c.get("followed")]
    trs = [[mark(c), c["followed"], pct(c["relapses"], c["followed"]), ci_str(c["relapses"], c["followed"])] for c in rows]
    out.append(table(["cohort", "followed", "relapsed", "95% CI"], trs))
    prim = [(c["relapses"], c["followed"]) for c in rows if c.get("primary")]
    if len(prim) >= 3:
        e = sum(p[0] for p in prim); n = sum(p[1] for p in prim)
        p, lo, hi, i2, _ = dl_pool(prim)
        out.append(f"\nCrude pooled, primary cohorts only: {pct(e, n)}. Random-effects pooled: {100 * p:.0f}% (95% CI {100 * lo:.0f} to {100 * hi:.0f}%), I² = {100 * i2:.0f}%. The heterogeneity is real: cohorts differ in era, stage mix, follow-up and whether they are registries or single centers. The pooled figure is a description of the literature, not a risk for any patient.\n")

    # deaths
    out.append("## Proportion dying of disease (ovary)\n")
    rows = [c for c in ov if c.get("deaths_of_disease") is not None and c.get("followed")]
    trs = [[mark(c), c["followed"], pct(c["deaths_of_disease"], c["followed"]), ci_str(c["deaths_of_disease"], c["followed"])] for c in rows]
    out.append(table(["cohort", "followed", "died of disease", "95% CI"], trs))
    prim = [(c["deaths_of_disease"], c["followed"]) for c in rows if c.get("primary")]
    if len(prim) >= 3:
        e = sum(p[0] for p in prim); n = sum(p[1] for p in prim)
        p, lo, hi, i2, _ = dl_pool(prim)
        out.append(f"\nCrude pooled, primary cohorts only: {pct(e, n)}. Random-effects pooled: {100 * p:.0f}% (95% CI {100 * lo:.0f} to {100 * hi:.0f}%), I² = {100 * i2:.0f}%.\n")

    # mitotic
    out.append("## Mitotic index and relapse\n")
    rows = [c for c in ov if c.get("mitotic_low_n")]
    trs = [[mark(c), f"{c['mitotic_low_events']}/{c['mitotic_low_n']}", f"{c['mitotic_high_events']}/{c['mitotic_high_n']}", c.get("mitotic_note", "")] for c in rows]
    out.append(table(["cohort", "events, fewer than 20 per 10 HPF", "events, 20 or more", "note"], trs))
    out.append("\nOnly two cohorts give counts, and they overlap neither each other nor the Kiel registry figure (event-free survival 1.0 below 20 versus 0.48 at 20 or more, counts not stated †). Two cohorts are not pooled. Together they are the strongest consistent signal in the JGCT literature: every relapse with a known index was in the high group.\n")

    # lymph nodes
    out.append("## Lymph node metastasis at staging\n")
    rows = [c for c in ov if c.get("lymphadenectomy")]
    trs = [[mark(c), c["lymphadenectomy"], c["node_positive"]] for c in rows]
    out.append(table(["cohort", "patients with nodes removed", "node positive"], trs))
    out.append("\nWith the MD Anderson sex cord-stromal series (0 of 58, 27 JGCT among 257 patients †) and the OTST registry (none), no series has found a positive node at primary staging.\n")

    # chemo at IC: side by side
    out.append("## Chemotherapy at stage IC: what each source reports, not pooled\n")
    out.append(table(["source", "patients", "with chemotherapy", "without chemotherapy", "what it shows"], [
        ["STEP 2025 (full text)", "18 at IC2/IC3", "13, no relapse", "5, no relapse", "no relapses either way; IC1 (14): 1 treated, none relapsed"],
        ["OTST 2025 (full text)", "IC2 to IC3 subgroup", "most", "few", "3-year EFS 63.6%; effect not analysable, sicker patients treated"],
        ["Stage IC meta-analysis 2025 (full text)", "33 JGCT of 695", "17: 4 relapsed", "16: 0 relapsed", "no benefit; authors attribute to confounding by indication"],
        ["TGM-95 (abstract and SIOP abstract)", "15 with rupture or malignant ascites, mixed histology", "11 VIP: 0 relapsed", "4: 4 relapsed, 2 died (both Sertoli-Leydig)", "only series favouring chemotherapy; mixed histologies"],
        ["MAKEI 2003 †", "21 at IC", "9 treated", "12 observed", "IC event-free survival 0.76 overall; recommends chemotherapy for preoperative rupture or malignant ascites"],
        ["Plantaz 1992 †", "16 stage III (Wollner), 1965-1990", "13 chemotherapy overall", "", "no evidence that rupture required chemotherapy"],
        ["Wang 2022 †", "26 IC of 35", "31 of 35 treated", "4", "adjuvant chemotherapy not associated with disease-free survival"],
        ["Published cases here", "see published-cases.md", "", "", "counts only"],
    ]))
    out.append("\nThese cannot be pooled: three different definitions of stage IC, two of chemotherapy indication, non-random treatment assignment in every one, and in the only series where untreated patients relapsed the histologies were mixed. The honest summary is that no study has shown chemotherapy to change relapse at stage IC in JGCT, and no study was designed to.\n")

    # testis
    out.append("## Testicular JGCT: relapse or metastasis\n")
    rows = [c for c in te if c.get("n")]
    trs = [[mark(c), c["n"], c.get("relapses", c.get("metastases", "not stated"))] for c in rows]
    out.append(table(["cohort", "n", "relapses or metastases"], trs))
    out.append("\nNo cohort reports a relapse or metastasis of testicular JGCT. The systematic review pools the published cases and overlaps every series.\n")
    out.append("\n## Sources\n\n" + ", ".join(f"[{c['record']}]" for c in {c["record"]: c for c in coh}.values()) + "\n")
    open(os.path.join(AN, "pooled-cohorts.md"), "w").write("\n".join(out))


if __name__ == "__main__":
    n = cases_report()
    cohorts_report()
    print(f"analyses written: published-cases.md ({n} patients analysed), pooled-cohorts.md")
