import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv("datasets/docx/Word_All_features.csv").drop_duplicates()

features = [
    "struct_typeface",
    "struct_script",
    "struct_pos",
    "struct_val",
    "struct_ContentType",
    "struct_PartName",
    "entropy",
    "file_size"
]

X = df[features].fillna(0)
y = df["label"]

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

scores = cross_validate(
    model,
    X,
    y,
    cv=cv,
    scoring=["accuracy", "precision", "recall", "f1"],
    n_jobs=-1
)

for metric in ["accuracy", "precision", "recall", "f1"]:
    values = scores["test_" + metric]
    print(f"{metric.capitalize()}: {values.mean():.4f} +/- {values.std():.4f}")
