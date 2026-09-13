import os
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

CSV = "datasets/docx/Word_All_features.csv"
MODEL = "model_docx_v2.pkl"

RANDOM_STATE = 42
TEST_SIZE = 0.20
VALIDATION_SIZE = 0.20


def main():
    print("=" * 70)
    print("HybridScan - DOCX V2 training")
    print("=" * 70)

    if not os.path.exists(CSV):
        raise FileNotFoundError(f"Dataset introuvable: {CSV}")

    df = pd.read_csv(CSV)

    print(f"\nDataset shape: {df.shape}")
    print("\nLabels:")
    print(df["label"].value_counts().to_dict())

    # ------------------------------------------------------------
    # Nettoyage
    # ------------------------------------------------------------
    df = df.dropna(subset=["label"]).copy()

    y = df["label"].astype(int)

    # Toutes les colonnes sauf label
    feature_columns = [c for c in df.columns if c != "label"]

    X = df[feature_columns].copy()

    # Convertir les colonnes en numérique.
    # Les valeurs non convertibles deviennent NaN.
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    # Remplacer les valeurs manquantes par 0.
    X = X.fillna(0)

    print(f"\nNombre de features utilisées: {len(feature_columns)}")

    # ------------------------------------------------------------
    # Train / validation / test
    #
    # 60% train
    # 20% validation
    # 20% test
    # ------------------------------------------------------------

    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    validation_relative = VALIDATION_SIZE / (1.0 - TEST_SIZE)

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=validation_relative,
        random_state=RANDOM_STATE,
        stratify=y_train_val,
    )

    print("\nSplit:")
    print("  Train      :", len(X_train))
    print("  Validation :", len(X_val))
    print("  Test       :", len(X_test))

    # ------------------------------------------------------------
    # Modèle
    # ------------------------------------------------------------

    clf = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        max_depth=None,
    )

    print("\nTraining RandomForest...")
    clf.fit(X_train, y_train)

    # ------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------

    def evaluate(name, X_eval, y_eval):
        pred = clf.predict(X_eval)
        proba = clf.predict_proba(X_eval)[:, 1]

        accuracy = accuracy_score(y_eval, pred)
        precision = precision_score(y_eval, pred, zero_division=0)
        recall = recall_score(y_eval, pred, zero_division=0)
        f1 = f1_score(y_eval, pred, zero_division=0)
        auc = roc_auc_score(y_eval, proba)

        print("\n" + "=" * 70)
        print(name)
        print("=" * 70)

        print(f"Accuracy  : {accuracy:.4f}")
        print(f"Precision : {precision:.4f}")
        print(f"Recall    : {recall:.4f}")
        print(f"F1        : {f1:.4f}")
        print(f"ROC-AUC   : {auc:.4f}")

        print("\nConfusion matrix:")
        print(confusion_matrix(y_eval, pred))

        return {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "roc_auc": float(auc),
            "confusion_matrix": confusion_matrix(
                y_eval, pred
            ).tolist(),
        }

    validation_metrics = evaluate(
        "VALIDATION",
        X_val,
        y_val,
    )

    test_metrics = evaluate(
        "TEST",
        X_test,
        y_test,
    )

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            clf.predict(X_test),
            target_names=["sain", "malveillant"],
            zero_division=0,
        )
    )

    # ------------------------------------------------------------
    # Feature importance
    # ------------------------------------------------------------

    importances = sorted(
        zip(feature_columns, clf.feature_importances_),
        key=lambda x: -x[1],
    )

    print("\nTop 20 features:")
    for name, value in importances[:20]:
        print(f"  {name:45s} {value:.6f}")

    # ------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------

    metadata = {
        "model_family": "RandomForestClassifier",
        "model_version": "docx_v2",
        "supported_formats": ["docx"],
        "random_seed": RANDOM_STATE,
        "n_estimators": 300,
        "class_weight": "balanced",

        "dataset": CSV,
        "dataset_rows": int(len(df)),
        "dataset_columns": int(len(df.columns)),

        "train_rows": int(len(X_train)),
        "validation_rows": int(len(X_val)),
        "test_rows": int(len(X_test)),

        "class_distribution": {
            "train": y_train.value_counts().to_dict(),
            "validation": y_val.value_counts().to_dict(),
            "test": y_test.value_counts().to_dict(),
        },

        "evaluation_validation": validation_metrics,
        "evaluation_test": test_metrics,

        "feature_count": len(feature_columns),
        "features": feature_columns,

        "research_only": True,
        "production_ready": False,
    }

    bundle = {
        "model": clf,
        "features": feature_columns,
        "seuil": 0.5,
        "metadata": metadata,
    }

    joblib.dump(bundle, MODEL)

    print("\n" + "=" * 70)
    print(f"Model saved: {MODEL}")
    print("=" * 70)

    print("\nFeatures saved:")
    for feature in feature_columns:
        print(" -", feature)


if __name__ == "__main__":
    main()