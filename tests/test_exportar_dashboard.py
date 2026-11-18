"""El dashboard solo presenta lo que exporta el motor: estas pruebas comprueban que lo exportado es fiel al modelo."""
import json

import joblib
import numpy as np
import pytest

from src.models import exportar_dashboard as ed

RAIZ = ed.RAIZ


@pytest.fixture(scope="module")
def corrida():
    modelo = joblib.load(RAIZ / "models" / "modelo_candidato.joblib")
    pre = joblib.load(RAIZ / "models" / "preprocesador.joblib")
    df, asign = ed.cargar()
    gs = ed.grupos(df, modelo)
    return {"modelo": modelo, "pre": pre, "df": df, "asign": asign, "gs": gs}


def test_cada_cliente_tiene_un_grupo_y_los_conteos_cuadran(corrida):
    df, gs = corrida["df"], corrida["gs"]
    assert len(df) == 50000 and df["cluster"].between(0, corrida["modelo"]["k"] - 1).all()
    assert sum(g["clientes"] for g in gs) == len(df)
    assert sum(g["porcentaje"] for g in gs) == pytest.approx(100, abs=0.2)
    assert sum(g["porcentajeGasto"] for g in gs) == pytest.approx(100, abs=0.2)


def test_modelo_exportado_reproduce_las_asignaciones_de_python(corrida):
    """Aplica solo las fórmulas de model.json (las mismas que implementa el navegador) y compara con predecir_lote."""
    mj = ed.modelo_navegador(corrida["modelo"], corrida["pre"], corrida["gs"], corrida["df"])
    m = corrida["df"].sample(3000, random_state=3)
    compras = m["total_purchases"].to_numpy(float)
    x = np.column_stack([
        m["days_since_last_purchase"], np.log1p(compras / np.maximum(m["tenure_months"], 1)), m["avg_order_value_usd"],
        np.log1p(m["return_count"] / (compras + 5)), m["complaint_count"], m["satisfaction_score"],
    ])
    z = (x - np.array(mj["scaler"]["mean"])) / np.array(mj["scaler"]["scale"]) * np.array(mj["pesos"])
    y = (z - np.array(mj["pca"]["mean"])) @ np.array(mj["pca"]["components"]).T
    d = np.linalg.norm(y[:, None, :] - np.array(mj["centroides"])[None, :, :], axis=2)
    assert (d.argmin(axis=1) == m["cluster"].to_numpy()).all()
    assert np.allclose(d.min(axis=1), m["distancia"].to_numpy(), atol=1e-3)


def test_los_archivos_publicados_corresponden_al_modelo_actual(corrida):
    publico = ed.PUBLIC
    dash = json.loads((publico / "data" / "dashboard.json").read_text(encoding="utf-8"))
    assert [g["clientes"] for g in dash["clusters"]] == [g["clientes"] for g in corrida["gs"]]
    assert dash["meta"]["clientes"] == 50000
    clientes = json.loads((publico / "data" / "customers.json").read_text(encoding="utf-8"))
    assert len(clientes["rows"]) == 50000 and len({r[0] for r in clientes["rows"]}) == 50000
    modelo_js = json.loads((publico / "data" / "model.json").read_text(encoding="utf-8"))
    assert np.allclose(modelo_js["centroides"], corrida["modelo"]["centroides"])
    asignaciones = (publico / "exports" / "customer_assignments.csv").read_text(encoding="utf-8").splitlines()
    assert len(asignaciones) == 50001


def test_las_alertas_y_recomendaciones_usan_datos_reales(corrida):
    df, gs = corrida["df"], corrida["gs"]
    alertas = ed.alertas(df, gs)
    assert len(alertas) == 4 and {a["targetSegment"] for a in alertas} <= {"all", *map(str, range(corrida["modelo"]["k"]))}
    sin_nivel = (df["loyalty_tier"] == "No Tier").sum()
    assert f"{sin_nivel:,} clientes sin nivel" == alertas[2]["metric"]
    recs = ed.recomendaciones(df, alertas)
    assert len(recs) == 4 and all(r["fact"] and r["action"] for r in recs)


def test_parametros_del_simulador_son_los_del_generador_y_sus_rangos_se_cumplen(corrida):
    from src.data import generate

    sim = json.loads((ed.PUBLIC / "data" / "model.json").read_text(encoding="utf-8"))["simulador"]
    assert sim["bandas"] == {k: list(v) for k, v in generate.FRECUENCIA_DIAS.items()}
    assert set(sim["arquetipos"]) == set(generate.ARQUETIPOS)
    assert sum(sim["frecuencia"].values()) == pytest.approx(1, abs=1e-3)
    # Con estructura 0 el generador de Python no sale de los rangos que usa el simulador del navegador
    df, _ = generate.generar(3000, 5, 0.0)
    for columna, clave in [("tenure_months", "tenure"), ("total_purchases", "purchases"), ("avg_order_value_usd", "aov"),
                           ("return_count", "returns"), ("complaint_count", "complaints"), ("satisfaction_score", "satisfaction")]:
        minimo, maximo = sim["base"][clave]
        assert df[columna].between(minimo, maximo).all(), columna


def test_no_hay_filtro_de_temporada_y_el_navegador_recibe_los_catalogos(corrida):
    """El dataset no tiene fechas: no se exporta ningún plan por temporada. Los catálogos permiten armar las vistas con clientes simulados."""
    dash = json.loads((ed.PUBLIC / "data" / "dashboard.json").read_text(encoding="utf-8"))
    assert "temporadas" not in dash
    modelo_js = json.loads((ed.PUBLIC / "data" / "model.json").read_text(encoding="utf-8"))
    cat = modelo_js["catalogos"]
    assert set(cat["regiones"]) == set(cfg_paises()) and set(cat["categoriasEs"]) == set(ed.CATEGORIAS_ES)
    assert all(g["rasgos"] for g in modelo_js["grupos"])
    assert set(modelo_js["simulador"]["pais"]) == set(cat["regiones"])


def cfg_paises():
    from src import config_columns as cfg

    return cfg.REGION_BY_COUNTRY


def test_ningun_texto_del_dashboard_usa_las_cifras_proyectadas_de_la_entrega_2(corrida):
    texto = (ed.PUBLIC / "data" / "dashboard.json").read_text(encoding="utf-8")
    for proyectada in ("17,000", "14,500", "$1,709M", "0.421"):
        assert proyectada not in texto
