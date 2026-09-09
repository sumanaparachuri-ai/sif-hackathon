"""
Synthetic UA/UC + Near-Miss + Incident report generator.

Since real OIL HSSE data isn't available for the hackathon, this script generates
realistic free-text safety observation reports covering the 9 IOGP Life-Saving
Rules, with weak-supervision labels for SIF-potential (Serious Injury or
Fatality potential) based on presence of high-energy sources + barrier failures.

Output: data/reports.csv
"""
import random
import csv
from datetime import datetime, timedelta

random.seed(42)

SITES = [
    "Duliajan Field", "Digboi Refinery", "Numaligarh Terminal", "Moran GGS",
    "Barekuri Well Pad", "Kumchai Compressor Station", "Naharkatiya Tank Farm",
    "Jorajan Pipeline ROW", "Duliajan Workshop", "Lakwa Gas Plant",
]

ACTIVITIES = [
    "working at height on scaffolding", "hot work / welding near flammable storage",
    "confined space entry into storage tank", "manual lifting with mobile crane",
    "driving light vehicle on site road", "energy isolation / LOTO on pump",
    "line of fire during pipe fitting removal", "electrical panel maintenance",
    "excavation near buried pipeline", "vehicle movement in loading bay",
    "routine equipment inspection round", "housekeeping / material storage",
]

# Keyword banks per IOGP Life-Saving Rule (used both for generation and later
# tagging validation)
LSR_KEYWORDS = {
    "Energy Isolation": ["isolation", "loto", "lock out", "tag out", "de-energized", "residual energy", "pump isolation"],
    "Hot Work": ["hot work", "welding", "grinding", "cutting torch", "spark", "gas test", "flammable"],
    "Confined Space": ["confined space", "tank entry", "vessel entry", "gas testing", "atmosphere monitoring", "manhole"],
    "Line of Fire": ["line of fire", "struck by", "pinch point", "dropped object", "suspended load", "swing radius"],
    "Working at Height": ["working at height", "scaffold", "fall arrest", "harness", "guardrail", "ladder", "edge protection"],
    "Safe Mechanical Lifting": ["crane", "lifting", "rigging", "sling", "load chart", "lifting plan", "tag line"],
    "Bypassing Safety Controls": ["bypass", "interlock defeated", "safety device disabled", "override", "alarm silenced"],
    "Driving Safety": ["driving", "vehicle", "seatbelt", "speeding", "fatigue", "journey management", "road"],
    "Work Authorization": ["permit to work", "work permit", "authorization", "unauthorized", "ptw not issued"],
}

BARRIER_FAILURES = [
    "permit to work not issued before starting job",
    "PPE (harness/gloves/goggles) not worn correctly",
    "gas test not performed before entry",
    "isolation point not verified with lock and tag",
    "barricade/warning signage missing at work area",
    "supervision inadequate for high-risk task",
    "communication breakdown between crew and control room",
    "toolbox talk / risk assessment not conducted",
    "equipment inspection overdue / defective tool used",
    "no lifting plan / unqualified rigger used",
]

REPORT_TYPES = ["UA", "UC", "Near-Miss", "Incident"]

TEMPLATES = [
    "During {activity} at {site}, it was observed that {barrier}. This created a direct exposure to {lsr_context}.",
    "{report_type} raised at {site}: worker engaged in {activity} without following procedure - {barrier}.",
    "While conducting {activity}, a {report_type_lc} occurred at {site} because {barrier}.",
    "Observation ({report_type}) at {site} - {activity} in progress, however {barrier}, increasing risk of {lsr_context}.",
    "Field audit at {site} identified {activity} where {barrier}. No injury occurred but potential for {lsr_context} was high.",
]

LSR_CONTEXT = {
    "Energy Isolation": "unexpected equipment start-up / stored energy release",
    "Hot Work": "fire or explosion in presence of flammable atmosphere",
    "Confined Space": "asphyxiation or toxic gas exposure",
    "Line of Fire": "being struck by moving/falling/suspended object",
    "Working at Height": "fall from height",
    "Safe Mechanical Lifting": "dropped load / crane failure",
    "Bypassing Safety Controls": "loss of critical safety function",
    "Driving Safety": "vehicle collision",
    "Work Authorization": "uncontrolled/unauthorized simultaneous operations",
}

ACTIVITY_TO_LSR = {
    "working at height on scaffolding": "Working at Height",
    "hot work / welding near flammable storage": "Hot Work",
    "confined space entry into storage tank": "Confined Space",
    "manual lifting with mobile crane": "Safe Mechanical Lifting",
    "driving light vehicle on site road": "Driving Safety",
    "energy isolation / LOTO on pump": "Energy Isolation",
    "line of fire during pipe fitting removal": "Line of Fire",
    "electrical panel maintenance": "Energy Isolation",
    "excavation near buried pipeline": "Line of Fire",
    "vehicle movement in loading bay": "Driving Safety",
    "routine equipment inspection round": "Work Authorization",
    "housekeeping / material storage": "Bypassing Safety Controls",
}

# High-severity barrier failures that materially increase SIF potential when combined
# with a high-energy activity (weak-supervision heuristic, mirrors PSIF classifiers).
HIGH_RISK_BARRIERS = {
    "permit to work not issued before starting job",
    "isolation point not verified with lock and tag",
    "gas test not performed before entry",
    "no lifting plan / unqualified rigger used",
    "PPE (harness/gloves/goggles) not worn correctly",
}

HIGH_ENERGY_ACTIVITIES = {
    "working at height on scaffolding", "hot work / welding near flammable storage",
    "confined space entry into storage tank", "manual lifting with mobile crane",
    "energy isolation / LOTO on pump", "line of fire during pipe fitting removal",
    "electrical panel maintenance",
}


def make_report(i, base_date):
    site = random.choice(SITES)
    activity = random.choice(ACTIVITIES)
    barrier = random.choice(BARRIER_FAILURES)
    report_type = random.choices(REPORT_TYPES, weights=[0.35, 0.30, 0.20, 0.15])[0]
    lsr = ACTIVITY_TO_LSR[activity]
    template = random.choice(TEMPLATES)

    text = template.format(
        activity=activity, site=site, barrier=barrier,
        report_type=report_type, report_type_lc=report_type.lower(),
        lsr_context=LSR_CONTEXT[lsr],
    )

    # Weak-supervision SIF label: high-energy activity + high-risk barrier failure
    # => genuine fatal potential. Add small random noise to mimic real-world messiness.
    is_high_energy = activity in HIGH_ENERGY_ACTIVITIES
    is_high_risk_barrier = barrier in HIGH_RISK_BARRIERS
    base_prob = 0.75 if (is_high_energy and is_high_risk_barrier) else (0.25 if is_high_energy else 0.05)
    sif_potential = 1 if random.random() < base_prob else 0

    date = base_date + timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))

    return {
        "report_id": f"RPT-{i:05d}",
        "date": date.strftime("%Y-%m-%d"),
        "site": site,
        "report_type": report_type,
        "activity": activity,
        "description": text,
        "sif_potential": sif_potential,  # ground-truth (weak) label for training/eval
    }


def main(n=800, out_path="data/reports.csv"):
    base_date = datetime(2025, 1, 1)
    rows = [make_report(i, base_date) for i in range(1, n + 1)]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic reports to {out_path}")


if __name__ == "__main__":
    main()
