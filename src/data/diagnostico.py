"""Diagnóstico de los datos: ¿hay relaciones entre las variables que puedan formar grupos?

Mide tres cosas y deja la evidencia en reports/ para que el documento cite cifras reales:
  1. Correlación de Pearson (relación lineal) entre las 8 numéricas de la Entrega 2.
  2. Correlación de Spearman (relación monótona, por rangos) entre las mismas.
  3. Razón de correlación (eta) entre cada columna categórica y cada variable conductual: 0 = la
     categoría no explica nada de la variable, 1 = la explica por completo.
Para cada medida también se calcula el ruido esperado: con n filas e independencia total, una
correlación de Pearson típica vale ±1/√n, y un eta² típico vale (categorías − 1)/(n − 1).
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import config_columns as cfg
from src.data import preprocess

CATEGORICAS = list(cfg.ORDINALS) + [c for c in cfg.NOMINALS if c != "region"] + ["country", "preferred_category_1"]


def razon_correlacion(categoria, valores):
    """eta = sqrt(SS_entre_grupos / SS_total): cuánto de la variación de `valores` explica la categoría."""
    valores = pd.Series(np.asarray(valores, dtype=float))
    grupos = valores.groupby(np.asarray(categoria))
    media = valores.mean()
    entre = (grupos.count() * (grupos.mean() - media) ** 2).sum()
    total = ((valores - media) ** 2).sum()
    return float(np.sqrt(entre / total)) if total else 0.0


def diagnosticar(df):
    n = len(df)
    A = cfg.FEATURES_A
    pearson, spearman = df[A].corr(), df[A].corr(method="spearman")
    i, j = np.triu_indices(len(A), k=1)
    pares = pd.DataFrame({"variable_1": [A[k] for k in i], "variable_2": [A[k] for k in j],
                          "pearson": pearson.to_numpy()[i, j], "spearman": spearman.to_numpy()[i, j]})
    pares["abs_pearson"] = pares.pearson.abs()
    peor = pares.loc[pares.abs_pearson.idxmax()]

    conductuales, _ = preprocess.construir_features(df, "B")
    filas = []
    for col in CATEGORICAS:
        k = df[col].nunique()
        piso = float(np.sqrt((k - 1) / (n - 1)))  # eta esperado por puro azar
        for var in conductuales.columns:
            filas.append({"categoria": col, "variable": var, "eta": razon_correlacion(df[col], conductuales[var]),
                          "eta_esperado_por_azar": piso, "categorias": int(k)})
    etas = pd.DataFrame(filas)
    mejor_eta = etas.loc[etas.eta.idxmax()]
    return {
        "filas": int(n),
        "pearson": pearson, "pares": pares, "etas": etas,
        "resumen": {
            "filas": int(n),
            "variables_numericas": A,
            "pearson_max_abs": float(peor.abs_pearson),
            "pearson_max_par": [peor.variable_1, peor.variable_2],
            "spearman_max_abs": float(pares.spearman.abs().max()),
            "ruido_esperado_pearson": float(1 / np.sqrt(n)),
            "eta_max": float(mejor_eta.eta),
            "eta_max_par": [mejor_eta.categoria, mejor_eta.variable],
            "eta_max_esperado_por_azar": float(mejor_eta.eta_esperado_por_azar),
            "pares_categoria_variable": int(len(etas)),
        },
    }


def guardar(resultado, carpeta):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    resultado["pearson"].to_csv(carpeta / "correlaciones_pearson.csv")
    resultado["pares"].sort_values("abs_pearson", ascending=False).to_csv(carpeta / "correlaciones_pares.csv", index=False)
    resultado["etas"].sort_values("eta", ascending=False).to_csv(carpeta / "correlaciones_categoricas.csv", index=False)
    (carpeta / "correlaciones.json").write_text(json.dumps(resultado["resumen"], ensure_ascii=False, indent=1), encoding="utf-8")
    m = resultado["pearson"]
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    im = ax.imshow(m.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(m)), m.columns, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(len(m)), m.index, fontsize=8)
    for a in range(len(m)):
        for b in range(len(m)):
            ax.text(b, a, f"{m.iat[a, b]:.2f}", ha="center", va="center", fontsize=7)
    ax.set_title("Correlación de Pearson entre las 8 numéricas")
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(carpeta / "correlaciones.png", dpi=130)
    plt.close(fig)
