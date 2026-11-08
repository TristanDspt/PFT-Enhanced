# core/constants.py

"""
Constantes partagées entre les couches du projet (app, api, pipelines, tests).

Contient uniquement des ensembles fermés de valeurs qui existent aussi en base
(ex : types de mouvement). Pas de règle de calcul, de paramètre ni de donnée
métier : voir ARCHITECTURE.md pour la répartition.

Règle d'ajout : une valeur n'entre ici que si elle est utilisée dans au moins
deux couches différentes.

Aucune dépendance vers Streamlit, pandas ou la base : importable de partout.
"""

from enum import StrEnum


class MovementType(StrEnum):
    """
    Types de mouvement de la table mouvement_mvt (colonne mvt_type_mouvement).

    Doit rester synchronisé avec la contrainte CHECK du schéma
    (db/schema/Create_DB_PFT.sql). StrEnum : chaque membre est une chaîne,
    donc utilisable tel quel dans les filtres pandas et les paramètres SQL.
    """

    ACHAT = "ACHAT"
    VENTE = "VENTE"
    DIVIDENDE = "DIVIDENDE"
    APPORT = "APPORT"
    RETRAIT = "RETRAIT"
    ABONDEMENT = "ABONDEMENT"
    INTERET = "INTERET"
    AJUSTEMENT = "AJUSTEMENT"
    RETRAIT_MIROIR = "RETRAIT_MIROIR"
    TRANSFERT = "TRANSFERT"