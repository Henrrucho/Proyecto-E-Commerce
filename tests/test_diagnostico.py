import numpy as np
import pandas as pd

from src.data import diagnostico, generate, preprocess


def test_razon_de_correlacion_en_los_extremos():
    categoria = np.repeat(["a", "b", "c"], 100)
    assert diagnostico.razon_correlacion(categoria, np.repeat([1.0, 5.0, 9.0], 100)) == 1.0
    rng = np.random.default_rng(0)
    assert diagnostico.razon_correlacion(rng.choice(["a", "b", "c"], 30000), rng.normal(size=30000)) < 0.03


def test_datos_independientes_tienen_correlaciones_de_ruido():
    df, _ = generate.generar(20000, semilla=1, estructura=0)
    r = diagnostico.diagnosticar(preprocess.limpiar(df)[0])["resumen"]
    assert r["pearson_max_abs"] < 5 * r["ruido_esperado_pearson"]
    assert r["eta_max"] < 3 * r["eta_max_esperado_por_azar"] + 0.02


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
