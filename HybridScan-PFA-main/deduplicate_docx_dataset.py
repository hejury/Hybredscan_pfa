from pathlib import Path
import hashlib
import shutil


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "datasets" / "docx_training"
OUTPUT_DIR = BASE_DIR / "datasets" / "docx_training_clean"

CLASSES = ["benign", "malicious"]


def file_hash(path):
    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    duplicates = 0

    for class_name in CLASSES:
        source = SOURCE_DIR / class_name
        target = OUTPUT_DIR / class_name
        target.mkdir(parents=True, exist_ok=True)

        seen_hashes = set()

        files = sorted(source.rglob("*.docx"))

        print(f"\n[{class_name.upper()}]")
        print(f"Found: {len(files)}")

        for i, path in enumerate(files, start=1):

            try:
                digest = file_hash(path)

                if digest in seen_hashes:
                    duplicates += 1
                    print(f"  DUPLICATE: {path.name}")
                    continue

                seen_hashes.add(digest)

                shutil.copy2(
                    path,
                    target / path.name
                )

                total += 1

            except Exception as e:
                print(f"  SKIPPED: {path.name} -> {e}")

            if i % 100 == 0 or i == len(files):
                print(f"  Processed: {i}/{len(files)}")

        print(f"Unique: {len(seen_hashes)}")


    print("\n========================================")
    print("DEDUPLICATION COMPLETE")
    print("========================================")
    print(f"Unique files : {total}")
    print(f"Duplicates   : {duplicates}")
    print(f"Output       : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()