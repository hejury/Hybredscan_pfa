import json, os, hashlib, hmac, secrets
_USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")

def _load_users():
    if not os.path.exists(_USERS_FILE):
        return {}
    try:
        with open(_USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def _save_users(users):
    with open(_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def _hash_password(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def register(username, password):
    username = username.strip()
    if not username or not password:
        return False, "Nom d'utilisateur et mot de passe requis."
    if len(password) < 4:
        return False, "Le mot de passe doit contenir au moins 4 caracteres."
    users = _load_users()
    if username in users:
        return False, "Ce nom d'utilisateur existe deja."
    salt = secrets.token_hex(16)
    users[username] = {"salt": salt, "hash": _hash_password(password, salt)}
    _save_users(users)
    return True, "Compte cree. Vous pouvez maintenant vous connecter."

def verify(username, password):
    users = _load_users()
    if username not in users:
        return False
    r = users[username]
    return _hash_password(password, r["salt"]) == r["hash"]

def _compte_configure():
    """Charge le compte administrateur unique configure via Streamlit
    secrets (section [auth]) puis, en repli, des variables d'environnement.
    N'utilise jamais users.json, qui reste present mais inerte pour
    l'application Streamlit (voir SECURITY-NOTE.md / PRODUCTION-HARDENING.md).

    Format attendu de password_hash : "<sel_hex>$<empreinte_sha256_hex>",
    reutilisant _hash_password() ci-dessus (meme algorithme, aucun nouveau
    schema de hachage introduit).

    Retour : (nom_utilisateur, sel, empreinte_attendue) ou (None, None, None)
    si la configuration est absente ou malformee — echoue toujours "ferme"."""
    nom = None
    valeur_hash = None
    try:
        import streamlit as st
        section = st.secrets.get("auth", {})
        nom = section.get("username")
        valeur_hash = section.get("password_hash")
    except Exception:
        pass
    nom = os.environ.get("HYBRIDSCAN_AUTH_USERNAME", nom)
    valeur_hash = os.environ.get("HYBRIDSCAN_AUTH_PASSWORD_HASH", valeur_hash)
    if not nom or not valeur_hash or "$" not in valeur_hash:
        return None, None, None
    sel, _, empreinte = valeur_hash.partition("$")
    if not sel or not empreinte:
        return None, None, None
    return nom, sel, empreinte

def verify_compte_configure(username, password):
    """Verifie des identifiants par rapport au compte unique configure
    (voir _compte_configure) — jamais par rapport a users.json. Reutilise
    l'algorithme de hachage existant (_hash_password). Comparaison en temps
    constant (hmac.compare_digest) sur le nom d'utilisateur ET l'empreinte,
    pour ne jamais laisser un ecart de temps reveler lequel des deux champs
    etait incorrect. Toute configuration absente ou invalide renvoie False —
    ne produit jamais de session authentifiee (echec ferme)."""
    if not username or not password:
        return False
    nom_configure, sel, empreinte_attendue = _compte_configure()
    if not nom_configure:
        return False
    empreinte_calculee = _hash_password(password, sel)
    nom_ok = hmac.compare_digest(username.strip().encode("utf-8"),
                                 nom_configure.encode("utf-8"))
    hash_ok = hmac.compare_digest(empreinte_calculee.encode("utf-8"),
                                  empreinte_attendue.encode("utf-8"))
    return nom_ok and hash_ok
