# SIF-Precursor Intelligence Prototype (OIL HSSE Hackathon)

A working prototype that ingests free-text UA/UC observations, near-miss, and
incident reports and:

1. **Classifies** each report as SIF-potential (Serious Injury or Fatality
   potential) vs non-SIF-potential.
2. **Tags** each report to the relevant IOGP Life-Saving Rule (Energy
   Isolation, Hot Work, Confined Space, Line of Fire, Working at Height, Safe
   Mechanical Lifting, Bypassing Safety Controls, Driving Safety, Work
   Authorization).
3. **Surfaces recurring precursor patterns** (activity, barrier failure,
   site) via an interactive Streamlit dashboard that ranks sites/activities
   by SIF-precursor density.

> No real OIL data was available for this hackathon build, so
> `data/generate_synthetic_data.py` produces realistic labeled reports using
> weak-supervision heuristics (high-energy activity + high-risk barrier
> failure => elevated SIF-potential probability), mirroring the logic behind
> DEKRA/EEI/VelocityEHS PSIF classifiers. Swap in real HSSE export data by
> matching the same CSV schema (see below) and skipping the generator step.

## Architecture

```
data/generate_synthetic_data.py   -> data/reports.csv (raw reports)
src/sif_classifier.py             -> TF-IDF + Logistic Regression, SIF-potential probability
src/lsr_tagger.py                 -> keyword-based IOGP Life-Saving Rule tagging (explainable)
src/precursor_extractor.py        -> activity/barrier-failure precursor extraction
src/pipeline.py                   -> orchestrates all of the above -> data/processed_reports.csv
                                      + data/site_activity_rank.csv (SIF-density ranking)
dashboard/app.py                  -> Streamlit dashboard consuming processed data
```

## Setup & Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Generate synthetic reports (skip if you have real data in the same schema)
python data\generate_synthetic_data.py

# 2. Run the classification + tagging + extraction pipeline
python src\pipeline.py

# 3. Launch the dashboard
streamlit run dashboard\app.py
```
Open http://localhost:8501

## Input CSV Schema (for plugging in real OIL data)
| column      | description                                   |
|-------------|------------------------------------------------|
| report_id   | unique report identifier                        |
| date        | YYYY-MM-DD                                       |
| site        | facility/site name                               |
| report_type | UA / UC / Near-Miss / Incident                   |
| activity    | free text or category of activity being performed|
| description | free-text observation/incident narrative         |
| sif_potential | (optional) 1/0 ground-truth label for training  |

If `sif_potential` labels aren't available, use the rule-based heuristic in
the generator as a bootstrapped weak-label set, then have HSE reviewers
correct a sample to fine-tune the classifier (active learning loop) —
recommended next step post-hackathon.

## Dashboard Features
- KPI summary: total reports, % SIF-potential, top Life-Saving Rule, sites covered.
- **SIF-Precursor Density Ranking**: top site x activity combinations with
  highest % of SIF-flagged reports — tells HSE where to focus interventions.
- **Heatmap**: Site x Life-Saving Rule count of SIF-flagged reports.
- **Recurring precursor patterns**: most common activity + barrier-failure combinations.
- **Report Explorer**: drill down into raw report text, filterable by site/rule/type.

## Next Steps (post-hackathon roadmap)
1. Replace synthetic data with real OIL HSSE export; retrain classifier on
   actual investigator-confirmed SIF labels.
2. Upgrade LSR tagging from keyword-based to a fine-tuned/zero-shot transformer
   for better recall on varied phrasing.
3. Add NER model for automated activity/location/equipment extraction instead
   of keyword pattern matching.
4. Add feedback loop: HSE reviewer confirms/corrects SIF flag -> retrain model
   periodically (active learning).
5. Integrate directly with OIL's HSSE platform via API for real-time ingestion
   instead of batch CSV.
