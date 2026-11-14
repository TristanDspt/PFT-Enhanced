# 🏛️ Personal Finance Tracker

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-green)

Migration d'une gestion financière complexe (anciennement sous Excel) vers une architecture **Python / PostgreSQL / Streamlit**.  
L'outil centralise des actifs variés (ETF, Actions, PEE, Livrets) et automatise le suivi de performance avec calcul du TRI.

> **Version 2** : refonte du projet, développée en public. La v1 (dépôt privé) est disponible sur demande.

---

## 🛠 Stack Technique

| Composant | Technologie |
| :--- | :--- |
| **Langage** | Python 3.14 |
| **Base de données** | PostgreSQL 18 |
| **Interface** | Streamlit |
| **DataViz** | Plotly |
| **Performance** | pyxirr (XIRR) |
| **Data Sources** | yfinance / CSV / Excel |
| **Configuration** | python-dotenv / PyYAML |

---

## ⚙️ Installation & Setup

**Prérequis**
- Python 3.14 (testé avec 3.14.2)
- PostgreSQL 18 : installeur officiel depuis [postgresql.org](https://www.postgresql.org/download/) (port 5432 par défaut), puis ajouter son dossier `bin` au `PATH` pour avoir `psql` (sous Windows, par défaut `C:\Program Files\PostgreSQL\18\bin`).

**Étapes**

1. Cloner le repo
2. Créer et activer un venv :
   - `python -m venv .venv`
   - Windows : `.venv\Scripts\activate` — Linux / macOS : `source .venv/bin/activate`
3. Installer les dépendances : `pip install -r requirements.txt`
4. Copier `.env.example` en `.env`, puis renseigner le bloc `DEMO` :
   - `ENVIRONMENT=DEMO`
   - `HOST_DEMO`, `USER_DEMO`, `PASSWORD_DEMO`, `PORT_DEMO` : paramètres de ton serveur PostgreSQL
   - `DB_NAME_DEMO=pft_demo` : le nom de la base créée à l'étape suivante
5. Créer la base, charger le schéma puis les vues (dans cet ordre) :
   - `psql -U postgres -c "CREATE DATABASE pft_demo;"`
   - `psql -U postgres -d pft_demo -f db/schema/create_schema_v1.sql`
   - `psql -U postgres -d pft_demo -f db/views/vues.sql`
   - `psql -U postgres -d pft_demo -f db/views/vue_globale.sql`
   - `psql -U postgres -d pft_demo -f db/views/vue_apport.sql`
   - `psql -U postgres -d pft_demo -f db/views/vue_historique.sql`
   - `psql -U postgres -d pft_demo -f db/views/vue_historique_pdt.sql`
6. Lancer l'application : `python -m streamlit run app/main.py`

L'application cible la base `DEMO` par défaut. La variable `ENVIRONMENT` du `.env` permet de basculer vers une autre base (voir `ARCHITECTURE.md`).

> 🚧 Un script de seed (données fictives) est prévu. Tant qu'il n'existe pas, la base de démonstration est vide et certaines pages peuvent afficher des erreurs.

### Schéma v2 (en préparation)

Le nouveau modèle de données ([`docs/merise/mcd.md`](docs/merise/mcd.md)) est prêt, mais l'application tourne encore sur le schéma v1 jusqu'à l'adaptation des vues et du code. Pour créer et vérifier une base v2 :

    psql -U postgres -c "CREATE DATABASE pft_v2;"
    psql -U postgres -d pft_v2 -f db/schema/create_schema_v2.sql
    psql -U postgres -d pft_v2 -c "\dt"

Résultat attendu : 6 tables (`app_user`, `asset`, `holding`, `movement`, `portfolio`, `quote`). Le script s'exécute dans une transaction : en cas d'erreur, rien n'est créé.

---

## 🔄 Mise à jour des données

Ces scripts **écrivent dans la base ciblée par `ENVIRONMENT`**. Vérifier l'environnement actif avant de les lancer.

- Cours boursiers (yfinance) : `python -m pipelines.etl.update_price`
- Fonds PEE (fichiers CSV / Excel téléchargés) : copier `settings/bank.example.yaml` en `settings/bank.yaml`, l'adapter, puis `python -m pipelines.etl.update_pee`

---

## 📚 Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) : structure des fichiers, fonctions, vues SQL, conventions.
- [`docs/merise/mcd.md`](docs/merise/mcd.md) : modèle conceptuel de données (Merise) du schéma v2.
- [`docs/veille.md`](docs/veille.md) : veille technologique et choix d'outils.

---

*Projet personnel développé dans le cadre d'une formation Dev IA en alternance. Licence : voir le fichier `LICENSE`.*