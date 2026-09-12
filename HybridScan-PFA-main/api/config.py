"""api/config.py — Configuration de l'API, meme discipline que le reste du
projet : variable d'environnement d'abord, valeur de repli sure sinon,
jamais de secret code en dur."""
import os

from backend_shared import EXTENSIONS_SCAN_DOSSIER

# Origines autorisees pour le frontend Next.js (dev). Jamais "*" : la
# session HybridScan repose sur un cookie (allow_credentials=True), qui
# exige une liste d'origines explicite cote navigateur (voir main.py).
_DEFAUT_ORIGINES = "http://localhost:3000,http://127.0.0.1:3000"
CORS_ORIGINS = [
    o.strip() for o in os.environ.get("HYBRIDSCAN_CORS_ORIGINS", _DEFAUT_ORIGINES).split(",")
    if o.strip()
]

# Cookie de session -- HttpOnly (jamais lisible par JavaScript cote
# navigateur), SameSite=Lax (le cookie n'est jamais envoye sur une requete
# POST/PUT/DELETE inter-site, ce qui neutralise le CSRF classique par
# formulaire cache sans avoir besoin d'un jeton CSRF distinct), Secure
# uniquement si explicitement demande (HTTPS en production -- desactive par
# defaut pour permettre le developpement local en http://).
SESSION_COOKIE_NAME = "hybridscan_session"
SESSION_COOKIE_SECURE = os.environ.get("HYBRIDSCAN_COOKIE_SECURE", "0") == "1"
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60  # 8 heures

# Meme limite que celle deja annoncee par le frontend (frontend/lib/api/
# analysis.ts::MAX_UPLOAD_SIZE_MB) et par le comportement par defaut de
# Streamlit (st.file_uploader sans server.maxUploadSize personnalise dans
# .streamlit/config.toml) -- jamais deux valeurs differentes annoncees.
MAX_UPLOAD_SIZE_MB = 200
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Extensions reellement acceptees par analyze.analyser() (voir
# analyze.py::EXTENSIONS_PE/EXTENSIONS_DOCUMENT) -- jamais une liste plus
# large que ce que le moteur sait effectivement router.
SUPPORTED_UPLOAD_EXTENSIONS = (".exe", ".dll", ".pdf", ".doc", ".docx")

# Portee actuelle du scan de dossier -- derivee de la SEULE source de
# verite (backend_shared.EXTENSIONS_SCAN_DOSSIER, partagee avec Streamlit)
# plutot que dupliquee ici, pour qu'il n'existe jamais deux listes
# pouvant diverger silencieusement.
FOLDER_SCAN_EXTENSIONS = EXTENSIONS_SCAN_DOSSIER

API_VERSION = "1.0.0"

# Bypass d'authentification pour l'usage local (PFA/soutenance) : quand la
# requete provient de la machine locale (voir LOCAL_BYPASS_HOSTS
# ci-dessous), api/dependencies.py::get_current_user() laisse passer les
# requetes non authentifiees -- mais UNIQUEMENT si aucune session reelle
# n'est deja presente (une vraie connexion garde toujours la priorite).
# Toujours actif pour ces hotes (plus besoin d'une variable d'environnement
# a positionner pour ouvrir l'application localement). Ne desactive ni ne
# supprime l'authentification reelle -- /auth/login, /auth/register,
# /auth/logout restent pleinement fonctionnels, et deviennent necessaires
# des qu'une requete ne provient plus d'un hote local.
LOCAL_BYPASS_HOSTS = {"127.0.0.1", "::1", "localhost"}
