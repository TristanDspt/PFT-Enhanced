# core/config.py

"""
Configuration globale du projet.

Responsabilités :
- chargement du fichier .env ;
- sélection et validation de l'environnement actif (DEMO ou PROD) ;
- détection de la racine du projet ;
- exposition des chemins utilisés par le code (PROJECT_ROOT, DATA_RAW_DIR,
    LOGS_DIR, DOWNLOADS_DIR, CONFIG_PATH) ;
- exposition des paramètres de connexion à la base (DB_PARAMS) ;
- chargement et validation des paramètres métier de settings/config.yaml
    (CONFIG, TAX_RATES).

Organisation du fichier : les fonctions internes en haut, puis les constantes
regroupées par thème (environnement, chemins, base de données, paramètres métier).

Les secrets et la connexion viennent du .env, les réglages métier du config.yaml.

Attention : tout est lu et validé à l'import. Un .env incomplet ou un config.yaml
invalide fait échouer l'import du module (échec volontaire, pour détecter
l'erreur au démarrage). Les fonctions de calcul ne doivent donc pas importer
ce module : elles reçoivent leurs paramètres en argument.

La racine du projet est détectée automatiquement en remontant
l'arborescence jusqu'à trouver le fichier requirements.txt,
considéré comme le point d'ancrage du projet.

Ce module lit les réglages mais ne se connecte à rien : la connexion
à la base est de la responsabilité de db_engine.py.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from core.utils import load_yaml

# ── Fonctions internes ────────────────────────────────────────────────────────

def _require_env(name: str) -> str:
    """
    Retourne la valeur d'une variable d'environnement obligatoire.

    Args:
        name: Nom de la variable à lire.

    Returns:
        Valeur de la variable.

    Raises:
        ValueError: Si la variable est absente ou vide.
    """
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Variable d'environnement manquante ou vide : {name}")
    return value


def find_project_root() -> Path:
    """
    Recherche la racine du projet à partir de l'emplacement
    du fichier courant.

    La fonction remonte l'arborescence des dossiers jusqu'à
    trouver un fichier requirements.txt, considéré comme le
    point d'ancrage du projet.

    Returns:
        Chemin absolu vers la racine du projet.

    Raises:
        FileNotFoundError: Si aucun fichier requirements.txt
            n'est trouvé dans l'arborescence parente.
    """
    current = Path(__file__).resolve()

    while current != current.parent:
        if (current / "requirements.txt").exists():
            return current
        current = current.parent

    raise FileNotFoundError("requirements.txt introuvable")


def _validate_tax_rates(tax_rates: dict) -> dict[str, float]:
    """
    Valide les taux d'imposition par type d'enveloppe.

    Args:
        tax_rates: Section 'tax_rates' du config.yaml.

    Returns:
        Le même dictionnaire {type_enveloppe: taux}, une fois validé.

    Raises:
        ValueError: Si la section est vide ou si un taux n'est pas
            un nombre entre 0 et 1.
    """
    if not tax_rates:
        raise ValueError(f"Section 'tax_rates' manquante ou vide dans {CONFIG_PATH}")

    for envelope, rate in tax_rates.items():
        if not isinstance(rate, (int, float)) or not 0 <= rate <= 1:
            raise ValueError(
                f"Taux invalide pour {envelope!r} : {rate!r} (attendu : nombre entre 0 et 1)"
            )
    return tax_rates

# ── Environnement ─────────────────────────────────────────────────────────────

load_dotenv()
ENVIRONMENT = os.getenv("ENVIRONMENT","DEMO").upper()
if ENVIRONMENT not in ("DEMO", "PROD"):
    raise ValueError(f"ENVIRONMENT invalide : {ENVIRONMENT!r} (attendu : DEMO ou PROD)")

# ── Chemins ───────────────────────────────────────────────────────────────────

PROJECT_ROOT = find_project_root()
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"
DOWNLOADS_DIR = Path(os.getenv("DOWNLOADS_DIR") or Path.home() / "Downloads")
CONFIG_PATH = PROJECT_ROOT / "settings" / "config.yaml"

# ── Base de données (.env) ────────────────────────────────────────────────────

DB_PARAMS = {
    "host": _require_env(f"HOST_{ENVIRONMENT}"),
    "db_name": _require_env(f"DB_NAME_{ENVIRONMENT}"),
    "username": _require_env(f"USER_{ENVIRONMENT}"),
    "password": _require_env(f"PASSWORD_{ENVIRONMENT}"),
    "port": int(_require_env(f"PORT_{ENVIRONMENT}")),
}

# ── Paramètres métier (config.yaml) ───────────────────────────────────────────

CONFIG = load_yaml(CONFIG_PATH, required=True)
TAX_RATES = _validate_tax_rates(CONFIG.get("tax_rates", {}))
