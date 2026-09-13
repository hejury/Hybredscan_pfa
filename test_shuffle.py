import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv("datasets/docx/Word_All_features.csv").drop_duplicates()

features = [
    "struct_pos",
    "struct_val",
    "struct_typeface",
    "struct_script"
]

X = df[features].fillna(0)
y = df["label"].copy()

rng = np.random.RandomState(42)
y = pd.Series(rng.permutation(y.values), index=y.index)

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

scores = cross_val_score(
    model,
    X,
    y,
    cv=cv,
    scoring="accuracy",
    n_jobs=-1
)

print("Label Shuffle Test")
print("Scores:", scores)
print(f"Mean Accuracy: {scores.mean():.4f}")
print(f"Std: {scores.std():.4f}")
