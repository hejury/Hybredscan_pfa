# HybridScan

**HybridScan est une application desktop de détection hybride de
malwares** (prototype académique de PFA — pas un antivirus commercial
ni un produit prêt pour la production) : analyse statique de fichiers
PE/PDF/DOCX combinant vérification par signature (VirusTotal) et
modèles d'apprentissage automatique, avec quarantaine, historique, scan
de dossier et surveillance en temps réel. L'utilisateur lance une seule
commande et obtient une fenêtre native — jamais un navigateur ou un
terminal à ouvrir manuellement.

## Architecture

```
Utilisateur
  ↓
Application Desktop HybridScan (run_desktop.py / desktop/launcher.py)
  ↓
Interface Next.js / React intégrée dans une fenêtre PyWebView
  ↓ HTTP/JSON local, cookie de session HttpOnly
API FastAPI locale (api/, 127.0.0.1:8000, /api/v1/*)
  ↓ appels directs, aucune logique dupliquée côté frontend
Moteur Python HybridScan (analyze.py, quarantine_manager.py, watcher.py, auth.py)
  ├── Réputation VirusTotal (signature)
  ├── Analyse statique PE (Random Forest)
  ├── Analyse statique PDF (prototype de recherche)
  ├── Analyse statique DOCX (prototype de recherche)
  ├── Historique (history.csv)
  ├── Quarantaine (quarantine/)
  ├── Scan de dossier
  └── Protection / Watcher
```

PyWebView n'est qu'une fenêtre native affichant la même interface
Next.js que celle servie sur `http://localhost:3000` — le frontend ne
prend jamais lui-même de décision de détection : FastAPI reste l'API
locale, et le moteur Python reste l'unique source de vérité. Aucun
modèle ML ne vit dans le frontend.

Streamlit (`app.py`) reste disponible comme interface de repli,
utilisant exactement les mêmes modules Python. Voir
`validation/SOUTENANCE-TECHNICAL-NOTES.md` pour le détail technique de
chaque composant.

## Prérequis

- Python 3.11+ avec les dépendances du projet (scikit-learn, pefile,
  oletools, streamlit, fastapi, uvicorn, pydantic, watchdog, etc.)
- Node.js 20+ et npm (pour `frontend/`)
- Pour l'application desktop uniquement : `pywebview` (voir
  `requirements-desktop.txt`) — sur Windows, il embarque le rendu via
  le runtime WebView2 (préinstallé avec Windows 10/11 + Edge).

## Installation

```powershell
# Dépendances Python (depuis la racine du projet)
python -m pip install fastapi uvicorn python-multipart pytest httpx `
    streamlit pandas pefile requests scikit-learn watchdog oletools

# Application desktop (en plus de ce qui précède)
python -m pip install -r requirements-desktop.txt

# Dépendances frontend
cd frontend
npm install
cd ..
```

## Configuration

Copier les fichiers d'exemple et ajuster selon votre environnement :

```powershell
Copy-Item frontend\.env.example frontend\.env.local
```

Variables backend (aucun fichier `.env` chargé automatiquement — les
exporter dans votre shell, ou utiliser `.streamlit/secrets.toml` pour
`VT_API_KEY`/`HYBRIDSCAN_ALLOWED_SCAN_DIRS`/`[auth]`) : voir
`.env.example` à la racine pour la liste complète et le comportement de
repli de chacune.

## Application Desktop HybridScan

Commande principale (à la racine du projet) :

```
python run_desktop.py
```

Cette commande unique démarre l'API FastAPI locale (127.0.0.1:8000,
jamais exposée sur `0.0.0.0`), démarre le frontend Next.js compilé en
production (port 3000), attend que les deux répondent réellement
(vérification HTTP avec timeout, pas de `time.sleep` fixe), puis ouvre
une fenêtre PyWebView native intitulée « HybridScan » affichant
directement le Tableau de bord — aucune page de connexion, aucun
onglet de navigateur à ouvrir à la main. Fermer la fenêtre arrête
proprement les deux processus.

Le tout premier lancement compile le frontend pour la production
(`next build`, jusqu'à ~1 minute) ; les lancements suivants réutilisent
ce build et démarrent en quelques secondes.

Options utiles (`python run_desktop.py --help`) :

| Option | Effet |
|---|---|
| `--dev` | Ne démarre rien : se rattache à des serveurs déjà lancés à la main (voir mode développeur ci-dessous) et ouvre seulement la fenêtre. |
| `--frontend-dev` | Démarre le frontend avec `next dev` au lieu du build de production. |
| `--rebuild-frontend` | Force un nouveau `next build` même si un build existe déjà. |
| `--backend-reload` | Démarre l'API avec `--reload`. |
| `--no-window` | Démarre les serveurs sans ouvrir PyWebView (débogage, Ctrl+C pour arrêter). |

## Mode développeur (web, sans PyWebView)

```powershell
# Les deux en une fois, dans des fenêtres séparées
.\scripts\start_hybridscan.ps1

# Ou séparément
.\scripts\start_backend.ps1     # API FastAPI — http://127.0.0.1:8000
.\scripts\start_frontend.ps1    # Frontend Next.js — http://localhost:3000

# Puis, éventuellement, ouvrir la fenêtre desktop par-dessus ces
# serveurs déjà lancés (sans les redémarrer) :
python run_desktop.py --dev
```

Vérification de bon fonctionnement :
- API : http://127.0.0.1:8000/api/v1/health
- Frontend : http://localhost:3000

Le comportement d'accès local est le même dans les deux modes : une
requête provenant de 127.0.0.1/localhost/::1 arrive directement sur le
Tableau de bord (voir `api/dependencies.py`) — aucun mode « démo » à
activer, ce mécanisme a été retiré du projet. Une authentification
réelle (`/login`) reste possible et prioritaire si nécessaire.

## Structure

```
run_desktop.py            Point d'entrée desktop (python run_desktop.py)
desktop/
  launcher.py              Démarrage/arrêt des processus + fenêtre PyWebView
  assets/hybridscan.ico    Icône (générée depuis frontend/public/branding/)
api/                       API FastAPI (routers/, schemas/, services/)
frontend/                  Interface Next.js (App Router) — inchangée
analyze.py, quarantine_manager.py, watcher.py, auth.py, backend_shared.py
                           Moteur de détection (source de vérité)
document_ml/               Pipelines PDF/DOCX
scripts/                   Lanceurs PowerShell (mode web, développement)
tests/                     Suite de tests (pytest + scripts autonomes)
```

## Build Windows (`HybridScan.exe`)

Le launcher desktop est déjà écrit pour être compatible avec un
empaquetage [PyInstaller](https://pyinstaller.org/) :
- `desktop/launcher.py::resolve_repo_root()` détecte `sys.frozen` et
  utilise le répertoire de l'exécutable plutôt qu'un chemin de
  développement — **aucun chemin n'est jamais codé en dur** vers un
  poste particulier.
- `analyze.py::BASE` (modèles, `history.csv`, `quarantine/`) accepte
  déjà une racine alternative via `HYBRIDSCAN_BASE_DIR`, utile pour
  séparer les fichiers en lecture seule (modèles, embarqués dans
  l'exécutable) des données modifiables par l'utilisateur (historique,
  quarantaine, `users.json`) une fois packagé.
- Une icône multi-résolution existe déjà : `desktop/assets/hybridscan.ico`.

Ce build n'a **pas** été produit dans le cadre de ce travail (cahier
des charges : rendre d'abord le launcher fonctionnel en développement).
Pour le préparer :

1. `cd frontend && npm run build` (produit `frontend/.next/`, à
   embarquer tel quel — `run_desktop.py` le fait déjà automatiquement
   au premier lancement s'il est absent).
2. `pyinstaller --name HybridScan --icon desktop/assets/hybridscan.ico
   --add-data "model.pkl;." --add-data "model_pdf.pkl;."
   --add-data "model_docx.pkl;." --add-data "frontend;frontend"
   --add-data "document_ml;document_ml" run_desktop.py` (liste
   indicative — à ajuster selon les fichiers réellement nécessaires à
   l'exécution : `users.json`, `.env`, etc. ne doivent PAS être
   embarqués s'ils contiennent des données utilisateur réelles).
3. Vérifier que `HYBRIDSCAN_BASE_DIR` pointe vers un dossier utilisateur
   inscriptible (ex. `%APPDATA%\HybridScan`) plutôt que le dossier
   d'installation, pour que `history.csv`/`quarantine/`/`users.json`
   survivent aux mises à jour de l'exécutable.

## Tests

```bash
# Suite de régression existante (scripts autonomes)
for f in tests/test_docx_features.py tests/test_docx_model_integration.py \
         tests/test_docx_regression.py tests/test_docx_security.py \
         tests/test_docx_validate.py tests/test_folder_scan_config.py \
         tests/test_quarantine_manager.py; do python "$f"; done

# Suite API FastAPI (pytest)
python -m pytest tests/test_api.py -v

# Frontend
cd frontend && npm run lint && npm run build

# Desktop (démarre les serveurs sans ouvrir de fenêtre, pratique en CI)
python run_desktop.py --no-window
# Ctrl+C pour arrêter -- vérifie aussi que l'API et le frontend
# s'arrêtent bien (aucun processus node/uvicorn résiduel).
```

Voir `validation/HYBRIDSCAN-FINALISATION.md` pour les derniers résultats
exacts (68/68 régression, 27/27 API, lint/build propres, E2E réel
27/27).

## Formats pris en charge

| Fonctionnalité | Formats |
|---|---|
| Analyse d'un fichier | `.exe`, `.dll`, `.pdf`, `.docx`, `.doc` |
| Scan de dossier | `.exe`, `.dll`, `.pdf`, `.docx` (mis à jour — `.doc` legacy toujours exclu du scan de dossier) |

Le scan de dossier route chaque fichier candidat via le même `analyser()`
que l'analyse d'un seul fichier (`backend_shared.EXTENSIONS_SCAN_DOSSIER`,
seule source de verité partagée par Streamlit et l'API) — même détection,
même anti-spoofing, même politique de quarantaine, y compris la garde de
sécurité DOCX (voir « Limitations de recherche » ci-dessous).

## Modèle de sécurité

- Analyse **statique uniquement** — aucun fichier n'est jamais exécuté.
- Fichiers téléversés : copie temporaire nommée côté serveur, jamais le
  chemin/nom fourni par le navigateur utilisé directement comme chemin
  disque.
- Scan de dossier : chemin validé contre une liste de racines
  autorisées configurée par l'administrateur, confinement vérifié par
  résolution canonique de chemin (jamais une comparaison de préfixe de
  chaîne).
- Quarantaine : métadonnées uniquement exposées par l'API/le frontend —
  jamais le contenu isolé (pas de téléchargement, pas de restauration,
  pas de suppression définitive).
- Authentification : cookie de session HttpOnly, `SameSite=Lax`,
  `Secure` configurable pour la production HTTPS. Sessions en mémoire,
  mono-processus — un redémarrage de l'API les invalide.
- CORS : origines explicites uniquement, jamais `*`.

## Limitations de recherche (PDF / DOCX)

Les modèles PDF et DOCX sont des **prototypes de recherche**, pas des
moteurs prêts pour la production :
- **PDF** : au moins un faux positif a été observé sur un fichier de
  test inoffensif lors des tests d'intégration réels de ce projet.
- **DOCX** : les performances élevées observées sur le jeu de données
  d'entraînement doivent être interprétées avec prudence (risque
  d'artefacts de corpus, absence de validation externe). Un verdict
  "malveillant" produit uniquement par ce modèle n'entraîne pas de mise
  en quarantaine automatique par défaut.

Le modèle PE (Random Forest) est le plus mature des trois, mais reste
un projet académique — voir `validation/` pour l'historique complet des
validations, faiblesses et decisions documentées.

## Repli Streamlit

```powershell
streamlit run app.py
```

Couvre les mêmes fonctionnalités que le frontend Next.js, avec la même
logique métier (les deux interfaces partagent `analyze.py`,
`quarantine_manager.py`, `watcher.py`, `auth.py`, et
`backend_shared.py`).

## Documentation complémentaire

- `validation/DEMO_FINAL.md` — séquence de démonstration.
- `validation/SOUTENANCE-TECHNICAL-NOTES.md` — points techniques pour
  la soutenance.
- `validation/HYBRIDSCAN-FINALISATION.md` — rapport de la phase de
  finalisation (tests, sécurité, limitations).
- `validation/NEXTJS-FASTAPI-INTEGRATION.md` — contrat API complet.
- `validation/` (autres fichiers) — historique des phases précédentes
  (quarantaine, scan de dossier, modèles PDF/DOCX).
