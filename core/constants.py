# core/constants.py

"""
Constantes partagées entre les couches du projet (app, api, pipelines, tests).

Ce module ne contient que des ensembles fermés de valeurs qui existent aussi
en base de données. Il n'y a ni règle de calcul, ni donnée métier, ni paramètre
technique :
- les règles de calcul (ex : quels types de mouvement entrent dans le TRI)
    restent dans les modules de logique, construites à partir de ces Enum ;
- les paramètres techniques vont dans config.yaml / .env ;
- les données métier (portefeuilles, taux fiscaux) vivent en base.

Règle d'ajout : une valeur n'entre ici que si elle est utilisée dans au moins
deux couches différentes.

Aucune dépendance vers Streamlit, pandas ou la base : ce module est importable
de partout.
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