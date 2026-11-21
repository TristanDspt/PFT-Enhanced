# tests/test_st_logic.py

import pandas as pd
import pytest

from app.components import st_logic
from core.constants import MovementType


@pytest.fixture
def global_df():
    """Mini view_global_portefeuille : PEA en plus-value, CTO en moins-value,
    + un produit cash et un produit inactif."""
    return pd.DataFrame({
        "pdt_id":             [1, 2, 3, 4],
        "pdt_cash":           [False, False, True, False],
        "pdt_est_actif":      [True, True, True, False],
        "ptf_type_enveloppe": ["PEA", "CTO", "PEA", "PEA"],
        "capital_actuel":     [1100.0, 900.0, 500.0, 300.0],
        "profit_euro":        [100.0, -100.0, 0.0, 50.0],
    })


# ── get_net_capital ─────────────────────────────────────────────────────────────────────────────

def test_net_capital_taxes_gain(global_df):
    """Plus-value : l'impôt du PEA (18,6 %) est déduit du capital."""
    result = st_logic.get_net_capital(global_df, [1], {"PEA": 0.186, "CTO": 0.314})
    assert result[1] == pytest.approx(1100 - 100 * 0.186)


def test_net_capital_no_tax_on_loss(global_df):
    """Moins-value : aucun impôt, le capital net est le capital brut."""
    result = st_logic.get_net_capital(global_df, [2], {"PEA": 0.186, "CTO": 0.314})
    assert result[2] == pytest.approx(900.0)


@pytest.mark.parametrize("product_id", [3, 4], ids=["cash", "inactif"])
def test_net_capital_ignores_cash_and_inactive(global_df, product_id):
    """Un produit cash ou inactif est exclu du calcul : capital net = 0."""
    result = st_logic.get_net_capital(global_df, [product_id], {"PEA": 0.186})
    assert result[product_id] == 0.0


def test_net_capital_unknown_envelope_raises(global_df):
    """Une enveloppe absente de tax_rates lève une ValueError explicite."""
    with pytest.raises(ValueError, match="PEA"):
        st_logic.get_net_capital(global_df, [1], {"CTO": 0.314})


# ── get_portfolio_tri ─────────────────────────────────────────────────────────────────────────────

def test_portfolio_tri_simple_case(flows_df):
    """1000 € investis, 1100 € un an plus tard : TRI de 10 %."""
    df = pd.DataFrame({"ptf_id": [1], "capital_actuel": [1100.0]})
    result = st_logic.get_portfolio_tri(df, flows_df, [1], today=pd.Timestamp("2026-01-01"))
    assert result == pytest.approx(10.0, abs=0.01)


def test_portfolio_tri_ignores_transfert():
    """Un transfert entre deux produits du même portefeuille ne change pas le TRI :
    1000 € investis, 1130 € un an plus tard (800 + 330) : TRI de 13 %."""
    flows = pd.DataFrame({
        "ptf_id":             [1, 1, 1],
        "pdt_id":             [1, 1, 2],
        "mvt_type_mouvement": [MovementType.APPORT, MovementType.TRANSFERT, MovementType.TRANSFERT],
        "mvt_date":           [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-07-01"), pd.Timestamp("2025-07-01")],
        "amount":             [-1000.0, 300.0, -300.0],
    })
    df = pd.DataFrame({"ptf_id": [1, 1], "capital_actuel": [800.0, 330.0]})

    result = st_logic.get_portfolio_tri(df, flows, [1], today=pd.Timestamp("2026-01-01"))

    assert result == pytest.approx(13.0, abs=0.01)


# ── get_product_tri ───────────────────────────────────────────────────────────────────────────────

def test_product_tri_simple_case(flows_df):
    """1000 € investis, 1100 € un an plus tard : TRI de 10 %."""
    df = pd.DataFrame({"pdt_id": [1], "capital_actuel": [1100.0]})
    result = st_logic.get_product_tri(df, flows_df, [1], today=pd.Timestamp("2026-01-01"))
    assert result[1] == pytest.approx(10.0, abs=0.01)


def test_product_tri_ignores_achat():
    """Un flux ACHAT n'entre pas dans le TRI : même résultat qu'avec l'apport seul."""
    flows = pd.DataFrame({
        "ptf_id":             [1, 1],
        "pdt_id":             [1, 1],
        "mvt_type_mouvement": [MovementType.APPORT, MovementType.ACHAT],
        "mvt_date":           [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-07-01")],
        "amount":             [-1000.0, -500.0],
    })
    df = pd.DataFrame({"pdt_id": [1], "capital_actuel": [1100.0]})

    result = st_logic.get_product_tri(df, flows, [1], today=pd.Timestamp("2026-01-01"))

    assert result[1] == pytest.approx(10.0, abs=0.01)


def test_product_tri_includes_transfert():
    """Côté produit, un transfert entrant est un vrai flux :
    300 € reçus par transfert, 330 € un an plus tard : TRI de 10 %."""
    flows = pd.DataFrame({
        "ptf_id":             [1],
        "pdt_id":             [2],
        "mvt_type_mouvement": [MovementType.TRANSFERT],
        "mvt_date":           [pd.Timestamp("2025-01-01")],
        "amount":             [-300.0],
    })
    df = pd.DataFrame({"pdt_id": [2], "capital_actuel": [330.0]})

    result = st_logic.get_product_tri(df, flows, [2], today=pd.Timestamp("2026-01-01"))

    assert result[2] == pytest.approx(10.0, abs=0.01)