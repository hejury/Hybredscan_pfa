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


# ========================================
# CONFIG
# ========================================

DATASET = r"C:\Users\tmt\Downloads\Word_All_features.csv"


# ========================================
# LOAD DATASET
# ========================================

df = pd.read_csv(DATASET)

print("Dataset loaded successfully")
print(f"Total samples: {len(df)}")


# ========================================
# REMOVE SUSPICIOUS / LEGACY FEATURES
# ========================================

DROP_FEATURES = [
    "macro_present",
    "dde_present",
    "vba_keywords_count",
    "ole_object_count",
    "ole_object_type_count",
]


existing_drop = [col for col in DROP_FEATURES if col in df.columns]

X = df.drop(columns=["label"] + existing_drop)
y = df["label"]

print("\nRemoved features:")
for feature in existing_drop:
    print(f"  - {feature}")

print(f"\nRemaining features: {X.shape[1]}")


# ========================================
# TRAIN / TEST SPLIT
# ========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


print("\n========================================")
print("DATA SPLIT")
print("========================================")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples : {len(X_test)}")
print(f"Features        : {X.shape[1]}")


# ========================================
# RANDOM FOREST
# ========================================

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1,
)


print("\nTraining model...")
model.fit(X_train, y_train)


# ========================================
# PREDICTION
# ========================================

y_pred = model.predict(X_test)


# ========================================
# RESULTS
# ========================================

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)


print("\n========================================")
print("BASELINE V2 RESULTS")
print("========================================")
print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1-Score : {f1:.4f}")


# ========================================
# CLASSIFICATION REPORT
# ========================================

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred,
        target_names=["Benign", "Malicious"],
    )
)


# ========================================
# CONFUSION MATRIX
# ========================================

print("Confusion Matrix:")

print(confusion_matrix(y_test, y_pred))


# ========================================
# FEATURE IMPORTANCE
# ========================================

importance = pd.Series(
    model.feature_importances_,
    index=X.columns,
).sort_values(ascending=False)


print("\n========================================")
print("TOP 15 FEATURE IMPORTANCES")
print("========================================")

print(importance.head(15))