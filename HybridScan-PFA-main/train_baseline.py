import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

DATASET = r"C:\Users\tmt\Downloads\Word_All_features.csv"

df = pd.read_csv(DATASET)

# Remove target and non-feature columns
X = df.drop(columns=["label"])
y = df["label"]

# Train/Test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print(f"Training samples: {len(X_train)}")
print(f"Testing samples : {len(X_test)}")
print(f"Features         : {X.shape[1]}")

# Random Forest
model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)

# Prediction
y_pred = model.predict(X_test)

# Metrics
print("\n========================================")
print("BASELINE RESULTS")
print("========================================")
print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision: {precision_score(y_test, y_pred):.4f}")
print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
print(f"F1-Score: {f1_score(y_test, y_pred):.4f}")

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    target_names=["Benign", "Malicious"]
))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))