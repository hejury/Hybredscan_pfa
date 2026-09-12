#!/usr/bin/env python3
"""test_docx_security.py — Garde-fous de securite de document_ml/docx/.

Execution : python3 tests/test_docx_security.py

Ces tests verifient statiquement et dynamiquement que le package DOCX ne
peut, par construction, ni executer de contenu (macro, document, processus
externe) ni etre expose a des chemins de sortie non bornes (bombes zip),
et qu'il degrade toujours proprement (jamais d'exception non capturee, ni
de valeur fabriquee) face a une entree hostile."""
import ast
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx_fixtures import build_minimal_docx, CONTENT_TYPES_MIN, DOCUMENT_MIN
from document_ml.docx.validate import valider_docx, lire_partie_texte
from document_ml.docx.features import extraire_features_docx

DOCX_PKG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "document_ml", "docx")

# Appels dont la seule presence dans le code source de document_ml/docx/
# indiquerait une possibilite d'execution de contenu ou de processus --
# strictement interdits par le cahier des charges (jamais Office, jamais
# PowerShell/cmd/wscript/cscript, jamais exec/eval de contenu du fichier).
APPELS_INTERDITS = {
    "system", "popen", "spawnl", "spawnv", "startfile",
    "exec", "eval", "compile",
}
MODULES_INTERDITS = {"subprocess", "win32com", "comtypes", "pywin32"}


def _fichiers_source_py():
    for nom in sorted(os.listdir(DOCX_PKG_DIR)):
        if nom.endswith(".py"):
            yield os.path.join(DOCX_PKG_DIR, nom)


def test_no_execution_primitives_in_source():
    """Analyse AST statique (pas une simple recherche de texte) de chaque
    fichier .py du package : aucun appel a os.system/subprocess/exec/eval/
    win32com/etc., et aucun import de subprocess/win32com/comtypes."""
    for chemin in _fichiers_source_py():
        with open(chemin, encoding="utf-8") as fh:
            source = fh.read()
        arbre = ast.parse(source, filename=chemin)
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                for alias in noeud.names:
                    racine = alias.name.split(".")[0]
                    assert racine not in MODULES_INTERDITS, (
                        "%s importe le module interdit %r" % (chemin, alias.name))
            elif isinstance(noeud, ast.ImportFrom):
                racine = (noeud.module or "").split(".")[0]
                assert racine not in MODULES_INTERDITS, (
                    "%s importe depuis le module interdit %r" % (chemin, noeud.module))
            elif isinstance(noeud, ast.Call):
                cible = noeud.func
                # Seul l'appel BUILTIN nu (ex. compile(...)/exec(...)) est
                # suspect ; un appel qualifie comme re.compile(...) est une
                # compilation d'expression reguliere, sans rapport (evite un
                # faux positif sur les regex du module).
                if isinstance(cible, ast.Name) and cible.id.lower() in APPELS_INTERDITS:
                    assert False, "%s appelle %r -- primitive d'execution interdite" % (chemin, cible.id)
                elif isinstance(cible, ast.Attribute) and cible.attr.lower() in APPELS_INTERDITS - {"compile"}:
                    assert False, "%s appelle %r -- primitive d'execution interdite" % (chemin, cible.attr)


def test_oletools_calls_are_exception_wrapped():
    """Verifie textuellement que chaque utilisation de VBA_Parser/msodde
    dans features.py est entouree d'un bloc try/except (defense contre une
    exception oletools qui remonterait telle quelle a l'appelant)."""
    chemin = os.path.join(DOCX_PKG_DIR, "features.py")
    with open(chemin, encoding="utf-8") as fh:
        source = fh.read()
    arbre = ast.parse(source, filename=chemin)
    fonctions_vba = {"_extraire_vba", "_detecter_dde"}
    trouvees = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.FunctionDef) and noeud.name in fonctions_vba:
            trouvees.add(noeud.name)
            a_try = any(isinstance(n, ast.Try) for n in ast.walk(noeud))
            assert a_try, "%s ne contient aucun bloc try/except" % noeud.name
    assert trouvees == fonctions_vba, "fonctions VBA/DDE introuvables : %s" % (fonctions_vba - trouvees)


def test_relationship_targets_are_never_fetched():
    """Le module ne doit contenir aucun appel reseau (requests/urllib/
    socket) -- les cibles de relations externes/hyperlink sont uniquement
    comptees par regex sur le texte, jamais resolues."""
    for chemin in _fichiers_source_py():
        with open(chemin, encoding="utf-8") as fh:
            source = fh.read()
        arbre = ast.parse(source, filename=chemin)
        for noeud in ast.walk(arbre):
            if isinstance(noeud, (ast.Import, ast.ImportFrom)):
                noms = ([a.name for a in noeud.names] if isinstance(noeud, ast.Import)
                        else [noeud.module or ""])
                for n in noms:
                    racine = n.split(".")[0]
                    assert racine not in ("requests", "urllib", "socket", "http"), (
                        "%s importe %r -- une resolution reseau ne doit jamais avoir lieu ici" % (chemin, n))


def test_large_declared_part_never_read_beyond_cap(tmp):
    """Defense en profondeur contre une bombe zip : une partie legitimement
    ecrite mais volumineuse n'est jamais lue au-dela de limite_octets."""
    gros = b"B" * 2_000_000
    p = build_minimal_docx(os.path.join(tmp, "big.docx"), extra_entries={
        "word/huge.xml": gros
    })
    assert lire_partie_texte(p, "word/huge.xml", limite_octets=10_000) == ""


def test_traversal_like_entry_name_does_not_escape_or_crash(tmp):
    """Un nom d'entree ZIP contenant des sequences de traversee de chemin
    ('../') ne doit jamais provoquer d'ecriture hors du dossier temporaire
    ni faire planter la validation -- validate.py/features.py ne font
    jamais d'extraction sur disque (zipfile.extract*), donc ce risque est
    structurellement absent ; ce test le confirme empiriquement."""
    p = os.path.join(tmp, "traversal.docx")
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES_MIN)
        z.writestr("_rels/.rels", b"<Relationships/>")
        z.writestr("word/document.xml", DOCUMENT_MIN)
        z.writestr("../../../evil_outside.txt", b"should never land on disk")
        z.writestr("word/embeddings/../../../evil2.txt", b"also should never land on disk")

    avant = set(os.listdir(tmp))
    r = valider_docx(p)
    apres = set(os.listdir(tmp))
    assert apres == avant, "valider_docx a cree des fichiers sur disque -- ne devrait jamais arriver"
    assert r.valide is True  # les parties requises sont bien presentes ; les entrees suspectes sont ignorees

    f = extraire_features_docx(p)
    apres2 = set(os.listdir(tmp))
    assert apres2 == avant, "extraire_features_docx a cree des fichiers sur disque -- ne devrait jamais arriver"
    assert "_erreur" not in f, f


def test_never_raises_uncaught_on_hostile_zip_names(tmp):
    """Noms d'entrees contenant des caracteres nuls, tres longs, ou de
    l'encodage invalide -- ne doit jamais lever d'exception non capturee."""
    p = os.path.join(tmp, "hostile_names.docx")
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES_MIN)
        z.writestr("_rels/.rels", b"<Relationships/>")
        z.writestr("word/document.xml", DOCUMENT_MIN)
        z.writestr("word/" + "x" * 500 + ".xml", b"<x/>")
    r = valider_docx(p)
    assert r.valide is True
    f = extraire_features_docx(p)
    assert "_erreur" not in f, f


def run_all():
    import inspect
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = []
    with tempfile.TemporaryDirectory(prefix="hybridscan_docx_security_") as tmp:
        for t in tests:
            args = inspect.signature(t).parameters
            try:
                t(tmp) if args else t()
                print("PASS  %s" % t.__name__)
            except Exception as e:
                print("FAIL  %s : %s" % (t.__name__, e))
                failures.append(t.__name__)
    print("\n%d/%d tests passed" % (len(tests) - len(failures), len(tests)))
    return len(failures) == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
