# pipelines/etl/update_pee.py

import os

import pandas as pd

from core import config
from core.db_engine import create_db_engine
from core.utils import load_yaml

# --------------------------------------------------------------------------------

engine = create_db_engine()

banks = load_yaml(config.PROJECT_ROOT / "settings" / "bank.yaml", required=True)
formats = banks["formats"]
products = banks["products"]

dossier = config.DOWNLOADS_DIR
tout_les_fichiers = os.listdir(dossier)  # Crée une liste de textes avec les noms des fichiers


for pdt_id, product in products.items():
    chemin = None
    read_params = formats[product["format"]]  # Réglages pandas du format de fichier de ce produit

    # --- ETAPE A : RECHERCHE ---
    for nom_fichier in tout_les_fichiers:
        if product["keyword"] in nom_fichier:
            chemin = os.path.join(dossier, nom_fichier)
            break

    # --- ETAPE B : LECTURE ---
    if chemin:
        if product["type"] == "csv":
            df = pd.read_csv(chemin, **read_params)
        else:
            df = pd.read_excel(chemin, **read_params)

        df["pdt_id"] = pdt_id  # On ajoute l'ID pour que la base sache de quel livret on parle
    else:
        print(f"Fichier {product['name']} non trouvé dans le dossier.")
        continue  # On passe au produit suivant si pas de fichier

    # --- ETAPE C : COMPARAISON ET ENVOI ---
    # 1. On récupère la date max en SQL pour ce pdt_id spécifique
    date_fichier = df["cot_date"].max()
    query = f"SELECT MAX(cot_date) FROM cotation_cot WHERE pdt_id = {pdt_id}"
    with engine.connect() as conn:
        res = pd.read_sql(query, conn).iloc[0, 0] # On stocke le résultat brut (Pandas n'aime pas le type datetime de SQL)
        date_db = pd.to_datetime(res) if res is not None else None # On convertit pour que Pandas soit content

        # 2. On traite le fichier uniquement si on trouve des dates plus récentes
        if date_db is None or date_fichier > date_db:
            if date_db is None:
                df_neuf = df
            else:
                df_neuf = df[df["cot_date"] > date_db]

            # On n'envoie que si le filtre n'est pas vide
            if not df_neuf.empty:
                df_neuf.to_sql("cotation_cot", engine, if_exists="append", index=False)
                print(f"Mis à jour : {len(df_neuf)} lignes ajoutées pour {product['name']}")
        else:
            print(f"{product['name']} est déjà à jour.")