# core/config.py

"""
Configuration globale du projet.

Responsabilités :
- chargement du fichier .env ;
- sélection et validation de l'environnement actif (DEMO ou PROD) ;
- détection de la racine du projet ;
- exposition des chemins utilisés par le code (PROJECT_ROOT, DATA_RAW_DIR,
LOGS_DIR, DOWNLOADS_DIR) ;
- exposition des paramètres de connexion à la base (DB_PARAMS).

La racine du projet est détectée automatiquement en remontant
l'arborescence jusqu'à trouver le fichier requirements.txt,
considéré comme le point d'ancrage du projet.

Ce module lit les réglages mais ne se connecte à rien : la connexion
à la base est de la responsabilité de db_engine.py.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# --------------------------------------------------------------------------------

load_dotenv()
ENVIRONMENT = os.getenv("ENVIRONMENT","DEMO").upper()
if ENVIRONMENT not in ("DEMO", "PROD"):
    raise ValueError(f"ENVIRONMENT invalide : {ENVIRONMENT!r} (attendu : DEMO ou PROD)")

# --------------------------------------------------------------------------------

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

# --------------------------------------------------------------------------------

DB_PARAMS = {
    "host": _require_env(f"HOST_{ENVIRONMENT}"),
    "db_name": _require_env(f"DB_NAME_{ENVIRONMENT}"),
    "username": _require_env(f"USER_{ENVIRONMENT}"),
    "password": _require_env(f"PASSWORD_{ENVIRONMENT}"),
    "port": int(_require_env(f"PORT_{ENVIRONMENT}")),
}


PROJECT_ROOT = find_project_root()

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"
DOWNLOADS_DIR = Path(os.getenv("DOWNLOADS_DIR") or Path.home() / "Downloads")
