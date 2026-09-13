#!/usr/bin/env python3
"""test_docx_features.py — Tests de document_ml/docx/features.py.

Execution : python3 tests/test_docx_features.py

Voir validation/DOCX-FEATURES.md §6 pour la limite connue : un flux
vbaProject.bin reellement decompilable par oletools (avec un vrai module
VBA contenant des mots-cles suspects) n'est pas reproduit ici -- la voie de
code correspondante est testee au niveau de la logique pure (dernier test
de ce fichier) et au niveau du branchement VBA_Parser (macro-free + echec
de parsing, couverts ici et dans test_docx_security.py)."""
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx_fixtures import build_minimal_docx, build_plain_text, DOC_RELS_EXTERNAL
from document_ml.docx.schema import FEATURES
from document_ml.docx.features import (extraire_features_docx, _entropie,
                                        _MOTS_CLES_SUSPECTS, _MOTS_CLES_AUTOEXEC,
                                        _RE_BASE64_LONG)


def test_macro_free_minimal(tmp):
    p = build_minimal_docx(os.path.join(tmp, "t1.docx"))
    r = extraire_features_docx(p)
    assert "_erreur" not in r, r
    assert list(r.keys()) == FEATURES
    assert r["has_vba_macros"] == 0
    assert r["nb_vba_modules"] == 0
    assert r["vba_source_length"] == 0
    assert r["vba_source_entropy"] == 0.0
    assert r["has_embeddings_dir"] == 0
    assert r["nb_relationships_external"] == 0
    assert r["file_size_bytes"] > 0


def test_external_relationships(tmp):
    p = build_minimal_docx(os.path.join(tmp, "t2.docx"), doc_rels=DOC_RELS_EXTERNAL)
    r = extraire_features_docx(p)
    assert "_erreur" not in r, r
    assert r["nb_relationships_external"] == 2
    assert r["has_attached_template"] == 1
    assert r["nb_hyperlink_relationships"] == 1
    assert r["nb_remote_targets_rels"] == 2
    assert r["has_oleobject_relationship"] == 0


def test_embeddings_activex_executable_name(tmp):
    p = build_minimal_docx(os.path.join(tmp, "t3.docx"), extra_entries={
        "word/embeddings/oleObject1.bin": b"\x00" * 16,
        "word/embeddings/payload.exe": b"MZ" + b"\x00" * 16,
        "word/activeX/activeX1.bin": b"\x00" * 8,
    })
    r = extraire_features_docx(p)
    assert "_erreur" not in r, r
    assert r["has_embeddings_dir"] == 1
    assert r["embedded_entry_count"] == 2
    assert r["has_activex"] == 1
    assert r["nb_executable_like_embedded_names"] == 1


def test_corrupt_vba_stream_reports_error_not_fabricated_value(tmp):
    """En-tete OLE2 valide mais tronque -- VBA_Parser doit lever, et
    features.py doit retourner _erreur, jamais has_vba_macros=0 fabrique."""
    p = build_minimal_docx(os.path.join(tmp, "t4.docx"), extra_entries={
        "word/vbaProject.bin": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 40,
    })
    r = extraire_features_docx(p)
    assert "_erreur" in r, "un flux OLE2 tronque doit produire une erreur explicite, pas un resultat fabrique"


def test_garbage_vba_bytes_is_a_true_negative_not_an_error(tmp):
    """A l'inverse : des octets sans rapport avec le format OLE2 ne sont pas
    une erreur de parsing -- oletools les reconnait legitimement comme
    'pas un flux VBA', ce qui est un vrai negatif, documente dans
    DOCX-FEATURES.md §6."""
    p = build_minimal_docx(os.path.join(tmp, "t4b.docx"), extra_entries={
        "word/vbaProject.bin": b"NOT_A_REAL_OLE2_STREAM" * 4,
    })
    r = extraire_features_docx(p)
    assert "_erreur" not in r, r
    assert r["has_vba_macros"] == 0


def test_invalid_container_returns_error_without_extraction(tmp):
    p = build_plain_text(os.path.join(tmp, "t5.docx"))
    r = extraire_features_docx(p)
    assert r == {"_erreur": "signature ZIP absente"}


def test_content_types_override_count(tmp):
    ct = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="x"/>
<Default Extension="xml" ContentType="x"/>
<Override PartName="/word/document.xml" ContentType="x"/>
<Override PartName="/docProps/core.xml" ContentType="x"/>
<Override PartName="/docProps/app.xml" ContentType="x"/>
</Types>"""
    p = build_minimal_docx(os.path.join(tmp, "t6.docx"), content_types=ct)
    r = extraire_features_docx(p)
    assert "_erreur" not in r, r
    assert r["nb_content_types_overrides"] == 3


def test_pure_logic_suspicious_vba_like_string():
    """Logique pure (regex/entropie) exercee directement sur une chaine VBA
    litterale, independamment d'un flux vbaProject.bin reel -- voir la
    limite documentee dans DOCX-FEATURES.md §6."""
    source = (
        "Sub AutoOpen()\n"
        "  Shell \"powershell.exe -enc \" & \"QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVphYmNkZWZnaGlqa2xtbm9wcXJzdHV2d3l6\"\n"
        "  Dim x As String\n"
        "  x = \"http://malicious-c2.example.test/payload\"\n"
        "End Sub\n"
    )
    nb_susp = sum(source.lower().count(kw) for kw in _MOTS_CLES_SUSPECTS)
    nb_url = source.lower().count("http://") + source.lower().count("https://")
    nb_auto = sum(1 for kw in _MOTS_CLES_AUTOEXEC if kw in source.lower())
    nb_b64 = len(_RE_BASE64_LONG.findall(source))
    ent = _entropie(source)
    assert nb_susp >= 2
    assert nb_url == 1
    assert nb_auto == 1
    assert nb_b64 >= 1
    assert ent > 0
    assert _entropie("") == 0.0


def run_all():
    tests_needing_tmp = [v for k, v in sorted(globals().items())
                          if k.startswith("test_") and v.__code__.co_argcount == 1]
    tests_no_tmp = [v for k, v in sorted(globals().items())
                    if k.startswith("test_") and v.__code__.co_argcount == 0]
    failures = []
    with tempfile.TemporaryDirectory(prefix="hybridscan_docx_features_") as tmp:
        for t in tests_needing_tmp:
            try:
                t(tmp)
                print("PASS  %s" % t.__name__)
            except Exception as e:
                print("FAIL  %s : %s" % (t.__name__, e))
                failures.append(t.__name__)
    for t in tests_no_tmp:
        try:
            t()
            print("PASS  %s" % t.__name__)
        except Exception as e:
            print("FAIL  %s : %s" % (t.__name__, e))
            failures.append(t.__name__)
    total = len(tests_needing_tmp) + len(tests_no_tmp)
    print("\n%d/%d tests passed" % (total - len(failures), total))
    return len(failures) == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
