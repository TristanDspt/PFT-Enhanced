# app/components/st_charts.py

import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# st_charts.py
# Contient toutes les figures Plotly de l'application.
# Aucun code Streamlit ici — uniquement des fonctions qui retournent des fig.
# =============================================================================


# --- 1. DONUTS ---

def apply_style(fig):
    """
    Applique le style commun à tous les donuts (texte, position, hover).
    Modifie la figure en place — pas de return nécessaire.

    Args:
        fig (go.Figure): figure Plotly à styler
    """
    fig.update_traces(
        textinfo='percent',
        texttemplate='<b>%{percent:.0%}</b>',
        textposition='inside',
        insidetextorientation='horizontal',
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} €<extra></extra>"
    )


def make_donuts(df, names, values, color_discrete_map, center_label, rotation=None, weight=None, height=200):
    """
    Crée un donut chart générique pour afficher la répartition d'une enveloppe.
    Utilisé dans Home.py (poids global) et Dashboards.py (répartition interne).

    Args:
        df (DataFrame): données filtrées pour ce donut (ex: df.query("ptf_id in [1, 2]"))
        names (str): nom de la colonne utilisée pour les labels (ex: 'legend_label')
        values (str): nom de la colonne utilisée pour les valeurs (ex: 'capital_actuel')
        color_discrete_map (dict): mapping label → couleur hex (ex: {"S&P 500": "#822A2A"})
        center_label (str): texte affiché au centre du donut (ex: "Poids ETF")
        rotation (int): angle de départ du premier secteur (en degrés)
        weight (float, optional): poids en % affiché en grand au centre. 
                                Si None, le label est centré sans valeur. Default: None
        height (int, optional): hauteur du graphique en pixels. Default: 200

    Returns:
        go.Figure: figure Plotly prête à être affichée avec st.plotly_chart()
    """
    # Layout commun : taille dynamique, fond transparent, pas de légende
    common_layout = dict(
        height=height,
        showlegend=False,
        margin=dict(t=0, b=10, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        separators=", "
    )

    # Création du pie chart avec trou (hole) pour l'effet donut
    fig = px.pie(
        df,
        names=names,
        values=values,
        hole=0.68,
        color=names,
        color_discrete_map=color_discrete_map
    )

    # Application du style commun + rotation spécifique à cette enveloppe
    apply_style(fig)
    if rotation is None:
        rotation = compute_rotation(df[values])
    fig.update_traces(rotation=rotation, sort=True, direction='clockwise')

    # Layout + annotations : label en haut, poids en grand en bas
    annotations = []
    if weight is not None:
        annotations.append(dict(text=center_label, x=0.5, y=0.6, showarrow=False, font=dict(size=18)))
        annotations.append(dict(text=f"<b>{weight:.0f}%</b>", x=0.51, y=0.4, showarrow=False, font=dict(size=35)))
    else:
        annotations.append(dict(text=center_label, x=0.5, y=0.5, showarrow=False, font=dict(size=18)))
    
    fig.update_layout(common_layout, hoverlabel=dict(font_size=15), annotations=annotations)

    return fig


# --- 2. GRAPH GLOBAL ---

def make_global_chart(contributions_chart_df, capital_chart_df, title=None):
    """
    Crée le graphique principal de la Home : évolution du capital vs apports + perf marchés.
    Combine 2 axes Y : barres (perf %) à gauche, lignes (capital €) à droite.

    Args:
        contributions_chart_df (DataFrame): apports cumulés filtrés sur la période
                                        doit contenir : index datetime, colonne 'cumsum'
        capital_chart_df (DataFrame): capital mensuel filtré sur la période
                                        doit contenir : index datetime, colonnes 'Total', 'delta', 'perf_graph'
        title (str, optional): titre affiché en haut du graphique. Default None.

    Returns:
        go.Figure: figure Plotly prête à être affichée avec st.plotly_chart()
    """
    global_chart = go.Figure()

    # Coloration dynamique des barres : rouge si perf négative, vert si positive
    bar_colors = capital_chart_df['perf_graph'].apply(
        lambda x: '#ff4b4b' if x < 0 else '#09ab3b'
    )

    # Ligne 1 : Capital total (axe Y droit)
    global_chart.add_trace(go.Scatter(
        x=capital_chart_df.index,
        y=capital_chart_df['Total'],
        name="Capital",
        mode='lines+markers',
        marker=dict(size=4),
        yaxis="y2",
        line=dict(color='#FFD700'),
        customdata=capital_chart_df['delta'],  # écart capital - apports cumulés
        hovertemplate="%{y:,.0f} €<br>Delta: %{customdata:,.0f} €"
    ))

    # Ligne 2 : Apports cumulés (axe Y droit) — sert de référence vs le capital réel
    global_chart.add_trace(go.Scatter(
        x=contributions_chart_df.index,
        y=contributions_chart_df['cumsum'],
        name="Injecté",
        mode='lines+markers',
        marker=dict(size=4),
        yaxis="y2",
        line=dict(color='#4DA6FF'),
        hovertemplate="%{y:,.0f} €",
    ))

    # Barres : performance mensuelle des marchés en % (axe Y gauche)
    global_chart.add_trace(go.Bar(
        x=capital_chart_df.index,
        y=capital_chart_df['perf_graph'],
        name="Perf Marchés",
        marker=dict(color=bar_colors, opacity=0.8),
        width=1000 * 3600 * 24 * 3,  # largeur des barres en millisecondes
        hovertemplate="%{y:,.2f} %"
    ))

    # Calcul des bornes de l'axe Y droit pour éviter que les lignes soient écrasées
    y_min = min(capital_chart_df['Total'].min(), contributions_chart_df['cumsum'].min()) * 0.95
    y_max = max(capital_chart_df['Total'].max(), contributions_chart_df['cumsum'].max()) * 1.05

    # Habillage général : double axe Y, légende horizontale en haut, hover unifié
    global_chart.update_layout(
        yaxis=dict(title="Perf %", showgrid=False),
        xaxis=dict(tickformat="%B %Y"),
        yaxis2=dict(
            side='right',
            overlaying='y',
            range=[y_min, y_max],
            title="Capital (€)"
        ),
        legend=dict(orientation='h', y=1.1, x=0.5, xanchor='center'),
        height=600,
        hovermode='x unified',
        hoverlabel=dict(font_size=15),
        separators=". "
    )
    if title:
        global_chart.update_layout(title=title)

    return global_chart


def compute_rotation(values, target_angle=0):
    """
    Calcule la rotation qui place le plus petit secteur du donut à un angle cible.

    Avec sort=True et direction='clockwise', Plotly dessine les secteurs du plus
    grand au plus petit dans le sens horaire à partir de `rotation` (0 = midi).
    Le plus petit est donc le dernier, et finit pile sur `rotation` : on recule
    le départ d'une demi-largeur de ce secteur pour centrer son milieu sur la cible.

    Args:
        values (iterable): valeurs des secteurs
        target_angle (int): position voulue du plus petit secteur, en degrés
            depuis midi dans le sens horaire (0 = midi). Default: 0

    Returns:
        float: rotation à passer à Plotly, entre 0 et 360
    """
    values = [float(v) for v in values if v > 0]
    total = sum(values)

    if total == 0:
        return 0
    smallest_share = min(values) / total

    return (target_angle + 180 * smallest_share) % 360