"""Preprocesamiento: validación, limpieza, construcción de variables, escalado y PCA.

El CSV original no se modifica: toda la limpieza ocurre en memoria cada vez que se corre el
pipeline, y las transformaciones se ajustan solo con el conjunto de entrenamiento.
"""
from dataclasses import dataclass, field

# joblib serializa con pickle: la plantilla exige guardar los modelos en disco, y solo se cargan
# artefactos generados por este mismo proyecto (carpeta models/). No cargar .joblib de fuentes ajenas.
import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src import config_columns as cfg


# ---------------------------------------------------------------- carga y limpieza
def cargar_y_validar(ruta):
    """Lee el CSV y verifica que tenga exactamente las 53 columnas esperadas."""
    df = pd.read_csv(ruta)
    faltan = [c for c in cfg.EXPECTED_COLUMNS if c not in df.columns]
    sobran = [c for c in df.columns if c not in cfg.EXPECTED_COLUMNS]
    if faltan or sobran:
        raise ValueError(f"El CSV no cumple el esquema. Faltan: {faltan}. Sobran: {sobran}.")
    return df


def limpiar(df):
    """Quita duplicados e imputa los nulos conocidos. Devuelve (DataFrame, informe)."""
    informe = {"filas_iniciales": int(len(df)), "columnas": int(df.shape[1])}
    antes = len(df)
    df = df.drop_duplicates(subset="customer_id").reset_index(drop=True)
    informe["duplicados_eliminados"] = int(antes - len(df))
    informe["nulos_imputados"] = {c: int(df[c].isna().sum()) for c in cfg.NULL_FILL}
    informe["nulos_imputados"]["loyalty_tier"] = int(df["loyalty_tier"].isna().sum())
    df = df.fillna(cfg.NULL_FILL)
    df["loyalty_tier"] = df["loyalty_tier"].fillna("No Tier")
    informe["nulos_restantes"] = int(df.isna().sum().sum())
    informe["filas_finales"] = int(len(df))
    informe["columnas_derivadas_excluidas"] = len(cfg.DERIVED_COLUMNS)
    informe["columnas_sin_valor_excluidas"] = len(cfg.IGNORED_COLUMNS)
    return df, informe


def particionar(df, semilla=cfg.SEED, test_size=cfg.TEST_SIZE):
    """Partición 80/20 con semilla fija (la misma para todos los experimentos)."""
    train, test = train_test_split(df, test_size=test_size, random_state=semilla, shuffle=True)
    return train.reset_index(drop=True), test.reset_index(drop=True)


# ---------------------------------------------------------------- construcción de variables
def columnas_requeridas(conjunto):
    """Columnas base que debe traer un registro para poder calcular el conjunto de variables."""
    if conjunto in ("A", "B"):
        return list(cfg.REQUIRED_BASE[conjunto])
    base = list(cfg.REQUIRED_BASE["B"]) + list(cfg.ORDINALS) + list(cfg.NOMINALS) + ["country"]
    base += ["preferred_category_1", "preferred_category_2", "preferred_category_3", "social_media_presence"]
    return [c for c in dict.fromkeys(base) if c != "region"]


def _bloque_categorico(df):
    """Devuelve las columnas 0/1 u ordinales del bloque categórico y el bloque de cada una."""
    cols, bloques = {}, {}
    for col, orden in cfg.ORDINALS.items():
        cols[f"{col}_ord"] = df[col].map({v: i + 1 for i, v in enumerate(orden)}).astype(float)
        bloques[f"{col}_ord"] = "ordinales"
    region = df["country"].map(cfg.REGION_BY_COUNTRY).fillna("Asia")
    fuente = {**{c: df[c] for c in cfg.NOMINALS if c != "region"}, "region": region}
    for col, valores in cfg.NOMINALS.items():
        for v in valores:
            cols[f"{col}={v}"] = (fuente[col] == v).astype(float)
            bloques[f"{col}={v}"] = "nominales"
    for categoria in cfg.CATEGORIES:
        peso = np.zeros(len(df))
        for k, w in enumerate(cfg.CATEGORY_WEIGHTS, start=1):
            peso = np.where(df[f"preferred_category_{k}"] == categoria, np.maximum(peso, w), peso)
        cols[f"cat={categoria}"] = peso
        bloques[f"cat={categoria}"] = "categorias"
    redes = df["social_media_presence"].fillna("None").astype(str)
    for red in cfg.SOCIAL_NETWORKS:
        cols[f"red={red}"] = redes.str.contains(red, regex=False).astype(float)
        bloques[f"red={red}"] = "redes"
    return pd.DataFrame(cols, index=df.index), bloques


def construir_features(df, conjunto):
    """Matriz de variables de entrada (solo columnas base) y el bloque de cada columna."""
    faltan = [c for c in columnas_requeridas(conjunto) if c not in df.columns]
    if faltan:
        raise ValueError(f"Faltan campos para el conjunto {conjunto}: {faltan}")
    if conjunto == "A":
        return df[cfg.FEATURES_A].astype(float), {c: "numericas" for c in cfg.FEATURES_A}
    compras = df["total_purchases"].astype(float)
    base = pd.DataFrame({
        "recencia_dias": df["days_since_last_purchase"].astype(float),
        # Las dos razones tienen colas muy pesadas (una compra en un mes, 19 devoluciones sobre 1 compra): se usa log(1 + x).
        "log_compras_por_mes": np.log1p(compras / df["tenure_months"].clip(lower=1)),
        "avg_order_value_usd": df["avg_order_value_usd"].astype(float),
        "log_tasa_devoluciones": np.log1p(df["return_count"] / compras.clip(lower=1)),
        "complaint_count": df["complaint_count"].astype(float),
        "satisfaction_score": df["satisfaction_score"].astype(float),
    }, index=df.index)
    bloques = {c: "numericas" for c in base.columns}
    if conjunto == "B":
        return base, bloques
    extra, bloques_extra = _bloque_categorico(df)
    return pd.concat([base, extra], axis=1), {**bloques, **bloques_extra}


# ---------------------------------------------------------------- escalado + PCA
@dataclass
class Preprocesador:
    """Estandariza, pondera los bloques categóricos y proyecta con PCA."""
    conjunto: str = "B"
    varianza_pca: float = 0.95
    columnas: list = field(default_factory=list)
    pesos: np.ndarray = None
    scaler: StandardScaler = None
    pca: PCA = None

    def fit(self, df):
        X, bloques = construir_features(df, self.conjunto)
        self.columnas = list(X.columns)
        ancho = pd.Series(bloques).value_counts()
        # Cada bloque categórico pesa como una sola variable: sus columnas se dividen por sqrt(ancho).
        self.pesos = np.array([1.0 if bloques[c] == "numericas" else 1.0 / np.sqrt(ancho[bloques[c]]) for c in self.columnas])
        self.scaler = StandardScaler().fit(X.to_numpy())
        Z = self.scaler.transform(X.to_numpy()) * self.pesos
        self.pca = PCA(n_components=self.varianza_pca, svd_solver="full", random_state=cfg.SEED).fit(Z)
        return self

    def escalar(self, df):
        X, _ = construir_features(df, self.conjunto)
        return self.scaler.transform(X[self.columnas].to_numpy()) * self.pesos

    def transform(self, df):
        return self.pca.transform(self.escalar(df))

    def guardar(self, carpeta, sufijo=""):
        joblib.dump(self, f"{carpeta}/preprocesador{sufijo}.joblib")
        joblib.dump(self.scaler, f"{carpeta}/scaler{sufijo}.joblib")
        joblib.dump(self.pca, f"{carpeta}/pca{sufijo}.joblib")


def cargar_preprocesador(ruta):
    return joblib.load(ruta)
