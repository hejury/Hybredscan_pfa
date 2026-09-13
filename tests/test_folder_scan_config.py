#!/usr/bin/env python3
"""test_folder_scan_config.py — Tests de la configuration persistante des
racines de scan de dossier autorisees (HYBRIDSCAN_ALLOWED_SCAN_DIRS).

Execution : python3 tests/test_folder_scan_config.py

Utilise streamlit.testing.v1.AppTest pour piloter reellement l'interface
(app.py), avec un HYBRIDSCAN_BASE_DIR isole (jamais le history.csv/
quarantine reels du depot). Fixtures synthetiques uniquement, jamais de
malware reel.

DECOUVERTE IMPORTANTE (documentee ici pour eviter de la re-decouvrir) :
Streamlit copie automatiquement les cles de premier niveau de
.streamlit/secrets.toml dans os.environ des le premier acces a st.secrets
(ce qui se produit des la page de connexion, via auth.py). Comme
HYBRIDSCAN_ALLOWED_SCAN_DIRS est desormais reellement configure dans le
secrets.toml du depot (voir validation/FOLDER-SCAN-CONFIG.md), une valeur
posee manuellement dans os.environ AVANT de lancer un AppTest est donc
ECRASEE par la valeur reelle du fichier des la premiere execution du
script. Pour isoler veritablement ces tests de la configuration reelle du
poste, ce fichier reecrit TEMPORAIREMENT .streamlit/secrets.toml (racine
de scan de test uniquement, section [auth] intacte) puis restaure
TOUJOURS le contenu original exact (verifie octet pour octet) dans un
bloc finally -- jamais de perte de configuration reelle, meme en cas
d'echec d'assertion."""
import contextlib
import csv
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_PATH = os.path.join(PROJECT_ROOT, ".streamlit", "secrets.toml")

_AUTH_TOML = (
    '[auth]\n'
    'username = "testrun"\n'
    'password_hash = "9e426c8ba422c41cfdcf5bcc33dfaaa3$dbbd245523ff3b403d5f1281c639b78a2d63babad1f686b821920a8e857583e5"\n'
)


@contextlib.contextmanager
def _secrets_temporaires(scan_root=None):
    """Reecrit .streamlit/secrets.toml pour la duree du bloc `with`
    (section [auth] toujours preservee, pour que la connexion continue de
    fonctionner) puis restaure TOUJOURS le contenu original exact, meme en
    cas d'exception. `scan_root=None` -> aucune cle
    HYBRIDSCAN_ALLOWED_SCAN_DIRS (simule une configuration absente)."""
    assert os.path.exists(SECRETS_PATH), "secrets.toml reel introuvable -- rien a sauvegarder"
    # newline="" preserve les fins de ligne EXACTES d'origine (jamais de
    # traduction LF<->CRLF implicite du mode texte Windows) -- restauration
    # veritablement octet pour octet, pas seulement textuellement identique.
    with open(SECRETS_PATH, "r", encoding="utf-8", newline="") as fh:
        original = fh.read()
    try:
        contenu = _AUTH_TOML
        if scan_root:
            racine_toml = scan_root.replace("\\", "\\\\")
            contenu = "HYBRIDSCAN_ALLOWED_SCAN_DIRS = \"%s\"\n\n" % racine_toml + contenu
        with open(SECRETS_PATH, "w", encoding="utf-8", newline="") as fh:
            fh.write(contenu)
        yield
    finally:
        with open(SECRETS_PATH, "w", encoding="utf-8", newline="") as fh:
            fh.write(original)
        with open(SECRETS_PATH, "r", encoding="utf-8", newline="") as fh:
            restaure = fh.read()
        assert restaure == original, (
            "ECHEC DE RESTAURATION de secrets.toml -- contenu different de l'original !")


def _pe_like(path):
    with open(path, "wb") as fh:
        fh.write(b"MZ" + b"\x90" * 62 + b"\x00" * 200)


def _preparer_fixtures(scan_root):
    os.makedirs(scan_root, exist_ok=True)
    os.makedirs(os.path.join(scan_root, "nested"), exist_ok=True)
    _pe_like(os.path.join(scan_root, "top.exe"))
    _pe_like(os.path.join(scan_root, "nested", "nested.exe"))
    with open(os.path.join(scan_root, "ignored.txt"), "w", encoding="utf-8") as fh:
        fh.write("non pris en charge")


def _preparer_base(base_dir):
    os.makedirs(base_dir, exist_ok=True)
    shutil.copy(os.path.join(PROJECT_ROOT, "model.pkl"), os.path.join(base_dir, "model.pkl"))
    os.environ.pop("VT_API_KEY", None)
    os.environ["HYBRIDSCAN_BASE_DIR"] = base_dir
    # Ne JAMAIS laisser une valeur residuelle d'un test precedent -- la
    # source de verite pour ces tests est desormais secrets.toml
    # (voir _secrets_temporaires), pas cette variable.
    os.environ.pop("HYBRIDSCAN_ALLOWED_SCAN_DIRS", None)


def _session_connectee():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(os.path.join(PROJECT_ROOT, "app.py"), default_timeout=60)
    at.run()
    at.text_input[0].set_value("testrun")
    at.text_input[1].set_value("TestRun2026!")
    for b in at.button:
        if b.label == "Se connecter":
            b.click().run()
            break
    assert not at.exception
    at.session_state.pg = "analyse"
    at.run()
    assert not at.exception
    return at


def _definir_dossier(at, chemin):
    """Recupere le widget de chemin FRAIS a chaque appel -- une reference
    capturee avant un at.run() precedent devient obsolete apres rerun
    (piege connu d'AppTest, deja rencontre et corrige dans cette phase)."""
    ti = [w for w in at.text_input if "dossier" in w.label.lower()][0]
    ti.set_value(chemin)
    return ti


def test_missing_root_handled_safely(tmp):
    """5. Racine absente (aucune configuration) geree proprement -- message
    explicite, jamais de crash, l'analyse de fichier reste utilisable."""
    base_dir = os.path.join(tmp, "base")
    _preparer_base(base_dir)
    with _secrets_temporaires(scan_root=None):
        at = _session_connectee()
        assert not at.exception
        textes = "\n".join(m.value for m in at.markdown) + "\n" + "\n".join(e.value for e in at.error)
        assert "n'est pas configuré" in textes
        boutons = [b.label for b in at.button]
        assert "Lancer l'analyse" in boutons


def test_configured_root_no_longer_shows_warning(tmp):
    """Configuration presente -> le message "non configure" disparait et
    "Dossiers autorisés" s'affiche."""
    base_dir = os.path.join(tmp, "base")
    scan_root = os.path.join(tmp, "scanroot")
    _preparer_base(base_dir)
    _preparer_fixtures(scan_root)
    with _secrets_temporaires(scan_root=scan_root):
        at = _session_connectee()
        textes = "\n".join(m.value for m in at.markdown) + "\n" + "\n".join(c.value for c in at.caption)
        assert "n'est pas configuré" not in textes
        assert "Dossiers autorisés" in textes


def test_allowed_root_and_nested_path_accepted(tmp):
    """1/3. La racine configuree et un sous-chemin imbrique sont acceptes."""
    base_dir = os.path.join(tmp, "base")
    scan_root = os.path.join(tmp, "scanroot")
    _preparer_base(base_dir)
    _preparer_fixtures(scan_root)
    with _secrets_temporaires(scan_root=scan_root):
        at = _session_connectee()
        for chemin in (scan_root, os.path.join(scan_root, "nested")):
            _definir_dossier(at, chemin)
            at.run()
            assert not at.exception
            erreurs = [e.value for e in at.error]
            assert not erreurs, "chemin autorise rejete a tort : %s (%s)" % (chemin, erreurs)


def test_outside_root_rejected(tmp):
    """3. Un chemin existant mais hors de la racine configuree est
    rejete."""
    base_dir = os.path.join(tmp, "base")
    scan_root = os.path.join(tmp, "scanroot")
    dehors = os.path.join(tmp, "ailleurs")
    _preparer_base(base_dir)
    _preparer_fixtures(scan_root)
    os.makedirs(dehors, exist_ok=True)
    with _secrets_temporaires(scan_root=scan_root):
        at = _session_connectee()
        _definir_dossier(at, dehors)
        at.run()
        assert not at.exception
        erreurs = [e.value for e in at.error]
        assert any("autoris" in e.lower() for e in erreurs)


def test_traversal_escape_rejected(tmp):
    """4. Une tentative de traversee de chemin (..) est resolue puis
    rejetee si elle sort de la racine autorisee."""
    base_dir = os.path.join(tmp, "base")
    scan_root = os.path.join(tmp, "scanroot")
    _preparer_base(base_dir)
    _preparer_fixtures(scan_root)
    chemin_traversee = os.path.join(scan_root, "..", "ailleurs_hors_racine")
    with _secrets_temporaires(scan_root=scan_root):
        at = _session_connectee()
        _definir_dossier(at, chemin_traversee)
        at.run()
        assert not at.exception
        erreurs = [e.value for e in at.error]
        assert erreurs, "une traversee de chemin n'a produit aucun rejet"


def test_recursive_on_finds_nested_file(tmp):
    """6. "Inclure les sous-dossiers" coche : le fichier imbrique est
    traite."""
    base_dir = os.path.join(tmp, "base")
    scan_root = os.path.join(tmp, "scanroot")
    _preparer_base(base_dir)
    _preparer_fixtures(scan_root)
    with _secrets_temporaires(scan_root=scan_root):
        at = _session_connectee()
        _definir_dossier(at, scan_root)
        at.run()
        bouton = [b for b in at.button if b.label == "Lancer le scan"][0]
        assert not bouton.disabled
        bouton.click().run()
        assert not at.exception

    with open(os.path.join(base_dir, "history.csv"), newline="", encoding="utf-8") as fh:
        lignes = list(csv.DictReader(fh))
    noms = {l["fichier"] for l in lignes}
    assert "nested.exe" in noms, "scan recursif : le fichier imbrique n'a pas ete traite"
    assert "top.exe" in noms
    assert "ignored.txt" not in noms


def test_recursive_off_skips_nested_file(tmp):
    """7. "Inclure les sous-dossiers" decoche : le fichier imbrique n'est
    PAS traite."""
    base_dir = os.path.join(tmp, "base")
    scan_root = os.path.join(tmp, "scanroot")
    _preparer_base(base_dir)
    _preparer_fixtures(scan_root)
    with _secrets_temporaires(scan_root=scan_root):
        at = _session_connectee()
        _definir_dossier(at, scan_root)
        recursif_cb = [c for c in at.checkbox if c.label == "Inclure les sous-dossiers"][0]
        recursif_cb.uncheck()
        at.run()
        bouton = [b for b in at.button if b.label == "Lancer le scan"][0]
        bouton.click().run()
        assert not at.exception

    with open(os.path.join(base_dir, "history.csv"), newline="", encoding="utf-8") as fh:
        lignes = list(csv.DictReader(fh))
    noms = {l["fichier"] for l in lignes}
    assert "top.exe" in noms
    assert "nested.exe" not in noms, "scan non recursif : le sous-dossier a ete parcouru a tort"


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = []
    anciens = {k: os.environ.get(k) for k in
               ("HYBRIDSCAN_BASE_DIR", "HYBRIDSCAN_ALLOWED_SCAN_DIRS", "VT_API_KEY")}
    secrets_original = None
    if os.path.exists(SECRETS_PATH):
        with open(SECRETS_PATH, "r", encoding="utf-8", newline="") as fh:
            secrets_original = fh.read()
    try:
        for t in tests:
            # analyze.py calcule BASE une seule fois a l'import et le cache
            # dans sys.modules -- sans cette purge, tous les tests apres le
            # premier reutiliseraient le HYBRIDSCAN_BASE_DIR du tout premier
            # test au lieu du leur (chaque test utilise un repertoire
            # temporaire distinct). app.py importe analyze a son tour et
            # doit donc lui aussi etre reimporte a chaque test.
            for mod in list(sys.modules):
                if mod.startswith("document_ml") or mod in ("analyze", "app", "quarantine_manager"):
                    del sys.modules[mod]
            with tempfile.TemporaryDirectory(prefix="hybridscan_folderscan_cfg_") as tmp:
                try:
                    t(tmp)
                    print("PASS  %s" % t.__name__)
                except Exception as e:
                    print("FAIL  %s : %s" % (t.__name__, e))
                    failures.append(t.__name__)
    finally:
        for k, v in anciens.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for mod in list(sys.modules):
            if mod.startswith("document_ml") or mod == "analyze":
                del sys.modules[mod]
        # Filet de securite final : si un test a interrompu la restauration
        # (ex. Ctrl+C entre le finally interne et cette ligne), on revalide
        # ici que secrets.toml correspond bien a l'original capture au debut.
        if secrets_original is not None and os.path.exists(SECRETS_PATH):
            with open(SECRETS_PATH, "r", encoding="utf-8", newline="") as fh:
                actuel = fh.read()
            if actuel != secrets_original:
                with open(SECRETS_PATH, "w", encoding="utf-8", newline="") as fh:
                    fh.write(secrets_original)
                print("ATTENTION : secrets.toml a du etre restaure par le filet de securite final.")

    print("\n%d/%d tests passed" % (len(tests) - len(failures), len(tests)))
    return len(failures) == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
