"""
SIF (Serious Injury or Fatality) potential classifier.

Baseline: TF-IDF + Logistic Regression trained on labeled report text.
Chosen for the hackathon because it:
  - trains in seconds on a few hundred rows,
  - is fully explainable (inspect top TF-IDF coefficients per class),
  - has no external API/model download dependency.

Swap-in upgrade path (post-hackathon): fine-tune a transformer (e.g.
DistilBERT) once real labeled OIL data is available for higher accuracy.
"""
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline

MODEL_PATH = "src/sif_model.joblib"


def train(reports_csv="data/reports.csv", model_path=MODEL_PATH):
    df = pd.read_csv(reports_csv)
    X_train, X_test, y_train, y_test = train_test_split(
        df["description"], df["sif_potential"], test_size=0.2, random_state=42, stratify=df["sif_potential"]
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english")),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    print("=== SIF Classifier Evaluation ===")
    print(classification_report(y_test, preds, target_names=["Non-SIF", "SIF-Potential"]))

    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")
    return pipeline


def load_model(model_path=MODEL_PATH):
    return joblib.load(model_path)


def predict(texts, model=None, model_path=MODEL_PATH):
    if model is None:
        model = load_model(model_path)
    probs = model.predict_proba(texts)[:, 1]
    preds = (probs >= 0.5).astype(int)
    return preds, probs


if __name__ == "__main__":
    train()
