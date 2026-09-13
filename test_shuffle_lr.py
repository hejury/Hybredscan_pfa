import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

df = pd.read_csv("datasets/docx/Word_All_features.csv").drop_duplicates()

features = [
    "struct_pos",
    "struct_val",
    "struct_typeface",
    "struct_script"
]

X = df[features].fillna(0)
y = pd.Series(np.random.RandomState(42).permutation(df["label"].values))

model = make_pipeline(
    StandardScaler(),
    LogisticRegression(max_iter=2000, random_state=42)
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

print("Logistic Regression - Label Shuffle Test")
print("Scores:", scores)
print(f"Mean Accuracy: {scores.mean():.4f}")
print(f"Std: {scores.std():.4f}")
