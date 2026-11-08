# 🚀 ROADMAP : Personal Finance Tracker — v2 (certif Dev IA)

> Chaque tâche est reliée aux compétences du REAC (C1…C19) qu'elle alimente.
> E5 (C20, C21) est traité en cours, hors PFT.
> 🔶 = décision en suspens · 🎓 = techno à apprendre avant de coder · 🛑 = point de contrôle · #N = issue GitHub correspondante

**Contraintes assumées**
- Budget 0 € : tout tourne en local (pré-prod locale dockerisée, pas de cloud payant).
- Démo, tests et CI sur données fictives uniquement : zéro donnée perso ni secret dans le repo.
- Temps hebdo encore inconnu : mesuré sur 2-3 semaines, planning réajusté au 🛑 de fin novembre.
- Règle d'or : viser la validation des critères, pas la perfection. Documenter chaque brique dès qu'elle est finie.

---

### ❓ Questions pour le prof (prochaine session)
- [ ] **Rapports** : un rapport par épreuve (E1 → E4) ou un dossier unique pour la soutenance ?
- [x] **Veille (C6)** : centrée sur le choix des technos IA, documentée au fil de la découverte des outils (techno choisie, fiabilité de la source, description rapide)
- [ ] **Programme / calendrier des modules** : pour caler les briques PFT sur le temps de cours (projet réalisable en cours si le sujet colle)

---

### 🧰 0. Socle (v1, fait)
- [x] **ETL** : scripts `update_price.py` et `update_pee.py` opérationnels
- [x] **Vues SQL** : vues métier créées (view_global_portefeuille, view_historique_*, view_apports_*, etc.)
- [x] **Page Saisie** : formulaire de saisie manuelle mensuel
- [x] **App v1** : page KPIs, 5 dashboards (ETF, PEA, CTO, STEF, CiC), import CSV
- [x] **Repo v1** passé en privé (preuve d'auteur)
- [x] **Sauvegarde de la base perso** : dump hebdo automatisé (`pg_dump` + Planificateur de tâches, 4 dumps conservés sur OneDrive), restauration testée — test de restauration à refaire chaque mois

---

### 🏗️ 1. Fondations v2 (oct–nov 2026)
> Uniquement ce qui conditionne la suite. Ordre à respecter.

**1.1 Repo propre**
- [x] Clone local de la v1, nettoyage complet avant le premier commit — C17 · #14
- [x] 🎓 Gestion de config : variables d'environnement, `.env`, python-dotenv — #15
- [x] Chemins relatifs/configurables (`.env` + module `config`) — C4, C17 · #15
- [x] `.gitignore` blindé, zéro secret, zéro donnée perso, `requirements.txt` à jour — #14
- [x] Nouveau repo public + liens croisés dans les README (v2 → v1 privée, "disponible sur demande") — #16

**1.2 Schéma v2**
- [ ] 🎓 Révision express Merise (MCD, MLD, MPD) + prise en main de Looping — #1
- [ ] MCD → MLD → MPD **PostgreSQL uniquement** (les news vont dans le stockage big data, hors Merise) — C4 · #1
- [ ] Correction de la modélisation (séparation actif / portefeuille, nettoyage des contraintes et index) — C4 · #1
- [x] Renommage FR → EN du code Python (commit séparé) — #3
- [ ] Renommage FR → EN du schéma SQL avec le nouveau MPD — #1
- [ ] Suppression du doublon `UNIQUE (pdt_id, cot_date)` sur `cotation_cot` — C4 · #1
- [ ] Régime fiscal : taux dans `config.yaml` + régime dérivé de `ptf_type_enveloppe` (fin des taux en dur dans `st_logic.py`) — C4, C17 · #4
- [x] Saisie : INSERT en f-strings → requêtes paramétrées (injection SQL) — C17 · #5
- [x] Refacto : sortie du SQL de `st_logic.py` (fonctions TRI pures, `MovementType` dans `core/constants.py`) — C17 · #17
- [ ] Adaptation des vues SQL et du code au schéma v2 — C4, C17 · #18

**1.3 Données de démo**
- [ ] 🎓 Principe d'un script de seed (génération de données fictives réalistes) — #6
- [ ] Script de seed : positions et mouvements fictifs, cotations réelles — C4, C17 · #6
- [ ] Bloc DEMO du `.env` rempli : l'app démarre en `ENVIRONMENT=DEMO` (prérequis README + CI) — #7
- [ ] Fichiers bancaires fictifs + `bank.yaml` démo pour montrer l'import PEE — #7
- [ ] Test d'installation depuis un venv vierge en suivant le README — C4, C17 · #8

**1.4 Tests & CI**
- [ ] 🎓 Bases de pytest — #9
- [ ] Premiers tests sur `st_logic.py` (fonctions pures, sans BDD) — C17 · #9
- [ ] 🎓 Principes CI/CD + bases de GitHub Actions (Quickstart) — à bosser en autonomie, vu en cours plus tard — #10
- [ ] CI minimale : lint (ruff) + pytest sur push/PR — C18 · #10
- [ ] Doc de la chaîne CI — C18 · #10

**1.5 Pilotage (à lancer dès maintenant, évalué "tout au long du projet")**
- [x] 🎓 Prise en main de GitHub Projects (issues, board, milestones) — #11
- [x] Board GitHub Projects : backlog, kanban, milestones = phases — C16 · #11
- [x] 🎓 Bases de l'agile : Scrum (sprints, rituels, rôles) vs Kanban — #11
- [x] Sprints de 2 semaines lancés (sprint 1 : 2 → 15 nov) — C16 · #11
- [ ] Rétro de 10 min notée dans une issue à chaque fin de sprint (en continu) — C16
- [ ] Cahier des charges minimal : contexte, acteurs, objectifs, contraintes (budget 0 €, local), planning — E1, C14 · #12
- [ ] Veille : fichier `docs/veille.md`, une fiche par techno découverte (techno, source + fiabilité, description rapide), alimenté au fil du projet — C6 · #13
- [ ] Doc d'installation PostgreSQL + script de création du schéma — C4 · #2

🛑 **Fin novembre** : bilan du temps réel mesuré → réajustement de toute la suite du planning.
⏸️ **Marge** : 1re quinzaine de décembre.

---

### 📥 2. Bloc Données (mi-déc 2026–fév 2027) — E1
**2.1 Conception globale de l'app (avant tout dev v2)**
- [ ] User stories de l'app avec critères d'acceptation incluant l'accessibilité (RGAA/WCAG) — C14 · #19
- [ ] Wireframes / parcours utilisateurs (rapides : la v1 existe déjà) — C14 · #20
- [ ] Specs techniques : archi n-tiers (Streamlit / API données / API modèle / PostgreSQL + big data), outils, services éco-responsables — C15 · #21
- [ ] Diagramme de flux de données — C15 · #21

**2.2 Cadrage du bloc données**
- [ ] Specs techniques du bloc (sources, flux, stockage) — C1, C15
- [ ] 🎓 Découverte big data : principes, technos citées par le REAC (Hive, Spark…) — #22
- [ ] Choix de la techno big data pour les news, justifié au regard du REAC — C1, C2 🔶 · #22

**2.3 Scraping news**
- [x] 🎓 Bases du scraping (HTML, parsing) + `requests` / `beautifulsoup4` dans `requirements.txt` — #23
- [ ] Specs d'extraction : sources, CGU / robots.txt, flux RSS privilégiés quand dispo (plus stables qu'une page HTML) — C1 · #23
- [ ] Scraper : point d'entrée, gestion d'erreurs, logs, sauvegarde — C1 · #23
- [ ] Tests du scraper sur des pages HTML sauvegardées (détecte la casse si un site change sa structure) — C1, C18 · #24

**2.4 Stockage & requêtes**
- [ ] 🎓 Bases de Docker + docker-compose (indispensable : Spark/Hive en natif sur Windows = galère) — #25
- [ ] Mise en place du stockage big data (local, dockerisé) — C1, C2 · #25
- [ ] Requêtes d'extraction documentées (PostgreSQL + big data) : filtres, jointures, optimisations — C2 · #26

**2.5 ETL & agrégation**
- [ ] ETL existants (APIs + import CSV) remis au standard : fonctions + `main()`, logger dédié (`LOG015`), gestion d'erreurs, dédoublonnage de `type` dans `bank.yaml` — C1 · #27
- [ ] Script d'agrégation : entrées corrompues, doublons, homogénéisation (dates, devises) + doc — C3 · #28
- [ ] Script d'import en BDD + doc versionnée à la racine — C4 · #29
- [ ] **Bascule v1 → v2** (en une seule fois) — #30 :
  - [ ] Script de migration des vraies données (schéma v1 FR → schéma v2 EN) dans `db/migrations/` — C3, C4
  - [ ] Tâches planifiées (update des cours, backup BDD) repointées vers PFT-Enhanced + chemins des `.bat` / `.vbs` mis à jour
  - [ ] Backup vérifié avant et après la bascule

**2.6 RGPD**
- [ ] 🎓 RGPD : registre des traitements, principes de minimisation et de conservation — #31
- [ ] Registre des traitements + procédures de tri (purge, fréquence) — C4 · #31

**2.7 API REST données**
- [ ] 🎓 FastAPI : auth, Pydantic, tests avec TestClient — #32
- [ ] 🎓 OWASP API Security Top 10 — #32
- [ ] Endpoints + auth + validation + OWASP API Top 10 + doc OpenAPI — C5 · #32
- [ ] Doc d'accès direct à la BDD — C5 · #32
- [ ] Tests API branchés à la CI — C5, C18 · #33
- [ ] L'app passe par l'API données (`api_client.py` remplace `database.py`) — C17 · #34

**2.8 Preuve de concept**
- [ ] PoC minimal dans l'env Docker local : scraping → stockage → API → affichage Streamlit — C15 · #35
- [ ] Conclusion go / no-go documentée (poursuite vers le service LLM) — C15 · #35

🛑 **Fin février** : bilan de phase.
⏸️ **Marge** : 1re quinzaine de mars.

---

### 🧠 3. Service LLM (mi-mars–avril 2027) — E2
- [ ] Expression de besoin reformulée : résumé des news + tendances, contraintes (budget 0 €) — C7
- [ ] Benchmark services LLM : étudiés / écartés (+ raisons), adéquation, éco-responsabilité, contraintes, conclusion — C7
- [ ] Paramétrage du service retenu : accès, clés, SDK, monitoring fournisseur — C8
- [ ] Doc du service (accès, install, test, dépendances, données impliquées) — C8
- [ ] Endpoint FastAPI de synthèse + page Streamlit "News & tendances" — C10

🛑 **Fin avril** : bilan de phase.

---

### 🤖 4. ML + MLOps (mai–juin 2027) — E3
> Modèle principal : sentiment sur les news. Forecasting → section Options.

**4.1 Modèle**
- [ ] Dataset labellisé (datasets financiers publics) + préparation — C12
- [ ] Entraînement + évaluation (accuracy, matrice de confusion)

**4.2 API & intégration**
- [ ] API FastAPI du modèle : auth, validation des entrées, OWASP, OpenAPI, tests de tous les endpoints — C9
- [ ] Intégration Streamlit : appels API, gestion des jetons, tests, contrôle accessibilité — C10

**4.3 Chaîne MLOps**
- [ ] 🎓 Bases MLOps : versionnement données/modèles (DVC ou MLflow), monitoring
- [ ] Tests automatisés du modèle : données, préparation, entraînement, éval + couverture — C12
- [ ] Versionnement données/modèles — C12, C13
- [ ] Monitoring : métriques (drift, perf), dashboard, alertes, testé en bac à sable, doc — C11
- [ ] Chaîne de livraison continue du modèle : tests → entraînement → éval → rapport attaché à la PR — C13

🛑 **Fin juin** : bilan de phase + décision de simplifier ou non l'audit accessibilité et le CD si la phase 5 s'annonce trop tendue.
⏸️ **Marge** : 1re quinzaine de juillet.

---

### 🖥️ 5. Application & livraison (mi-juillet–mi-août 2027) — E4
> Conception déjà faite en 2.1 : ici uniquement du dev, de la livraison et une mise à jour des specs si besoin.
- [ ] 🎓 Accessibilité : RGAA / WCAG, limites de Streamlit
- [ ] Authentification + gestion des droits — C17
- [ ] Sécurité OWASP + éco-conception — C17
- [ ] Audit accessibilité : contrastes, alternatives textuelles des graphs, navigation clavier — C14, C17
- [ ] Tests composants métier + gestion des accès — C17
- [ ] Dockerisation app + APIs (install reproductible sur n'importe quel PC) — C19
- [ ] 🎓 Livraison continue : build d'images, releases, PR automatisées
- [ ] CD GitHub Actions : build des images → livraison (PR/release) — C19
- [ ] Pré-prod locale de livraison — C19
- [ ] Doc technique app : install, archi, dépendances, exécution des tests — C17

---

### 📝 6. Rapport & soutenance (mi-août–sept 2027)
> Le rapport s'écrit au fil de l'eau (doc de chaque brique) : ici uniquement la finalisation.
- [ ] Rapport(s) professionnel(s) finalisé(s) (format à confirmer avec le prof)
- [ ] Démo scénarisée sur données fictives
- [ ] Répétitions (1h30 chrono) — début septembre

---

### ✨ Options (seulement si tout le reste est bouclé)
- [ ] **Forecasting** : modèle d'entraînement + éval, sans chaîne MLOps complète (le sentiment peut servir de variable d'entrée)
- [ ] **MCP** : interrogation de la BDD en langage naturel depuis Streamlit (accès en lecture seule, sécurisé)
- [ ] **Page Projection** : finaliser `get_projection` / `make_graph_projection` / page
- [ ] **Badge d'environnement** (DEMO / PROD) dans la sidebar

---

### 🚨 7. Bugs Mineurs
- [ ] **Graph dashboards** : premier mois sans data `NaN sur diff`
- [ ] **Graph perf mensuelle** : mois civils (mois en cours partiel) ≠ fenêtre des KPI → aligner ou légender
- [ ] **Cosmétique** : en-têtes qui parlent encore de `Home.py` (`KPIs.py`, `st_charts.py`), docstring de `config.py` (`database.py` → `db_engine.py`)

---

## 🗺️ Couverture REAC

| Compétence | Phase(s) | Compétence | Phase(s) |
| :--- | :--- | :--- | :--- |
| C1 Extraction multi-sources | 2 | C11 Monitoring modèle | 4 |
| C2 Requêtes SQL + big data | 2 | C12 Tests modèle | 4 |
| C3 Agrégation / nettoyage | 2 | C13 Livraison continue modèle | 4 |
| C4 BDD Merise + RGPD | 1, 2 | C14 Besoin, US, accessibilité | 1, 2, 5 |
| C5 API REST données | 2 | C15 Cadre technique + PoC | 2 |
| C6 Veille | 1 → 6 (au fil de l'eau) | C16 Agile | 1 → 6 |
| C7 Benchmark IA | 3 | C17 Dev app | 1, 5 |
| C8 Paramétrage service IA | 3 | C18 CI | 1, 2 |
| C9 API modèle | 4 | C19 CD | 5 |
| C10 Intégration API IA | 3, 4 | C20–C21 | Hors PFT (E5) |