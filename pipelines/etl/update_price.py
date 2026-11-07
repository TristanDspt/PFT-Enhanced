# pipelines/etl/update_price.py

import logging
import sys
from datetime import datetime

import pandas as pd
import yfinance as yf

from core import config
from core.db_engine import create_db_engine

# --------------------------------------------------------------------------------

# Configure le journal (va créer un fichier update_price.log)
config.LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=config.LOGS_DIR / "update_price.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

logging.debug("Démarrage de la mise à jour automatique.")  # info sur le lancement du script

# 1. Connection à la DB
engine = create_db_engine()

logging.debug("Connexion établie !")  # pour savoir s'il se connecte bien à la base

# 2. Récupérer uniquement les produits "boursiers"
query = """
    SELECT pdt_id, pdt_ticker
    FROM public.produit_financier_pdt
    WHERE pdt_ticker is not null
"""
ticker_list_df = pd.read_sql(query, engine)

# 3. On demande à la base la date la plus récente qu'on possède
query_last_date = "SELECT MAX(cot_date) FROM public.cotation_cot"  # SELECT MAX envoi NONE si la table est vide
last_date_in_db = pd.read_sql(query_last_date, engine).iloc[0, 0]

# 4. On définit la date de début pour Yahoo Finance
if last_date_in_db is None:
    start_date = "2024-01-01"
    logging.debug("Base vide, on récupère tout depuis 2024.")  # debug 1er import
else:
    # On ajoute +1 jour pour ne pas re-télécharger le dernier jour déjà présent
    start_date = last_date_in_db + pd.Timedelta(days=1)
    if start_date > datetime.now().date():
        logging.info(f"Déjà à jour (Dernière date : {last_date_in_db}).")  # si le script a déjà été lancé ce jour
        logging.info("-" * 50)  # pour améliorer la lisibilité des logs
        engine.dispose()
        sys.exit()
    logging.info(f"Dernière donnée en base : {last_date_in_db}. Ajout à partir du {start_date}")  # info sur l'action du script

# 5. LA BOUCLE
for index, row in ticker_list_df.iterrows():
    ticker = row["pdt_ticker"]
    product_id = row["pdt_id"]

    try:
        temp_df = yf.download(ticker, start=start_date, multi_level_index=False)

        if not temp_df.empty:
            temp_df = temp_df["Close"].reset_index()
            temp_df.columns = ["cot_date", "cot_prix"]
            temp_df["pdt_id"] = product_id
            temp_df["cot_date"] = pd.to_datetime(temp_df["cot_date"]).dt.date

            # On injecte uniquement les nouvelles lignes
            temp_df.to_sql("cotation_cot", engine, if_exists="append", index=False)
            logging.info(f"Ajout de {len(temp_df)} nouvelles lignes pour {ticker}")  # info sur le bon déroulement de l'import
        else:
            logging.info(f"Déjà à jour pour {ticker}.")  # info sur le bon déroulement de l'import
    except Exception as e:  # noqa: BLE001
        logging.error(f"Erreur sur {ticker} : {e}")  # info sur le type d'erreur rencontrée
engine.dispose()  # ferme la connection SQL pour liberer de la place en memoire
logging.debug("Connexion fermée. Traitement terminé !")  # info sur la fermeture du script
logging.info("-" * 50)  # pour améliorer la lisibilité des logs
