"""
Precursor pattern extractor.

Extracts structured precursor signals from free-text reports:
- activity category (what task was being performed)
- barrier_failure (what safety control failed / was missing)
- site (already structured in most HSSE systems, passed through)

This enables the dashboard to compute recurring precursor combinations
(e.g., "Confined Space entry + gas test not performed" at "Duliajan Field")
which is the core of the SIF-precursor density ranking.
"""
import re

BARRIER_PATTERNS = {
    "Permit Not Issued": ["permit to work not issued", "ptw not issued", "no lifting plan"],
    "PPE Non-Compliance": ["ppe", "harness/gloves/goggles", "not worn correctly"],
    "Gas Test Skipped": ["gas test not performed", "atmosphere monitoring"],
    "Isolation Not Verified": ["isolation point not verified", "lock and tag"],
    "Barricade/Signage Missing": ["barricade", "warning signage missing"],
    "Inadequate Supervision": ["supervision inadequate"],
    "Communication Failure": ["communication breakdown"],
    "Risk Assessment Skipped": ["toolbox talk", "risk assessment not conducted"],
    "Defective Equipment": ["equipment inspection overdue", "defective tool"],
    "Unqualified Personnel": ["unqualified rigger"],
}

ACTIVITY_PATTERNS = {
    "Working at Height": ["working at height", "scaffolding"],
    "Hot Work": ["hot work", "welding"],
    "Confined Space Entry": ["confined space entry", "tank entry", "vessel entry"],
    "Mechanical Lifting": ["lifting with mobile crane", "crane"],
    "Driving / Vehicle Movement": ["driving light vehicle", "vehicle movement"],
    "Energy Isolation / LOTO": ["energy isolation", "loto"],
    "Line of Fire Exposure": ["line of fire", "pipe fitting removal"],
    "Electrical Maintenance": ["electrical panel maintenance"],
    "Excavation": ["excavation near buried pipeline"],
    "Inspection / Housekeeping": ["routine equipment inspection", "housekeeping"],
}


def _match_category(text_l: str, patterns: dict) -> str:
    for category, keywords in patterns.items():
        if any(kw in text_l for kw in keywords):
            return category
    return "Other"


def extract_precursors(text: str) -> dict:
    text_l = text.lower()
    return {
        "activity_category": _match_category(text_l, ACTIVITY_PATTERNS),
        "barrier_failure": _match_category(text_l, BARRIER_PATTERNS),
    }


if __name__ == "__main__":
    sample = "During confined space entry into storage tank at Duliajan Field, gas test not performed before entry."
    print(extract_precursors(sample))
