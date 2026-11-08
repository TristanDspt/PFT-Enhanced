# app/components/st_logic.py

"""
Logique métier de l'application Personal Finance Tracker.

Ce module contient tous les calculs et transformations de données : KPIs,
performances sur période, tableaux mensuels, TRI, fiscalité.

Règles d'architecture :
- Fonctions pures uniquement : aucun code Streamlit, aucun accès à la base
    (ni engine, ni requête SQL). Les données arrivent déjà chargées en
    DataFrames, fournis par app/components/database.py.
- Les graphiques sont construits dans st_charts.py, pas ici.
- Les fonctions dépendantes de la date du jour (TRI) acceptent un paramètre
    optionnel `today` pour rester testables de façon déterministe.

Constantes :
- PORTFOLIO_TRI_TYPES / PRODUCT_TRI_TYPES : types de mouvement qui entrent dans
    le calcul du TRI. La différence (TRANSFERT seulement côté produit) est
    voulue ; ne pas harmoniser sans valider l'impact sur les TRI affichés.
- PORTFOLIO_TO_PRODUCT_IDS : correspondance enveloppe → produits.
"""

import pandas as pd
from pyxirr import xirr

from core.constants import MovementType

# --------------------------------------------------------------------------------

PORTFOLIO_TRI_TYPES = (MovementType.APPORT, MovementType.ABONDEMENT)
PRODUCT_TRI_TYPES = (MovementType.APPORT, MovementType.ABONDEMENT, MovementType.TRANSFERT)

PORTFOLIO_TO_PRODUCT_IDS = {
    1: [1, 7],
    2: [2, 8],
    3: [3],
    4: [4, 5, 6, 9],
    6: [10, 11],
}

# --------------------------------------------------------------------------------

def get_total_wealth(df):
    """
    Calcule la valeur totale du patrimoine (cash + titres).

    Args:
        df (DataFrame): view_global_portefeuille (ou sous-ensemble filtré)

    Returns:
        float: somme de capital_actuel sur tous les produits
    """
    capital = df['capital_actuel'].sum()
    return capital


def get_market_perf(df):
    """
    Calcule la performance globale des marchés (hors produits cash).
    Inclut l'abondement dans la base de calcul du pourcentage.

    Args:
        df (DataFrame): view_global_portefeuille (ou sous-ensemble filtré)

    Returns:
        dict: {"euro": float, "pct": float}
    """
    # On exclut le cash (livrets, poches broker) — ils ne font pas de perf boursière
    market_df = df.query("pdt_cash == False")
    profit_euro = market_df['profit_euro'].sum()

    # Base de calcul : effort perso + abondement employeur
    market_invested = market_df['capital_investi'].sum()
    employer_match = market_df['abondement_recu'].sum()
    total_invested = market_invested + employer_match

    # Garde-fou pour éviter une division par zéro
    profit_pct = (profit_euro / total_invested * 100) if total_invested > 0 else 0

    return {"euro": profit_euro, "pct": profit_pct}


def get_account_weights(df):
    """
    Calcule le poids de chaque enveloppe dans le patrimoine total (en %).

    Args:
        df (DataFrame): view_global_portefeuille

    Returns:
        dict: {"etf": float, "pee": float, "savings": float}
    """
    # IDs des portefeuilles par catégorie
    etf_ids = [1, 2]
    pee_ids = [3, 4]
    savings_ids = [6]

    # Appel de la fonction dédiée pour éviter de recalculer le capital
    capital = get_total_wealth(df)

    if capital > 0:
        # Poids = capital de l'enveloppe / capital total * 100
        etf_weight = df.query("ptf_id in @etf_ids and pdt_est_actif == True")['capital_actuel'].sum() / capital * 100
        pee_weight = df.query("ptf_id in @pee_ids and pdt_est_actif == True")['capital_actuel'].sum() / capital * 100
        savings_weight = df.query("ptf_id in @savings_ids and pdt_est_actif == True")['capital_actuel'].sum() / capital * 100
    else:
        # Sécurité si le patrimoine est vide (DB vide, premier lancement)
        etf_weight = pee_weight = savings_weight = 0

    return {"etf": etf_weight, "pee": pee_weight, "savings": savings_weight}


def get_months_count(period):
    """
    Convertit le label du slider en nombre de mois.
    Retourne 0 pour le cas "Début Mois" (non présent dans le mapping).

    Args:
        period (str): valeur du slider (ex: "6 Mois", "1 An", "Max", "Début Mois")

    Returns:
        int: nombre de mois correspondant, 0 si cas spécial
    """
    period_months = {
        "1 Mois": 1,
        "3 Mois": 3,
        "6 Mois": 6,
        "1 An": 12,
        "3 Ans": 36,
        "5 Ans": 60,
        "Max": 600
    }

    # "Début Mois" n'est pas dans le mapping → retourne 0
    if period in period_months:
        months_count = period_months[period]
    else:
        months_count = 0

    return months_count


def get_start_date(period):
    """
    Calcule la date de début de la période sélectionnée via le slider.
    Cas "Début Mois" : retourne le 1er du mois en cours.
    Autres cas : retourne aujourd'hui - months_count, normalisé à minuit.

    ⚠️ Le normalize() est essentiel pour éviter les décalages d'un jour
    liés à l'heure exacte d'exécution lors des comparaisons avec history_df.

    Args:
        period (str): valeur du slider

    Returns:
        pd.Timestamp: date de début de la période (minuit)
    """
    months_count = get_months_count(period)
    current_month_start = pd.Timestamp.now().replace(day=1).normalize()

    if months_count > 0:
        # Cas normal : on recule de months_count à partir d'aujourd'hui
        start_date = pd.Timestamp.now() - pd.DateOffset(months=months_count)
        # Cas "15 jours" : on recule de 15j à partir d'aujourd'hui
    elif period == "15 Jours":
        start_date = pd.Timestamp.now() - pd.DateOffset(days=15)
    else:
        # Cas "Début Mois" : on repart du 1er du mois en cours
        start_date = current_month_start

    # Normalisation à minuit — évite les décalages lors des comparaisons avec les dates SQL
    start_date = pd.Timestamp(start_date).normalize()

    return start_date


def get_period_df(history_df, start_date):
    """
    Filtre history_df sur la période sélectionnée.

    Args:
        history_df (DataFrame): view_historique_portefeuille
        start_date (pd.Timestamp): date de début calculée par get_start_date()

    Returns:
        DataFrame: history_df filtré >= start_date
    """
    # Conversion sécurisée en datetime (au cas où l'import SQL ne l'a pas fait)
    history_df['jour'] = pd.to_datetime(history_df['jour'])
    period_df = history_df[history_df['jour'] >= start_date]
    return period_df


def get_etf_period_perf(history_df, period_df, start_date, period):
    """
    Calcule la performance des ETF (PEA + CTO) sur la période sélectionnée.
    Gère les cas spéciaux "Début Mois" et "Max".

    ⚠️ Si snap_start['jour'] > start_date, cela signifie que la période demandée
    remonte avant le premier mouvement — on traite alors comme "Max" (profit total).

    Args:
        history_df (DataFrame): view_historique_portefeuille (complet, non filtré)
        period_df (DataFrame): history_df filtré sur la période
        start_date (pd.Timestamp): date de début calculée par get_start_date()
        period (str): valeur du slider

    Returns:
        dict: {"euro": float, "pct": float}
    """
    # Utilisé pour le cas "Début Mois" : on cherche le snapshot avant le 1er du mois
    current_month_start = pd.Timestamp.now().replace(day=1).normalize()

    # Agrégation journalière des deux ETF sur la période
    etf_period_df = (period_df.query("ptf_id in [1, 2]")
                        .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi']]
                        .sum()
                        .reset_index()
                        .query("capital_investi > 1")  # filtre les jours sans position réelle
                        .sort_values('jour'))

    if not etf_period_df.empty:
        snap_end = etf_period_df.iloc[-1]  # dernier jour de la période

        if period == "Début Mois":
            # On cherche le dernier snapshot AVANT le 1er du mois dans l'historique complet
            snap_start = (history_df.query("ptf_id in [1, 2] and jour < @current_month_start")
                            .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi']]
                            .sum()
                            .reset_index()
                            .query("capital_investi > 1")
                            .sort_values('jour')
                            .iloc[-1])
        else:
            snap_start = etf_period_df.iloc[0]  # premier jour de la période filtrée

        # Si snap_start est postérieur à start_date → la période remonte avant le 1er mouvement
        # On traite comme "Max" : profit total depuis le début
        if period == "Max" or snap_start['jour'] > start_date:
            perf_etf_period_euro = snap_end['profit_euro']
        else:
            # Variation de profit entre début et fin de période
            perf_etf_period_euro = snap_end['profit_euro'] - snap_start['profit_euro']

        perf_etf_period_pct = (perf_etf_period_euro / snap_end['capital_investi'] * 100) if snap_end['capital_investi'] > 0 else 0
    else:
        # Pas de données sur la période
        perf_etf_period_euro, perf_etf_period_pct = 0, 0

    return {"euro": perf_etf_period_euro, "pct": perf_etf_period_pct}


def get_portfolio_period_perf(history_df, period_df, period, start_date, mapping):
    """
    Calcule la performance de chaque portefeuille sur la période sélectionnée.
    Gère les cas spéciaux "Début Mois" et "Max".

    ⚠️ Si snap_start['jour'] > start_date, cela signifie que la période demandée
    remonte avant le premier mouvement — on traite alors comme "Max" (profit total).

    Args:
        history_df (DataFrame): view_historique_portefeuille (complet, non filtré)
        period_df (DataFrame): history_df filtré sur la période
        period (str): valeur du slider
        start_date (pd.Timestamp): date de début calculée par get_start_date()
        mapping (dict): {ptf_id: nom_affiche} — ex: {1: "PEA", 2: "CTO"}

    Returns:
        dict: {"PEA": {"euro": float, "pct": float}, "CTO": {...}, ...}
    """
    current_month_start = pd.Timestamp.now().replace(day=1).normalize()

    portfolios = mapping
    perf = {}

    for portfolio_id, portfolio_name in portfolios.items():
        # Agrégation journalière pour ce portefeuille sur la période
        temp_df = (period_df.query("ptf_id == @portfolio_id")
                    .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                    .sum()
                    .reset_index()
                    .query("capital_investi + abondement_recu > 1")
                    .sort_values('jour'))

        if not temp_df.empty:
            snap_end = temp_df.iloc[-1]

            if period == "Début Mois":
                # Snapshot avant le 1er du mois dans l'historique complet
                snap_start = (history_df.query("ptf_id == @portfolio_id and jour < @current_month_start")
                                .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                                .sum()
                                .reset_index()
                                .query("capital_investi + abondement_recu > 1")
                                .sort_values('jour')
                                .iloc[-1])
            else:
                snap_start = temp_df.iloc[0]

            # Si snap_start est postérieur à start_date → la période remonte avant le 1er mouvement
            # On traite comme "Max" : profit total depuis le début
            if period == "Max" or snap_start['jour'] > start_date:
                euro = snap_end['profit_euro']
            else:
                euro = snap_end['profit_euro'] - snap_start['profit_euro']

            # Base = effort perso + abondement pour un calcul de ROI correct
            base = snap_end['capital_investi'] + snap_end['abondement_recu']
            pct = (euro / base * 100) if base > 0 else 0
        else:
            euro, pct = 0, 0

        perf[portfolio_name] = {"euro": euro, "pct": pct}

    return perf


def get_monthly_table_by_portfolio(history_df, contributions_df, period, portfolio_name_map):
    """
    Construit le tableau mensuel du journal de bord.
    Retourne deux DataFrames :
    - table_df : version nettoyée pour l'affichage (tri décroissant, 1er mois viré)
    - table_buffer_df : version avec le mois de buffer nécessaire au calcul du graph
                            (trié croissant, 1er mois conservé pour le shift(1) de perf_graph)

    Args:
        history_df (DataFrame): view_historique_portefeuille
        contributions_df (DataFrame): view_apports_mensuels
        period (str): valeur du slider
        portfolio_name_map (dict): {ptf_id: nom_enveloppe}
                        Les valeurs identiques permettent de regrouper plusieurs ptf sous une même colonne

    Returns:
        tuple: (table_df, table_buffer_df)
    """
    months_count = get_months_count(period)
    current_month_start = pd.Timestamp.now().replace(day=1).normalize()
    # Date de départ du tableau — inclut 1 mois de buffer pour permettre le calcul des évolutions m-1
    table_start_date = current_month_start - pd.DateOffset(months=months_count)

    # Copies pour ne pas modifier les DataFrames originaux
    monthly_df = history_df.copy()
    contributions_df = contributions_df.copy()

    # Ajout de la colonne enveloppe pour le regroupement
    monthly_df['Enveloppe'] = monthly_df['ptf_id'].map(portfolio_name_map)

    # Agrégation journalière par enveloppe
    daily_df = (monthly_df.groupby(['Enveloppe', 'jour'])
                    .agg({'capital_actuel': 'sum', 'capital_investi': 'sum'})
                    .reset_index())

    # Pivot mensuel : dernière valeur du mois par enveloppe
    pivot_df = (daily_df.groupby(['Enveloppe', pd.Grouper(key='jour', freq='ME')])
                .agg({'capital_actuel': 'last', 'capital_investi': 'last'})
                .unstack(level=0))

    table_df = pivot_df['capital_actuel'].copy()

    # --- Calcul des colonnes de performance ---
    table_df['Total'] = table_df.sum(axis=1)
    table_df['Evo Patrimoine'] = table_df['Total'].diff()
    table_df['Evo (%)'] = (table_df['Evo Patrimoine'] / table_df['Total'].shift(1)) * 100

    # Alignement des apports sur l'index mensuel du tableau
    # La vue SQL retourne des dates avec timezone → on la vire proprement avant le reindex
    contributions_df['mois'] = contributions_df['mois'].apply(lambda x: pd.Timestamp(x).replace(tzinfo=None).normalize())
    contributions_df = contributions_df.set_index('mois')
    monthly_invested = contributions_df['injecte'].reindex(table_df.index, fill_value=0)

    # Perf marchés = variation patrimoine - argent injecté ce mois
    table_df['Perf Marchés (€)'] = table_df['Evo Patrimoine'] - monthly_invested
    table_df['Perf Marchés (%)'] = (table_df['Perf Marchés (€)'] / table_df['Total'].shift(1)) * 100

    # Colonnes glissantes sur 12 mois (activées via toggle dans Home.py)
    table_df['Evo 12m (€)'] = table_df['Total'] - table_df['Total'].shift(12)
    table_df['Evo 12m (%)'] = (table_df['Evo 12m (€)'] / table_df['Total'].shift(12)) * 100

    # --- Nettoyage ---
    # Filtre sur la période sélectionnée
    table_df = table_df.query("index >= @table_start_date")

    # Ordre d'affichage : enveloppes dynamiques (dédupliquées) + colonnes fixes
    column_order = list(dict.fromkeys(portfolio_name_map.values())) + [
        'Total', 'Evo Patrimoine', 'Evo (%)', 'Perf Marchés (€)', 'Perf Marchés (%)', 'Evo 12m (€)', 'Evo 12m (%)'
        ]

    # On n'affiche une enveloppe que si elle a des données non nulles
    account_columns = set(portfolio_name_map.values())
    visible_columns = []
    for c in column_order:
        if c in account_columns:
            if c in table_df.columns and table_df[c].notna().any() and table_df[c].sum() > 0:
                visible_columns.append(c)
        else:
            if c in table_df.columns and table_df[c].notna().any():
                visible_columns.append(c)

    table_df = table_df[visible_columns]

    # Buffer pour le graph : trié croissant, conserve le 1er mois
    # (nécessaire pour que get_chart_data puisse calculer perf_graph via shift(1))
    table_buffer_df = table_df.sort_index(ascending=True)

    # Tableau d'affichage : tri décroissant + suppression du 1er mois (artefact du diff())
    if months_count > 0:
        table_df = table_df.iloc[1:].sort_index(ascending=False)
    else:
        table_df = table_df.sort_index(ascending=False)

    table_df.index.name = 'Mois'

    return table_df, table_buffer_df


def get_chart_data(table_buffer_df, contributions_df, period):
    """
    Prépare les deux DataFrames nécessaires au graphique principal.
    - contributions_chart_df : cumul des apports mensuels, filtré et réindexé sur la période
    - capital_chart_df : capital mensuel + perf, avec le 1er mois viré après calculs

    ⚠️ Reçoit table_buffer_df (avec mois de buffer) et non table_df (version affichage).
    Le buffer est indispensable pour calculer perf_graph via shift(1) sans perdre le 1er mois affiché.

    Args:
        table_buffer_df (DataFrame): résultat de get_monthly_table_by_portfolio()[1] — trié croissant avec buffer
        contributions_df (DataFrame): view_apports_mensuels brut (avec colonne 'mois')
        period (str): valeur du slider

    Returns:
        tuple: (contributions_chart_df, capital_chart_df)
    """
    months_count = get_months_count(period)
    current_month_start = pd.Timestamp.now().replace(day=1).normalize()
    table_start_date = current_month_start - pd.DateOffset(months=months_count)

    # --- Préparation contributions_chart_df ---

    # Tri croissant pour les calculs cumulatifs
    table_buffer_df = table_buffer_df.sort_index(ascending=True)

    contributions_df = contributions_df.copy()
    contributions_df = contributions_df.set_index('mois')

    # La vue SQL retourne des dates propres (::date) — conversion simple sans timezone
    contributions_df.index = pd.to_datetime(contributions_df.index)

    # Cumul des apports depuis le début (toute l'histoire, pas juste la période)
    contributions_df['cumsum'] = contributions_df['injecte'].cumsum()

    # Remplissage des mois manquants (mois sans mouvement) par forward fill
    # Nécessaire pour avoir une courbe continue même les mois sans apport
    full_index = pd.date_range(
        start=pd.Timestamp(contributions_df.index.min()).tz_localize(None),
        end=pd.Timestamp.today() + pd.offsets.MonthEnd(0),
        freq='ME'
    )
    contributions_df = contributions_df.reindex(full_index).ffill()

    # Filtre sur la période + réindexation en début de mois pour aligner avec capital_chart_df
    contributions_chart_df = contributions_df[contributions_df.index >= table_start_date]
    contributions_chart_df.index = contributions_chart_df.index.to_period('M').to_timestamp()

    # Suppression du 1er mois : il sert de référence pour le diff() mais ne doit pas s'afficher
    contributions_chart_df = contributions_chart_df.iloc[1:]

    # --- Préparation capital_chart_df ---

    capital_chart_df = table_buffer_df

    # Perf marchés en % : variation mensuelle du patrimoine / total du mois précédent
    # Le shift(1) utilise le mois de buffer — c'est pour ça qu'on a besoin de table_buffer_df
    capital_chart_df['perf_graph'] = (capital_chart_df['Perf Marchés (€)'] / capital_chart_df['Total'].shift(1)) * 100

    # Réindexation en début de mois pour aligner avec contributions_chart_df
    capital_chart_df.index = capital_chart_df.index.to_period('M').to_timestamp()

    # Delta = écart entre capital réel et apports cumulés = performance pure des marchés en €
    capital_chart_df['delta'] = capital_chart_df['Total'] - contributions_chart_df['cumsum']

    # Suppression du 1er mois (buffer) — il a servi pour le shift(1), on ne l'affiche pas
    capital_chart_df = capital_chart_df.iloc[1:]

    return contributions_chart_df, capital_chart_df


def get_period_invested(history_df, period_df, period, start_date, product_ids):
    """
    Calcule le capital total injecté sur une liste de produits sur la période sélectionnée.
    Gère les cas spéciaux "Début Mois" et "Max".

    ⚠️ Basé sur capital_investi (cumulatif) — calcule la variation entre snap_start et snap_end.
    Si snap_start['jour'] > start_date, la période remonte avant le 1er mouvement :
    on traite alors comme "Max" et retourne le capital_investi total.

    Args:
        history_df (DataFrame): view_historique_portefeuille (complet, non filtré)
        period_df (DataFrame): history_df filtré sur la période
        period (str): valeur du slider
        start_date (pd.Timestamp): date de début calculée par get_start_date()
        product_ids (list): liste des pdt_id à inclure — ex: [1, 7] pour PEA (ETF + cash)

    Returns:
        float: somme du capital injecté sur les produits listés sur la période
    """
    current_month_start = pd.Timestamp.now().replace(day=1).normalize()

    invested = 0

    for product_id in product_ids:
        # Agrégation journalière pour ce produit sur la période
        temp_df = (period_df.query("pdt_id == @product_id")
                    .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                    .sum()
                    .reset_index()
                    .query("capital_investi + abondement_recu > 1")
                    .sort_values('jour'))

        if not temp_df.empty:
            snap_end = temp_df.iloc[-1]

            if period == "Début Mois":
                # Snapshot avant le 1er du mois dans l'historique complet
                snap_start = (history_df.query("pdt_id == @product_id and jour < @current_month_start")
                                .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                                .sum()
                                .reset_index()
                                .query("capital_investi + abondement_recu > 1")
                                .sort_values('jour')
                                .iloc[-1])
            else:
                snap_start = temp_df.iloc[0]

            # Si snap_start est postérieur à start_date → la période remonte avant le 1er mouvement
            # On traite comme "Max" : capital investi total depuis le début
            if period == "Max" or snap_start['jour'] > start_date:
                invested += snap_end['capital_investi']
            else:
                invested += snap_end['capital_investi'] - snap_start['capital_investi']

        else:
            invested += 0

    return invested


def get_net_capital(df, product_ids):
    """
    Calcule le capital net et la performance après fiscalité sur les plus-values.
    PEA/PEE : 18.6% | CTO : 31.4%
    Si pas de plus-value, retourne le capital actuel brut.

    Args:
        df (DataFrame): view_global_portefeuille
        product_ids (list): liste des pdt_id à inclure — ex: [1, 7] pour PEA (ETF + cash)

    Returns:
        dict: {"net": float, "euro": float, "pct": float}
    """
    tax_rates = {1: 18.6, 2: 31.4, 3: 18.6, 4: 18.6, 5: 18.6, 6: 18.6}
    net_capital = {}
    df = df.copy()

    for product_id in product_ids:
        temp_df = df.query("pdt_id == @product_id and pdt_cash == False and pdt_est_actif == True")
        capital_gain = temp_df['profit_euro'].sum()

        # Fiscalité uniquement si plus-value positive
        if capital_gain > 0:
            tax = capital_gain * tax_rates[product_id] / 100
            net_capital[product_id] = temp_df['capital_actuel'].sum() - tax
        else:
            net_capital[product_id] = temp_df['capital_actuel'].sum()

    return net_capital


def get_portfolio_tri(df, flows_df, portfolio_ids, today=None):
    """
    Calcule le TRI (XIRR) annualisé d'une ou plusieurs enveloppes.

    Args:
        df (DataFrame): view_global_portefeuille (snapshot instantané)
        flows_df (DataFrame): flux de get_tri_flows() (non filtré)
        portfolio_ids (list): ptf_id à inclure
        today (pd.Timestamp): date du flux final (défaut : aujourd'hui)

    Returns:
        float: TRI annualisé en %
    """
    today = today if today is not None else pd.Timestamp.today()

    flows = flows_df[
        flows_df['mvt_type_mouvement'].isin(PORTFOLIO_TRI_TYPES)
        & flows_df['ptf_id'].isin(portfolio_ids)
    ].sort_values('mvt_date')

    amounts = flows['amount'].tolist()
    dates = flows['mvt_date'].tolist()

    capital = df.query("ptf_id == @portfolio_ids")['capital_actuel'].sum()
    amounts.append(capital)
    dates.append(today)

    return xirr(dates, amounts) * 100


def get_product_tri(df, flows_df, product_ids, today=None):
    """
    Calcule le TRI (XIRR) annualisé de chaque produit d'une liste.

    Un XIRR indépendant est calculé par produit, sur ses propres flux
    (APPORT, ABONDEMENT, TRANSFERT) et son propre capital actuel. Les produits
    ne sont pas agrégés entre eux.

    Args:
        df (DataFrame): view_global_portefeuille (snapshot instantané)
        flows_df (DataFrame): flux de get_tri_flows() (non filtré)
        product_ids (list): pdt_id à inclure — ex: [4, 5, 6] pour le PEE CiC
        today (pd.Timestamp): date du flux final (défaut : aujourd'hui)

    Returns:
        dict: {pdt_id: tri_annualisé_en_%}
    """
    today = today if today is not None else pd.Timestamp.today()
    tri = {}

    for product_id in product_ids:
        flows = flows_df[
            flows_df['mvt_type_mouvement'].isin(PRODUCT_TRI_TYPES)
            & (flows_df['pdt_id'] == product_id)
        ].sort_values('mvt_date')

        amounts = flows['amount'].tolist()
        dates = flows['mvt_date'].tolist()

        # Flux final : capital actuel de CE produit à la date du jour
        capital = df.query("pdt_id == @product_id")['capital_actuel'].sum()
        amounts.append(capital)
        dates.append(today)

        tri[product_id] = xirr(dates, amounts) * 100

    return tri


def get_product_period_perf(history_product_df, period_product_df, period, start_date, product_ids, aggregate=False):
    """
    Calcule la performance de chaque produit sur la période sélectionnée.
    Gère les cas spéciaux "Début Mois" et "Max".

    ⚠️ Si snap_start['jour'] > start_date, cela signifie que la période demandée
    remonte avant le premier mouvement — on traite alors comme "Max" (profit total).

    Args:
        history_product_df (DataFrame): view_historique_portefeuille_pdt (complet, non filtré)
        period_product_df (DataFrame): history_product_df filtré sur la période
        period (str): valeur du slider
        start_date (pd.Timestamp): date de début calculée par get_start_date()
        product_ids (list): liste des pdt_id à inclure
        aggregate (bool): si True, retourne un dict agrégé {euro, pct} au lieu du détail par pdt_id
                            ⚠️ le % est recalculé sur la base totale, pas une moyenne des % individuels

    Returns:
        dict: si aggregate=False → {pdt_id: {"euro": float, "pct": float}}
            si aggregate=True  → {"euro": float, "pct": float}
    """
    current_month_start = pd.Timestamp.now().replace(day=1).normalize()

    perf = {}
    total_base = 0

    for product_id in product_ids:
        # Agrégation journalière pour ce produit sur la période
        temp_df = (period_product_df.query("pdt_id == @product_id")
                    .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                    .sum()
                    .reset_index()
                    .query("capital_investi + abondement_recu > 1")
                    .sort_values('jour'))

        if not temp_df.empty:
            snap_end = temp_df.iloc[-1]

            if period == "Début Mois":
                # Snapshot avant le 1er du mois dans l'historique complet
                snap_start = (history_product_df.query("pdt_id == @product_id and jour < @current_month_start")
                                .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                                .sum()
                                .reset_index()
                                .query("capital_investi + abondement_recu > 1")
                                .sort_values('jour')
                                .iloc[-1])
            else:
                snap_start = temp_df.iloc[0]

            # Si snap_start est postérieur à start_date → la période remonte avant le 1er mouvement
            # On traite comme "Max" : profit total depuis le début
            if period == "Max" or snap_start['jour'] > start_date:
                euro = snap_end['profit_euro']
            else:
                euro = snap_end['profit_euro'] - snap_start['profit_euro']

            # Base = effort perso + abondement pour un calcul de ROI correct
            base = snap_end['capital_investi'] + snap_end['abondement_recu']
            total_base += base
            pct = (euro / base * 100) if base > 0 else 0
        else:
            euro, pct = 0, 0

        perf[product_id] = {"euro": euro, "pct": pct}

    if aggregate:
        # somme euros + recalcul pct sur base totale
        total_euro = sum(v['euro'] for v in perf.values())
        pct = (total_euro / total_base * 100) if total_base > 0 else 0
        return {"euro": total_euro, "pct": pct}
    
    return perf


def get_monthly_table_by_product(history_df, contributions_df, period, product_group_map):
    """
    Construit le tableau mensuel du journal de bord.
    Retourne deux DataFrames :
    - table_df : version nettoyée pour l'affichage (tri décroissant, 1er mois viré)
    - table_buffer_df : version avec le mois de buffer nécessaire au calcul du graph
                            (trié croissant, 1er mois conservé pour le shift(1) de perf_graph)

    Args:
        history_df (DataFrame): view_historique_portefeuille
        contributions_df (DataFrame): view_apports_mensuels
        period (str): valeur du slider
        product_group_map (dict): {pdt_id: nom_enveloppe}
                        Les valeurs identiques permettent de regrouper plusieurs ptf sous une même colonne

    Returns:
        tuple: (table_df, table_buffer_df)
    """
    months_count = get_months_count(period)
    current_month_start = pd.Timestamp.now().replace(day=1).normalize()
    # Date de départ du tableau — inclut 1 mois de buffer pour permettre le calcul des évolutions m-1
    table_start_date = current_month_start - pd.DateOffset(months=months_count)

    # Copies pour ne pas modifier les DataFrames originaux
    monthly_df = history_df.copy()
    contributions_df = contributions_df.copy()

    # Ajout de la colonne enveloppe pour le regroupement
    monthly_df['Enveloppe'] = monthly_df['pdt_id'].map(product_group_map)

    # Agrégation journalière par enveloppe
    daily_df = (monthly_df.groupby(['Enveloppe', 'jour'])
                        .agg({'capital_actuel': 'sum', 'capital_investi': 'sum'})
                        .reset_index())

    # Pivot mensuel : dernière valeur du mois par enveloppe
    pivot_df = (daily_df.groupby(['Enveloppe', pd.Grouper(key='jour', freq='ME')])
                .agg({'capital_actuel': 'last', 'capital_investi': 'last'})
                .unstack(level=0))

    table_df = pivot_df['capital_actuel'].copy()

    # --- Calcul des colonnes de performance ---
    table_df['Total'] = table_df.sum(axis=1)
    table_df['Evo Patrimoine'] = table_df['Total'].diff()
    table_df['Evo (%)'] = (table_df['Evo Patrimoine'] / table_df['Total'].shift(1)) * 100

    # Alignement des apports sur l'index mensuel du tableau
    # La vue SQL retourne des dates avec timezone → on la vire proprement avant le reindex
    contributions_df['mois'] = contributions_df['mois'].apply(lambda x: pd.Timestamp(x).replace(tzinfo=None).normalize())
    contributions_df = contributions_df.set_index('mois')
    monthly_invested = contributions_df['injecte'].reindex(table_df.index, fill_value=0)

    # Perf marchés = variation patrimoine - argent injecté ce mois
    table_df['Perf Marchés (€)'] = table_df['Evo Patrimoine'] - monthly_invested
    table_df['Perf Marchés (%)'] = (table_df['Perf Marchés (€)'] / table_df['Total'].shift(1)) * 100

    # Colonnes glissantes sur 12 mois (activées via toggle dans Home.py)
    table_df['Evo 12m (€)'] = table_df['Total'] - table_df['Total'].shift(12)
    table_df['Evo 12m (%)'] = (table_df['Evo 12m (€)'] / table_df['Total'].shift(12)) * 100

    # --- Nettoyage ---
    # Filtre sur la période sélectionnée
    table_df = table_df.query("index >= @table_start_date")

    # Ordre d'affichage : enveloppes dynamiques (dédupliquées) + colonnes fixes
    column_order = list(dict.fromkeys(product_group_map.values())) + [
        'Total', 'Evo Patrimoine', 'Evo (%)', 'Perf Marchés (€)', 'Perf Marchés (%)', 'Evo 12m (€)', 'Evo 12m (%)'
        ]

    # On n'affiche une enveloppe que si elle a des données non nulles
    account_columns = set(product_group_map.values())
    visible_columns = []
    for c in column_order:
        if c in account_columns:
            if c in table_df.columns and table_df[c].notna().any() and table_df[c].sum() > 0:
                visible_columns.append(c)
        else:
            if c in table_df.columns and table_df[c].notna().any():
                visible_columns.append(c)

    table_df = table_df[visible_columns]

    # Buffer pour le graph : trié croissant, conserve le 1er mois
    # (nécessaire pour que get_chart_data puisse calculer perf_graph via shift(1))
    table_buffer_df = table_df.sort_index(ascending=True)

    # Tableau d'affichage : tri décroissant + suppression du 1er mois (artefact du diff())
    if months_count > 0:
        table_df = table_df.iloc[1:].sort_index(ascending=False)
    else:
        table_df = table_df.sort_index(ascending=False)

    table_df.index.name = 'Mois'

    return table_df, table_buffer_df


