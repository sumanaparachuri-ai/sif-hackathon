"""
IOGP Life-Saving Rule tagger.

Uses keyword/phrase matching against the 9 IOGP Life-Saving Rules. This is a
transparent, explainable rule-based approach - ideal for a hackathon demo since
it requires no training data and HSE reviewers can audit exactly why a tag was
applied. Can be swapped later for a zero-shot embedding classifier
(sentence-transformers) for better recall on unseen phrasing.
"""
import re

LSR_KEYWORDS = {
    "Energy Isolation": ["isolation", "loto", "lock out", "tag out", "de-energiz", "residual energy", "stored energy"],
    "Hot Work": ["hot work", "welding", "grinding", "cutting torch", "spark", "flammable atmosphere"],
    "Confined Space": ["confined space", "tank entry", "vessel entry", "gas test", "atmosphere monitoring", "manhole"],
    "Line of Fire": ["line of fire", "struck by", "pinch point", "dropped object", "suspended load", "swing radius"],
    "Working at Height": ["working at height", "scaffold", "fall arrest", "harness", "guardrail", "ladder", "edge protection"],
    "Safe Mechanical Lifting": ["crane", "lifting", "rigging", "sling", "load chart", "lifting plan", "tag line"],
    "Bypassing Safety Controls": ["bypass", "interlock defeated", "safety device disabled", "override", "alarm silenced"],
    "Driving Safety": ["driving", "vehicle", "seatbelt", "speeding", "fatigue", "journey management", "road"],
    "Work Authorization": ["permit to work", "work permit", "authorization", "unauthorized", "ptw not issued", "ptw"],
}


def tag_life_saving_rules(text: str, top_k: int = 2):
    """Return a list of (rule, score) tuples ranked by keyword-hit count.

    score is the raw number of keyword phrase matches found in the text.
    Only rules with score > 0 are returned, capped at top_k matches.
    """
    text_l = text.lower()
    scores = {}
    for rule, keywords in LSR_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text_l)
        if hits:
            scores[rule] = hits
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_k] if ranked else [("Unclassified", 0)]


def primary_rule(text: str) -> str:
    ranked = tag_life_saving_rules(text, top_k=1)
    return ranked[0][0]


if __name__ == "__main__":
    sample = "Worker was on scaffold without fall arrest harness during working at height task."
    print(tag_life_saving_rules(sample))
