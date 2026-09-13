"""api/dependencies.py — Dependances FastAPI partagees (authentification)."""
from fastapi import Cookie, HTTPException, Request, status

from api.config import LOCAL_BYPASS_HOSTS, SESSION_COOKIE_NAME
from api.services import auth_service

# Session synthetique utilisee UNIQUEMENT par le bypass local -- jamais
# stockee dans auth_service._SESSIONS, jamais associee a un cookie reel.
_LOCAL_SESSION = {"username": "local", "is_local_session": True}


def _requete_locale(request: Request) -> bool:
    hote = request.client.host if request.client else None
    return hote in LOCAL_BYPASS_HOSTS


def get_current_user(
    request: Request,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> dict:
    """Dependance utilisee par toutes les routes protegees.

    Une vraie session (cookie valide) a TOUJOURS priorite : si une
    session reelle existe, le bypass local n'entre jamais en jeu (cahier
    des charges, section 4 -- "no password should be automatically
    submitted", donc une connexion reelle explicite reste pleinement
    possible et prioritaire).

    En l'absence de session reelle, le bypass local s'applique
    automatiquement des que la requete provient de la machine locale (voir
    _requete_locale) -- jamais pour une requete distante, qui recoit
    toujours un 401 et doit passer par /auth/login.

    Sinon, comportement inchange : 401, jamais de donnees fabriquees pour
    masquer l'absence d'authentification (cahier des charges §10)."""
    session = auth_service.get_session(session_token)
    if session is not None:
        return {**session, "is_local_session": False}

    if _requete_locale(request):
        return _LOCAL_SESSION

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentification requise.")
