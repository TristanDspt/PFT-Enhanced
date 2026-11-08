# Veille technologique — PFT-Enhanced

> Une fiche par techno découverte au fil du projet : pourquoi ce choix, source et fiabilité, description rapide.
> Fiabilité : ★★★ doc officielle · ★★ auteur reconnu / article technique daté · ★ tuto ou forum (à recouper)

---

## FastAPI — octobre 2026
- **Choix / usage dans PFT** : framework retenu pour l'API données (#32) et l'API du modèle (phase 4).
- **Source** : [Documentation officielle FastAPI](https://fastapi.tiangolo.com/) — ★★★
- **Description** : framework web Python pour construire des API REST, avec validation des données par Pydantic et documentation OpenAPI générée automatiquement.
- **Alternatives** : Flask, Django REST Framework — écartées : FastAPI intègre nativement la validation des entrées (Pydantic) et la doc OpenAPI, deux exigences de C5 et C9 qui demanderaient des extensions avec Flask ; DRF impose Django, hors périmètre du projet. Framework déjà pratiqué en cours ([projet cinedata](https://github.com/TristanDspt/cinedata)).

## GitHub Projects — novembre 2026
- **Choix / usage dans PFT** : pilotage agile du projet : board Kanban, sprints de 2 semaines (champ Iteration), milestones par phase, issues fermées par les commits (`closes #N`).
- **Source** : [Documentation GitHub — About Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects) — ★★★
- **Description** : outil de gestion de projet intégré à GitHub, relié directement aux issues et aux pull requests du dépôt.
- **Alternatives** : Jira, Trello — écartées : GitHub Projects est intégré au dépôt, les issues sont liées directement au code et se ferment automatiquement par les commits (`closes #N`), sans outil ni compte supplémentaire. Gratuit, ce qui respecte la contrainte de budget 0 €.

## ruff — novembre 2026
- **Choix / usage dans PFT** : linter du projet (`pyproject.toml`), lancé en local et bientôt en CI (#10).
- **Source** : [Documentation officielle ruff](https://docs.astral.sh/ruff/) — ★★★
- **Description** : linter Python écrit en Rust, configurable par familles de règles (E, F, I, UP…).
- **Alternatives** : flake8, pylint, isort — écartées : ruff regroupe leurs règles dans un seul outil, configuré dans un seul fichier, et s'exécute beaucoup plus vite, ce qui compte une fois lancé à chaque push en CI.

## Docker — novembre 2026
- **Choix / usage dans PFT** : prévu pour le stockage big data local (#25) puis la livraison de l'app et des API (phase 5).
- **Source** : [Documentation officielle Docker](https://docs.docker.com/get-started/) — ★★★ ; découverte initiale via plusieurs tutos YouTube (★), recoupés avec la doc
- **Description** : outil de conteneurisation : chaque service tourne dans un conteneur isolé et reproductible, orchestrés ensemble avec docker-compose.
- **Alternatives** : Podman, installation native des services — écartées : Docker est le standard du marché, vu en cours, et rend la stack reproductible en une commande (la stack big data en natif sous Windows serait ingérable).

## pytest — novembre 2026
- **Choix / usage dans PFT** : framework de tests du projet, prévu pour les tests des fonctions pures de `st_logic.py` (#9) puis lancé en CI (#10).
- **Source** : [Documentation officielle pytest](https://docs.pytest.org/) — ★★★
- **Description** : framework de tests Python : des fonctions préfixées `test_` contenant des `assert`, découvertes et lancées automatiquement par la commande `pytest`.
- **Alternatives** : unittest (bibliothèque standard Python) — écarté : pytest demande moins de code (un simple `assert` au lieu des méthodes `assertEqual`…), propose des fixtures pour préparer les données de test, et c'est l'outil vu en cours et le plus répandu.