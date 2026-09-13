from pathlib import Path
import csv
import sys

from extract_docx_features import extract_docx_features


BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets" / "docx_training"
OUTPUT_FILE = DATASET_DIR / "docx_features.csv"

CLASSES = {
    "benign": 0,
    "malicious": 1,
}


def main():
    rows = []

    for class_name, label in CLASSES.items():
        folder = DATASET_DIR / class_name
        files = sorted(folder.rglob("*.docx"))

        print(f"\n[{class_name.upper()}] {len(files)} DOCX files")

        for i, path in enumerate(files, start=1):
            try:
                features = extract_docx_features(str(path))
                features["label"] = label
                rows.append(features)

                if i % 100 == 0 or i == len(files):
                    print(f"  Processed: {i}/{len(files)}")

            except Exception as e:
                print(f"  SKIPPED: {path.name} -> {e}")

    if not rows:
        print("No valid DOCX files found.")
        sys.exit(1)

    fieldnames = list(rows[0].keys())

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("\n========================================")
    print("DATASET CREATED")
    print("========================================")
    print(f"Rows    : {len(rows)}")
    print(f"Features: {len(fieldnames) - 1}")
    print(f"Output  : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()