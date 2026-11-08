# Veille technologique — PFT-Enhanced

> Une fiche par techno découverte au fil du projet : pourquoi ce choix, source et fiabilité, description rapide.
> Fiabilité : ★★★ doc officielle · ★★ auteur reconnu / article technique daté · ★ tuto ou forum (à recouper)

---

## ruff — novembre 2026
- **Choix / usage dans PFT** : linter du projet (`pyproject.toml`), lancé en local et bientôt en CI (#10). Choisi pour sa rapidité et parce qu'il remplace plusieurs outils (flake8, isort…).
- **Source** : [Documentation officielle ruff](https://docs.astral.sh/ruff/) — ★★★
- **Description** : linter Python écrit en Rust, configurable par familles de règles (E, F, I, UP…).

## python-dotenv — octobre 2026
- **Choix / usage dans PFT** : charge le `.env` dans `core/config.py`, pour garder les secrets hors du code et du repo.
- **Source** : [python-dotenv sur PyPI](https://pypi.org/project/python-dotenv/) — ★★★
- **Description** : lit un fichier `.env` et place ses valeurs dans les variables d'environnement du processus.

## pg_dump / pg_restore — octobre 2026
- **Choix / usage dans PFT** : sauvegarde hebdo automatisée de la base perso, restauration testée.
- **Source** : [Documentation PostgreSQL — pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html) — ★★★
- **Description** : exporte une base PostgreSQL dans un fichier cohérent (format custom compressé), restaurable avec pg_restore.