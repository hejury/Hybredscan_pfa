import pandas as pd

from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import make_scorer, accuracy_score, precision_score, recall_score, f1_score


# ========================================
# CONFIG
# ========================================

DATASET = r"C:\Users\tmt\Downloads\Word_All_features.csv"

DROP_FEATURES = [
    "macro_present",
    "dde_present",
    "vba_keywords_count",
    "ole_object_count",
    "ole_object_type_count",
]


# ========================================
# LOAD DATA
# ========================================

df = pd.read_csv(DATASET)

existing_drop = [c for c in DROP_FEATURES if c in df.columns]

X = df.drop(columns=["label"] + existing_drop)
y = df["label"]

print("========================================")
print("CROSS-VALIDATION EVALUATION")
print("========================================")
print(f"Samples  : {len(X)}")
print(f"Features : {X.shape[1]}")
print(f"Dropped  : {len(existing_drop)}")


# ========================================
# MODEL
# ========================================

model = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    (
        "classifier",
        RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            n_jobs=-1,
        ),
    ),
])


# ========================================
# 5-FOLD STRATIFIED CROSS-VALIDATION
# ========================================

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42,
)


scoring = {
    "accuracy": make_scorer(accuracy_score),
    "precision": make_scorer(precision_score),
    "recall": make_scorer(recall_score),
    "f1": make_scorer(f1_score),
}


results = cross_validate(
    model,
    X,
    y,
    cv=cv,
    scoring=scoring,
    n_jobs=-1,
)


# ========================================
# RESULTS
# ========================================

print("\n========================================")
print("5-FOLD RESULTS")
print("========================================")

for i in range(5):
    print(
        f"Fold {i + 1}: "
        f"Accuracy={results['test_accuracy'][i]:.4f} | "
        f"Precision={results['test_precision'][i]:.4f} | "
        f"Recall={results['test_recall'][i]:.4f} | "
        f"F1={results['test_f1'][i]:.4f}"
    )


print("\n========================================")
print("MEAN RESULTS")
print("========================================")

print(
    f"Accuracy : "
    f"{results['test_accuracy'].mean():.4f} "
    f"+/- {results['test_accuracy'].std():.4f}"
)

print(
    f"Precision: "
    f"{results['test_precision'].mean():.4f} "
    f"+/- {results['test_precision'].std():.4f}"
)

print(
    f"Recall   : "
    f"{results['test_recall'].mean():.4f} "
    f"+/- {results['test_recall'].std():.4f}"
)

print(
    f"F1-Score : "
    f"{results['test_f1'].mean():.4f} "
    f"+/- {results['test_f1'].std():.4f}"
)