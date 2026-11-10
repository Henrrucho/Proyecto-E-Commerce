"""Reglas con las que el dataset calcula sus columnas derivadas.

Se obtuvieron observando el CSV original (rangos mínimos y máximos por categoría) y se usan en dos
lugares: el generador de datos las aplica para que un dataset nuevo sea coherente, y una prueba
comprueba que reproducen las columnas del original.
"""
import numpy as np
import pandas as pd


def _cortes(valores, limites, etiquetas):
    """Etiqueta según el primer límite que el valor no supera (`limites` ascendentes; el límite pertenece al grupo inferior)."""
    idx = np.searchsorted(np.asarray(limites), np.asarray(valores), side="left")
    return np.asarray(etiquetas, dtype=object)[idx]


def age_group(age):
    return _cortes(age, [24, 34, 44, 54, 64], ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])


def satisfaction_level(score):
    mapa = {1: "Very Dissatisfied", 2: "Dissatisfied", 3: "Neutral", 4: "Satisfied", 5: "Very Satisfied"}
    return pd.Series(score).map(mapa).to_numpy(dtype=object)


def recency_score(days):
    return 5 - _cortes_num(days, [30, 60, 90, 180])


def frequency_score(purchases):
    return 1 + _cortes_num(purchases, [4, 19, 49, 99])


def monetary_score(spent):
    return 1 + _cortes_num(spent, [5000, 10000, 25000, 50000], derecha=False)


def _cortes_num(valores, limites, derecha=True):
    """Número de límites superados. Con derecha=True el límite pertenece al grupo inferior (<=)."""
    v = np.asarray(valores, dtype=float)
    lado = "left" if derecha else "right"
    return np.searchsorted(np.asarray(limites, dtype=float), v, side=lado)


def rfm_category(rfm_score):
    return _cortes(rfm_score, [5, 8, 10, 12], ["Need Attention", "At Risk", "Potential Loyalists", "Loyal", "Champions"])


def activity_status(days):
    return _cortes(days, [29, 59, 89], ["Active", "At Risk", "Dormant", "Inactive"])


def loyalty_tier(spent):
    nivel = _cortes(spent, [999.99, 4999.99, 9999.99, 24999.99, 49999.99], [None, "Bronze", "Silver", "Gold", "Platinum", "Diamond"])
    return nivel


def customer_value_category(spent):
    return _cortes(spent, [4999.99, 9999.99, 24999.99, 49999.99], ["Very Low", "Low", "Medium", "High", "Very High"])


def segment_category(spent, days):
    spent = np.asarray(spent, dtype=float)
    activo = np.asarray(days) <= 7  # en este campo "activo" es una compra en la última semana
    salida = np.empty(len(spent), dtype=object)
    salida[:] = "Low Value"
    salida[spent < 1000] = "Dormant"
    medio = (spent >= 5000) & (spent < 10000)
    alto = spent >= 10000
    salida[medio & activo] = "Medium Value Active"
    salida[medio & ~activo] = "Medium Value Inactive"
    salida[alto & activo] = "High Value Active"
    salida[alto & ~activo] = "High Value Inactive"
    return salida


def churn_risk_category(score):
    return _cortes(score, [20, 40, 60, 80], ["Very Low", "Low", "Medium", "High", "Very High"])


def health_status(score):
    return _cortes(score, [40, 60, 80], ["Poor", "Fair", "Good", "Excellent"])


def clv_category(clv):
    return _cortes(clv, [4999.99, 9999.99], ["Low CLV", "Medium CLV", "High CLV"])


def profitability_category(profit):
    return _cortes(profit, [-0.0001, 100, 500, 1000], ["Loss Making", "Break Even", "Low Profit", "Medium Profit", "High Profit"])


def engagement_level(open_rate, ctr):
    open_rate, ctr = np.asarray(open_rate), np.asarray(ctr)
    salida = np.full(len(open_rate), "Medium", dtype=object)
    salida[open_rate <= 0.3] = "Low"
    salida[(open_rate > 0.5) & (ctr > 0.2)] = "High"
    return salida


def behavior_segment(purchases, frequency):
    purchases = np.asarray(purchases)
    frecuente = np.isin(frequency, ["Daily", "Weekly"])
    regular = np.isin(frequency, ["Monthly", "Quarterly"])
    salida = np.full(len(purchases), "Occasional Buyer", dtype=object)
    salida[regular & (purchases >= 21)] = "Regular Buyer"
    salida[frecuente & (purchases >= 51)] = "Frequent Buyer"
    salida[purchases <= 5] = "New Buyer"
    return salida


def device_preference(device):
    mapa = {"Multiple": "Multi-Device", "Tablet": "Multi-Device", "Desktop": "Desktop-First", "Mobile": "Mobile-First"}
    return pd.Series(device).map(mapa).to_numpy(dtype=object)


# Coeficientes por mínimos cuadrados sobre el original (días, devoluciones, quejas, satisfacción, constante).
# En el original ambos puntajes llevan ruido (desviación residual ≈ 11 y ≈ 9), que el generador reproduce.
COEF_CHURN = (0.0931, 1.0565, 1.1310, -7.2683, 24.8845)
SD_CHURN = 11.17
COEF_HEALTH = (-0.0302, -0.3014, -0.4852, 9.0744, 67.5409)
SD_HEALTH = 8.82


def derivar(df, rng):
    """Calcula las columnas derivadas de un DataFrame que ya tiene las columnas base."""
    n = len(df)
    df["total_spent_usd"] = (df["total_purchases"] * df["avg_order_value_usd"]).round(2)
    df["age_group"] = age_group(df["age"])
    df["satisfaction_level"] = satisfaction_level(df["satisfaction_score"])
    df["recency_score"] = recency_score(df["days_since_last_purchase"])
    df["frequency_score"] = frequency_score(df["total_purchases"])
    df["monetary_score"] = monetary_score(df["total_spent_usd"])
    df["rfm_score"] = df["recency_score"] + df["frequency_score"] + df["monetary_score"]
    df["rfm_category"] = rfm_category(df["rfm_score"])
    df["activity_status"] = activity_status(df["days_since_last_purchase"])
    df["loyalty_tier"] = loyalty_tier(df["total_spent_usd"])
    df["customer_value_category"] = customer_value_category(df["total_spent_usd"])
    df["segment_category"] = segment_category(df["total_spent_usd"], df["days_since_last_purchase"])
    X = np.column_stack([df["days_since_last_purchase"], df["return_count"], df["complaint_count"], df["satisfaction_score"], np.ones(n)])
    df["churn_risk_score"] = np.clip(np.round(X @ np.array(COEF_CHURN) + rng.normal(0, SD_CHURN, n)), 0, 100).astype(int)
    df["customer_health_score"] = np.clip(np.round(X @ np.array(COEF_HEALTH) + rng.normal(0, SD_HEALTH, n)), 30, 100).astype(int)
    df["churn_risk_category"] = churn_risk_category(df["churn_risk_score"])
    df["health_status"] = health_status(df["customer_health_score"])
    df["customer_lifetime_value_usd"] = (df["total_spent_usd"] * rng.uniform(0.8, 1.5, n)).round(2)
    df["customer_profitability_usd"] = (df["customer_lifetime_value_usd"] - df["customer_acquisition_cost_usd"]).round(2)
    df["clv_category"] = clv_category(df["customer_lifetime_value_usd"])
    df["profitability_category"] = profitability_category(df["customer_profitability_usd"])
    df["engagement_level"] = engagement_level(df["email_open_rate"], df["click_through_rate"])
    df["behavior_segment"] = behavior_segment(df["total_purchases"], df["purchase_frequency"])
    df["device_preference"] = device_preference(df["device_used"])
    return df
