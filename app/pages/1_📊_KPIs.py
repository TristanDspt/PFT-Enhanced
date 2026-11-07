# app/pages/KPIs.py

import streamlit as st

import app.components.database as db
import app.components.st_charts as charts
import app.components.st_logic as logic

# =============================================================================
# Home.py
# Page principale de l'application Personal Finance Tracker.
# Ce fichier ne contient que : imports, chargement, sidebar, appels de fonctions
# et affichage Streamlit.
# Zéro calcul ici → st_logic.py | Zéro figure construite ici → st_charts.py
# =============================================================================


# --- 1. CONFIGURATION PAGE ---

st.set_page_config(page_title="PFT", page_icon="🏠", layout="wide")

# Centrage des métriques via CSS
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    [data-testid="stMetricLabel"] {
        justify-content: center;
        width: 100%;
        min-height: 2rem;
        display: flex;
        align-items: flex-end;
    }
    [data-testid="stMetricValue"] {
        width: 100%;
    }
    [data-testid="stMetricDelta"] {
    justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 2. CONNEXION & CHARGEMENT DES VUES SQL ---

engine = db.get_engine()

# Les quatre vues SQL sont la source de toutes les données de l'app
df             = db.get_view("view_global_portefeuille", engine)      # snapshot instantané
history_df       = db.get_view("view_historique_portefeuille", engine)  # historique quotidien par ptf_id
history_product_df   = db.get_view("view_historique_pdt", engine)           # historique quotidien par pdt_id
contributions_df     = db.get_view("view_apports_mensuels", engine)         # flux cash mensuels


# --- 3. SIDEBAR ---

with st.sidebar:
    st.title("⚙️ Menu")

    # Affichage du cash en attente sur les poches broker (alerte si > 400€ sur le PEA)
    st.subheader("💰 Cash en attente")
    cash_pea = df.query("pdt_id == 7")['capital_actuel'].fillna(0).iloc[0]
    cash_cto = df.query("pdt_id == 8")['capital_actuel'].fillna(0).iloc[0]
    st.write(f"**PEA :** `{cash_pea:,.2f} €`".replace(',', ' '))
    st.write(f"**CTO :** `{cash_cto:,.2f} €`".replace(',', ' '))
    if cash_pea > 400:
        st.warning(f"⚠️ {cash_pea:,.2f}€ sur le PEA !".replace(',', ' '))

    st.divider()

    # Slider de période — contrôle tous les blocs réactifs de la page
    st.subheader("🛠️ Configuration")
    period = st.select_slider(
        "Période d'analyse",
        options=["Début Mois", "1 Mois", "3 Mois", "6 Mois", "1 An", "3 Ans", "5 Ans", "Max"],
        value="6 Mois"
    )
    # Toggle pour afficher les colonnes d'évolution sur 12 mois glissants dans le tableau
    show_12m = st.toggle("12 mois roulants", value=False)


# --- 4. CALCULS GÉNÉRAUX (indépendants de la période) ---
# Ces valeurs ne changent pas quand on bouge le slider

capital      = logic.get_total_wealth(df)
market_perf = logic.get_market_perf(df)
etf_df       = df.query("ptf_id in (1, 2)")
perf_etf     = logic.get_market_perf(etf_df)
weights       = logic.get_account_weights(df)
tri_global   = logic.get_portfolio_tri(df, engine, [1, 2, 3, 4])


# --- 5. LOGIQUE TEMPORELLE (réactive au slider) ---
# Ces valeurs sont recalculées à chaque changement de période

start_date     = logic.get_start_date(period)
period_df     = logic.get_period_df(history_df, start_date)
period_product_df = logic.get_period_df(history_product_df, start_date)
# Mapping ptf_id → nom affiché
portfolio_name_map  = {1: "PEA", 2: "CTO", 3: "STEF"}
perf_portfolio     = logic.get_portfolio_period_perf(history_df, period_df, period, start_date, portfolio_name_map)
perf_overall = logic.get_product_period_perf(history_product_df, period_product_df, period, start_date, [1,2,3,4,5,6], aggregate=True)
perf_cic     = logic.get_product_period_perf(history_product_df, period_product_df, period, start_date, [4, 5, 6], aggregate=True)

# Le tableau doit être calculé avant le graph — get_chart_data dépend de table_buffer_df
# table_buffer_df : version avec mois de buffer, pour le calcul de perf_graph via shift(1)
# Mapping ptf_id → enveloppe pour regrouper les lignes
table_group_map = {
    1: "ETF",
    2: "ETF",
    3: "STEF",
    4: "CiC",
    6: "Livrets",
}
table_df, table_buffer_df      = logic.get_monthly_table_by_portfolio(history_df, contributions_df, period, table_group_map)
contributions_chart_df, capital_chart_df = logic.get_chart_data(table_buffer_df, contributions_df, period)


# --- 6. INTERFACE GRAPHIQUE ---

st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.divider()

# KPIs GÉNÉRAUX — Patrimoine total + perfs globales (hors période)
_, col1, col2, col3, _ = st.columns([0.5, 2, 2, 2, 0.5])

with col1:
    st.metric(
        label="Patrimoine Total",
        value=f"{capital:,.0f} €".replace(",", " "),
        help="Somme totale de tous les actifs (Cash + Titres)"
    )
with col2:
    st.metric(
        label="Performance Marchés",
        value=f"{market_perf['pct']:.0f} %",
        delta=f"{market_perf['euro']:,.0f} €".replace(",", " "),
        help="Rendement total par rapport au capital investi (Hors livrets d'épargne)"
    )
with col3:
    st.metric(
        label="Performance Annualisée",
        value=f"{tri_global:.1f} %",
        help="TRI : conversion de la performance en base annuelle"
    )

# DONUTS — Préparation des DataFrames filtrés par enveloppe
etf_donut_df = df.query("ptf_id in [1, 2]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
etf_donut_df['legend_label'] = etf_donut_df['ptf_id'].map({1: "S&P 500", 2: "Gold"})

pee_donut_df = df.query("ptf_id in [3, 4]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
pee_donut_df['legend_label'] = pee_donut_df['ptf_id'].map({3: "STEF", 4: "CiC"})

savings_donut_df = df.query("pdt_id in [10, 11]").groupby('pdt_id')['capital_actuel'].sum().reset_index()
savings_donut_df['legend_label'] = savings_donut_df['pdt_id'].map({10: "Livret A", 11: "LEP"})

# Création des 3 donuts via st_charts (même fonction, params différents)
fig_etf = charts.make_donuts(
    df=etf_donut_df, names='legend_label', values='capital_actuel',
    color_discrete_map={"S&P 500": "#822A2A", "Gold": "#D3AF37"},
    rotation=50, center_label="Poids ETF", weight=weights['etf']
)
fig_pee = charts.make_donuts(
    df=pee_donut_df, names='legend_label', values='capital_actuel',
    color_discrete_map={"STEF": "#00519e", "CiC": "#018289"},
    rotation=80, center_label="Poids PEE", weight=weights['pee']
)
fig_liv = charts.make_donuts(
    df=savings_donut_df, names='legend_label', values='capital_actuel',
    color_discrete_map={"Livret A": "#FF8C00", "LEP": "#540A88"},
    rotation=10, center_label="Poids Livrets", weight=weights['savings']
)

col4, col5, col6 = st.columns(3)
with col4: st.plotly_chart(fig_etf, width='stretch', config={'displayModeBar': False})
with col5: st.plotly_chart(fig_pee, width='stretch', config={'displayModeBar': False})
with col6: st.plotly_chart(fig_liv, width='stretch', config={'displayModeBar': False})

st.divider()

# JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {period}</h4>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Performance Globale",
        value=f"{perf_overall['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_overall['pct']:.0f} %"
    )
with col2:
    st.metric(
        label="Performance PEA",
        value=f"{perf_portfolio['PEA']['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_portfolio['PEA']['pct']:.0f} %"
    )
with col3:
    st.metric(
        label="Performance CTO",
        value=f"{perf_portfolio['CTO']['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_portfolio['CTO']['pct']:.0f} %"
    )
with col4:
    st.metric(
        label="Performance STEF",
        value=f"{perf_portfolio['STEF']['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_portfolio['STEF']['pct']:.0f} %"
    )
with col5:
    st.metric(
        label="Performance CiC",
        value=f"{perf_cic['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_cic['pct']:.0f} %"
    )

# TABLEAU MENSUEL
# La traduction des mois en français et le formatage restent ici — c'est du pur affichage
french_months = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

display_df = table_df.copy()

# Colonnes 12m roulants — ajoutées uniquement si le toggle est activé
if not show_12m:
    display_df = display_df.drop(columns=['Evo 12m (€)', 'Evo 12m (%)'])

# Traduction de l'index datetime en label lisible (ex: "Octobre 2025")
display_df.index = display_df.index.map(lambda x: f"{french_months[x.month]} {x.year}")

# Format d'affichage complet — on filtre ensuite sur les colonnes réellement présentes
full_format = {
    'ETF': "{:,.2f} €", 'STEF': "{:,.2f} €", 'CiC': "{:,.2f} €",
    'Livrets': "{:,.2f} €", 'Total': "{:,.2f} €", 'Evo Patrimoine': "{:,.2f} €",
    'Perf Marchés (€)': "{:,.2f} €", 'Perf Marchés (%)': "{:,.2f} %", 'Evo 12m (€)': "{:,.0f} €",
    'Evo (%)': "{:.2f} %", 'Evo 12m (%)': "{:.1f} %"
}
filtered_format = {k: v for k, v in full_format.items() if k in display_df.columns}

st.dataframe(
    display_df.style
    .format(filtered_format, na_rep='-', thousands=" ")
    # Coloration conditionnelle : rouge si négatif, vert si positif
    .map(
        lambda x: 'color: #ff4b4b' if x < 0 else 'color: #09ab3b',
        subset=[c for c in ['Evo Patrimoine', 'Evo (%)', 'Perf Marchés (€)', 'Perf Marchés (%)'] if c in display_df.columns]
    ),
    column_config={"Mois": st.column_config.Column(width=140)},
    width='stretch',
    height=min(35 * len(display_df) + 38, 458)  # hauteur dynamique selon le nombre de lignes
)

# GRAPHIQUE GLOBAL — masqué sur les courtes périodes (pas assez de points pour être lisible)
if period not in ("1 Mois", "Début Mois"):
    fig_global = charts.make_global_chart(contributions_chart_df, capital_chart_df)
    st.plotly_chart(fig_global, width='stretch')