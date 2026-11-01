# core/db_engine.py

from sqlalchemy import URL, create_engine

from core import config

# --------------------------------------------------------------------------------

def create_db_engine():
    """
    Crée l'engine SQLAlchemy à partir de la configuration active.

    L'engine gère un pool de connexions vers PostgreSQL. Les paramètres
    (hôte, port, base, identifiants) viennent de core.config.DB_PARAMS
    et dépendent de l'environnement actif (DEMO ou PROD).

    Returns:
        Un nouvel engine SQLAlchemy à chaque appel. Le cache éventuel
        est géré par l'appelant.
    """
    url_object = URL.create(
        "postgresql+psycopg2",
        username=config.DB_PARAMS["username"],
        password=config.DB_PARAMS["password"],
        host=config.DB_PARAMS["host"],
        database=config.DB_PARAMS["db_name"],
        port=config.DB_PARAMS["port"],
    )
    return create_engine(url_object)