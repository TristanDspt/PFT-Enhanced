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

folder = config.DOWNLOADS_DIR
all_files = os.listdir(folder)  # Crée une liste de textes avec les noms des fichiers


for product_id, product in products.items():
    file_path = None
    read_params = formats[product["format"]]  # Réglages pandas du format de fichier de ce produit

    # --- ETAPE A : RECHERCHE ---
    for file_name in all_files:
        if product["keyword"] in file_name:
            file_path = os.path.join(folder, file_name)
            break

    # --- ETAPE B : LECTURE ---
    if file_path:
        if product["type"] == "csv":
            df = pd.read_csv(file_path, **read_params)
        else:
            df = pd.read_excel(file_path, **read_params)

        df["pdt_id"] = product_id  # On ajoute l'ID pour que la base sache de quel livret on parle
    else:
        print(f"Fichier {product['name']} non trouvé dans le dossier.")
        continue  # On passe au produit suivant si pas de fichier

    # --- ETAPE C : COMPARAISON ET ENVOI ---
    # 1. On récupère la date max en SQL pour ce pdt_id spécifique
    file_date = df["cot_date"].max()
    query = f"SELECT MAX(cot_date) FROM cotation_cot WHERE pdt_id = {product_id}"
    with engine.connect() as conn:
        res = pd.read_sql(query, conn).iloc[0, 0] # On stocke le résultat brut (Pandas n'aime pas le type datetime de SQL)
        db_date = pd.to_datetime(res) if res is not None else None # On convertit pour que Pandas soit content

        # 2. On traite le fichier uniquement si on trouve des dates plus récentes
        if db_date is None or file_date > db_date:
            if db_date is None:
                new_df = df
            else:
                new_df = df[df["cot_date"] > db_date]

            # On n'envoie que si le filtre n'est pas vide
            if not new_df.empty:
                new_df.to_sql("cotation_cot", engine, if_exists="append", index=False)
                print(f"Mis à jour : {len(new_df)} lignes ajoutées pour {product['name']}")
        else:
            print(f"{product['name']} est déjà à jour.")