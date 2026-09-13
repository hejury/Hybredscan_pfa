#!/usr/bin/env python3
"""test_api.py — Tests de l'API FastAPI (api/), executes via pytest
(contrairement aux autres fichiers de tests/, qui sont des scripts
autonomes -- voir leur propre bloc run_all()/__main__). TestClient se
prete naturellement a pytest (fixtures, isolation par test), d'ou ce
choix ; execution : python -m pytest tests/test_api.py -q

Toutes les requetes passent par un BASE isole (HYBRIDSCAN_BASE_DIR, un
repertoire temporaire) exactement comme tests/test_docx_model_integration.py
et tests/test_quarantine_manager.py : jamais le history.csv/quarantine/
reel du depot. Les modeles reels (model.pkl/model_pdf.pkl/model_docx.pkl)
sont COPIES (jamais deplaces/modifies) dans ce repertoire isole, pour
exercer le vrai pipeline plutot qu'un modele factice."""
import os
import shutil
import sys
import tempfile

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx_fixtures import build_fake_pe, build_minimal_docx, build_plain_zip  # noqa: E402

_MINIMAL_PDF_BYTES = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF"
)


def _write_minimal_pdf(path):
    with open(path, "wb") as fh:
        fh.write(_MINIMAL_PDF_BYTES)
    return path

_HYBRIDSCAN_MODULE_PREFIXES = ("api", "analyze", "auth", "backend_shared",
                              "quarantine_manager", "watcher", "document_ml")


def _purge_hybridscan_modules():
    for mod in list(sys.modules):
        if mod.startswith(_HYBRIDSCAN_MODULE_PREFIXES) or mod in _HYBRIDSCAN_MODULE_PREFIXES:
            del sys.modules[mod]


@pytest.fixture()
def api_client(tmp_path, monkeypatch):
    """Un TestClient FastAPI relie a un BASE HybridScan isole et jetable.
    Fixture par test (pas par module) : chaque test repart d'un
    history.csv/quarantine/ vides, jamais d'etat partage entre tests."""
    base = str(tmp_path)
    for nom_modele in ("model.pkl", "model_pdf.pkl", "model_docx.pkl"):
        source = os.path.join(PROJECT_ROOT, nom_modele)
        assert os.path.exists(source), "%s introuvable a la racine du projet" % nom_modele
        shutil.copy(source, os.path.join(base, nom_modele))

    monkeypatch.setenv("HYBRIDSCAN_BASE_DIR", base)
    monkeypatch.delenv("VT_API_KEY", raising=False)
    monkeypatch.setenv("HYBRIDSCAN_ALLOWED_SCAN_DIRS", base)

    _purge_hybridscan_modules()

    # auth.py::_USERS_FILE is hardcoded next to auth.py itself (a single
    # shared users.json for the whole app -- never BASE-relative, unlike
    # history.csv/quarantine/). Left unpatched, every test run would
    # register into the REAL project's users.json. Redirect it into the
    # isolated tmp dir instead -- test isolation only, auth.py itself is
    # untouched.
    import auth as _auth_module
    monkeypatch.setattr(_auth_module, "_USERS_FILE", os.path.join(base, "users.json"))

    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()
        _purge_hybridscan_modules()


@pytest.fixture()
def local_bypass_api_client(tmp_path, monkeypatch):
    """Meme isolation que api_client, mais le TestClient se presente comme
    un hote local reel ("127.0.0.1", jamais atteignable via un vrai reseau
    distant) plutot que la valeur "testclient" par defaut de Starlette --
    c'est ce qui declenche le bypass d'authentification toujours actif
    d'api/dependencies.py::get_current_user() pour 127.0.0.1/localhost/::1
    (plus de variable d'environnement a positionner). Fixture separee
    plutot que de parametrer api_client, pour ne jamais faire fuiter ce
    bypass vers les autres tests qui doivent continuer a exercer le mode
    authentifie normal (host "testclient", absent de LOCAL_BYPASS_HOSTS)."""
    base = str(tmp_path)
    for nom_modele in ("model.pkl", "model_pdf.pkl", "model_docx.pkl"):
        source = os.path.join(PROJECT_ROOT, nom_modele)
        shutil.copy(source, os.path.join(base, nom_modele))

    monkeypatch.setenv("HYBRIDSCAN_BASE_DIR", base)
    monkeypatch.delenv("VT_API_KEY", raising=False)
    monkeypatch.setenv("HYBRIDSCAN_ALLOWED_SCAN_DIRS", base)

    _purge_hybridscan_modules()

    import auth as _auth_module
    monkeypatch.setattr(_auth_module, "_USERS_FILE", os.path.join(base, "users.json"))

    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app, client=("127.0.0.1", 51000))
    try:
        yield client
    finally:
        client.close()
        _purge_hybridscan_modules()


def _register_and_login(client, username="api_test_user", password="ApiTest1234"):
    r = client.post("/api/v1/auth/register", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r


def _write_fixture(tmp_path, name, builder):
    path = os.path.join(str(tmp_path), name)
    builder(path)
    return path


# --- HEALTH -----------------------------------------------------------

def test_health_returns_200(api_client):
    r = api_client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["models"] == {"pe": True, "pdf": True, "docx": True}


def test_health_never_analyzes_a_file(api_client):
    """Section 6 : /health ne doit accepter aucun televersement."""
    r = api_client.post("/api/v1/health")
    assert r.status_code in (404, 405)


# --- AUTH ---------------------------------------------------------------

def test_invalid_login_rejected(api_client):
    r = api_client.post("/api/v1/auth/login", json={"username": "nobody", "password": "wrong"})
    assert r.status_code == 401


def test_valid_login_accepted(api_client):
    _register_and_login(api_client)


def test_me_requires_authentication(api_client):
    r = api_client.get("/api/v1/auth/me")
    assert r.status_code == 401

    _register_and_login(api_client)
    r = api_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["username"] == "api_test_user"


def test_logout_invalidates_session(api_client):
    _register_and_login(api_client)
    assert api_client.get("/api/v1/auth/me").status_code == 200

    r = api_client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    assert api_client.get("/api/v1/auth/me").status_code == 401


def test_protected_routes_require_authentication(api_client):
    for path in ("/api/v1/history", "/api/v1/quarantine", "/api/v1/protection/status",
                 "/api/v1/dashboard", "/api/v1/scan/folder/config"):
        assert api_client.get(path).status_code == 401


# --- LOCAL BYPASS (api/dependencies.py, toujours actif pour 127.0.0.1/
# localhost/::1, sans variable d'environnement) ----------------------------

def test_local_bypass_does_not_apply_to_non_local_host(api_client):
    """Le fixture api_client standard se presente comme "testclient"
    (absent de LOCAL_BYPASS_HOSTS) -- comportement normal inchange (401
    sans session)."""
    assert api_client.get("/api/v1/auth/me").status_code == 401


def test_local_bypass_grants_access_for_local_request(local_bypass_api_client):
    """Requete non authentifiee provenant d'un hote local (127.0.0.1) --
    le bypass s'applique automatiquement, sans aucune variable
    d'environnement a positionner."""
    r = local_bypass_api_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "local"
    assert body["is_local_session"] is True


def test_local_bypass_grants_access_to_all_protected_routes(local_bypass_api_client):
    for path in ("/api/v1/history", "/api/v1/quarantine", "/api/v1/protection/status",
                 "/api/v1/dashboard", "/api/v1/scan/folder/config"):
        assert local_bypass_api_client.get(path).status_code == 200, path


def test_local_bypass_real_session_takes_priority(local_bypass_api_client):
    """Une vraie connexion reste prioritaire sur le bypass local -- jamais
    is_local_session=True pour une session reelle, meme si la requete
    provient d'un hote local (cahier des charges section 4)."""
    _register_and_login(local_bypass_api_client)
    r = local_bypass_api_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "api_test_user"
    assert body["is_local_session"] is False


def test_local_bypass_rejects_non_local_request(local_bypass_api_client, monkeypatch):
    """Le bypass ne s'applique JAMAIS a une requete qui ne provient pas
    d'un hote local -- simule ici en vidant la liste des hotes locaux
    acceptes cote module reellement consulte par get_current_user (cahier
    des charges section 5 : jamais silencieusement pour un deploiement
    expose)."""
    import api.dependencies as deps
    monkeypatch.setattr(deps, "LOCAL_BYPASS_HOSTS", set())
    r = local_bypass_api_client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_local_bypass_login_and_logout_still_work(local_bypass_api_client):
    """Le bypass local ne desactive pas l'authentification reelle --
    login/logout restent pleinement fonctionnels par-dessus le bypass."""
    _register_and_login(local_bypass_api_client)
    r = local_bypass_api_client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    # Apres logout, le bypass local reprend la main (hote local) -- jamais
    # un 401 permanent, jamais non plus une session reelle fantome.
    r = local_bypass_api_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["is_local_session"] is True


# --- ANALYSIS -------------------------------------------------------------

def test_harmless_docx_fixture_analyzed(api_client, tmp_path):
    _register_and_login(api_client)
    path = _write_fixture(tmp_path, "harmless.docx", build_minimal_docx)
    with open(path, "rb") as fh:
        r = api_client.post(
            "/api/v1/analysis/file",
            files={"file": ("harmless.docx", fh, "application/octet-stream")},
            data={"auto_quarantine": "false"},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["filename"] == "harmless.docx"
    assert body["family"] == "docx"
    assert body["verdict"] in ("sain", "malveillant", "indetermine")
    assert len(body["sha256"]) == 64


def test_pe_renamed_docx_still_routes_as_pe(api_client, tmp_path):
    """Anti-spoofing (section 14) : un faux PE (entete MZ) nomme .docx doit
    rester route PE, jamais transmis au modele DOCX."""
    _register_and_login(api_client)
    path = _write_fixture(tmp_path, "disguised.docx", build_fake_pe)
    with open(path, "rb") as fh:
        r = api_client.post(
            "/api/v1/analysis/file",
            files={"file": ("disguised.docx", fh, "application/octet-stream")},
            data={"auto_quarantine": "false"},
        )
    assert r.status_code == 200, r.text
    assert r.json()["family"] == "pe"


def test_unsupported_extension_rejected(api_client, tmp_path):
    _register_and_login(api_client)
    path = os.path.join(str(tmp_path), "notes.txt")
    with open(path, "w") as fh:
        fh.write("hello")
    with open(path, "rb") as fh:
        r = api_client.post("/api/v1/analysis/file", files={"file": ("notes.txt", fh, "text/plain")})
    assert r.status_code == 400


def test_upload_requires_authentication(api_client, tmp_path):
    path = _write_fixture(tmp_path, "harmless.docx", build_minimal_docx)
    with open(path, "rb") as fh:
        r = api_client.post("/api/v1/analysis/file", files={"file": ("harmless.docx", fh, "application/octet-stream")})
    assert r.status_code == 401


def test_malicious_original_filename_does_not_escape_temp_handling(api_client, tmp_path):
    """Le nom fourni par le navigateur n'est jamais utilise comme chemin
    disque (section 13/40) -- un nom hostile ne doit ni planter ni creer de
    fichier en dehors du repertoire temporaire du systeme."""
    _register_and_login(api_client)
    path = _write_fixture(tmp_path, "harmless.docx", build_minimal_docx)
    hostile_name = "..\\..\\..\\evil.docx"
    with open(path, "rb") as fh:
        r = api_client.post(
            "/api/v1/analysis/file",
            files={"file": (hostile_name, fh, "application/octet-stream")},
            data={"auto_quarantine": "false"},
        )
    assert r.status_code == 200, r.text
    assert r.json()["filename"] == hostile_name  # nom affiche tel quel, jamais utilise comme chemin
    assert not os.path.exists(os.path.join(os.path.dirname(str(tmp_path)), "evil.docx"))


def test_temp_upload_file_is_cleaned_up(api_client, tmp_path):
    _register_and_login(api_client)
    path = _write_fixture(tmp_path, "harmless.docx", build_minimal_docx)
    before = set(os.listdir(tempfile.gettempdir()))
    with open(path, "rb") as fh:
        api_client.post(
            "/api/v1/analysis/file",
            files={"file": ("harmless.docx", fh, "application/octet-stream")},
            data={"auto_quarantine": "false"},
        )
    after = set(os.listdir(tempfile.gettempdir()))
    leftover = [n for n in (after - before) if n.startswith("hybridscan_upload_")]
    assert leftover == []


# --- FOLDER SCAN ------------------------------------------------------

def test_folder_scan_allowed_path_accepted(api_client, tmp_path):
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan"
    scan_dir.mkdir()
    build_fake_pe(str(scan_dir / "sample.exe"))
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": True, "automatic_quarantine": False,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processed"] == 1
    assert body["results"][0]["family"] == "pe"


def test_folder_scan_outside_root_rejected(api_client, tmp_path):
    _register_and_login(api_client)
    outside = tmp_path.parent / "not_allowed"
    outside.mkdir(exist_ok=True)
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(outside), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 403


def test_folder_scan_traversal_rejected(api_client, tmp_path):
    _register_and_login(api_client)
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(tmp_path) + os.sep + "..", "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 403


def test_folder_scan_recursive_flag_controls_nested_discovery(api_client, tmp_path):
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan2"
    nested = scan_dir / "nested"
    nested.mkdir(parents=True)
    build_fake_pe(str(nested / "nested.exe"))

    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 200
    assert r.json()["processed"] == 0

    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": True, "automatic_quarantine": False,
    })
    assert r.status_code == 200
    assert r.json()["processed"] == 1


def test_folder_scan_config_reports_real_root(api_client, tmp_path):
    _register_and_login(api_client)
    r = api_client.get("/api/v1/scan/folder/config")
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["supported_extensions"] == [".exe", ".dll", ".pdf", ".docx"]


def test_folder_scan_accepts_dll(api_client, tmp_path):
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan_dll"
    scan_dir.mkdir()
    build_fake_pe(str(scan_dir / "library.dll"))
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processed"] == 1
    assert body["results"][0]["family"] == "pe"


def test_folder_scan_accepts_pdf_and_routes_to_pdf_pipeline(api_client, tmp_path):
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan_pdf"
    scan_dir.mkdir()
    _write_minimal_pdf(str(scan_dir / "report.pdf"))
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processed"] == 1
    result = body["results"][0]
    assert result["family"] == "pdf"
    assert result["detection_source"] in ("2 (ia_pdf)", "1 (signature)")


def test_folder_scan_accepts_docx_and_routes_to_docx_pipeline(api_client, tmp_path):
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan_docx"
    scan_dir.mkdir()
    build_minimal_docx(str(scan_dir / "contract.docx"))
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processed"] == 1
    result = body["results"][0]
    assert result["family"] == "docx"
    assert result["detection_source"] in ("2 (ia_docx)", "1 (signature)")


def test_folder_scan_uppercase_extensions_accepted(api_client, tmp_path):
    """Section 22 : .PDF/.DOCX/.EXE/.DLL en majuscules doivent etre traites
    comme leurs equivalents en minuscules (comportement Windows courant)."""
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan_upper"
    scan_dir.mkdir()
    build_fake_pe(str(scan_dir / "APPLICATION.EXE"))
    build_fake_pe(str(scan_dir / "LIBRARY.DLL"))
    _write_minimal_pdf(str(scan_dir / "REPORT.PDF"))
    build_minimal_docx(str(scan_dir / "CONTRACT.DOCX"))
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 200, r.text
    assert r.json()["processed"] == 4


def test_folder_scan_skips_unsupported_extensions(api_client, tmp_path):
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan_mixed"
    scan_dir.mkdir()
    build_fake_pe(str(scan_dir / "application.exe"))
    _write_minimal_pdf(str(scan_dir / "report.pdf"))
    build_minimal_docx(str(scan_dir / "contract.docx"))
    with open(scan_dir / "photo.jpg", "wb") as fh:
        fh.write(b"not a real jpeg, just an unsupported extension fixture")
    with open(scan_dir / "notes.txt", "w") as fh:
        fh.write("plain text, unsupported")
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processed"] == 3  # exe + pdf + docx only, jpg/txt skipped
    families = {result["family"] for result in body["results"]}
    assert families == {"pe", "pdf", "docx"}


def test_folder_scan_recursive_includes_nested_pdf_and_docx(api_client, tmp_path):
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan_nested"
    nested = scan_dir / "sous_dossier"
    nested.mkdir(parents=True)
    _write_minimal_pdf(str(nested / "nested_report.pdf"))
    build_minimal_docx(str(nested / "nested_contract.docx"))

    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 200
    assert r.json()["processed"] == 0

    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": True, "automatic_quarantine": False,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["processed"] == 2
    families = {result["family"] for result in body["results"]}
    assert families == {"pdf", "docx"}


def test_folder_scan_anti_spoofing_pe_renamed_docx(api_client, tmp_path):
    """Anti-spoofing via le scan de dossier (section 6) : un faux PE
    (entete MZ) nomme .docx doit rester route PE, jamais transmis au
    modele DOCX -- meme garantie que pour le televersement unique."""
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan_spoof_pe"
    scan_dir.mkdir()
    build_fake_pe(str(scan_dir / "disguised.docx"))
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processed"] == 1
    assert body["results"][0]["family"] == "pe"


def test_folder_scan_anti_spoofing_zip_renamed_docx_rejected_safely(api_client, tmp_path):
    """Une archive ZIP quelconque (sans structure OOXML) renommee .docx
    doit echouer la validation DOCX en toute securite -- jamais transmise
    au modele, jamais un plantage du scan (section 6/24)."""
    _register_and_login(api_client)
    scan_dir = tmp_path / "to_scan_spoof_zip"
    scan_dir.mkdir()
    build_plain_zip(str(scan_dir / "fake.docx"))
    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": False,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processed"] == 1
    result = body["results"][0]
    assert result["family"] == "docx"
    assert result["detection_source"] == "2 (format invalide)"
    assert result["verdict"] == "indetermine"


def test_folder_scan_docx_malicious_verdict_not_auto_quarantined(api_client, tmp_path):
    """Regression critique (section 9/25) : un verdict malveillant issu
    SEULEMENT du prototype IA_DOCX via le scan de dossier ne doit jamais
    declencher de mise en quarantaine automatique -- meme politique de
    securite que l'analyse d'un seul fichier (BF §14, analyze.py::
    analyser()), meme avec "Quarantaine automatique" active."""
    _register_and_login(api_client)
    import analyze
    analyze._predire_docx = lambda path: {"statut": "malveillant", "confiance": 0.99, "features": {}}

    scan_dir = tmp_path / "to_scan_docx_quarantine"
    scan_dir.mkdir()
    build_minimal_docx(str(scan_dir / "force_malveillant.docx"))

    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": True,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processed"] == 1
    result = body["results"][0]
    assert result["verdict"] == "malveillant"
    assert result["action"]["kind"] == "auto_quarantine_disabled"
    quarantine_dir = tmp_path / "quarantine"
    assert not quarantine_dir.is_dir() or not any(quarantine_dir.iterdir())


def test_folder_scan_pe_quarantine_behavior_unchanged(api_client, tmp_path):
    """Non-regression (section 25) : un PE malveillant via le scan de
    dossier continue d'etre mis en quarantaine normalement quand
    "Quarantaine automatique" est active -- la garde DOCX ne doit pas
    deborder sur PE."""
    _register_and_login(api_client)
    import analyze
    analyze.etape2_ia = lambda path: {"statut": "malveillant", "confiance": 0.99, "features": {}}

    scan_dir = tmp_path / "to_scan_pe_quarantine"
    scan_dir.mkdir()
    build_fake_pe(str(scan_dir / "force_malveillant.exe"))

    r = api_client.post("/api/v1/scan/folder", json={
        "path": str(scan_dir), "recursive": False, "automatic_quarantine": True,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    result = body["results"][0]
    assert result["verdict"] == "malveillant"
    assert result["action"]["kind"] == "quarantined"


# --- HISTORY ------------------------------------------------------------

def test_history_returns_structured_data_after_analysis(api_client, tmp_path):
    _register_and_login(api_client)
    path = _write_fixture(tmp_path, "harmless.docx", build_minimal_docx)
    with open(path, "rb") as fh:
        api_client.post(
            "/api/v1/analysis/file",
            files={"file": ("harmless.docx", fh, "application/octet-stream")},
            data={"auto_quarantine": "false"},
        )
    r = api_client.get("/api/v1/history")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    # history.csv["fichier"] is populated by analyze.journaliser() from the
    # temp path's basename (analyze.py behavior, unchanged) -- a random
    # token prefix is prepended server-side for collision-safety, but the
    # sanitized original name is preserved as a readable suffix.
    assert body["items"][0]["file_name"].endswith("harmless.docx")


def test_malformed_history_row_does_not_crash_endpoint(api_client, tmp_path):
    _register_and_login(api_client)
    history_path = tmp_path / "history.csv"
    history_path.write_text(
        "date,fichier,sha256,etape,verdict,confiance,detections,action\n"
        "not-a-date,broken.exe,,,valeur_inconnue,,,aucune\n",
        encoding="utf-8",
    )
    r = api_client.get("/api/v1/history")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert any("verdict" in w for w in body["warnings"])


# --- QUARANTINE -----------------------------------------------------------

def test_quarantine_list_and_details_metadata_only(api_client, tmp_path):
    _register_and_login(api_client)
    malicious_pdf = tmp_path / "malicious.pdf"
    malicious_pdf.write_bytes(b"%PDF-1.4\nnot a real structure, forced quarantine test")

    import quarantine_manager
    meta = quarantine_manager.quarantine_file(
        str(malicious_pdf), verdict="malveillant", detection_source="1 (signature)",
        source_context=quarantine_manager.SOURCE_UPLOAD, base_dir=str(tmp_path),
    )

    r = api_client.get("/api/v1/quarantine")
    assert r.status_code == 200
    listing = r.json()
    assert listing["total"] == 1
    assert listing["isolated"] == 1

    item_id = listing["items"][0]["id"]
    assert item_id == meta["id"]

    r = api_client.get("/api/v1/quarantine/%s" % item_id)
    assert r.status_code == 200
    detail = r.json()
    assert detail["display_name"] == "malicious.pdf"
    assert "payload" not in detail
    assert "content" not in detail


def test_quarantine_invalid_id_rejected(api_client):
    _register_and_login(api_client)
    r = api_client.get("/api/v1/quarantine/does-not-exist")
    assert r.status_code == 404


def test_no_quarantine_payload_route_exists(api_client):
    """Section 25 : aucune route ne doit jamais servir le contenu isole."""
    paths = {getattr(route, "path", "") for route in api_client.app.routes}
    assert not any("download" in p or "payload" in p or "content" in p for p in paths)


# --- PROTECTION -----------------------------------------------------------

def test_protection_status_endpoint_safe_when_never_started(api_client):
    _register_and_login(api_client)
    r = api_client.get("/api/v1/protection/status")
    assert r.status_code == 200
    body = r.json()
    assert body["active"] is False
    assert isinstance(body["configured_directories"], list)


def test_protection_not_started_automatically(api_client):
    """Section 29 : ne jamais demarrer le watcher automatiquement."""
    _register_and_login(api_client)
    api_client.get("/api/v1/health")
    api_client.get("/api/v1/protection/status")
    assert api_client.get("/api/v1/protection/status").json()["active"] is False


# --- DASHBOARD --------------------------------------------------------

def test_dashboard_reflects_real_analysis(api_client, tmp_path):
    _register_and_login(api_client)
    path = _write_fixture(tmp_path, "harmless.docx", build_minimal_docx)
    with open(path, "rb") as fh:
        api_client.post(
            "/api/v1/analysis/file",
            files={"file": ("harmless.docx", fh, "application/octet-stream")},
            data={"auto_quarantine": "false"},
        )
    r = api_client.get("/api/v1/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["kpis"]["total_analyzed"] == 1
    assert sum(body["file_type_breakdown"].values()) == 1
    assert body["file_type_breakdown"]["docx"] == 1
    assert body["kpis"]["protection_active"] is False


def test_dashboard_never_reports_a_fabricated_detection_rate(api_client):
    """Section 32 : aucun champ 'detection_rate'/'taux_detection' ne doit
    exister -- history.csv n'a pas de verite terrain."""
    _register_and_login(api_client)
    body = api_client.get("/api/v1/dashboard").json()
    flat = str(body).lower()
    assert "detection_rate" not in flat
    assert "taux_detection" not in flat


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
