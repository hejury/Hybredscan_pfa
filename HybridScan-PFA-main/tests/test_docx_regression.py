#!/usr/bin/env python3
"""test_docx_regression.py — Non-regression PE/PDF + contrat d'integration DOCX.

Execution : python3 tests/test_docx_regression.py

HISTORIQUE : ce fichier verifiait initialement que document_ml/docx/
n'etait PAS integre a analyze.py/app.py (phase de fondation). Ce
n'est plus le contrat actuel : l'integration du prototype de recherche
IA_DOCX a ete explicitement autorisee et realisee (voir
validation/DOCX-RESEARCH-MODEL-TRAINING.md). Les tests ci-dessous ont ete
mis a jour pour verifier le NOUVEAU contrat, pas l'ancien -- l'historique
est garde dans ce commentaire pour la tracabilite, pas dans le code.

Verifie que l'integration DOCX :
  1. n'a modifie AUCUN artefact modele PE/PDF (model.pkl, model_pdf.pkl,
     document_ml/pdf/*, extract_features.py, train_model.py) ;
  2. n'importe document_ml.docx dans analyze.py QUE via le chemin
     d'inference dedie (_predire_docx -> document_ml.docx.predict), jamais
     un import direct qui contournerait le contrat de schema/validation ;
  3. applique desormais une VRAIE validation structurelle DOCX dans
     identifier_fichier() (plus une confiance aveugle a l'extension) ;
  4. ecrit son historique/quarantaine UNIQUEMENT dans le repertoire isole
     fourni par HYBRIDSCAN_BASE_DIR pendant ce test -- jamais dans le
     history.csv/quarantine/ reels du projet.

PROJECT_ROOT et BASELINE_HASHES_FILE pointent vers le depot reel (lecture
seule) ; toute execution de analyser() se fait dans un repertoire temporaire
distinct via HYBRIDSCAN_BASE_DIR."""
import ast
import hashlib
import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASELINE_HASHES_FILE = (
    r"C:\Users\user\AppData\Local\Temp\claude\c--Users-user-Desktop-PFA-PRJECT-main"
    r"\3340bdf8-4e02-4932-bf47-12dab94b92e7\scratchpad\baseline_hashes_docx_phase.txt"
)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _lire_baseline():
    attendu = {}
    with open(BASELINE_HASHES_FILE, encoding="utf-8") as fh:
        for ligne in fh:
            ligne = ligne.strip()
            if not ligne:
                continue
            digest, chemin = ligne.split(" *", 1)
            attendu[chemin] = digest
    return attendu


# history.csv grandit legitimement a chaque analyser() reel (usage normal
# de l'application) -- exclu du controle strict, verifie seulement pour
# existence. analyze.py/app.py sont EXCLUS de la comparaison a l'ancienne
# baseline : leur modification est le resultat EXPLICITEMENT AUTORISE de
# cette phase d'integration (voir DOCX-RESEARCH-MODEL-TRAINING.md) --
# seuls les artefacts modele/pipeline PE et PDF eux-memes doivent rester
# figes, jamais le routage qui les entoure une fois une integration DOCX
# approuvee.
_FICHIERS_NON_STATIQUES = {"history.csv"}
_FICHIERS_MODIFIES_CETTE_PHASE = {"analyze.py", "app.py"}


def test_pe_pdf_model_artifacts_unchanged_since_baseline():
    attendu = _lire_baseline()
    assert attendu, "fichier de baseline vide ou introuvable : %s" % BASELINE_HASHES_FILE
    ecarts = []
    for chemin_relatif, digest_attendu in attendu.items():
        if chemin_relatif in _FICHIERS_NON_STATIQUES or chemin_relatif in _FICHIERS_MODIFIES_CETTE_PHASE:
            continue
        chemin_abs = os.path.join(PROJECT_ROOT, chemin_relatif)
        if not os.path.exists(chemin_abs):
            ecarts.append("%s : fichier absent" % chemin_relatif)
            continue
        digest_actuel = _sha256(chemin_abs)
        if digest_actuel != digest_attendu:
            ecarts.append("%s : %s != %s (attendu)" % (chemin_relatif, digest_actuel, digest_attendu))
    chemin_history = os.path.join(PROJECT_ROOT, "history.csv")
    if not os.path.exists(chemin_history):
        ecarts.append("history.csv : fichier absent")
    assert not ecarts, "artefacts modele PE/PDF modifies depuis la ligne de base :\n" + "\n".join(ecarts)


_MODULES_DOCX_AUTORISES_DANS_ANALYZE = {
    "document_ml.docx.predict",  # inference -- verification de contrat de schema incluse
    "document_ml.docx.validate",  # validation structurelle reelle (identifier_fichier)
}


def test_docx_import_scope_in_analyze_is_narrow():
    """Analyse AST : document_ml.docx est desormais importe par analyze.py
    (integration autorisee), mais UNIQUEMENT via .predict (inference) et
    .validate (validation structurelle) -- jamais .train/.features/.schema
    importes DIRECTEMENT dans analyze.py (ils restent des details
    d'implementation internes a predict.py/validate.py). app.py ne doit
    importer AUCUN sous-module document_ml.docx directement (il passe par
    analyze.analyser())."""
    chemin = os.path.join(PROJECT_ROOT, "analyze.py")
    with open(chemin, encoding="utf-8") as fh:
        source = fh.read()
    arbre = ast.parse(source, filename=chemin)
    imports_docx = []
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.ImportFrom):
            module = noeud.module or ""
            if module.startswith("document_ml.docx"):
                imports_docx.append(module)
    assert imports_docx, "analyze.py devrait importer document_ml.docx.predict/.validate (integration attendue)"
    inattendus = [m for m in imports_docx if m not in _MODULES_DOCX_AUTORISES_DANS_ANALYZE]
    assert not inattendus, (
        "analyze.py importe document_ml.docx au-dela de predict/validate : %s" % inattendus)

    chemin_app = os.path.join(PROJECT_ROOT, "app.py")
    with open(chemin_app, encoding="utf-8") as fh:
        source_app = fh.read()
    arbre_app = ast.parse(source_app, filename=chemin_app)
    for noeud in ast.walk(arbre_app):
        if isinstance(noeud, ast.ImportFrom):
            module = noeud.module or ""
            assert not module.startswith("document_ml.docx"), (
                "app.py importe document_ml.docx directement : %s (doit passer par analyze.analyser())" % module)
        if isinstance(noeud, ast.Import):
            for alias in noeud.names:
                assert not alias.name.startswith("document_ml.docx"), (
                    "app.py importe document_ml.docx directement : %s" % alias.name)


def test_identifier_fichier_docx_now_validates_structure(tmp):
    """identifier_fichier() applique desormais une VRAIE validation
    structurelle DOCX (document_ml/docx/validate.py) -- un fichier
    quelconque renomme .docx doit etre signale invalide, plus jamais
    valide=True par la seule extension (contrat de la phase de fondation,
    volontairement remplace par cette phase d'integration)."""
    os.environ["HYBRIDSCAN_BASE_DIR"] = tmp
    for mod in list(sys.modules):
        if mod.startswith("document_ml") or mod == "analyze":
            del sys.modules[mod]
    import analyze

    p = os.path.join(tmp, "quelconque.docx")
    with open(p, "wb") as fh:
        fh.write(b"this is not even a real docx, just bytes")

    info = analyze.identifier_fichier(p)
    assert info["famille"] == "docx"
    assert info["valide"] is False
    assert info["motif_invalide"] is not None


def test_analyser_docx_isolation_preserved(tmp):
    """Chaine complete analyser() sur un .docx invalide, dans un BASE
    isole : doit aboutir a verdict='indetermine' (format invalide, jamais
    transmis au modele), et n'ecrire que dans le repertoire isole --
    jamais dans le history.csv/quarantine reels du depot."""
    os.environ.pop("VT_API_KEY", None)
    os.environ["HYBRIDSCAN_BASE_DIR"] = tmp
    for mod in list(sys.modules):
        if mod.startswith("document_ml") or mod == "analyze":
            del sys.modules[mod]
    import analyze

    assert str(analyze.BASE) == os.path.abspath(tmp) or os.path.samefile(str(analyze.BASE), tmp)

    history_reel = os.path.join(PROJECT_ROOT, "history.csv")
    digest_avant = _sha256(history_reel) if os.path.exists(history_reel) else None

    p = os.path.join(tmp, "sample.docx")
    with open(p, "wb") as fh:
        fh.write(b"PK\x03\x04" + b"fake docx content, not a real ooxml archive")

    r = analyze.analyser(p, isoler=True)
    assert r["famille"] == "docx"
    assert r["etape"] == "2 (format invalide)"
    assert r["verdict"] == "indetermine"
    assert r["action"] == "aucune"

    history_isole = os.path.join(tmp, "history.csv")
    assert os.path.exists(history_isole), "l'historique doit etre ecrit dans le BASE isole"

    quarantine_reel = os.path.join(PROJECT_ROOT, "quarantine")
    if digest_avant is not None:
        assert _sha256(history_reel) == digest_avant, (
            "history.csv REEL du depot a ete modifie par ce test -- fuite d'isolation")
    if os.path.isdir(quarantine_reel):
        avant = set(os.listdir(quarantine_reel))
        assert not any("sample.docx" in n for n in avant), (
            "un artefact du test isole est apparu dans quarantine/ reel")


def run_all():
    import inspect
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = []
    ancien_base_dir = os.environ.get("HYBRIDSCAN_BASE_DIR")
    try:
        with tempfile.TemporaryDirectory(prefix="hybridscan_docx_regression_") as tmp:
            for t in tests:
                args = inspect.signature(t).parameters
                try:
                    t(tmp) if args else t()
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
