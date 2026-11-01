# 🏛️ ARCHITECTURE — Personal Finance Tracker

## Vue d'ensemble

Application Streamlit de suivi financier personnel, adossée à une base PostgreSQL.
La logique est **strictement séparée** de l'affichage :

- les calculs vivent dans `st_logic.py` (fonctions pures, sans accès à la base) ;
- les graphiques vivent dans `st_charts.py` ;
- la connexion à la base est construite dans `core/db_engine.py`, les requêtes de l'application vivent dans `app/components/database.py` ;
- les pages Streamlit appellent ces fonctions et affichent les résultats, sans aucun calcul ;
- les scripts de collecte (ETL) vivent dans `pipelines/`, le SQL dans `db/`.

```
.env ──► core/config.py ──► core/db_engine.py
                                   │  (engine SQLAlchemy)
                  ┌────────────────┴────────────────┐
                  ▼                                 ▼
      app/components/database.py          pipelines/etl/*.py
      (vues SQL → DataFrames)             (collecte → base)
                  │
                  ▼
      app/components/st_logic.py     ← calculs pandas
      app/components/st_charts.py    ← figures Plotly
                  │
                  ▼
      app/main.py + app/pages/       ← interface Streamlit
```

---

## Règles d'architecture

| Règle | Détail |
| :--- | :--- |
| Calculs | Uniquement dans `app/components/st_logic.py`, fonctions pures (pas de requête interne) |
| Graphiques | Uniquement dans `app/components/st_charts.py` |
| Connexion à la base | Construite uniquement dans `core/db_engine.py` (`create_db_engine()`) |
| Requêtes de l'application | Uniquement dans `app/components/database.py` |
| Pages | `app/pages/` : aucune logique de calcul |
| ETL | Dans `pipelines/`, lancés en module depuis la racine du projet |
| SQL | Dans `db/` |
| Configuration | Tout passe par `core/config.py` : les autres modules ne lisent jamais `os.environ` directement |
| Secrets et données personnelles | Jamais dans le dépôt (voir la section Configuration) |

---

## Fichiers

| Fichier | Rôle |
| :--- | :--- |
| `app/main.py` | Point d'entrée Streamlit |
| `app/components/database.py` | Requêtes de l'application : chargement des vues SQL en DataFrame, avec cache Streamlit |
| `app/components/st_logic.py` | Toute la logique métier (calculs, transformations), zéro Streamlit |
| `app/components/st_charts.py` | Toutes les figures Plotly |
| `app/pages/1_📊_KPIs.py` | Page KPIs globaux |
| `app/pages/2_📈_Dashboards.py` | Dashboards par enveloppe |
| `app/pages/3_🚀_Projection.py` | Projections patrimoniales |
| `app/pages/4_✍️_Saisie.py` | Saisie des mouvements, et bouton de mise à jour des fonds |
| `core/config.py` | Configuration : environnement actif, chemins, paramètres de connexion |
| `core/db_engine.py` | Création de l'engine SQLAlchemy, sans dépendance à Streamlit |
| `core/utils.py` | Fonctions utilitaires partagées (`load_yaml`) |
| `pipelines/etl/update_price.py` | ETL : cours boursiers (yfinance) |
| `pipelines/etl/update_pee.py` | ETL : fonds d'épargne salariale (fichiers CSV / Excel téléchargés) |
| `db/schema/` | Schéma de la base |
| `db/views/` | Vues SQL (sources de données de l'application) |
| `settings/` | Réglages non secrets, et modèle des réglages personnels |

---

## 📁 Structure du projet

```
├── app/
│   ├── components/
│   │   ├── database.py        ← Requêtes de l'application (vues → DataFrames)
│   │   ├── st_logic.py        ← Logique métier (calculs pandas)
│   │   └── st_charts.py       ← Figures Plotly
│   ├── pages/
│   │   ├── 1_📊_KPIs.py
│   │   ├── 2_📈_Dashboards.py
│   │   ├── 3_🚀_Projection.py
│   │   └── 4_✍️_Saisie.py
│   └── main.py                ← Point d'entrée Streamlit
├── core/
│   ├── config.py              ← Configuration (lit le .env)
│   ├── db_engine.py           ← Engine SQLAlchemy
│   └── utils.py               ← Utilitaires partagés
├── pipelines/
│   ├── etl/                   ← update_price.py, update_pee.py
│   ├── scraping/              ← (réservé)
│   └── aggregation/           ← (réservé)
├── db/
│   ├── schema/                ← Schéma de la base
│   ├── views/                 ← Vues SQL
│   ├── migrations/            ← (réservé)
│   └── seed/                  ← (réservé : données fictives)
├── settings/
│   ├── bank.example.yaml      ← Modèle des réglages d'import (versionné)
│   └── config.yaml            ← Réglages non secrets (vide pour l'instant)
├── api/                       ← (réservé : API de données, API de modèle)
├── data/                      ← raw/ et processed/ (contenu ignoré par git)
├── models/                    ← (réservé, contenu ignoré par git)
├── logs/                      ← Journaux des scripts (contenu ignoré par git)
├── tests/                     ← (réservé)
├── docker/                    ← (réservé)
├── .github/workflows/         ← (réservé : CI)
├── docs/images/               ← Assets visuels
├── .env.example               ← Modèle des variables d'environnement
├── .gitignore
├── ARCHITECTURE.md
├── LICENSE
├── pyproject.toml             ← Configuration de ruff (linter)
├── README.md
├── requirements.txt
└── roadmap.md
```

Les dossiers marqués « réservé » ne contiennent qu'un fichier `.gitkeep` : ils accueilleront les briques à venir. `settings/bank.yaml` (réglages personnels), `.env`, `notebooks/` et les scripts de lancement locaux ne sont pas versionnés.

---

## ⚙️ Configuration

Toute la configuration passe par `core/config.py`.

### Variables d'environnement (`.env`)

Le fichier `.env` n'est jamais versionné. Copier `.env.example` en `.env`, puis renseigner les valeurs.

| Variable | Obligatoire | Rôle |
| :--- | :--- | :--- |
| `ENVIRONMENT` | non (défaut `DEMO`) | Base ciblée : `DEMO` ou `PROD`. Toute autre valeur arrête l'application au démarrage. |
| `HOST_<ENV>`, `DB_NAME_<ENV>`, `USER_<ENV>`, `PASSWORD_<ENV>`, `PORT_<ENV>` | oui, pour l'environnement actif | Paramètres de connexion PostgreSQL. |
| `DOWNLOADS_DIR` | non | Dossier des fichiers téléchargés (défaut : dossier Téléchargements de l'utilisateur). |

### Ce que `core/config.py` expose

| Constante | Contenu |
| :--- | :--- |
| `ENVIRONMENT` | Environnement actif (`DEMO` ou `PROD`) |
| `DB_PARAMS` | Dictionnaire `host`, `db_name`, `username`, `password`, `port` (entier) |
| `PROJECT_ROOT` | Racine du projet, détectée en remontant jusqu'au dossier contenant `requirements.txt` |
| `DATA_RAW_DIR`, `LOGS_DIR` | Dossiers du dépôt, dérivés de `PROJECT_ROOT` |
| `DOWNLOADS_DIR` | Dossier des fichiers téléchargés |

Une variable obligatoire absente ou vide arrête l'application au démarrage avec un message explicite, plutôt qu'à la première requête.

### Réglages personnels (`settings/`)

Les réglages d'import des fonds sont dans `settings/bank.yaml`, ignoré par git. Le modèle versionné est `settings/bank.example.yaml` : le copier en `bank.yaml`, puis l'adapter.

Le fichier contient deux blocs :

- `formats` : réglages pandas de lecture, un par mise en page de fichier téléchargé (séparateur, lignes à ignorer, format de date...) ;
- `products` : un produit par `pdt_id`, avec `name`, `keyword` (texte présent dans le nom du fichier), `type` (`csv` ou `xls`) et `format` (nom d'une entrée de `formats`).

`settings/config.yaml` est réservé aux futurs réglages non secrets (il est vide pour l'instant). La fonction `load_yaml(filepath, required=False)` de `core/utils.py` lit ces fichiers. Avec `required=True`, un fichier absent ou vide arrête le script avec un message explicite.

---

## 🔄 Pipelines (ETL)

Les scripts de `pipelines/etl/` **écrivent dans la base ciblée par `ENVIRONMENT`**. Ils se lancent en module, depuis la racine du projet :

```
python -m pipelines.etl.update_price
python -m pipelines.etl.update_pee
```

Le lancement en module place la racine du projet dans les imports : c'est ce qui permet à un script de faire `from core import config`.

| Script | Rôle |
| :--- | :--- |
| `update_price.py` | Récupère les cours des produits ayant un ticker (yfinance), à partir de la dernière date en base. Journal : `logs/update_price.log`. |
| `update_pee.py` | Cherche dans `DOWNLOADS_DIR` les fichiers dont le nom contient le `keyword` de chaque produit de `settings/bank.yaml`, ne conserve que les dates absentes de la base, puis les insère. |

La page de saisie lance `update_pee.py` en sous-processus (`sys.executable -m pipelines.etl.update_pee`, depuis `PROJECT_ROOT`), donc sur la même base que celle affichée à l'écran.

---

## Base de données

Le schéma est dans `db/schema/Create_DB_PFT.sql` (4 tables : portefeuille, produit financier, cotation, mouvement). Il sera remplacé par le nouveau modèle Merise.

### Vues SQL (sources de données)

| Vue | Fichier | Contenu |
| :--- | :--- | :--- |
| `view_positions_actuelles` | `vues.sql` | Quantités détenues par produit |
| `view_pru` | `vues.sql` | Prix de revient unitaire par produit |
| `view_global_portefeuille` | `vue_globale.sql` | État instantané : capital, profit €/%, PRU par produit |
| `view_apports_mensuels` | `vue_apport.sql` | Flux d'argent réels entrant et sortant par mois |
| `view_apports_mensuels_pdt` | `vue_apport.sql` | Même chose, par produit |
| `view_historique_portefeuille` | `vue_historique.sql` | Reconstitution quotidienne du patrimoine par `ptf_id` (base des graphiques) |
| `view_historique_pdt` | `vue_historique_pdt.sql` | Reconstitution quotidienne du patrimoine par `pdt_id` |

### Ordre de chargement

`view_global_portefeuille` s'appuie sur `view_positions_actuelles` et `view_pru` : `vues.sql` doit être chargé avant `vue_globale.sql`. Les autres fichiers ne dépendent que des tables. L'ordre complet est dans le README.

---

## st_logic.py — Fonctions

### 1. Calculs généraux
> Indépendants de la période. Basés sur `df` (`view_global_portefeuille` ou sous-ensemble filtré).

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `get_patrimoine_total(df)` | df | `float` |
| `get_perf_marches(df)` | df | `dict {euro, pct}` |
| `get_poids_enveloppes(df)` | df | `dict {etf, pee, livret}` |
| `get_capital_net(df, liste_pdt)` | df, list[int] | `dict {pdt_id: net}` |
| `get_tri_ptf(df, engine, liste_ptf)` | df, engine, list | `float` |
| `get_tri_pdt(df, engine, liste_pdt)` | df, engine, list | `dict {pdt_id: float}` |

> ⚠️ `get_perf_etf` **supprimée** : doublon avec `get_perf_marches`. La perf ETF se calcule via `get_perf_marches(df.query("ptf_id in (1, 2)"))`.

> ⚠️ `get_capital_net` prend une `liste_pdt` (`list[int]`) et retourne un `dict {pdt_id: net}`. Fiscalité par `pdt_id` : PEA / PEE 18.6 % | CTO 31.4 %. Pas d'impôt s'il n'y a pas de plus-value.

> ⚠️ `get_tri_ptf` calcule le TRI pour une ou plusieurs **enveloppes** (`ptf_id`) → `float`.
> `get_tri_pdt` calcule le TRI pour un ou plusieurs **produits** (`pdt_id`) → `dict {pdt_id: float}`.

### 2. Logique temporelle
> Liées au slider de période. Basées sur `df_histo` et `df_apports`.

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `get_nb_mois(duree)` | `str` | `int` |
| `get_date_debut(duree)` | `str` | `pd.Timestamp` (normalisé à minuit) |
| `get_df_periode(df_histo, date_debut)` | df_histo, date | `DataFrame` |
| `get_perf_etf_periode(df_histo, df_periode, date_debut, duree)` | df_histo, df_periode, date, str | `dict {euro, pct}` |
| `get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping)` | df_histo, df_periode, str, date, dict | `dict {nom: {euro, pct}, ...}` |
| `get_perf_pdt_periode(df_histo_pdt, df_periode_pdt, duree, date_debut, liste_pdt, aggregate=False)` | df, df, str, date, list, bool | `dict {pdt_id: {euro, pct}}`, ou `dict {euro, pct}` si `aggregate=True` |
| `get_injecte_periode(df_histo, df_periode, duree, date_debut, liste_pdt)` | df_histo, df_periode, str, date, list | `float` |
| `get_tableau_mensuel_ptf(df_histo, df_apports, duree, mapping_ptf)` | df_histo, df_apports, str, dict | `tuple (df_tableau, df_tableau_buffer)` |
| `get_tableau_mensuel_pdt(df_histo, df_apports, duree, mapping_pdt)` | df_histo, df_apports, str, dict | `tuple (df_tableau, df_tableau_buffer)` |
| `get_donnees_graph(df_tableau_buffer, df_apports, duree)` | df_tableau_buffer, df_apports, str | `tuple (df_apports_graph, df_capital_graph)` |

> ⚠️ `get_tableau_mensuel_ptf` et `get_tableau_mensuel_pdt` retournent un tuple :
> - `df_tableau` : version nettoyée pour l'affichage (tri décroissant, 1er mois retiré)
> - `df_tableau_buffer` : version avec le mois de buffer, pour `get_donnees_graph` (tri croissant, 1er mois conservé pour le calcul du `shift(1)`)

> ⚠️ `get_perf_etf_periode`, `get_perf_ptf_periode`, `get_perf_pdt_periode`, `get_injecte_periode` :
> si `snap_debut['jour'] > date_debut`, la période remonte avant le premier mouvement : elle est traitée comme « Max » (valeur totale).

> ⚠️ `get_perf_pdt_periode(..., aggregate=True)` recalcule le pourcentage sur la base totale, il ne fait pas la moyenne des pourcentages individuels.

> ⚠️ Les graphiques mensuels comptent en **mois civils**, alors que les KPI du journal de bord couvrent une période glissante : les deux ne portent pas exactement sur la même fenêtre. Le mois en cours est partiel.

---

## st_charts.py — Fonctions

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `apply_style(fig)` | `go.Figure` | `None` (modifie en place) |
| `make_donuts(df, names, values, color_discrete_map, rotation, labels, poids, taille)` | DataFrame + paramètres visuels | `go.Figure` |
| `make_graph_global(df_apports_graph, df_capital_graph)` | 2 DataFrames | `go.Figure` |

> ⚠️ `make_donuts` : `poids` est optionnel (défaut `None`). S'il est absent, le libellé central s'affiche sans valeur en %. Le paramètre `taille` (défaut `200`) contrôle la hauteur en pixels.

---

## Structure type d'une page

```python
# 1. Chargement des vues (database.py)
engine = db.get_engine()
df = db.get_view("view_global_portefeuille", engine)
df_histo = db.get_view("view_historique_portefeuille", engine)

# 2. Sidebar : choix de l'enveloppe + slider de période
duree = st.select_slider(...)

# 3. Logique temporelle
date_debut = logic.get_date_debut(duree)
df_periode = logic.get_df_periode(df_histo, date_debut)

# 4. Calculs généraux (indépendants de la période)
capital = logic.get_patrimoine_total(df_filtre)
perf = logic.get_perf_marches(df_filtre)

# 5. Calculs sur la période (réactifs au slider)
perf_periode = logic.get_perf_ptf_periode(...)
injecte = logic.get_injecte_periode(...)

# 6. Tableau, puis données du graphique (le tableau doit précéder le graphique)
df_tableau, df_tableau_buffer = logic.get_tableau_mensuel_ptf(...)
df_apports_graph, df_capital_graph = logic.get_donnees_graph(df_tableau_buffer, ...)

# 7. Affichage : st.metric, donuts (charts.make_donuts), graphique (charts.make_graph_global)
#    Le graphique est masqué si la période est trop courte ("1 Mois", "15 Jours", "Début Mois")
```

---

## Conventions

### Nommage

| Préfixe | Usage |
| :--- | :--- |
| `get_` | Fonction qui calcule et retourne une valeur |
| `make_` | Fonction qui crée et retourne une figure Plotly |
| `df_` | DataFrame pandas |
| `fig_` | Figure Plotly |
| `pdt_` | Colonne liée à un produit financier (convention de la base) |
| `ptf_` | Colonne liée à un portefeuille (convention de la base) |
| `mvt_` | Colonne liée à un mouvement (convention de la base) |
| `cot_` | Colonne liée à une cotation (convention de la base) |
| `MAJUSCULES` | Constante de module exposée aux autres fichiers (ex. `DB_PARAMS`) |

### Langue

Code en anglais (variables, fonctions, classes, fichiers). Documentation, docstrings, commentaires et messages de commit en français.

### Qualité de code

Lint avec ruff (`ruff check .`), configuré dans `pyproject.toml`. Le formateur `ruff format` n'est pas utilisé.

---

## Choix de conception

- **Environnement `DEMO` par défaut** : sans configuration explicite, l'application ne touche jamais aux données réelles. Une valeur invalide arrête l'application, elle ne retombe pas silencieusement sur une autre base.
- **Échec au démarrage** : une variable obligatoire manquante arrête l'application avec un message clair, plutôt qu'à la première requête.
- **Connexion hors Streamlit** : `core/db_engine.py` ne dépend pas de Streamlit, pour que les scripts ETL obtiennent un engine sans embarquer l'interface. Le cache Streamlit est ajouté par `get_engine()` dans `app/components/database.py`.
- **URL de connexion construite avec `URL.create`** (SQLAlchemy) et non avec une chaîne : les caractères spéciaux d'un mot de passe ne cassent pas la connexion.
- **Point d'entrée `app/main.py`** : un fichier `app.py` à côté d'un dossier `app/` crée un conflit de noms à l'import.
- **Scripts lancés en module** (`python -m ...`) depuis la racine : les imports `core.*` fonctionnent sans manipuler `sys.path`.
- **Réglages personnels hors dépôt** : le modèle `bank.example.yaml` est versionné, le fichier réel ne l'est pas.