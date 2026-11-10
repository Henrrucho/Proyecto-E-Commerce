"""Generador de datasets sintéticos con el mismo esquema de 53 columnas del original.

Uso:
    python -m src.data.generate                       # pregunta "N. de filas:"
    python -m src.data.generate --rows 5000 --seed 7 --estructura 0.6

Sin --seed se elige una semilla al azar, se imprime y queda en el nombre del archivo, de modo que
cualquier corrida se puede repetir. Con --estructura 0 cada columna se sortea por separado (como en
el dataset original, donde las variables son independientes). Con valores mayores, esa fracción de
los clientes sigue un arquetipo (grupos de rasgos que van juntos). El arquetipo de cada cliente NO se
escribe en el CSV: va en un archivo aparte (*_arquetipos.csv) para poder calificar al modelo después.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src import config_columns as cfg
from src.data import reglas

RAIZ = Path(__file__).resolve().parents[2]
PERFIL = Path(__file__).with_name("perfil_referencia.json")
RAW = RAIZ / "data" / "raw" / "E-commerce_Customer_Segmentation_2026.csv"

COLUMNAS_PERFIL = [
    "gender", "income_bracket", "education_level", "employment_type", "marital_status", "shopping_channel",
    "device_used", "payment_method", "purchase_frequency", "customer_segment", "preferred_category_1",
]


def construir_perfil(ruta_csv=RAW, salida=PERFIL):
    """Guarda las proporciones del dataset original (lo único que el generador toma de él)."""
    df = pd.read_csv(ruta_csv)
    perfil = {c: df[c].value_counts(normalize=True).round(6).to_dict() for c in COLUMNAS_PERFIL}
    pares = df.groupby(["country", "city"]).size().reset_index(name="n")
    pares["p"] = (pares["n"] / pares["n"].sum()).round(8)
    perfil["country_city"] = pares[["country", "city", "p"]].values.tolist()
    perfil["p_cat2"] = float(df.preferred_category_2.notna().mean())
    perfil["p_cat3_dado_cat2"] = float(df.preferred_category_3.notna().sum() / df.preferred_category_2.notna().sum())
    perfil["p_social"] = float(df.social_media_presence.notna().mean())
    Path(salida).write_text(json.dumps(perfil, ensure_ascii=False, indent=1), encoding="utf-8")
    return perfil


def cargar_perfil():
    if not PERFIL.exists():
        construir_perfil()
    return json.loads(PERFIL.read_text(encoding="utf-8"))


def _elegir(rng, tabla, n):
    valores, probs = list(tabla.keys()), np.array(list(tabla.values()), dtype=float)
    return rng.choice(valores, size=n, p=probs / probs.sum())


# Cada arquetipo fija rangos de las variables conductuales y favorece a algunas categorías.
ARQUETIPOS = {
    "leal_frecuente": dict(tenure=(40, 119), purchases=(110, 199), aov=(300, 1000), days=(0, 20), returns=(0, 6), complaints=(0, 4),
                           satisfaction=[4, 5], income_alto=True, categorias=["Electronics", "Home & Kitchen"]),
    "ocasional_gastador": dict(tenure=(10, 119), purchases=(5, 60), aov=(500, 1000), days=(20, 120), returns=(3, 12), complaints=(2, 9),
                               satisfaction=[3, 4], income_alto=True, categorias=["Fashion", "Beauty"]),
    "en_riesgo": dict(tenure=(20, 119), purchases=(40, 199), aov=(50, 600), days=(90, 365), returns=(8, 19), complaints=(7, 14),
                      satisfaction=[1, 2], income_alto=False, categorias=["Grocery", "Automotive"]),
    "nuevo": dict(tenure=(1, 12), purchases=(0, 15), aov=(10, 400), days=(0, 60), returns=(0, 5), complaints=(0, 6),
                  satisfaction=[3, 4, 5], income_alto=False, categorias=["Books", "Toys"]),
    "ahorrador_regular": dict(tenure=(15, 119), purchases=(20, 100), aov=(10, 250), days=(0, 60), returns=(0, 10), complaints=(0, 8),
                              satisfaction=[3, 4], income_alto=False, categorias=["Office Supplies", "Pet Supplies"]),
}


def _aplicar_arquetipos(df, rng, estructura, perfil):
    n = len(df)
    nombres = list(ARQUETIPOS)
    asignado = np.where(rng.random(n) < estructura, rng.integers(0, len(nombres), n), -1)
    etiquetas = np.array(["ruido"] + nombres, dtype=object)[asignado + 1]
    ingresos = cfg.ORDINALS["income_bracket"]
    for i, nombre in enumerate(nombres):
        idx = np.flatnonzero(asignado == i)
        if not len(idx):
            continue
        a = ARQUETIPOS[nombre]
        m = len(idx)
        df.loc[idx, "tenure_months"] = rng.integers(a["tenure"][0], a["tenure"][1] + 1, m)
        df.loc[idx, "total_purchases"] = rng.integers(a["purchases"][0], a["purchases"][1] + 1, m)
        df.loc[idx, "avg_order_value_usd"] = rng.uniform(a["aov"][0], a["aov"][1], m).round(2)
        df.loc[idx, "days_since_last_purchase"] = rng.integers(a["days"][0], a["days"][1] + 1, m)
        df.loc[idx, "return_count"] = rng.integers(a["returns"][0], a["returns"][1] + 1, m)
        df.loc[idx, "complaint_count"] = rng.integers(a["complaints"][0], a["complaints"][1] + 1, m)
        df.loc[idx, "satisfaction_score"] = rng.choice(a["satisfaction"], m)
        df.loc[idx, "income_bracket"] = rng.choice(ingresos[3:] if a["income_alto"] else ingresos[:3], m)
        favorece = rng.random(m) < 0.7
        df.loc[idx[favorece], "preferred_category_1"] = rng.choice(a["categorias"], int(favorece.sum()))
    return etiquetas


def generar(filas, semilla=None, estructura=0.0):
    """Devuelve (DataFrame de 53 columnas, Serie con el arquetipo de cada cliente)."""
    if semilla is None:
        semilla = int(np.random.SeedSequence().entropy % 1_000_000)
    rng = np.random.default_rng(semilla)
    perfil = cargar_perfil()
    n = int(filas)
    df = pd.DataFrame({"customer_id": [f"CUST-{i + 1:06d}" for i in range(n)]})

    grupo = rng.integers(0, 6, n)
    limites = [(18, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 84)]
    df["age"] = [int(rng.integers(limites[g][0], limites[g][1] + 1)) for g in grupo]
    for col in ["gender", "income_bracket", "education_level", "employment_type", "marital_status", "shopping_channel",
                "device_used", "payment_method", "purchase_frequency", "customer_segment"]:
        df[col] = _elegir(rng, perfil[col], n)
    pares = perfil["country_city"]
    probs = np.array([p[2] for p in pares])
    elegido = rng.choice(len(pares), size=n, p=probs / probs.sum())
    df["country"] = [pares[i][0] for i in elegido]
    df["city"] = [pares[i][1] for i in elegido]

    df["tenure_months"] = rng.integers(1, 120, n)
    df["total_purchases"] = rng.integers(0, 200, n)
    df["avg_order_value_usd"] = rng.uniform(10, 1000, n).round(2)
    df["days_since_last_purchase"] = rng.choice([0, 1], n)  # se reemplaza abajo
    bins = [(0, 30, 0.5968), (31, 60, 0.0998), (61, 90, 0.0998), (91, 180, 0.0681), (181, 365, 0.1356)]
    cual = rng.choice(len(bins), size=n, p=np.array([b[2] for b in bins]) / sum(b[2] for b in bins))
    df["days_since_last_purchase"] = [int(rng.integers(bins[c][0], bins[c][1] + 1)) for c in cual]
    df["return_count"] = rng.integers(0, 20, n)
    df["complaint_count"] = rng.integers(0, 15, n)
    df["satisfaction_score"] = rng.integers(1, 6, n)
    df["email_open_rate"] = rng.uniform(0, 1, n).round(3)
    df["click_through_rate"] = rng.uniform(0, 0.5, n).round(3)
    df["conversion_rate"] = rng.uniform(0, 0.3, n).round(3)
    df["customer_acquisition_cost_usd"] = rng.uniform(5, 200, n).round(2)
    df["dataset_year"] = 2026

    cat1 = _elegir(rng, perfil["preferred_category_1"], n)
    df["preferred_category_1"] = cat1
    cats = np.array(cfg.CATEGORIES, dtype=object)
    cat2 = np.empty(n, dtype=object)
    cat3 = np.empty(n, dtype=object)
    tiene2 = rng.random(n) < perfil["p_cat2"]
    tiene3 = tiene2 & (rng.random(n) < perfil["p_cat3_dado_cat2"])
    for i in range(n):
        libres = [c for c in cats if c != cat1[i]]
        cat2[i] = rng.choice(libres) if tiene2[i] else None
        if tiene3[i]:
            cat3[i] = rng.choice([c for c in libres if c != cat2[i]])
    df["preferred_category_2"], df["preferred_category_3"] = cat2, cat3

    redes = np.array(cfg.SOCIAL_NETWORKS, dtype=object)
    social = np.empty(n, dtype=object)
    con_social = rng.random(n) < perfil["p_social"]
    cuantas = rng.integers(1, 4, n)
    for i in np.flatnonzero(con_social):
        social[i] = ", ".join(rng.choice(redes, size=cuantas[i], replace=False))
    df["social_media_presence"] = social

    etiquetas = _aplicar_arquetipos(df, rng, float(estructura), perfil) if estructura > 0 else np.array(["ruido"] * n, dtype=object)
    reglas.derivar(df, rng)
    df = df[cfg.EXPECTED_COLUMNS]
    return df, pd.Series(etiquetas, index=df["customer_id"], name="arquetipo")


def main(argv=None):
    p = argparse.ArgumentParser(description="Genera un dataset sintético de clientes con el esquema de 53 columnas.")
    p.add_argument("--rows", type=int, help="número de filas (si se omite, se pregunta)")
    p.add_argument("--seed", type=int, help="semilla (si se omite, se elige al azar y se imprime)")
    p.add_argument("--estructura", type=float, default=0.0, help="0 a 1: fracción de clientes que siguen un arquetipo")
    p.add_argument("--output", help="ruta del CSV (por defecto data/generated/)")
    p.add_argument("--rebuild-profile", action="store_true", help="reconstruye perfil_referencia.json desde data/raw")
    a = p.parse_args(argv)
    if a.rebuild_profile:
        construir_perfil()
        print("perfil_referencia.json reconstruido")
        return
    filas = a.rows if a.rows is not None else int(input("N. de filas: "))
    if filas < 1:
        raise SystemExit("El número de filas debe ser positivo.")
    if not 0 <= a.estructura <= 1:
        raise SystemExit("--estructura debe estar entre 0 y 1.")
    semilla = a.seed if a.seed is not None else int(np.random.SeedSequence().entropy % 1_000_000)
    df, arquetipos = generar(filas, semilla, a.estructura)
    salida = Path(a.output) if a.output else RAIZ / "data" / "generated" / f"clientes_{filas}_s{semilla}_e{a.estructura:g}.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(salida, index=False)
    print(f"Filas: {len(df)} | columnas: {df.shape[1]} | semilla: {semilla} | estructura: {a.estructura:g}")
    print(f"Archivo: {salida}")
    if a.estructura > 0:
        lado = salida.with_name(salida.stem + "_arquetipos.csv")
        arquetipos.to_csv(lado)
        print(f"Arquetipos (solo para evaluar, no para entrenar): {lado}")


if __name__ == "__main__":
    main()
