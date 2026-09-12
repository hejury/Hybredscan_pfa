"""api/services/auth_service.py — Pont vers auth.py, la SEULE source de
verite pour l'authentification HybridScan.

Reproduit exactement la regle deja appliquee par app.py::page_connexion() :
un identifiant est valide s'il correspond a un compte cree via
auth.register() (verify()) OU au compte administrateur unique configure
via .streamlit/secrets.toml / variables d'environnement
(verify_compte_configure()) -- jamais une nouvelle logique d'authentification,
jamais un identifiant code en dur, jamais un hachage affaibli.

Le seul element vraiment nouveau ici est la session HTTP : auth.py n'a
jamais eu de notion de session (Streamlit gere cela via st.session_state,
propre a chaque onglet de navigateur). Ce module ajoute la plus petite
couche necessaire -- un jeton opaque genere par secrets.token_urlsafe(),
associe en memoire process a un nom d'utilisateur. Limitation assumee et
documentee (validation/NEXTJS-FASTAPI-INTEGRATION.md) : la session ne
survit pas a un redemarrage du processus API et n'est pas partagee entre
plusieurs workers -- un choix deliberement minimal pour cette phase,
jamais un jeton/mot de passe stocke cote navigateur."""
import secrets
import threading
from datetime import datetime, timezone

from auth import verify, verify_compte_configure, register as _auth_register

_lock = threading.Lock()
_SESSIONS: dict[str, dict] = {}


def login(username: str, password: str) -> str | None:
    """Verifie les identifiants via auth.py (voir docstring du module) et,
    si valides, cree une session en memoire. Retourne le jeton de session,
    ou None si les identifiants sont invalides -- jamais de session creee
    sur un echec."""
    username = (username or "").strip()
    if not username or not password:
        return None
    if not (verify(username, password) or verify_compte_configure(username, password)):
        return None
    token = secrets.token_urlsafe(32)
    with _lock:
        _SESSIONS[token] = {
            "username": username,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    return token


def get_session(token: str | None) -> dict | None:
    if not token:
        return None
    with _lock:
        return _SESSIONS.get(token)


def logout(token: str | None) -> None:
    if not token:
        return
    with _lock:
        _SESSIONS.pop(token, None)


def register(username: str, password: str) -> tuple[bool, str]:
    """Delegue entierement a auth.register() -- meme regles (longueur
    minimale du mot de passe, unicite du nom d'utilisateur, meme sel/hachage
    SHA-256), jamais reimplementees ici."""
    return _auth_register(username, password)
