from pathlib import Path
import shutil


BASE_DIR = Path(__file__).resolve().parent

SOURCE_DIR = BASE_DIR / "datasets" / "docx_training"
OUTPUT_DIR = BASE_DIR / "datasets" / "docx_training_clean"

CLASSES = ["benign", "malicious"]


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    duplicates = 0

    for class_name in CLASSES:

        source = SOURCE_DIR / class_name
        target = OUTPUT_DIR / class_name

        target.mkdir(parents=True, exist_ok=True)

        files = sorted(source.glob("*.docx"))

        print(f"\n[{class_name.upper()}]")
        print(f"Found: {len(files)}")

        seen = set()

        for i, path in enumerate(files, start=1):

            # IMPORTANT:
            # We do NOT open/read the file.
            # Only filename and filesystem-reported size are used.

            key = (path.name, path.stat().st_size)

            if key in seen:
                duplicates += 1
                print(f"  DUPLICATE: {path.name}")
                continue

            seen.add(key)

            destination = target / path.name

            try:
                shutil.copy2(path, destination)
                total += 1

            except Exception as e:
                print(f"  COPY FAILED: {path.name} -> {e}")

            if i % 100 == 0 or i == len(files):
                print(f"  Processed: {i}/{len(files)}")

        print(f"Unique filename+size: {len(seen)}")

    print("\n========================================")
    print("SAFE DEDUPLICATION COMPLETE")
    print("========================================")
    print(f"Files copied : {total}")
    print(f"Duplicates   : {duplicates}")
    print(f"Output       : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()