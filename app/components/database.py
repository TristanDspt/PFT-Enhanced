# app/components/database.py

import pandas as pd
import streamlit as st

from core.db_engine import create_db_engine

# --------------------------------------------------------------------------------

@st.cache_resource
def get_engine():
    """Retourne l'engine de l'application, mis en cache par Streamlit."""
    return create_db_engine()


@st.cache_data
def get_view(view_name, _engine):
    """
    Charge une vue SQL complète en DataFrame et la met en cache.
    
    Args:
        view_name (str): nom de la vue SQL (ex: "view_global_portefeuille")
        _engine: connexion SQLAlchemy (préfixe _ pour exclure du cache Streamlit)
    
    Returns:
        DataFrame: contenu complet de la vue
    """
    df = pd.read_sql(f"SELECT * FROM {view_name}", _engine)
    return df


def get_product_quotes(engine, product_id, start_date):
    """
    Récupère le cours actuel et les extremes de prix sur la période sélectionnée.

    Args:
        engine: connexion SQLAlchemy
        pdt_id (int): id du produit financier
        start_date (pd.Timestamp): date de début de la période (depuis get_start_date())

    Returns:
        DataFrame: une ligne avec [max, min, cot_date, cot_prix]
    """
    query = """
        WITH slider AS (
            -- High et Low sur la période filtrée
            SELECT 
                max(cot_prix) AS max,
                min(cot_prix) AS min
            FROM cotation_cot
            WHERE 
                pdt_id = %(pdt_id)s
                AND cot_date >= %(start_date)s
        ),
        dernier AS (
            -- Dernière cotation connue (pas de filtre période)
            SELECT 
                cot_date,
                cot_prix,
                ROW_NUMBER() OVER (PARTITION BY pdt_id ORDER BY cot_date DESC) AS rn
            FROM cotation_cot
            WHERE 
                pdt_id = %(pdt_id)s
        )
        -- Jointure sans clé : une seule ligne dans chaque CTE
        SELECT
            s.max,
            s.min,
            d.cot_date,
            d.cot_prix
        FROM dernier d
        CROSS JOIN slider s
        WHERE rn = 1
    """
    quote_df = pd.read_sql(query, engine, params={"pdt_id": product_id, "start_date": start_date})
    cols = ['min', 'max', 'cot_prix']
    quote_df[cols] = quote_df[cols].astype(float)
    quote_df['min'] = quote_df['min'].fillna(quote_df['cot_prix'])
    quote_df['max'] = quote_df['max'].fillna(quote_df['cot_prix'])

    return quote_df