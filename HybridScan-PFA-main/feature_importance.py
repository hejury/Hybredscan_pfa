import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv("datasets/docx/Word_All_features.csv").drop_duplicates()

features = [
    "struct_typeface",
    "struct_script"
]

X = df[features].fillna(0)
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    stratify=y,
    random_state=42
)

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("Feature Importance:")
for feature, importance in zip(features, model.feature_importances_):
    print(f"{feature}: {importance:.4f}")
