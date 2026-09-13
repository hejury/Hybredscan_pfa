"""Protection en temps réel — surveillance de dossiers."""
import os, time, threading, json
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler
from analyze import analyser
import quarantine_manager

EXTENSIONS = (".exe", ".dll")
DOSSIERS = [
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Documents"),
    "/tmp",
]

JOURNAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'detections_rt.json')
_lock = threading.Lock()

def journal():
    try:
        with open(JOURNAL) as f:
            return list(reversed(json.load(f)))
    except Exception:
        return []

def _enregistrer(entree):
    with _lock:
        try:
            with open(JOURNAL) as f:
                data = json.load(f)
        except Exception:
            data = []
        data.append(entree)
        data = data[-100:]
        with open(JOURNAL, 'w') as f:
            json.dump(data, f)


class Gestionnaire(FileSystemEventHandler):
    def __init__(self, isoler=True):
        self.isoler = isoler

    def _traiter(self, chemin):
        if not chemin.lower().endswith(EXTENSIONS):
            return
        if not os.path.isfile(chemin):
            return

        time.sleep(1.5)          # laisse le fichier finir de s'écrire
        try:
            # Chemin local reel surveille (Downloads/Desktop/Documents) --
            # une mise en quarantaine deplace bien le fichier original.
            r = analyser(chemin, isoler=self.isoler, source_context=quarantine_manager.SOURCE_WATCHER)
            _enregistrer({
                "heure": time.strftime("%H:%M:%S"),
                "fichier": os.path.basename(chemin),
                "verdict": r.get("verdict", "?"),
                "confiance": r.get("confiance", ""),
                "etape": r.get("etape", ""),
                "chemin": chemin,
            })
        except Exception as e:
            _enregistrer({
                "heure": time.strftime("%H:%M:%S"),
                "fichier": os.path.basename(chemin),
                "verdict": "erreur", "confiance": "",
                "etape": "", "chemin": str(e),
            })

    def on_created(self, event):
        if not event.is_directory:
            self._traiter(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._traiter(event.dest_path)


class Protection:
    """Démarre / arrête la surveillance."""
    def __init__(self):
        self.observer = None

    @property
    def active(self):
        return self.observer is not None and self.observer.is_alive()

    def demarrer(self, isoler=True):
        if self.active:
            return []
        self.observer = Observer()
        g = Gestionnaire(isoler=isoler)
        surveilles = []
        for d in DOSSIERS:
            if os.path.isdir(d):
                self.observer.schedule(g, d, recursive=False)
                surveilles.append(d)
        self.observer.start()
        return surveilles

    def arreter(self):
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=3)
            self.observer = None


if __name__ == "__main__":
    import sys

    # isoler=True => quarantaine automatique. Passer "--no-isoler" pour désactiver.
    isoler = "--no-isoler" not in sys.argv

    protection = Protection()
    surveilles = protection.demarrer(isoler=isoler)

    print("=" * 50)
    print("Protection ACTIVÉE — surveillance en cours")
    print("Quarantaine automatique :", "OUI" if isoler else "NON")
    print("Dossiers surveillés :")
    for d in surveilles:
        print("  OK ", d)
    print("=" * 50)
    print("Ctrl+C pour arrêter.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt de la protection...")
        protection.arreter()
        print("Protection arrêtée.")
