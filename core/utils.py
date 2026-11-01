# core/utils.py

from pathlib import Path

import yaml

# --------------------------------------------------------------------------------

def load_yaml(filepath: Path, required: bool = False) -> dict:
    """
    Charge et retourne le contenu d'un fichier YAML.

    Args:
        filepath: Chemin du fichier YAML.
        required: Si True, un fichier absent ou vide lève une erreur.
            Si False (défaut), un fichier absent ou vide donne un
            dictionnaire vide.

    Returns:
        Dictionnaire contenant les données du fichier.

    Raises:
        FileNotFoundError: Si le fichier est absent et que required est True.
        ValueError: Si le fichier est vide et que required est True.
    """
    if not filepath.exists():
        if required:
            raise FileNotFoundError(
                f"Fichier introuvable : {filepath} "
                "(copier le fichier .example correspondant et le renseigner)"
            )
        return {}
    with open(filepath, encoding="utf-8") as f:
        data = yaml.safe_load(f)
        if data is None:
            if required:
                raise ValueError(f"Fichier YAML vide : {filepath}")
            return {}
        return data