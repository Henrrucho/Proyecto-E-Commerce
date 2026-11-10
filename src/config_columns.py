"""Columnas del dataset y su papel en el modelo.

Las columnas derivadas son fórmulas de las columnas base (por ejemplo `activity_status` son
cortes de `days_since_last_purchase`). Usarlas como entrada haría que el modelo reaprendiera
la regla y no un patrón de los clientes, así que quedan fuera de todas las variables de entrada
y solo se leen para comparar contra la segmentación por reglas.
"""

EXPECTED_COLUMNS = [
    "customer_id", "customer_segment", "segment_category", "age", "age_group", "gender", "country", "city",
    "income_bracket", "education_level", "employment_type", "marital_status", "tenure_months",
    "total_purchases", "avg_order_value_usd", "total_spent_usd", "purchase_frequency",
    "days_since_last_purchase", "preferred_category_1", "preferred_category_2", "preferred_category_3",
    "shopping_channel", "device_used", "payment_method", "return_count", "complaint_count",
    "satisfaction_score", "satisfaction_level", "loyalty_tier", "email_open_rate", "click_through_rate",
    "conversion_rate", "social_media_presence", "customer_lifetime_value_usd",
    "customer_acquisition_cost_usd", "customer_profitability_usd", "recency_score", "frequency_score",
    "monetary_score", "rfm_score", "churn_risk_score", "customer_health_score", "dataset_year",
    "customer_value_category", "activity_status", "health_status", "churn_risk_category", "rfm_category",
    "profitability_category", "engagement_level", "behavior_segment", "device_preference", "clv_category",
]

# Columnas calculadas a partir de otras. Quedan excluidas de las entradas del modelo.
DERIVED_COLUMNS = [
    "customer_segment", "segment_category", "age_group", "satisfaction_level", "loyalty_tier",
    "customer_value_category", "total_spent_usd", "customer_lifetime_value_usd",
    "customer_profitability_usd", "recency_score", "frequency_score", "monetary_score", "rfm_score",
    "churn_risk_score", "customer_health_score", "activity_status", "health_status",
    "churn_risk_category", "rfm_category", "profitability_category", "engagement_level",
    "behavior_segment", "device_preference", "clv_category",
]

# Sin valor para el modelo: identificador y constante.
IGNORED_COLUMNS = ["customer_id", "dataset_year", "customer_acquisition_cost_usd", "city"]

# Valores que se imputan (nulos reales del dataset).
NULL_FILL = {
    "preferred_category_2": "None",
    "preferred_category_3": "None",
    "social_media_presence": "None",
}

# Conjunto A: las 8 variables numéricas comprometidas en la Entrega 2.
FEATURES_A = [
    "age", "tenure_months", "total_purchases", "avg_order_value_usd", "days_since_last_purchase",
    "return_count", "complaint_count", "satisfaction_score",
]
# Conjunto B: variables conductuales (se construyen en preprocess.py a partir de columnas base).
FEATURES_B = [
    "recencia_dias", "log_compras_por_mes", "avg_order_value_usd", "log_tasa_devoluciones", "complaint_count",
    "satisfaction_score",
]
# Columnas base que necesita cada conjunto para poder calcularse.
REQUIRED_BASE = {
    "A": FEATURES_A,
    "B": ["days_since_last_purchase", "total_purchases", "tenure_months", "avg_order_value_usd",
          "return_count", "complaint_count", "satisfaction_score"],
}

# Conjunto C = B + bloque categórico.
ORDINALS = {
    "income_bracket": ["0-25K", "25K-50K", "50K-75K", "75K-100K", "100K-150K", "150K+"],
    # Supuesto: Professional (posgrado profesional) se ubica entre Masters y PhD.
    "education_level": ["High School", "Bachelors", "Masters", "Professional", "PhD"],
    "purchase_frequency": ["Rarely", "Quarterly", "Monthly", "Weekly", "Daily"],
}
NOMINALS = {
    "gender": ["Female", "Male"],
    "marital_status": ["Divorced", "Married", "Single", "Widowed"],
    "employment_type": ["Employed", "Retired", "Self-Employed", "Student", "Unemployed"],
    "shopping_channel": ["In-Store", "Marketplace", "Mobile App", "Online"],
    "device_used": ["Desktop", "Mobile", "Multiple", "Tablet"],
    "payment_method": ["Bank Transfer", "Cash on Delivery", "Credit Card", "Debit Card", "Digital Wallet"],
    "region": ["Asia", "Europa", "Norteamérica", "Latinoamérica", "Medio Oriente", "Oceanía"],
}
CATEGORIES = [
    "Automotive", "Beauty", "Books", "Electronics", "Fashion", "Grocery", "Home & Kitchen",
    "Office Supplies", "Pet Supplies", "Sports & Fitness", "Toys", "Health & Personal Care",
]
CATEGORY_WEIGHTS = [1.0, 0.6, 0.3]
SOCIAL_NETWORKS = ["Facebook", "Instagram", "LinkedIn", "TikTok", "Twitter", "YouTube"]

REGION_BY_COUNTRY = {
    "United States": "Norteamérica", "Canada": "Norteamérica", "Mexico": "Latinoamérica",
    "Brazil": "Latinoamérica", "United Kingdom": "Europa", "Germany": "Europa", "France": "Europa",
    "Spain": "Europa", "Italy": "Europa", "Netherlands": "Europa", "Pakistan": "Asia", "India": "Asia",
    "Japan": "Asia", "Singapore": "Asia", "Saudi Arabia": "Medio Oriente",
    "United Arab Emirates": "Medio Oriente", "Australia": "Oceanía",
}

SEED = 42
TEST_SIZE = 0.20
