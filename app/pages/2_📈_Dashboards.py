# app/pages/Dashboards.py

"""
Page Dashboards : détail par enveloppe (ETF, PEA, CTO, STEF, CiC).

Un menu latéral choisit l'enveloppe affichée (bloc `match`). Chaque dashboard
présente le capital, la performance, le TRI, le capital net, le journal de
bord sur la période choisie (slider) et le graphique d'évolution. Le dashboard
CiC propose en plus une vue détaillée par produit (Obligation, Equilibre,
Stratégie).

Architecture :
- Les données sont chargées une seule fois en haut de page via
    app/components/database.py (vues SQL + flux pour les TRI), puis filtrées
    par enveloppe dans chaque `case`.
- Aucun calcul ici : tout vient de st_logic.py.
- Aucune figure construite ici : tout vient de st_charts.py.
- La page ne contient que : chargement, sidebar, appels de fonctions et
    affichage Streamlit.
"""

import streamlit as st

import app.components.database as db
import app.components.st_charts as charts
import app.components.st_logic as logic

# --------------------------------------------------------------------------------

# --- 1. CONFIGURATION PAGE ---
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

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

# Données de l'app : vues SQL + les flux pour les TRI
df                       = db.get_view("view_global_portefeuille", engine)      # snapshot instantané
history_df               = db.get_view("view_historique_portefeuille", engine)  # historique quotidien
history_product_df       = db.get_view("view_historique_pdt", engine)           # historique quotidien par pdt_id
contributions_df         = db.get_view("view_apports_mensuels", engine)         # flux cash mensuels
contributions_product_df = db.get_view("view_apports_mensuels_pdt", engine)     # flux cash mensuels par pdt_id
flows_df                 = db.get_tri_flows(engine)                             # mouvements d'argent (apports, abondements) pour les TRI


# --- 3. SIDEBAR ---

with st.sidebar:
    st.title("⚙️ Menu")

    # Choix de l'enveloppe
    selected_view = st.sidebar.radio("Menu", ["ETF", "PEA", "CTO", "STEF", "CiC"], label_visibility="collapsed")

    st.divider()

    # Slider de période — contrôle tous les blocs réactifs de la page
    st.subheader("🛠️ Configuration")
    period = st.select_slider(
        "Période d'analyse",
        options=["Début Mois", "1 Mois", "3 Mois", "6 Mois", "1 An", "3 Ans", "5 Ans", "Max"],
        value="6 Mois"
    )
    # Toggle pour afficher les graphs détaillés sur le desh CiC
    if selected_view == "CiC":
        show_detail = st.toggle("Vue détaillée", value=False)


# --- 4. LOGIQUE TEMPORELLE ---

start_date = logic.get_start_date(period)
period_df = logic.get_period_df(history_df, start_date)
period_product_df = logic.get_period_df(history_product_df, start_date)


# --- 5. INTERFACE GRAPHIQUE ---

st.markdown("<h1 style='text-align: center;'>📊 Dashboards</h1>", unsafe_allow_html=True)

match selected_view:

# DASH ETF

    case "ETF":
        etf_df = df.query("ptf_id in (1, 2)")
        quote_df = db.get_product_quotes(engine, 2, start_date)
        capital = logic.get_total_wealth(etf_df)
        perf = logic.get_market_perf(etf_df)
        invested_capital = etf_df['capital_investi'].sum()
        tri = logic.get_portfolio_tri(df, flows_df, [1, 2])

        # DONUTS — Préparation des DataFrames filtrés par enveloppe
        donut_df = df.query("ptf_id in [1, 2]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
        donut_df['legend_label'] = donut_df['ptf_id'].map({1: "S&P 500", 2: "Gold"})

        fig = charts.make_donuts(
        df=donut_df, names='legend_label', values='capital_actuel',
        color_discrete_map={"S&P 500": "#822A2A", "Gold": "#D3AF37"},
        rotation=50, center_label="Poids ETF", height=194
        )

        st.markdown("<h2 style='text-align: center;'>ETF : PEA & CTO</h2>", unsafe_allow_html=True)
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )
            st.metric(
                label="Capital injecté",
                value=f"{invested_capital:,.0f} €".replace(",", " ")
            )

        with col2:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )


        with col3: st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {period}</h4>", unsafe_allow_html=True)
    
        portfolio_name_map = {1: "PEA", 2: "CTO"}
        perf_portfolio = logic.get_portfolio_period_perf(history_df, period_df, period, start_date, portfolio_name_map)
        perf_etf_period = logic.get_etf_period_perf(history_df, period_df, start_date, period)
        invested = logic.get_period_invested(history_df, period_df, period, start_date, [1, 2, 7, 8])

        col6, col7, col8, col9 = st.columns(4)

        with col6:
            st.metric(
                label="Performance ETF",
                value=f"{perf_etf_period['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_etf_period['pct']:.0f} %"
            )
        with col7:
            st.metric(
                label="Injecté",
                value=f"{invested:,.0f} €".replace(",", " "),
                help="Somme des dépots sur la periode"
            )
        with col8:
            st.metric(
                label="Performance PEA",
                value=f"{perf_portfolio['PEA']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_portfolio['PEA']['pct']:.0f} %"
            )
        with col9:
            st.metric(
                label="Performance CTO",
                value=f"{perf_portfolio['CTO']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_portfolio['CTO']['pct']:.0f} %"
            )

        # GRAPHIQUES — (réactif au slider)

        # Lineplot global
        contributions_chart_df = contributions_product_df.query("pdt_id in (7, 8)").groupby('mois')['injecte'].sum().reset_index()
        table_group_map = {1: "PEA", 2: "CTO"}
        table_df, table_buffer_df      = logic.get_monthly_table_by_portfolio(history_df, contributions_chart_df, period, table_group_map)
        contributions_chart_df, capital_chart_df = logic.get_chart_data(table_buffer_df, contributions_chart_df, period)

        if period not in ("1 Mois", "15 Jours", "Début Mois"):
            fig_global = charts.make_global_chart(contributions_chart_df, capital_chart_df)
            st.plotly_chart(fig_global, width='stretch')


# DASH PEA

    case "PEA":

        pea_df = df.query("ptf_id == 1")
        quote_df = db.get_product_quotes(engine, 1, start_date)
        last = quote_df.iloc[0]['cot_prix']
        capital = logic.get_total_wealth(pea_df)
        perf = logic.get_market_perf(pea_df)
        invested_capital = pea_df['capital_investi'].sum()
        net_capital = logic.get_net_capital(df, [1])
        tri = logic.get_portfolio_tri(df, flows_df, [1])

        st.markdown("<h2 style='text-align: center;'>PEA : S&P 500</h2>", unsafe_allow_html=True)

        st.metric(
            label="Dernier Cours",
            value=f"{last:,.2f} €".replace(",", " ")
        )
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        _, col1, col2, col3, _ = st.columns([0.5, 2, 2, 2, 0.5])

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )

        with col2:
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )


        with col3:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )

        _, col4, col5, _ = st.columns([0.5, 1, 1, 0.5])

        with col4:
            st.metric(
                label="Capital net",
                value=f"{net_capital[1]:,.0f} €".replace(",", " "),
                help="Capital net d'impots : 18.6 %"
            )
        with col5:
            st.metric(
                label="Capital injecté",
                value=f"{invested_capital:,.0f} €".replace(",", " ")
            )

        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {period}</h4>", unsafe_allow_html=True)
    
        portfolio_name_map = {1: "PEA"}
        perf_portfolio = logic.get_portfolio_period_perf(history_df, period_df, period, start_date, portfolio_name_map)
        invested = logic.get_period_invested(history_df, period_df, period, start_date, [1, 7])
        high = quote_df.iloc[0]['max']
        low = quote_df.iloc[0]['min']

        col6, col7, col8, col9 = st.columns(4)

        with col6:
            st.metric(
                label="Performance",
                value=f"{perf_portfolio['PEA']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_portfolio['PEA']['pct']:.0f} %"
            )
        with col7:
            st.metric(
                label="Haut",
                value=f"{high:,.2f} €".replace(",", " "),
                help="Cours le plus haut sur"
            )
        with col8:
            st.metric(
                label="Bas",
                value=f"{low:,.2f} €".replace(",", " "),
                help="Cours le plus bas"
            )
        with col9:
            st.metric(
                label="Injecté",
                value=f"{invested:,.0f} €".replace(",", " "),
                help="Somme des dépots sur la periode"
            )
        
        # GRAPHIQUES — (réactif au slider)

        # Lineplot global
        contributions_df = contributions_product_df.query("pdt_id == 7")
        table_group_map = {1: "PEA"}
        table_df, table_buffer_df      = logic.get_monthly_table_by_portfolio(history_df, contributions_df, period, table_group_map)
        contributions_chart_df, capital_chart_df = logic.get_chart_data(table_buffer_df, contributions_df, period)

        if period not in ("1 Mois", "15 Jours", "Début Mois"):
            fig_global = charts.make_global_chart(contributions_chart_df, capital_chart_df)
            st.plotly_chart(fig_global, width='stretch')

# DASH CTO

    case "CTO":
        cto_df = df.query("ptf_id == 2")
        quote_df = db.get_product_quotes(engine, 2, start_date)
        last = quote_df.iloc[0]['cot_prix']
        capital = logic.get_total_wealth(cto_df)
        perf = logic.get_market_perf(cto_df)
        invested_capital = cto_df['capital_investi'].sum()
        net_capital = logic.get_net_capital(df, [2])
        tri = logic.get_portfolio_tri(df, flows_df, [2])

        st.markdown("<h2 style='text-align: center;'>CTO : GOLD</h2>", unsafe_allow_html=True)

        st.metric(
            label="Dernier Cours",
            value=f"{last:,.2f} €".replace(",", " ")
        )
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        _, col1, col2, col3, _ = st.columns([0.5, 2, 2, 2, 0.5])

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )
        with col2:
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )
        with col3:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )

        _, col4, col5, _ = st.columns([0.5, 1, 1, 0.5])

        with col4:
            st.metric(
                label="Capital net",
                value=f"{net_capital[2]:,.0f} €".replace(",", " "),
                help="Capital net d'impots : 18.6 %"
            )
        with col5:
            st.metric(
                label="Capital injecté",
                value=f"{invested_capital:,.0f} €".replace(",", " ")
            )

        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {period}</h4>", unsafe_allow_html=True)
    
        portfolio_name_map = {2: "CTO"}
        perf_portfolio = logic.get_portfolio_period_perf(history_df, period_df, period, start_date, portfolio_name_map)
        invested = logic.get_period_invested(history_df, period_df, period, start_date, [2, 8])
        high = quote_df.iloc[0]['max']
        low = quote_df.iloc[0]['min']

        col6, col7, col8, col9 = st.columns(4)

        with col6:
            st.metric(
                label="Performance",
                value=f"{perf_portfolio['CTO']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_portfolio['CTO']['pct']:.0f} %"
            )
        with col7:
            st.metric(
                label="Haut",
                value=f"{high:,.2f} €".replace(",", " "),
                help="Cours le plus haut sur"
            )
        with col8:
            st.metric(
                label="Bas",
                value=f"{low:,.2f} €".replace(",", " "),
                help="Cours le plus bas"
            )
        with col9:
            st.metric(
                label="Injecté",
                value=f"{invested:,.0f} €".replace(",", " "),
                help="Somme des dépots sur la periode"
            )

        # GRAPHIQUES — (réactif au slider)

        # Lineplot global
        contributions_df = contributions_product_df.query("pdt_id == 8")
        table_group_map = {2: "CTO"}
        table_df, table_buffer_df      = logic.get_monthly_table_by_portfolio(history_df, contributions_df, period, table_group_map)
        contributions_chart_df, capital_chart_df = logic.get_chart_data(table_buffer_df, contributions_df, period)

        if period not in ("1 Mois", "15 Jours", "Début Mois"):
            fig_global = charts.make_global_chart(contributions_chart_df, capital_chart_df)
            st.plotly_chart(fig_global, width='stretch')


# DASH STEF

    case "STEF":
        stef_df = df.query("ptf_id == 3")
        quote_df = db.get_product_quotes(engine, 3, start_date)
        last = quote_df.iloc[0]['cot_prix']
        capital = logic.get_total_wealth(stef_df)
        employer_match = stef_df["abondement_recu"].sum()
        perf = logic.get_market_perf(stef_df)
        invested_capital = stef_df['capital_investi'].sum()
        net_capital = logic.get_net_capital(df, [3])
        tri = logic.get_portfolio_tri(df, flows_df, [3])

        st.markdown("<h2 style='text-align: center;'>PEE : STEF</h2>", unsafe_allow_html=True)

        st.metric(
            label="Dernier Cours",
            value=f"{last:,.2f} €".replace(",", " ")
        )
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )
        with col2:
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )
        with col3:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )

        col4, col5, col6 = st.columns(3)

        with col4:
            st.metric(
                label="Capital net",
                value=f"{net_capital[3]:,.0f} €".replace(",", " "),
                help="Capital net d'impots : 18.6 %"
            )
        with col5:
            st.metric(
                label="Capital injecté",
                value=f"{invested_capital:,.0f} €".replace(",", " ")
            )
        with col6:
            st.metric(
                label="Abondement reçu",
                value=f"{employer_match:,.0f} €".replace(",", " ")
            )

        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {period}</h4>", unsafe_allow_html=True)
    
        portfolio_name_map = {3: "STEF"}
        perf_portfolio = logic.get_portfolio_period_perf(history_df, period_df, period, start_date, portfolio_name_map)
        invested = logic.get_period_invested(history_df, period_df, period, start_date, [3])
        high = quote_df.iloc[0]['max']
        low = quote_df.iloc[0]['min']

        col7, col8, col9, col10 = st.columns(4)

        with col7:
            st.metric(
                label="Performance",
                value=f"{perf_portfolio['STEF']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_portfolio['STEF']['pct']:.0f} %"
            )
        with col8:
            st.metric(
                label="Injecté",
                value=f"{invested:,.0f} €".replace(",", " "),
                help="Somme des dépots sur la periode"
            )
        with col9:
            st.metric(
                label="Haut",
                value=f"{high:,.2f} €".replace(",", " "),
                help="Cours le plus haut sur"
            )
        with col10:
            st.metric(
                label="Bas",
                value=f"{low:,.2f} €".replace(",", " "),
                help="Cours le plus bas"
            )
            
        # GRAPHIQUES — (réactif au slider)

        # Lineplot global
        contributions_df = contributions_product_df.query("pdt_id == 3")
        table_group_map = {3: "STEF"}
        table_df, table_buffer_df      = logic.get_monthly_table_by_portfolio(history_df, contributions_df, period, table_group_map)
        contributions_chart_df, capital_chart_df = logic.get_chart_data(table_buffer_df, contributions_df, period)

        if period not in ("1 Mois", "15 Jours", "Début Mois"):
            fig_global = charts.make_global_chart(contributions_chart_df, capital_chart_df)
            st.plotly_chart(fig_global, width='stretch')


# DASH CiC

    case "CiC":
        cic_df = df.query("ptf_id == 4")
        quote_df = db.get_product_quotes(engine, 4, start_date)
        capital = logic.get_total_wealth(cic_df)
        employer_match = cic_df["abondement_recu"].sum()
        perf = logic.get_market_perf(cic_df)
        invested_capital = cic_df['capital_investi'].sum()
        net_capital = logic.get_net_capital(df, [4, 5, 6])
        tri = logic.get_portfolio_tri(df, flows_df, [4])

        # DONUTS — Préparation des DataFrames filtrés par enveloppe
        donut_df = df.query("pdt_id in [4, 5, 6]").groupby('pdt_id')['capital_actuel'].sum().reset_index()
        donut_df['legend_label'] = donut_df['pdt_id'].map({4: "Obligation", 5: "Equilibre", 6: "Stratégie"})

        fig = charts.make_donuts(
        df=donut_df, names='legend_label', values='capital_actuel',
        color_discrete_map={"Obligation": "#018289", "Equilibre": "#0f228b", "Stratégie": "#fe330f"},
        rotation=175, center_label="Poids CiC", height=194
        )

        st.markdown("<h2 style='text-align: center;'>PEE : CiC</h2>", unsafe_allow_html=True)
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )
            st.metric(
                label="Capital net",
                value=f"{sum(net_capital.values()):,.0f} €".replace(",", " "),
                help="Capital net d'impots : 18.6 %"
            )
        with col2:
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )
            st.metric(
                label="Capital injecté",
                value=f"{invested_capital:,.0f} €".replace(",", " ")
            )
        with col3:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )
            st.metric(
                label="Abondement reçu",
                value=f"{employer_match:,.0f} €".replace(",", " ")
            )

        with col4: st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
            
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales par ENVELOPPES (hors période)
        perf_product_max = logic.get_product_period_perf(history_product_df, period_product_df, period='Max', start_date=None, product_ids=[4, 5, 6])
        tri_product = logic.get_product_tri(df, flows_df, [4, 5, 6])

        col5, col6, col7 = st.columns(3)
        
        with col5:
            st.metric(
                label="Performance Obligation",
                value=f"{perf_product_max[4]['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_product_max[4]['pct']:.0f} %"
            )
            st.metric(
                label="Performance Annualisée",
                value=f"{tri_product[4]:.1f} %",
            )
        with col6:
            st.metric(
                label="Performance Equilibre",
                value=f"{perf_product_max[5]['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_product_max[5]['pct']:.0f} %"
            )
            st.metric(
                label="Performance Annualisée",
                value=f"{tri_product[5]:.1f} %",
            )
        with col7:
            st.metric(
                label="Performance Stratégie",
                value=f"{perf_product_max[6]['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_product_max[6]['pct']:.0f} %"
            )
            st.metric(
                label="Performance Annualisée",
                value=f"{tri_product[6]:.1f} %",
            )
        
        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {period}</h4>", unsafe_allow_html=True)
    
        perf_portfolio = logic.get_product_period_perf(history_product_df, period_product_df, period, start_date, [4, 5, 6], aggregate=True)
        perf_product = logic.get_product_period_perf(history_product_df, period_product_df, period, start_date, [4, 5, 6])

        col8, col9, col10, col11 = st.columns(4)

        with col8:
            st.metric(
                label="Performance CiC",
                value=f"{perf_portfolio['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_portfolio['pct']:.0f} %"
            )
        with col9:
            st.metric(
                label="Performance Obligation",
                value=f"{perf_product[4]['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_product[4]['pct']:.0f} %"
            )
        with col10:
            st.metric(
                label="Performance Equilibre",
                value=f"{perf_product[5]['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_product[5]['pct']:.0f} %"
            )
        with col11:
            st.metric(
                label="Performance Stratégie",
                value=f"{perf_product[6]['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_product[6]['pct']:.0f} %"
            )

        # GRAPHIQUES — (réactif au slider)

        # Lineplot global
        contributions_df = contributions_product_df.query("pdt_id in (4, 5, 6, 9)").groupby('mois')['injecte'].sum().reset_index()
        table_group_map = {4: "CiC"}
        table_df, table_buffer_df      = logic.get_monthly_table_by_portfolio(history_df, contributions_df, period, table_group_map)
        contributions_chart_df, capital_chart_df = logic.get_chart_data(table_buffer_df, contributions_df, period)

        # Lineplot detaillé
        contributions_bond_df = contributions_product_df.query("pdt_id == 4").reset_index()
        contributions_balanced_df = contributions_product_df.query("pdt_id == 5").reset_index()
        contributions_strategy_df = contributions_product_df.query("pdt_id == 6").reset_index()

        table_bond_df, table_buffer_bond_df = logic.get_monthly_table_by_product(history_df, contributions_bond_df, period, {4: "Obligation"})
        table_balanced_df, table_buffer_balanced_df = logic.get_monthly_table_by_product(history_df, contributions_balanced_df, period, {5: "Equilibre"})
        table_strategy_df, table_buffer_strategy_df = logic.get_monthly_table_by_product(history_df, contributions_strategy_df, period, {6: "Stratégie"})

        chart_bond_df = table_buffer_bond_df[['Obligation', 'Evo Patrimoine', 'Perf Marchés (€)']].rename(columns={'Obligation': 'Total'})
        chart_balanced_df = table_buffer_balanced_df[['Equilibre', 'Evo Patrimoine', 'Perf Marchés (€)']].rename(columns={'Equilibre': 'Total'})
        chart_strategy_df = table_buffer_strategy_df[['Stratégie', 'Evo Patrimoine', 'Perf Marchés (€)']].rename(columns={'Stratégie': 'Total'})

        contributions_chart_bond_df, capital_bond_df = logic.get_chart_data(chart_bond_df, contributions_bond_df, period)
        contributions_chart_balanced_df, capital_balanced_df = logic.get_chart_data(chart_balanced_df, contributions_balanced_df, period)
        contributions_chart_strategy_df, capital_strategy_df = logic.get_chart_data(chart_strategy_df, contributions_strategy_df, period)   

        if period not in ("1 Mois", "15 Jours", "Début Mois"):
            if not show_detail:
                fig_global = charts.make_global_chart(contributions_chart_df, capital_chart_df)
                st.plotly_chart(fig_global, width='stretch')
            else:
                tab1, tab2, tab3 = st.tabs(["Obligation", "Equilibre", "Stratégie"])
                with tab1:
                    fig_global = charts.make_global_chart(contributions_chart_bond_df, capital_bond_df)
                    st.plotly_chart(fig_global, width='stretch')
                with tab2:
                    fig_global = charts.make_global_chart(contributions_chart_balanced_df, capital_balanced_df)
                    st.plotly_chart(fig_global, width='stretch')
                with tab3:
                    fig_global = charts.make_global_chart(contributions_chart_strategy_df, capital_strategy_df)
                    st.plotly_chart(fig_global, width='stretch')