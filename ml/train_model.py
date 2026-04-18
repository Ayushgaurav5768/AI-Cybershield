import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "ml" / "dataset"
MODEL_PATH = BASE_DIR / "ml" / "model.pkl"
META_PATH = BASE_DIR / "ml" / "model_meta.json"


def find_dataset_path() -> Path:
    preferred = DATASET_DIR / "phishing.csv"
    if preferred.exists():
        return preferred

    csv_files = sorted(DATASET_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV dataset found in: {DATASET_DIR}")
    return csv_files[0]


dataset_path = find_dataset_path()
df = pd.read_csv(dataset_path)

if df.empty:
    raise ValueError(f"Dataset is empty: {dataset_path}")

target_candidates = ["label", "target", "class", "is_phishing", "result"]
column_lookup = {col.strip().lower(): col for col in df.columns}
target_col = next(
    (column_lookup[candidate] for candidate in target_candidates if candidate in column_lookup),
    None,
)
if target_col is None:
    raise ValueError(
        f"Target column not found. Expected one of {target_candidates}. "
        f"Found columns: {list(df.columns)}"
    )

X = df.drop(columns=[target_col])
y = df[target_col]

if X.shape[1] == 0:
    raise ValueError("No feature columns found after removing target column.")

non_numeric_cols = X.select_dtypes(exclude=["number", "bool"]).columns.tolist()
if non_numeric_cols:
    raise ValueError(
        f"Non-numeric feature columns found: {non_numeric_cols}. "
        "Encode or remove them before training."
    )

stratify_y = y if y.nunique() > 1 else None
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=stratify_y
)

model = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.4f}")

joblib.dump(model, MODEL_PATH)

meta = {
    "dataset_path": str(dataset_path),
    "target_column": target_col,
    "feature_columns": X.columns.tolist(),
    "n_rows": int(df.shape[0]),
    "n_features": int(X.shape[1]),
    "accuracy": float(accuracy),
}
with open(META_PATH, "w", encoding="utf-8") as file:
    json.dump(meta, file, indent=2)

print(f"Model saved successfully at: {MODEL_PATH}")
print(f"Metadata saved successfully at: {META_PATH}")
