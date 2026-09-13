#!/usr/bin/env python3
"""test_docx_validate.py — Tests de document_ml/docx/validate.py.

Execution : python3 tests/test_docx_validate.py (aucune dependance a
pytest, coherent avec le reste du projet qui n'utilise pas de framework de
test). Aucun fichier reel du projet (history.csv, quarantine/, model*.pkl)
n'est touche par ce fichier : toutes les fixtures vivent sous un dossier
temporaire isole (tempfile.TemporaryDirectory)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx_fixtures import (build_minimal_docx, build_plain_zip, build_plain_text,
                            build_truncated_zip, build_fake_pe)
from document_ml.docx.validate import valider_docx, a_signature_zip, lire_partie_texte


def test_valid_minimal_docx(tmp):
    p = build_minimal_docx(os.path.join(tmp, "valid.docx"))
    r = valider_docx(p)
    assert r.valide is True, r.motif_invalide
    assert r.motif_invalide is None
    assert "word/document.xml" in r.entrees
    assert r.indicateurs["a_vba"] is False
    assert r.indicateurs["a_core_properties"] is True


def test_plain_zip_rejected(tmp):
    p = build_plain_zip(os.path.join(tmp, "random.docx"))
    r = valider_docx(p)
    assert r.valide is False
    assert "Content_Types" in r.motif_invalide


def test_plain_text_rejected(tmp):
    p = build_plain_text(os.path.join(tmp, "text.docx"))
    r = valider_docx(p)
    assert r.valide is False
    assert r.motif_invalide == "signature ZIP absente"
    assert a_signature_zip(p) is False


def test_truncated_zip_rejected(tmp):
    p = build_truncated_zip(os.path.join(tmp, "truncated.docx"))
    r = valider_docx(p)
    assert r.valide is False
    assert "illisible/corrompue" in r.motif_invalide
    # La signature ZIP en tete est bien presente ; c'est l'ouverture complete
    # de l'archive qui echoue ensuite -- distinction importante avec le cas
    # "signature ZIP absente".
    assert a_signature_zip(p) is True


def test_fake_pe_rejected(tmp):
    p = build_fake_pe(os.path.join(tmp, "notepad.docx"))
    r = valider_docx(p)
    assert r.valide is False
    assert r.motif_invalide == "signature ZIP absente"


def test_missing_document_xml(tmp):
    # build_minimal_docx ecrit toujours document.xml -- on construit donc a
    # la main un cas qui l'omet.
    import zipfile
    from docx_fixtures import CONTENT_TYPES_MIN
    p = os.path.join(tmp, "no_doc.docx")
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES_MIN)
        z.writestr("_rels/.rels", b"<Relationships/>")
    r = valider_docx(p)
    assert r.valide is False
    assert "word/document.xml" in r.motif_invalide


def test_missing_content_types(tmp):
    import zipfile
    from docx_fixtures import DOCUMENT_MIN
    p = os.path.join(tmp, "no_ct.docx")
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("word/document.xml", DOCUMENT_MIN)
    r = valider_docx(p)
    assert r.valide is False
    assert "Content_Types" in r.motif_invalide


def test_indicators_detect_vba_embeddings_activex(tmp):
    p = build_minimal_docx(os.path.join(tmp, "indicators.docx"), extra_entries={
        "word/vbaProject.bin": b"\x00" * 8,
        "word/embeddings/x.bin": b"\x00",
        "word/activeX/x.bin": b"\x00",
        "customXml/item1.xml": b"<x/>",
    })
    r = valider_docx(p)
    assert r.valide is True
    assert r.indicateurs["a_vba"] is True
    assert r.indicateurs["a_embeddings"] is True
    assert r.indicateurs["a_activex"] is True
    assert r.indicateurs["a_customxml"] is True


def test_lire_partie_texte_absent_returns_empty(tmp):
    p = build_minimal_docx(os.path.join(tmp, "novba.docx"))
    assert lire_partie_texte(p, "word/vbaProject.bin") == ""
    assert lire_partie_texte(p, "does/not/exist.xml") == ""


def test_lire_partie_texte_size_cap(tmp):
    """Defense en profondeur : une partie legitimement volumineuse n'est
    jamais lue au-dela de `limite_octets`, meme si elle existe reellement
    (pas besoin d'une vraie bombe zip pour verifier ce garde-fou)."""
    gros_contenu = b"A" * (500_000)
    p = build_minimal_docx(os.path.join(tmp, "big.docx"), extra_entries={
        "word/big_part.xml": gros_contenu
    })
    texte = lire_partie_texte(p, "word/big_part.xml", limite_octets=1000)
    assert texte == "", "une partie depassant limite_octets doit etre ignoree (chaine vide), pas tronquee silencieusement en valeur exploitable"
    texte_ok = lire_partie_texte(p, "word/big_part.xml", limite_octets=1_000_000)
    assert texte_ok == gros_contenu.decode()


def test_never_raises_on_garbage_path(tmp):
    """valider_docx ne doit jamais lever d'exception, meme sur un chemin
    inexistant."""
    r = valider_docx(os.path.join(tmp, "does_not_exist_at_all.docx"))
    assert r.valide is False


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = []
    with tempfile.TemporaryDirectory(prefix="hybridscan_docx_validate_") as tmp:
        for t in tests:
            try:
                t(tmp)
                print("PASS  %s" % t.__name__)
            except Exception as e:
                print("FAIL  %s : %s" % (t.__name__, e))
                failures.append(t.__name__)
    print("\n%d/%d tests passed" % (len(tests) - len(failures), len(tests)))
    return len(failures) == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
