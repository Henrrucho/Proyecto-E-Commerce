"""Las reglas de derivación deben reproducir las columnas del dataset original."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data import reglas

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "E-commerce_Customer_Segmentation_2026.csv"
pytestmark = pytest.mark.skipif(not RAW.exists(), reason="falta el dataset original")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(RAW)


def coincide(esperado, obtenido):
    esperado = pd.Series(esperado).astype(object).where(pd.Series(esperado).notna(), None)
    obtenido = pd.Series(obtenido).astype(object).where(pd.Series(obtenido).notna(), None)
    return float((esperado.to_numpy() == obtenido.to_numpy()).mean())


@pytest.mark.parametrize("columna,calculo", [
    ("age_group", lambda d: reglas.age_group(d.age)),
    ("satisfaction_level", lambda d: reglas.satisfaction_level(d.satisfaction_score)),
    ("recency_score", lambda d: reglas.recency_score(d.days_since_last_purchase)),
    ("frequency_score", lambda d: reglas.frequency_score(d.total_purchases)),
    ("monetary_score", lambda d: reglas.monetary_score(d.total_spent_usd)),
    ("rfm_category", lambda d: reglas.rfm_category(d.rfm_score)),
    ("activity_status", lambda d: reglas.activity_status(d.days_since_last_purchase)),
    ("loyalty_tier", lambda d: reglas.loyalty_tier(d.total_spent_usd)),
    ("customer_value_category", lambda d: reglas.customer_value_category(d.total_spent_usd)),
    ("segment_category", lambda d: reglas.segment_category(d.total_spent_usd, d.days_since_last_purchase)),
    ("churn_risk_category", lambda d: reglas.churn_risk_category(d.churn_risk_score)),
    ("health_status", lambda d: reglas.health_status(d.customer_health_score)),
    ("clv_category", lambda d: reglas.clv_category(d.customer_lifetime_value_usd)),
    ("profitability_category", lambda d: reglas.profitability_category(d.customer_profitability_usd)),
    ("behavior_segment", lambda d: reglas.behavior_segment(d.total_purchases, d.purchase_frequency)),
    ("device_preference", lambda d: reglas.device_preference(d.device_used)),
])
def test_regla_reproduce_la_columna(df, columna, calculo):
    assert coincide(df[columna], calculo(df)) >= 0.999, columna


def test_engagement_es_aproximado(df):
    # La regla original combina más variables; esta aproximación acierta en la gran mayoría.
    assert coincide(df.engagement_level, reglas.engagement_level(df.email_open_rate, df.click_through_rate)) >= 0.90


def test_total_gastado_es_compras_por_valor_medio(df):
    assert np.allclose(df.total_spent_usd, df.total_purchases * df.avg_order_value_usd, atol=0.01)
