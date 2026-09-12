import sys
from pathlib import Path

sys.path.insert(0, "..")

from document_ml.docx.features import extraire_features_docx

for f in Path(r"C:\Users\tmt\Downloads").rglob("*.docx"):
    try:
        d = extraire_features_docx(f)
        if d["has_vba_macros"] == 1:
            print(f"{f.name} | size={d['file_size_bytes']} | VBA=1")
    except Exception:
        pass
