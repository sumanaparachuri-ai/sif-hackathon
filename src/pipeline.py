"""
End-to-end pipeline: ingest raw reports -> classify SIF potential ->
tag Life-Saving Rule -> extract precursors -> aggregate for dashboard.

Run:
    python src/pipeline.py

Produces:
    data/processed_reports.csv   (row-level enriched data)
    data/site_activity_rank.csv  (site x activity SIF-precursor density ranking)
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from lsr_tagger import tag_life_saving_rules, primary_rule
from precursor_extractor import extract_precursors
from sif_classifier import train, load_model, predict, MODEL_PATH

RAW_PATH = "data/reports.csv"
PROCESSED_PATH = "data/processed_reports.csv"
RANK_PATH = "data/site_activity_rank.csv"


def run_pipeline():
    df = pd.read_csv(RAW_PATH)

    # 1) Train (or load) SIF classifier and predict probability for every report.
    if not os.path.exists(MODEL_PATH):
        model = train(RAW_PATH, MODEL_PATH)
    else:
        model = load_model(MODEL_PATH)
    preds, probs = predict(df["description"].tolist(), model=model)
    df["sif_predicted"] = preds
    df["sif_probability"] = probs.round(3)

    # 2) Tag IOGP Life-Saving Rule.
    df["life_saving_rule"] = df["description"].apply(primary_rule)
    df["lsr_all_matches"] = df["description"].apply(lambda t: [r for r, s in tag_life_saving_rules(t, top_k=3) if s > 0])

    # 3) Extract precursor signals.
    precursors = df["description"].apply(extract_precursors).apply(pd.Series)
    df = pd.concat([df, precursors], axis=1)

    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Processed {len(df)} reports -> {PROCESSED_PATH}")

    # 4) Aggregate: SIF-precursor density ranking per site x activity_category.
    agg = (
        df.groupby(["site", "activity_category"])
        .agg(
            total_reports=("report_id", "count"),
            sif_flagged=("sif_predicted", "sum"),
        )
        .reset_index()
    )
    agg["sif_density_pct"] = (agg["sif_flagged"] / agg["total_reports"] * 100).round(1)
    agg = agg.sort_values(["sif_density_pct", "sif_flagged"], ascending=False)
    agg.to_csv(RANK_PATH, index=False)
    print(f"Site x Activity SIF-density ranking -> {RANK_PATH}")

    return df, agg


if __name__ == "__main__":
    run_pipeline()
