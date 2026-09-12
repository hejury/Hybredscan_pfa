#!/usr/bin/env python3
"""test_docx_model_integration.py — Tests d'integration du prototype
model_docx.pkl (PROTOTYPE DE RECHERCHE PFA, voir
validation/DOCX-RESEARCH-MODEL-TRAINING.md) dans analyze.py/predict.py.

Execution : python3 tests/test_docx_model_integration.py

Toutes les analyses passent par un BASE isole (HYBRIDSCAN_BASE_DIR) --
jamais le history.csv/quarantine/model*.pkl reels du depot. Le
model_docx.pkl REEL du depot est copie (jamais deplace/modifie) dans
chaque repertoire isole pour tester le chargement/l'inference reels."""
import os
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx_fixtures import build_minimal_docx, build_plain_text, build_fake_pe

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_REEL = os.path.join(PROJECT_ROOT, "model_docx.pkl")


def _analyze_isole(tmp):
    os.environ.pop("VT_API_KEY", None)
    os.environ["HYBRIDSCAN_BASE_DIR"] = tmp
    for mod in list(sys.modules):
        if mod.startswith("document_ml") or mod == "analyze":
            del sys.modules[mod]
    import analyze
    return analyze


def _preparer_base_avec_modele(tmp):
    assert os.path.exists(MODEL_REEL), "model_docx.pkl introuvable a la racine du projet"
    shutil.copy(MODEL_REEL, os.path.join(tmp, "model_docx.pkl"))


def test_model_loads_and_schema_enforced(tmp):
    """Chargement direct du bundle + verification de contrat de schema
    (predict._verifier_contrat_schema), via le vrai model_docx.pkl."""
    _preparer_base_avec_modele(tmp)
    sys.path.insert(0, PROJECT_ROOT)
    import pickle
    from document_ml.docx.predict import _verifier_contrat_schema
    from document_ml.docx.schema import FEATURES, SCHEMA_VERSION

    with open(os.path.join(tmp, "model_docx.pkl"), "rb") as fh:
        bundle = pickle.load(fh)

    assert _verifier_contrat_schema(bundle) is None
    assert bundle["metadata"]["feature_schema_version"] == SCHEMA_VERSION
    # Ordre relatif dans schema.FEATURES respecte (contrat, pas necessairement contigu).
    indices = [FEATURES.index(c) for c in bundle["features"]]
    assert indices == sorted(indices)
    # Transparence du prototype -- jamais retiree silencieusement.
    assert bundle["metadata"]["research_only"] is True
    assert bundle["metadata"]["production_ready"] is False


def test_valid_docx_prediction_end_to_end(tmp):
    """analyze.analyser() sur un .docx valide et sans macro doit atteindre
    l'etape IA_DOCX et renvoyer un verdict avec confiance."""
    _preparer_base_avec_modele(tmp)
    analyze = _analyze_isole(tmp)
    p = build_minimal_docx(os.path.join(tmp, "benin.docx"))
    r = analyze.analyser(p, isoler=True)
    assert r["famille"] == "docx"
    assert r["etape"] == "2 (ia_docx)"
    assert r["verdict"] in ("sain", "malveillant")
    assert isinstance(r["confiance"], float)
    assert r["document_ml_supported"] is True


def test_invalid_spoofed_docx_rejected_before_ml(tmp):
    """Un fichier non authentiquement DOCX ne doit jamais atteindre le
    modele -- rejete des identifier_fichier()."""
    _preparer_base_avec_modele(tmp)
    analyze = _analyze_isole(tmp)
    for nom, builder in (("texte", build_plain_text), ("PE", build_fake_pe)):
        p = builder(os.path.join(tmp, "spoof_%s.docx" % nom))
        r = analyze.analyser(p, isoler=True)
        if nom == "PE":
            # Un vrai PE renomme .docx doit rester route comme PE (garde
            # anti-spoof deja existante, prioritaire sur l'extension).
            assert r["famille"] == "pe"
        else:
            assert r["famille"] == "docx"
            assert r["etape"] == "2 (format invalide)"
            assert r["verdict"] == "indetermine"
            assert r["document_ml_supported"] is False


def test_legacy_doc_never_uses_docx_model(tmp):
    """.doc (OLE legacy) doit rester indetermine, jamais transmis au
    modele DOCX ni valide structurellement."""
    _preparer_base_avec_modele(tmp)
    analyze = _analyze_isole(tmp)
    p = os.path.join(tmp, "legacy.doc")
    with open(p, "wb") as fh:
        fh.write(b"\xd0\xcf\x11\xe0" + b"\x00" * 200)  # entete OLE2 reelle
    r = analyze.analyser(p, isoler=True)
    assert r["famille"] == "doc"
    assert r["etape"] == "2 (document)"
    assert r["verdict"] == "indetermine"
    assert r["document_ml_supported"] is False


def test_pe_renamed_docx_preserves_pe_routing(tmp):
    """Un veritable executable renomme .docx doit continuer a suivre le
    pipeline PE (garde anti-spoof), jamais echapper vers 'non pris en
    charge' en se faisant passer pour un document."""
    _preparer_base_avec_modele(tmp)
    analyze = _analyze_isole(tmp)
    p = build_fake_pe(os.path.join(tmp, "evil.docx"))
    info = analyze.identifier_fichier(p)
    assert info["famille"] == "pe"


def test_vt_conclusive_docx_never_invokes_ml(tmp):
    """Si VirusTotal (etape 1) est concluant, le modele DOCX ne doit
    jamais etre appele -- verifie par monkeypatch de _predire_docx pour
    detecter tout appel inattendu."""
    _preparer_base_avec_modele(tmp)
    analyze = _analyze_isole(tmp)

    appele = {"valeur": False}

    def _espion(path):
        appele["valeur"] = True
        return {"statut": "sain", "confiance": 0.5, "features": {}}

    analyze._predire_docx = _espion
    analyze.etape1_virustotal = lambda digest: {
        "statut": "malveillant", "detections": 5, "total_moteurs": 60}

    p = build_minimal_docx(os.path.join(tmp, "vt_conclusif.docx"))
    r = analyze.analyser(p, isoler=False)
    assert r["etape"] == "1 (signature)"
    assert r["verdict"] == "malveillant"
    assert appele["valeur"] is False, "le modele DOCX a ete invoque alors que VT etait concluant"


def test_vt_inconclusive_docx_invokes_ml(tmp):
    """Si VirusTotal est inconclusif (pas de cle / inconnu), le modele
    DOCX doit etre invoque pour un DOCX structurellement valide."""
    _preparer_base_avec_modele(tmp)
    analyze = _analyze_isole(tmp)

    appele = {"valeur": False}
    original = analyze._predire_docx

    def _espion(path):
        appele["valeur"] = True
        return original(path)

    analyze._predire_docx = _espion
    p = build_minimal_docx(os.path.join(tmp, "vt_inconclusif.docx"))
    analyze.analyser(p, isoler=True)
    assert appele["valeur"] is True


def test_quarantine_safety_ia_docx_malveillant_not_auto_quarantined(tmp):
    """Un verdict malveillant issu SEULEMENT du prototype IA_DOCX ne doit
    jamais declencher une mise en quarantaine automatique (BF §14) --
    verifie via monkeypatch (pas une pretention de detection reelle)."""
    _preparer_base_avec_modele(tmp)
    analyze = _analyze_isole(tmp)
    analyze._predire_docx = lambda path: {
        "statut": "malveillant", "confiance": 0.99, "features": {}}

    p = build_minimal_docx(os.path.join(tmp, "force_malveillant.docx"))
    r = analyze.analyser(p, isoler=True)
    assert r["verdict"] == "malveillant"
    assert "quarantaine :" not in r["action"]
    assert "desactivee" in r["action"]
    quarantine_dir = os.path.join(tmp, "quarantine")
    assert not os.path.isdir(quarantine_dir) or not os.listdir(quarantine_dir)


def test_vt_conclusive_malveillant_docx_still_quarantined_normally(tmp):
    """Rappel de non-regression : un verdict malveillant issu de la
    SIGNATURE VirusTotal (pas du prototype IA_DOCX) doit continuer a etre
    mis en quarantaine normalement -- la garde de securite ne s'applique
    qu'a l'IA_DOCX."""
    _preparer_base_avec_modele(tmp)
    analyze = _analyze_isole(tmp)
    analyze.etape1_virustotal = lambda digest: {
        "statut": "malveillant", "detections": 5, "total_moteurs": 60}
    p = build_minimal_docx(os.path.join(tmp, "vt_malveillant.docx"))
    r = analyze.analyser(p, isoler=True)
    assert r["verdict"] == "malveillant"
    assert r["action"].startswith("quarantaine :")


def test_pdf_pipeline_unaffected(tmp):
    """Non-regression legere : le pipeline PDF (identifier_fichier,
    module document_ml.pdf) reste importable et fonctionnel."""
    analyze = _analyze_isole(tmp)
    p = os.path.join(tmp, "x.pdf")
    with open(p, "wb") as fh:
        fh.write(b"%PDF-1.4\n%%EOF")
    info = analyze.identifier_fichier(p)
    assert info["famille"] == "pdf"
    from document_ml.pdf.predict import predire  # doit toujours s'importer sans erreur
    assert callable(predire)


def test_pe_pipeline_unaffected(tmp):
    """Non-regression legere : etape2_ia/extraire_features (PE) restent
    importables et le seuil PE (0.45) est inchange."""
    analyze = _analyze_isole(tmp)
    assert analyze.SEUIL == 0.45
    assert callable(analyze.etape2_ia)
    assert callable(analyze.extraire_features)


def run_all():
    import inspect
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = []
    ancien_base_dir = os.environ.get("HYBRIDSCAN_BASE_DIR")
    try:
        for t in tests:
            with tempfile.TemporaryDirectory(prefix="hybridscan_docx_model_it_") as tmp:
                try:
                    t(tmp)
                    print("PASS  %s" % t.__name__)
                except Exception as e:
                    print("FAIL  %s : %s" % (t.__name__, e))
                    failures.append(t.__name__)
    finally:
        if ancien_base_dir is None:
            os.environ.pop("HYBRIDSCAN_BASE_DIR", None)
        else:
            os.environ["HYBRIDSCAN_BASE_DIR"] = ancien_base_dir
        for mod in list(sys.modules):
            if mod.startswith("document_ml") or mod == "analyze":
                del sys.modules[mod]

    print("\n%d/%d tests passed" % (len(tests) - len(failures), len(tests)))
    return len(failures) == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
