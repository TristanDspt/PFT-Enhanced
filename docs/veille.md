# Veille technologique — PFT-Enhanced

> Une fiche par techno découverte au fil du projet : pourquoi ce choix, source et fiabilité, description rapide.
> Fiabilité : ★★★ doc officielle · ★★ auteur reconnu / article technique daté · ★ tuto ou forum (à recouper)

---

## pg_dump / pg_restore — octobre 2026
- **Choix / usage dans PFT** : sauvegarde hebdo automatisée de la base perso, restauration testée.
- **Source** : [Documentation PostgreSQL — pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html) — ★★★
- **Description** : exporte une base PostgreSQL dans un fichier cohérent (format custom compressé), restaurable avec pg_restore.

## python-dotenv — octobre 2026
- **Choix / usage dans PFT** : charge le `.env` dans `core/config.py`, pour garder les secrets hors du code et du repo.
- **Source** : [python-dotenv sur PyPI](https://pypi.org/project/python-dotenv/) — ★★★
- **Description** : lit un fichier `.env` et place ses valeurs dans les variables d'environnement du processus.

## FastAPI — octobre 2026
- **Choix / usage dans PFT** : framework retenu pour l'API données (#32) et l'API du modèle (phase 4). Déjà utilisé en cours.
- **Source** : [Documentation officielle FastAPI](https://fastapi.tiangolo.com/) — ★★★
- **Description** : framework web Python pour construire des API REST, avec validation des données par Pydantic et documentation OpenAPI générée automatiquement.

## GitHub Projects — novembre 2026
- **Choix / usage dans PFT** : pilotage agile du projet : board Kanban, sprints de 2 semaines (champ Iteration), milestones par phase, issues fermées par les commits (`closes #N`).
- **Source** : [Documentation GitHub — About Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects) — ★★★
- **Description** : outil de gestion de projet intégré à GitHub, relié directement aux issues et aux pull requests du dépôt.

## ruff — novembre 2026
- **Choix / usage dans PFT** : linter du projet (`pyproject.toml`), lancé en local et bientôt en CI (#10). Choisi pour sa rapidité et parce qu'il remplace plusieurs outils (flake8, isort…).
- **Source** : [Documentation officielle ruff](https://docs.astral.sh/ruff/) — ★★★
- **Description** : linter Python écrit en Rust, configurable par familles de règles (E, F, I, UP…).

## Docker — novembre 2026
- **Choix / usage dans PFT** : prévu pour le stockage big data local (#25) puis la livraison de l'app et des API (phase 5). Découvert en préparation de la session de cours.
- **Source** : [Documentation officielle Docker](https://docs.docker.com/get-started/) — ★★★ ; découverte initiale via plusieurs tutos YouTube (★), recoupés avec la doc
- **Description** : outil de conteneurisation : chaque service tourne dans un conteneur isolé et reproductible, orchestrés ensemble avec docker-compose.

## pytest — novembre 2026
- **Choix / usage dans PFT** : framework de tests du projet, prévu pour les tests des fonctions pures de `st_logic.py` (#9) puis lancé en CI (#10). Vu en cours (session du 16 au 20 novembre), démarche TDD.
- **Source** : [Documentation officielle pytest](https://docs.pytest.org/) — ★★★
- **Description** : framework de tests Python : des fonctions préfixées `test_` contenant des `assert`, découvertes et lancées automatiquement par la commande `pytest`. Fixtures pour préparer les données de test.