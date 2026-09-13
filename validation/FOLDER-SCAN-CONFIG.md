# FOLDER-SCAN-CONFIG.md — Configuration du scan de dossier

## 1. Racine de scan configurée

```
C:\Users\user\Desktop\HybridScan-Scan
```

Le scan de dossier accepte cette racine **et tous ses descendants**,
récursivement. Rien en dehors n'est autorisé.

## 2. Mécanisme de configuration

**Aucun nouveau mécanisme inventé.** Le projet dispose déjà exactement de
ce pattern pour `VT_API_KEY` (`analyze.py::_charger_cle_vt()`) : variable
d'environnement en premier, `.streamlit/secrets.toml` en repli. Le scan de
dossier utilisait déjà la variable d'environnement seule
(`HYBRIDSCAN_ALLOWED_SCAN_DIRS`, lue par `app.py::_racines_autorisees()`)
mais n'avait pas de repli persistant — c'est ce qui manquait, pas un
mécanisme entièrement nouveau.

`app.py` ajoute une seule fonction, `_config_racines_scan()`, reprenant
littéralement le même repli :

```python
def _config_racines_scan():
    brut = os.environ.get("HYBRIDSCAN_ALLOWED_SCAN_DIRS")
    if brut:
        return brut
    try:
        return st.secrets.get("HYBRIDSCAN_ALLOWED_SCAN_DIRS", "") or ""
    except Exception:
        return ""
```

`_racines_autorisees()` (inchangée sur le fond : parsing `os.pathsep`,
résolution canonique, `is_dir()`, échec silencieux fail-safe) appelle
désormais `_config_racines_scan()` au lieu de lire `os.environ`
directement.

### Où c'est configuré

`.streamlit/secrets.toml` (racine du dépôt), clé de premier niveau (pas
sous `[auth]`) :

```toml
HYBRIDSCAN_ALLOWED_SCAN_DIRS = 'C:\Users\user\Desktop\HybridScan-Scan'
```

- **Persiste après redémarrage de Streamlit** — c'est un fichier, pas une
  variable de processus éphémère.
- **Ce n'est pas un secret** (chemin de dossier, pas une clé/API/mot de
  passe) mais réutilise le fichier `secrets.toml` déjà en place pour
  `VT_API_KEY`/`[auth]` plutôt que d'introduire un second fichier de
  configuration.
- **Non commité** (`secrets.toml` déjà gitignored, confirmé avant
  modification).

### Pour changer la racine plus tard

Éditer `.streamlit/secrets.toml`, modifier la valeur de
`HYBRIDSCAN_ALLOWED_SCAN_DIRS`, redémarrer Streamlit. Plusieurs racines :
séparer par `;` (Windows) — ex.
`'C:\A\Scan;C:\B\Autre'`. La variable d'environnement
`HYBRIDSCAN_ALLOWED_SCAN_DIRS` reste disponible et prioritaire (utile pour
un déploiement/conteneur), sans avoir à toucher `secrets.toml`.

### ⚠️ Piège découvert et documenté (comportement Streamlit, pas un bug HybridScan)

Streamlit copie automatiquement les clés de premier niveau de
`secrets.toml` dans `os.environ` dès le premier accès à `st.secrets` (dès
la page de connexion). Une valeur posée manuellement dans `os.environ`
**avant** le démarrage du script peut donc être écrasée par la valeur
réelle de `secrets.toml` dès que Streamlit charge ses secrets. Sans
incidence en usage normal (une seule source de vérité en pratique), mais
documenté ici car il a fait échouer les premières versions des tests
automatisés de cette phase (voir `tests/test_folder_scan_config.py`, qui
réécrit temporairement `secrets.toml` plutôt que de compter sur
`os.environ` seul pour isoler ses scénarios).

## 3. Limite fonctionnelle préexistante — non modifiée

`valider_dossier_scan()` ne traite que les fichiers `.exe`/`.dll`
(inchangé par cette phase — voir le code, ligne filtrant explicitement
`n.lower().endswith((".exe", ".dll"))`). **Un `.pdf`/`.docx` placé dans le
dossier scanné est ignoré, exactement comme un `.txt`** — ce n'est pas
une décision de cette phase, c'est le périmètre du scan de dossier tel
qu'il existait déjà. Les fixtures `safe_test.pdf`/`safe_test.docx`/
`nested/safe_nested.docx` demandées ont été créées comme demandé, mais
ne sont **pas** traitées par le scan de dossier (elles restent utilisables
via "Analyser un fichier", qui prend en charge PDF/DOCX). Des fixtures
`.exe` supplémentaires (`safe_test.exe`, `nested/safe_nested.exe`) ont été
ajoutées pour que le test de récursivité soit réellement démonstratif.

## 4. Frontière de sécurité

| Chemin | Résultat | Raison |
|---|---|---|
| `C:\Users\user\Desktop\HybridScan-Scan` | **AUTORISÉ** | racine exacte |
| `...\HybridScan-Scan\test-files` | **AUTORISÉ** | descendant direct |
| `...\HybridScan-Scan\test-files\nested` | **AUTORISÉ** | descendant imbriqué |
| `C:\` | **REJETÉ** | racine du système de fichiers (`_cible_interdite`) |
| `C:\Windows` | **REJETÉ** | hors racine autorisée |
| `C:\Users\user\Downloads` | **REJETÉ** | hors racine autorisée |
| `C:\Users\user\Desktop` (parent de la racine) | **REJETÉ** | n'est pas un descendant de la racine — seul le dossier configuré et ses enfants sont autorisés, jamais son parent |
| `...\HybridScan-Scan\..\Downloads` (traversée) | **REJETÉ** | résolu canoniquement (`Path.resolve(strict=True)`) puis rejeté (introuvable ou hors racine selon le cas réel) |

Confinement vérifié par `Path.relative_to()` après résolution canonique
(`_cible_dans_racines_autorisees`) — jamais une comparaison de préfixe de
chaîne. Mécanisme inchangé par cette phase, seulement la source de sa
configuration.

## 5. Comportement récursif

- **Coché** (par défaut) : `os.walk()` — descend dans tous les
  sous-dossiers.
- **Décoché** : `os.listdir()` — dossier indiqué uniquement, aucune
  descente.

Vérifié avec les fixtures : `nested\safe_nested.exe` traité uniquement
quand la case est cochée.

## 6. Interaction avec la quarantaine

Inchangée. Le scan de dossier continue de passer
`source_context=quarantine_manager.SOURCE_FOLDER_SCAN` (chemin local réel
→ `original_removed=true` en cas de mise en quarantaine réelle). La case
"Quarantaine automatique" du DOSSIER active seulement `isoler=True` dans
l'appel à `analyser()` — elle ne modifie aucun seuil ni aucune règle de
verdict. La politique DOCX (verdict malveillant du prototype de recherche
IA_DOCX jamais mis en quarantaine automatiquement) reste inchangée et
n'a pas été contournée pour ce test.

## 7. Résultat du smoke-test réel

Exécuté via `streamlit.testing.v1.AppTest` pilotant réellement
l'interface (identifiants réels, clic réel sur les cases à cocher et le
bouton), contre la configuration **persistante réelle** du dépôt (pas une
valeur isolée artificielle) :

- Message "non configuré" : absent. "Dossiers autorisés" affiche
  `HybridScan-Scan`.
- Scan non récursif sur `test-files` : 1 fichier traité
  (`safe_test.exe`), aucune exception.
- Scan récursif sur `test-files` : 2 fichiers traités (`safe_test.exe` +
  `safe_nested.exe`), aucune exception.
- `ignored_test.txt`/`safe_test.pdf`/`safe_test.docx` : jamais traités
  (hors périmètre du scan de dossier, §3).
- `history.csv` réel du dépôt : 78 → 81 lignes (3 nouvelles entrées
  légitimes). `quarantine/` réel : inchangé (14 → 14, aucun verdict
  malveillant sur ces fixtures synthétiques).
- Verdicts obtenus : `indetermine` pour les deux `.exe` (bytes MZ
  synthétiques, pas un PE valide — `pefile` échoue proprement, comportement
  honnête attendu, pas un bug).

## 8. Tests automatisés (permanents)

`tests/test_folder_scan_config.py` — 7/7 : racine absente gérée
proprement, racine configurée fait disparaître l'avertissement, racine +
sous-dossier imbriqué acceptés, chemin hors racine rejeté, traversée de
chemin rejetée, récursif ON trouve le fichier imbriqué, récursif OFF
l'ignore. Utilise `HYBRIDSCAN_BASE_DIR` isolé (jamais le `history.csv`/
`quarantine` réels) et réécrit **temporairement** `.streamlit/secrets.toml`
(restauration octet pour octet vérifiée en `finally`, y compris fins de
ligne) pour contrôler la configuration testée indépendamment du poste réel.

## 9. Limites connues

- Le scan de dossier reste strictement `.exe`/`.dll` — PDF/DOCX non
  couverts par cette fonctionnalité (voir §3). Une extension éventuelle
  serait un changement de comportement à valider séparément, pas
  entreprise ici.
- La configuration vit dans un fichier local non versionné
  (`secrets.toml`) : sur une nouvelle machine/déploiement, elle doit être
  reconfigurée (documentée ici précisément pour cette raison).
- Le comportement de copie automatique secrets→environ de Streamlit
  (§2) peut surprendre quiconque tenterait de surcharger
  `HYBRIDSCAN_ALLOWED_SCAN_DIRS` par variable d'environnement APRÈS le
  premier chargement des secrets dans le même processus — sans impact en
  usage normal (un seul redémarrage, une seule source), documenté par
  prudence.
