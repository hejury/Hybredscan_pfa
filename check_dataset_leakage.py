import pandas as pd


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

df = df.drop(columns=existing_drop)

features = [c for c in df.columns if c != "label"]


# ========================================
# CHECK 1 — UNIQUE VALUES
# ========================================

print("========================================")
print("DATASET LEAKAGE CHECK")
print("========================================")

print(f"Samples  : {len(df)}")
print(f"Features : {len(features)}")


# ========================================
# CHECK 2 — CLASS STATISTICS
# ========================================

print("\n========================================")
print("FEATURE CLASS SEPARATION")
print("========================================")

suspicious = []

for feature in features:

    benign = df[df["label"] == 0][feature]
    malicious = df[df["label"] == 1][feature]

    benign_min = benign.min()
    benign_max = benign.max()

    malicious_min = malicious.min()
    malicious_max = malicious.max()

    overlap = not (
        benign_max < malicious_min
        or malicious_max < benign_min
    )

    if not overlap:
        suspicious.append(feature)

    print(f"\n{feature}")
    print(f"  Benign   : min={benign_min} max={benign_max}")
    print(f"  Malicious: min={malicious_min} max={malicious_max}")
    print(f"  Overlap  : {'YES' if overlap else 'NO'}")


# ========================================
# SUMMARY
# ========================================

print("\n========================================")
print("SUMMARY")
print("========================================")

print(
    f"Features with NO class overlap: "
    f"{len(suspicious)} / {len(features)}"
)

if suspicious:

    print("\nPotentially suspicious features:")

    for feature in suspicious:
        print(f"  - {feature}")

else:

    print("\nNo feature has completely separated classes.")

print("\n========================================")
print("INTERPRETATION")
print("========================================")

if len(suspicious) >= 3:

    print(
        "WARNING: Several features completely separate "
        "Benign and Malicious classes."
    )

    print(
        "This strongly suggests dataset bias, leakage, "
        "or source-specific patterns."
    )

elif len(suspicious) > 0:

    print(
        "Some features completely separate the classes."
    )

    print(
        "Further investigation is recommended."
    )

else:

    print(
        "No complete feature-level separation detected."
    )

print("========================================")