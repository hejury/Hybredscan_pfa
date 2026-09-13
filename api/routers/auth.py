from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from api.config import SESSION_COOKIE_NAME, SESSION_COOKIE_SECURE, SESSION_MAX_AGE_SECONDS
from api.dependencies import get_current_user
from api.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, UserResponse
from api.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse)
async def login(payload: LoginRequest, response: Response) -> UserResponse:
    """Verifie les identifiants via auth.py (verify() ou
    verify_compte_configure(), memes regles que app.py::page_connexion())
    et pose un cookie de session HttpOnly. Jamais de jeton/mot de passe
    renvoye dans le corps JSON (cahier des charges §10)."""
    token = auth_service.login(payload.username, payload.password)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects.")
    session = auth_service.get_session(token)
    response.set_cookie(
        key=SESSION_COOKIE_NAME, value=token, httponly=True, samesite="lax",
        secure=SESSION_COOKIE_SECURE, max_age=SESSION_MAX_AGE_SECONDS, path="/",
    )
    return UserResponse(username=session["username"], is_local_session=False)


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(username=user["username"], is_local_session=user.get("is_local_session", False))


@router.post("/logout")
async def logout(
    response: Response,
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> dict:
    auth_service.logout(session_token)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"success": True}


@router.post("/register", response_model=RegisterResponse)
async def register(payload: RegisterRequest) -> RegisterResponse:
    """Delegue a auth.register() -- deja pris en charge par l'application
    Streamlit existante (onglet "Créer un compte"), jamais une nouvelle
    fonctionnalite inventee ici (cahier des charges §9)."""
    ok, message = auth_service.register(payload.username, payload.password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return RegisterResponse(success=ok, message=message)
