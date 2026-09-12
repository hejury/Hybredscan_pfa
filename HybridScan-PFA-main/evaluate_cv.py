import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer

df = pd.read_csv("datasets/docx_baseline_dedup.csv")

drop = [
    "label",
    "macro_present",
    "dde_present",
    "vba_keywords_count",
    "ole_object_count",
    "ole_object_type_count",
]

X = df.drop(columns=drop)
y = df["label"]

model = make_pipeline(
    SimpleImputer(strategy="median"),
    RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    )
)

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

results = cross_validate(
    model,
    X,
    y,
    cv=cv,
    scoring=["accuracy", "precision", "recall", "f1"],
    n_jobs=1
)

for metric in ["accuracy", "precision", "recall", "f1"]:
    values = results["test_" + metric]
    print(
        metric,
        f"mean={values.mean():.4f}",
        f"std={values.std():.4f}"
    )