"""Corrida rápida de extremo a extremo y contrato de predecir()."""
import json

import numpy as np
import pandas as pd
import pytest

from src.data import generate
from src.models import predict, train


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    base = tmp_path_factory.mktemp("corrida")
    csv = base / "clientes.csv"
    df, _ = generate.generar(2500, semilla=4, estructura=0.6)
    df.to_csv(csv, index=False)
    modelos, reportes, salidas = base / "models", base / "reports", base / "outputs"
    train.main(["--data", str(csv), "--output", str(modelos), "--reports", str(reportes), "--outputs", str(salidas), "--quick"])
    return {"modelos": modelos, "reportes": reportes, "salidas": salidas, "df": df}


def test_se_generan_todos_los_artefactos(corrida):
    m, r, s = corrida["modelos"], corrida["reportes"], corrida["salidas"]
    for archivo in ("modelo_candidato.joblib", "scaler.joblib", "pca.joblib", "preprocesador.joblib", "kmeans_B_k4.joblib", "ga_B_k4.joblib"):
        assert (m / archivo).exists(), archivo
    for archivo in ("experimentos.csv", "metrics.json", "convergencia.png", "comparacion.png", "robustez.csv", "log_entrenamiento.txt"):
        assert (r / archivo).exists(), archivo
    assert (s / "customer_assignments.csv").exists() and (s / "segments_summary.json").exists()


def test_la_matriz_de_experimentos_tiene_los_seis_experimentos(corrida):
    tabla = pd.read_csv(corrida["reportes"] / "experimentos.csv")
    assert set(tabla.exp) == {1, 2, 3, 4, 5, 6}
    assert tabla.silueta_test.notna().all()


def test_las_asignaciones_cubren_todos_los_clientes(corrida):
    asig = pd.read_csv(corrida["salidas"] / "customer_assignments.csv")
    assert len(asig) == len(corrida["df"]) and asig.cluster_id.notna().all()
    assert asig.confianza.between(0.5, 1).all()
    resumen = json.loads((corrida["salidas"] / "segments_summary.json").read_text(encoding="utf-8"))
    assert sum(g["clientes"] for g in resumen["grupos"]) == len(asig)


def test_contrato_de_predecir(corrida):
    rutas = dict(ruta_modelo=corrida["modelos"] / "modelo_candidato.joblib", ruta_pre=corrida["modelos"] / "preprocesador.joblib")
    cliente = corrida["df"].iloc[0].to_dict()
    r = predict.predecir(cliente, **rutas)
    assert r["status"] == "success"
    assert set(r) >= {"cluster_id", "clase_etiqueta", "distancia_centroide", "confianza", "estatus_alerta", "status"}
    # Una llamada individual coincide con la asignación por lote (se busca por id: el modo rápido reordena filas).
    asig = pd.read_csv(corrida["salidas"] / "customer_assignments.csv")
    assert r["cluster_id"] == asig.set_index("customer_id").loc[cliente["customer_id"], "cluster_id"]


def test_predecir_no_lanza_excepciones_con_datos_malos(corrida):
    rutas = dict(ruta_modelo=corrida["modelos"] / "modelo_candidato.joblib", ruta_pre=corrida["modelos"] / "preprocesador.joblib")
    assert predict.predecir({}, **rutas)["status"] == "error"
    assert predict.predecir("hola", **rutas)["status"] == "error"
    cliente = corrida["df"].iloc[0].to_dict()
    cliente["satisfaction_score"] = "texto"
    assert predict.predecir(cliente, **rutas)["status"] == "error"


def test_sin_modelo_entrenado_responde_error(tmp_path):
    r = predict.predecir({"x": 1}, ruta_modelo=tmp_path / "no.joblib", ruta_pre=tmp_path / "no2.joblib")
    assert r["status"] == "error"


def test_mismo_comando_misma_semilla_mismo_resultado(corrida, tmp_path):
    csv = tmp_path / "c.csv"
    corrida["df"].to_csv(csv, index=False)
    r2 = tmp_path / "r2"
    train.main(["--data", str(csv), "--output", str(tmp_path / "m2"), "--reports", str(r2), "--outputs", str(tmp_path / "o2"), "--quick"])
    a = pd.read_csv(corrida["reportes"] / "experimentos.csv")
    b = pd.read_csv(r2 / "experimentos.csv")
    assert np.allclose(a.silueta_test, b.silueta_test)
