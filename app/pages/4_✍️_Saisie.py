# app/pages/Saisie.py

import subprocess
import sys
import time

import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.components.database import get_engine
from core import config

# --------------------------------------------------------------------------------------------------------------

# 0. CONFIGURATION PAGE
st.set_page_config(page_title="Saisie", page_icon="✍️", layout="wide")

# SQL
# 1 Connection à la DB
engine = get_engine()

# 2. Fonction pour charger les données (mise en cache pour la rapidité)
@st.cache_data
def load_data():
    query_portfolios = """
        SELECT ptf_id, ptf_nom_banque, ptf_type_enveloppe
        FROM public.portefeuille_ptf
        WHERE ptf_est_actif is TRUE
    """
    portfolios_df = pd.read_sql(query_portfolios, engine)
    query_products = """
        SELECT pdt_id, pdt_nom_produit, pdt_ticker, pdt_cash, ptf_id
        FROM public.produit_financier_pdt
        WHERE pdt_est_actif is TRUE
    """
    products_df = pd.read_sql(query_products, engine)
    return portfolios_df, products_df

# 3 Appel de la fonction
portfolio_list_df, product_list_df = load_data()

# --------------------------------------------------------------------------------------------------------------

# CREATION DES LISTE DEROULANTES
# Création de df
cash_products_df = product_list_df[product_list_df['pdt_cash'] == True].copy()
cash_products_df = cash_products_df.merge(portfolio_list_df[['ptf_id', 'ptf_nom_banque']], on='ptf_id')
cash_products_df['cash_label'] = cash_products_df['ptf_nom_banque'] + " - " + cash_products_df['pdt_nom_produit']

securities_portfolios_df = portfolio_list_df[portfolio_list_df['ptf_type_enveloppe'] != 'Livrets'].copy()
securities_portfolios_df['securities_label'] = securities_portfolios_df['ptf_nom_banque'] + " - " + securities_portfolios_df['ptf_type_enveloppe']

# Listes dynamiques
cash_account_options = cash_products_df['cash_label'].tolist()
securities_account_options = securities_portfolios_df['securities_label'].tolist()

# Listes fixes
cash_types = ["Dépôt", "Retrait", "Ajustement", "Intérêts"]
securities_types = ["Achat", "Vente", "Ajustement", "Abondement", "Dividende"]

# --------------------------------------------------------------------------------------------------------------

# BLOC TITRE
#st.markdown("<h1 style='text-align: center; margin-bottom: 40px;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>✍️ Saisie</h2>", unsafe_allow_html=True)
st.divider() # Un petit trait pour séparer proprement

# MENU
with st.sidebar:
    st.title("⚙️ Menu")

    selected_view = st.sidebar.radio("Choix", ["💸 Flux Cash", "📈 Titres"], label_visibility="collapsed")

    st.divider()

    # Bouton de mise à jour manuelle des fonds PEE (lance update_pee.py en subprocess)
    if st.button("🔄 MAJ PEE"):
        result = subprocess.run(
            [sys.executable, "-m", "pipelines.etl.update_pee"],
            capture_output=True, text=True,
            cwd=config.PROJECT_ROOT,
        )
        st.cache_data.clear()
        if result.stderr:
            st.error("⚠️ Erreur !")
            st.text(result.stderr)
        elif "non trouvé" in result.stdout:
            st.warning("⚠️ Fichiers absents...")
            st.text(result.stdout)
        else:
            st.success("🚀 Données envoyées !")
            st.text(result.stdout)
        time.sleep(8)
        st.rerun()
    st.caption("⚠️ Télécharger CSV avant MAJ")

# CASH
if selected_view == "💸 Flux Cash":

    # Ligne 1
    col1, col2, col3 = st.columns([0.5, 2, 0.5])
    with col2:
        selected_cash_account = st.selectbox("Livret", cash_account_options)
        # On récupère tout d'un coup
        selection = cash_products_df[cash_products_df['cash_label'] == selected_cash_account].iloc[0]
        product_id = selection['pdt_id'] 
        portfolio_id = selection['ptf_id'] # Utile pour les frais/banque plus tard
        product_name = selection['pdt_nom_produit'] # Pour l'affichage popup

    # Ligne 2
    col4, col5, col6 = st.columns(3)
    with col4:
        movement_date = st.date_input("Date de l'opération")
    with col5:
        shares_input = st.text_input("Montant", value="0", help="Saisir un montant positif, le signe est géré automatiquement")
        try:
            shares = float(shares_input.replace(',', '.'))
        except ValueError:
            st.error("⚠️ Montant invalide")
            shares = None
    with col6:
        movement_type = st.selectbox("Type", cash_types)

    # Valeurs fixes pour le cash
    price = 1
    fees = 0

# ACTIONS        
elif selected_view == "📈 Titres":

    # Ligne 1
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_account = st.selectbox("Livret", securities_account_options)
        portfolio_id = securities_portfolios_df[securities_portfolios_df['securities_label'] == selected_account]['ptf_id'].values[0]
        
    with col2:
        portfolio_products_df = product_list_df[(product_list_df['ptf_id'] == portfolio_id) & (product_list_df['pdt_cash'] == False)]
        product_name = st.selectbox("Placement", portfolio_products_df['pdt_nom_produit'].tolist())
        # On récupère l'id 
        product_id = portfolio_products_df[portfolio_products_df['pdt_nom_produit'] == product_name]['pdt_id'].values[0]
        
    with col3:
        movement_type = st.selectbox("Type", securities_types)

    # Ligne 2
    col4, col5, col6 , col7 = st.columns(4)
    with col4:
        movement_date = st.date_input("Date de l'opération")
    with col5:
        shares_input = st.text_input("Nombre de parts", value="0", help="Saisir une valeur positive — le signe est appliqué automatiquement")
        try:
            shares = float(shares_input.replace(',', '.'))
        except ValueError:
            st.error("⚠️ Nombre de parts invalide")
            shares = None
    with col6:
        price_input = st.text_input("Prix de la part", value="0")
        try:
            price = float(price_input.replace(',', '.'))
        except ValueError:
            st.error("⚠️ Prix invalide")
            price = None
    with col7:
        fees_input = st.text_input("Frais", value="0")
        try:
            fees = float(fees_input.replace(',', '.'))
        except ValueError:
            st.error("⚠️ Frais invalide")
            fees = None

# --------------------------------------------------------------------------------------------------------------

# AJOUT EN BASE

# POP UP DE CONFIRMATION
@st.dialog("Confirmer l'opération") # crée la popup
def confirm_operation(target_product_id, op_date, quantity, op_fees, op_type, op_price, category, op_product_name, cash_product_id=None):
    # Gestion de la syntaxe "réelle vs DB"
    if op_type == "Dépôt":
        db_type = "APPORT"
    elif op_type == "Intérêts":
        db_type = "INTERET"
    else:
        db_type = str(op_type).upper()
    # Gestion des ventes / retrait à passer en négatif
    if op_type in ["Vente", "Retrait"]:
        # On force le négatif quoi qu'il arrive
        signed_quantity = -abs(quantity)
    elif op_type in ["Ajustement"]:
        # On garde le signe saisi par l'utilisateur (permet de corriger + ou -)
        signed_quantity = quantity
    else:
        # Pour les achats/dépôts, on force le positif
        signed_quantity = abs(quantity)

    # On adapte l'affichage selon si c'est du Cash ou des Actions
    if category == "💸 Flux Cash":
        # Affichage pour le CASH
        st.write(f"## 💸 Enregistrer un **{op_type}**")
        st.info(f"Montant : **{quantity}€**")
        st.write(f"### 🏛️ {op_product_name}")
    else:
        # Affichage pour les ACTIONS
        st.write(f"## 📈 Enregistrer un **{op_type}**")
        col1, col2 = st.columns(2)
        col1.metric("Parts", f"{quantity:.6f}")
        col2.metric("Prix", f"{op_price:.4f}€")
        col3, col4 = st.columns(2)
        col3.metric("Montant Total", f"{quantity * op_price:.2f}€")
        col4.metric("Frais de courtage", f"{op_fees:.2f}€")
        st.write(f"### 🏛️ {op_product_name}")

    st.write(f"📅 *Date : {op_date}*")
    st.divider()

    if st.button("Valider ✅", width='stretch', type='primary'):
        # Connection à la DB
        with engine.begin() as conn:
        
            # On crée la requête SQL
            security_query = text("""
                INSERT INTO public.mouvement_mvt
                    (pdt_id, mvt_date, mvt_nb_parts, mvt_frais, mvt_type_mouvement, mvt_prix)
                VALUES
                    (:pdt_id, :mvt_date, :nb_parts, :frais, :type_mvt, :prix)
            """)
            conn.execute(security_query, {
                "pdt_id": target_product_id, "mvt_date": op_date, "nb_parts": signed_quantity,
                "frais": op_fees, "type_mvt": db_type, "prix": op_price,
            })

            # Cas spécifique pour les achat vente passage de l'argent de ou vers la poche cash
            if cash_product_id:
                # 1. Calcul du montant net (le cash qui bouge réellement)
                security_amount = (quantity * op_price)
                
                if op_type == "Achat":
                    cash_amount = -(security_amount + op_fees)
                    cash_type = "RETRAIT_MIROIR"
                elif op_type == "Vente":
                    cash_amount = (security_amount - op_fees)
                    cash_type = "APPORT"
                else:
                    # Pour Ajustement ou Dividende, à toi de voir la logique
                    cash_amount = security_amount 
                    cash_type = "AJUSTEMENT"

                # 2. Requête miroir
                cash_query = text("""
                    INSERT INTO public.mouvement_mvt
                        (pdt_id, mvt_date, mvt_nb_parts, mvt_frais, mvt_type_mouvement, mvt_prix)
                    VALUES
                        (:pdt_id, :mvt_date, :nb_parts, 0, :type_mvt, 1)
                """)
                conn.execute(cash_query, {
                    "pdt_id": cash_product_id, "mvt_date": op_date,
                    "nb_parts": cash_amount, "type_mvt": cash_type,
                })

        st.cache_data.clear()
        st.success("🚀 Données envoyées !")
        time.sleep(1)
        st.rerun()

st.divider()

# BOUTON ET ACTIVATION

_, col_btn, _ = st.columns(3)
with col_btn:
    if st.button("Enregistrer l'opération 💾", width='stretch'):
        # 1. Initialisation par défaut (pour le Cash)
        mirror_cash_id = None
        
        # 2. Logique spécifique aux Actions (Miroir + Frais)
        if selected_view == "📈 Titres":
            # On trouve l'ID de la poche cash
            mirror_cash_id = product_list_df[(product_list_df['ptf_id'] == portfolio_id) & (product_list_df['pdt_cash'] == True)]['pdt_id'].values[0]

        # 3. Appel de la fonction (mvt_frais sera soit 0 (Cash), soit le calcul ci-dessus)
        if None not in (shares, price, fees):
            confirm_operation(
                product_id, 
                movement_date, 
                shares, 
                fees, 
                movement_type, 
                price, 
                selected_view, 
                product_name, 
                mirror_cash_id
            )
        else:
            st.error("⚠️ Veuillez corriger les champs invalides avant d'enregistrer.")