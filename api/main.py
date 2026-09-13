"""api/main.py — Point d'entree FastAPI. Assemble les routeurs ; ne
contient elle-meme AUCUNE logique d'analyse (cahier des charges §4).

Lancement (depuis le repertoire racine du projet, celui contenant
analyze.py) :
    python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
"""
import sys
from pathlib import Path

# Meme filet de securite que app.py (sys.path.insert du repertoire racine)
# -- garantit que `import analyze`/`import auth`/etc. fonctionne quel que
# soit le repertoire courant depuis lequel uvicorn est lance.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from analyze import BASE
from api.config import API_VERSION, CORS_ORIGINS
from api.routers import analysis, auth, dashboard, folder_scan, history, protection, quarantine

app = FastAPI(title="HybridScan API", version=API_VERSION)

# allow_credentials=True exige une liste d'origines explicite -- jamais
# "*" (cahier des charges §37).
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(folder_scan.router)
app.include_router(history.router)
app.include_router(quarantine.router)
app.include_router(protection.router)
app.include_router(dashboard.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request, _exc):
    """Ne renvoie jamais une trace Python au navigateur (cahier des
    charges §39) -- le detail technique reste dans les logs serveur
    (comportement par defaut d'uvicorn, qui journalise l'exception avant
    que ce gestionnaire ne s'execute)."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erreur interne. Réessayez plus tard."},
    )


@app.get("/api/v1/health")
async def health() -> dict:
    """Ne charge ni n'analyse aucun fichier utilisateur -- verifie
    uniquement la presence sur disque des artefacts modele (cahier des
    charges §6)."""
    return {
        "status": "ok",
        "service": "HybridScan API",
        "version": API_VERSION,
        "models": {
            "pe": (BASE / "model.pkl").exists(),
            "pdf": (BASE / "model_pdf.pkl").exists(),
            "docx": (BASE / "model_docx.pkl").exists(),
        },
    }
