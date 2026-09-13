"""desktop/launcher.py — Lanceur de l'application desktop HybridScan.

Rôle UNIQUEMENT : démarrer/arrêter les processus (API FastAPI, frontend
Next.js) et ouvrir une fenêtre PyWebView pointant dessus. Ce module ne
contient et ne doit jamais contenir de logique de détection : le moteur
Python (analyze.py, quarantine_manager.py, watcher.py, document_ml/) et
l'API (api/) restent la seule source de vérité, exactement comme pour
l'usage web existant (frontend/lib/api/client.ts -> FastAPI -> analyze.py).
PyWebView n'est qu'une fenêtre native affichant la même interface Next.js
que celle déjà servie sur http://localhost:3000 — rien n'est dupliqué ni
réimplémenté côté client lourd.

Deux modes :
  - géré (par défaut)   : ce script démarre lui-même uvicorn et Next.js,
                          attend qu'ils répondent, ouvre la fenêtre, puis
                          arrête proprement les deux processus à la
                          fermeture de la fenêtre.
  - --dev (attache-toi) : suppose que le développeur a déjà lancé
                          `python -m uvicorn api.main:app --host 127.0.0.1
                          --port 8000` et `npm run dev` dans deux
                          terminaux séparés (workflow existant, inchangé) ;
                          se contente d'attendre que les deux répondent
                          puis ouvre la fenêtre par-dessus.

Aucun chemin ne doit jamais être en dur vers un poste de développement
particulier (voir resolve_repo_root ci-dessous) — condition nécessaire
pour qu'un futur packaging PyInstaller (voir README.md, section « Build
Windows ») fonctionne sur n'importe quelle machine.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import IO, Optional

IS_WINDOWS = sys.platform == "win32"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000

BACKEND_HEALTH_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/v1/health"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}/"

_CREATE_NEW_PROCESS_GROUP = subprocess.CREATE_NEW_PROCESS_GROUP if IS_WINDOWS else 0


def resolve_repo_root() -> Path:
    """Répertoire racine du dépôt (contient api/, frontend/, analyze.py).

    En exécution normale (`python run_desktop.py`), c'est le parent de ce
    fichier (desktop/launcher.py -> repo racine). Une fois gelé par
    PyInstaller (sys.frozen), le binaire lui-même vit à la racine de
    l'application packagée — voir README.md, section « Build Windows »,
    pour la disposition attendue. Jamais un chemin absolu propre à une
    machine."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _log(message: str) -> None:
    print(f"[HybridScan] {message}", flush=True)


def wait_for_http(url: str, timeout: float, interval: float = 0.4) -> bool:
    """Interroge `url` jusqu'à obtenir une réponse HTTP (< 500) ou expirer.

    Remplace les `time.sleep(N)` fixes par une vérification réelle de
    disponibilité, avec une borne haute explicite."""
    deadline = time.monotonic() + timeout
    last_error: Optional[BaseException] = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status < 500:
                    return True
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_error = exc
        time.sleep(interval)
    if last_error:
        _log(f"Timeout en attendant {url} ({last_error}).")
    else:
        _log(f"Timeout en attendant {url}.")
    return False


def check_dependencies(frontend_dir: Path, need_node: bool) -> list[str]:
    """Retourne la liste des dépendances manquantes (vide si tout est OK).
    Ne lève jamais d'exception -- un launcher desktop doit pouvoir
    expliquer clairement ce qui manque plutôt que planter avec une
    traceback Python."""
    missing: list[str] = []

    try:
        import webview  # noqa: F401
    except ImportError:
        missing.append("pywebview (pip install pywebview)")

    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        missing.append("fastapi / uvicorn (pip install fastapi uvicorn)")

    if need_node:
        if shutil.which("node") is None:
            missing.append("Node.js (node introuvable dans le PATH)")
        if not (frontend_dir / "node_modules" / "next").exists():
            missing.append(f"frontend/node_modules -- lancez `npm install` dans {frontend_dir}")

    return missing


def ensure_frontend_env(frontend_dir: Path) -> None:
    """Crée frontend/.env.local depuis .env.example s'il est absent (même
    logique que scripts/start_frontend.ps1) -- garantit que
    NEXT_PUBLIC_HYBRIDSCAN_API_URL pointe vers l'API locale."""
    env_local = frontend_dir / ".env.local"
    env_example = frontend_dir / ".env.example"
    if not env_local.exists() and env_example.exists():
        shutil.copy(env_example, env_local)
        _log(f"{env_local.name} créé depuis .env.example.")


def _next_command(frontend_dir: Path, args: list[str]) -> list[str]:
    """Invoque le binaire Next.js directement via `node` plutôt que par
    `npm run ...`. Sur Windows, `npm`/`next` sont des scripts .cmd : les
    lancer via un sous-shell (cmd.exe) crée un intermédiaire qui se
    termine dès qu'il a délégué à node.exe, laissant celui-ci orphelin
    (constaté en test : `taskkill /T` sur le PID du sous-shell ne trouve
    alors plus rien à tuer, et le port 3000 reste occupé). Appeler
    `node <next_bin> ...` fait de node.exe l'enfant DIRECT du launcher :
    un simple arrêt de ce PID suffit, sans sous-shell à traverser."""
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js (node) introuvable dans le PATH.")
    next_bin = frontend_dir / "node_modules" / "next" / "dist" / "bin" / "next"
    if not next_bin.exists():
        raise RuntimeError(f"Binaire Next.js introuvable : {next_bin} (lancez `npm install`).")
    return [node, str(next_bin), *args]


def _log_streams(log_dir: Optional[Path], name: str, log_files: list[IO[str]]):
    """En exécution normale (console attachée), on laisse les enfants
    hériter de la console du launcher -- utile en développement. Une fois
    gelé en application fenêtrée (PyInstaller --windowed, section 10 :
    jamais de fenêtre terminal derrière l'app), il n'y a plus de console à
    hériter : on redirige alors vers des fichiers journaux."""
    if not getattr(sys, "frozen", False) or log_dir is None:
        return None, None
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = open(log_dir / f"{name}.log", "w", encoding="utf-8", errors="replace")
    log_files.append(fh)
    return fh, subprocess.STDOUT


def start_backend(repo_root: Path, reload: bool, log_dir: Optional[Path], log_files: list[IO[str]]) -> subprocess.Popen:
    cmd = [sys.executable, "-m", "uvicorn", "api.main:app",
           "--host", BACKEND_HOST, "--port", str(BACKEND_PORT)]
    if reload:
        cmd.append("--reload")
    _log(f"Démarrage de l'API FastAPI ({BACKEND_HOST}:{BACKEND_PORT})...")
    stdout, stderr = _log_streams(log_dir, "backend", log_files)
    return subprocess.Popen(
        cmd, cwd=str(repo_root), stdout=stdout, stderr=stderr,
        creationflags=_CREATE_NEW_PROCESS_GROUP,
    )


def start_frontend(frontend_dir: Path, mode: str, rebuild: bool,
                    log_dir: Optional[Path], log_files: list[IO[str]]) -> subprocess.Popen:
    """mode == "prod" : build de production une seule fois (mis en cache
    via .next/BUILD_ID), puis `next start` -- démarrage rapide à chaque
    lancement suivant, sortie sans rechargement à chaud (le choix le plus
    stable pour un usage desktop packagé, cahier des charges section 9).
    mode == "dev"  : `next dev`, pour itérer sur l'interface."""
    if mode == "prod":
        build_id = frontend_dir / ".next" / "BUILD_ID"
        if rebuild or not build_id.exists():
            _log("Build de production du frontend (une seule fois, jusqu'à ~1 min)...")
            build = subprocess.run(
                _next_command(frontend_dir, ["build"]), cwd=str(frontend_dir),
            )
            if build.returncode != 0:
                raise RuntimeError("`next build` a échoué -- voir la sortie ci-dessus.")
        cmd = _next_command(frontend_dir, ["start", "-p", str(FRONTEND_PORT)])
    else:
        cmd = _next_command(frontend_dir, ["dev", "-p", str(FRONTEND_PORT)])

    _log(f"Démarrage du frontend Next.js ({mode}, port {FRONTEND_PORT})...")
    stdout, stderr = _log_streams(log_dir, "frontend", log_files)
    return subprocess.Popen(
        cmd, cwd=str(frontend_dir), stdout=stdout, stderr=stderr,
        creationflags=_CREATE_NEW_PROCESS_GROUP,
    )


def stop_process(name: str, proc: Optional[subprocess.Popen]) -> None:
    """Arrêt propre. `proc.pid` est déjà le PID réel de node.exe/python.exe
    (voir _next_command -- aucun sous-shell npm/cmd.exe intermédiaire), un
    simple arrêt de ce PID suffit donc en principe ; `/T` sur Windows reste
    une marge de sécurité (Next.js peut démarrer ses propres processus
    worker internes selon la configuration)."""
    if proc is None or proc.poll() is not None:
        return
    _log(f"Arrêt de {name} (pid {proc.pid})...")
    try:
        if IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True, check=False,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    except Exception as exc:  # pragma: no cover - best effort cleanup
        _log(f"Avertissement : arrêt de {name} incomplet ({exc}).")


def _watch_managed_processes(managed: list[tuple[str, subprocess.Popen]], on_crash) -> None:
    """Fil d'arrière-plan : si un processus géré (API ou frontend) meurt de
    lui-même pendant que la fenêtre est ouverte, on le signale et on ferme
    la fenêtre plutôt que de laisser l'utilisateur face à une interface
    figée sans explication."""
    while True:
        time.sleep(2)
        for name, proc in managed:
            code = proc.poll()
            if code is not None:
                _log(f"{name} s'est arrêté de façon inattendue (code {code}).")
                on_crash()
                return


def _resolve_icon_path() -> Optional[Path]:
    icon_path = Path(__file__).resolve().parent / "assets" / "hybridscan.ico"
    return icon_path if icon_path.exists() else None


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_desktop.py",
        description="Lance HybridScan comme application desktop (fenêtre PyWebView "
                     "affichant l'interface Next.js, connectée à l'API FastAPI locale).",
    )
    parser.add_argument(
        "--dev", action="store_true",
        help="Ne démarre ni l'API ni le frontend -- suppose qu'ils tournent déjà "
             "(uvicorn --reload / npm run dev dans des terminaux séparés) et ouvre "
             "seulement la fenêtre par-dessus.",
    )
    parser.add_argument(
        "--frontend-dev", action="store_true",
        help="Démarre le frontend avec `npm run dev` au lieu du build de production "
             "(ignoré avec --dev).",
    )
    parser.add_argument(
        "--rebuild-frontend", action="store_true",
        help="Force un nouveau `npm run build` même si un build existe déjà.",
    )
    parser.add_argument(
        "--backend-reload", action="store_true",
        help="Démarre uvicorn avec --reload (développement, ignoré avec --dev).",
    )
    parser.add_argument(
        "--no-window", action="store_true",
        help="Démarre les serveurs sans ouvrir PyWebView (débogage) -- Ctrl+C pour arrêter.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    repo_root = resolve_repo_root()
    frontend_dir = repo_root / "frontend"
    log_dir = repo_root / "logs"

    missing = check_dependencies(frontend_dir, need_node=not args.dev)
    if missing:
        _log("Dépendances manquantes :")
        for item in missing:
            print(f"  - {item}")
        return 1

    managed: list[tuple[str, subprocess.Popen]] = []
    log_files: list[IO[str]] = []

    try:
        if not args.dev:
            ensure_frontend_env(frontend_dir)

            backend_proc = start_backend(repo_root, args.backend_reload, log_dir, log_files)
            managed.append(("backend", backend_proc))
            if not wait_for_http(BACKEND_HEALTH_URL, timeout=30):
                _log("L'API FastAPI n'a pas répondu à temps -- abandon.")
                return 1

            frontend_mode = "dev" if args.frontend_dev else "prod"
            frontend_proc = start_frontend(
                frontend_dir, frontend_mode, args.rebuild_frontend, log_dir, log_files,
            )
            managed.append(("frontend", frontend_proc))
        else:
            _log("Mode --dev : rattachement aux serveurs déjà lancés manuellement.")

        # Le premier `npm run build` peut prendre jusqu'à ~1 min ; le
        # démarrage (dev ou `next start`) est ensuite rapide.
        frontend_timeout = 180 if (not args.dev and not args.frontend_dev) else 60
        if not wait_for_http(FRONTEND_URL, timeout=frontend_timeout):
            _log("Le frontend Next.js n'a pas répondu à temps -- abandon.")
            return 1

        _log(f"Prêt -- API {BACKEND_HEALTH_URL} / Frontend {FRONTEND_URL}")

        if args.no_window:
            _log("--no-window : serveurs démarrés, Ctrl+C pour arrêter.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            return 0

        import webview  # importé ici pour que --no-window fonctionne même sans backend GUI

        window = webview.create_window(
            "HybridScan",
            FRONTEND_URL,
            width=1400,
            height=900,
            min_size=(1100, 700),
            resizable=True,
            confirm_close=False,
        )

        if managed:
            threading.Thread(
                target=_watch_managed_processes,
                args=(managed, window.destroy),
                daemon=True,
            ).start()

        storage_path = Path.home() / ".hybridscan" / "webview-profile"
        storage_path.mkdir(parents=True, exist_ok=True)

        webview.start(
            icon=str(_resolve_icon_path()) if _resolve_icon_path() else None,
            private_mode=False,
            storage_path=str(storage_path),
        )
        return 0
    finally:
        for name, proc in reversed(managed):
            stop_process(name, proc)
        for fh in log_files:
            try:
                fh.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
