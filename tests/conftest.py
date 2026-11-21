# tests/conftest.py

import pandas as pd
import pytest

from core.constants import MovementType


@pytest.fixture
def flows_df():
    """Flux fictifs : un apport de 1000 € sur le produit 1 (PEA, ptf 1)."""
    return pd.DataFrame({
        "ptf_id":             [1],
        "pdt_id":             [1],
        "mvt_type_mouvement": [MovementType.APPORT],
        "mvt_date":           [pd.Timestamp("2025-01-01")],
        "amount":             [-1000.0],
    })