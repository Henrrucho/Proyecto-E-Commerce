import numpy as np
import pandas as pd

from src.data import diagnostico, generate, preprocess


def test_razon_de_correlacion_en_los_extremos():
    categoria = np.repeat(["a", "b", "c"], 100)
    assert diagnostico.razon_correlacion(categoria, np.repeat([1.0, 5.0, 9.0], 100)) == 1.0
    rng = np.random.default_rng(0)
    assert diagnostico.razon_correlacion(rng.choice(["a", "b", "c"], 30000), rng.normal(size=30000)) < 0.03


def test_datos_sin_estructura_solo_tienen_la_relacion_frecuencia_recencia():
    df, _ = generate.generar(20000, semilla=1, estructura=0)
    dx = diagnostico.diagnosticar(preprocess.limpiar(df)[0])
    r, etas = dx["resumen"], dx["etas"]
    assert r["pearson_max_abs"] < 5 * r["ruido_esperado_pearson"]  # las 8 numéricas son independientes
    assert r["eta_max_par"] == ["purchase_frequency", "recencia_dias"] and r["eta_max"] > 0.9
    resto = etas[~((etas.categoria == "purchase_frequency") & (etas.variable == "recencia_dias"))]
    assert resto.eta.max() < 0.08  # ninguna otra categoría explica nada


def test_datos_con_estructura_muestran_correlaciones_claras():
    df, _ = generate.generar(5000, semilla=1, estructura=1.0)
    r = diagnostico.diagnosticar(preprocess.limpiar(df)[0])["resumen"]
    assert r["pearson_max_abs"] > 0.25


def test_se_guardan_los_reportes(tmp_path):
    df, _ = generate.generar(800, semilla=2)
    diagnostico.guardar(diagnostico.diagnosticar(preprocess.limpiar(df)[0]), tmp_path)
    for archivo in ("correlaciones.json", "correlaciones_pearson.csv", "correlaciones_pares.csv", "correlaciones_categoricas.csv", "correlaciones.png"):
        assert (tmp_path / archivo).exists()
    assert pd.read_csv(tmp_path / "correlaciones_pearson.csv", index_col=0).shape == (8, 8)
