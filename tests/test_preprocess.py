from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import config_columns as cfg
from src.data import generate, preprocess

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "E-commerce_Customer_Segmentation_2026.csv"


@pytest.fixture(scope="module")
def datos():
    df, _ = generate.generar(1500, semilla=11)
    return preprocess.limpiar(df)[0]


def test_ninguna_variable_de_entrada_es_derivada():
    for conjunto in "ABC":
        assert not set(preprocess.columnas_requeridas(conjunto)) & set(cfg.DERIVED_COLUMNS), conjunto
    assert not set(cfg.FEATURES_A) & set(cfg.DERIVED_COLUMNS)


def test_limpieza_deja_cero_nulos(datos):
    assert datos.isna().sum().sum() == 0


def test_particion_80_20_reproducible(datos):
    a1, b1 = preprocess.particionar(datos)
    a2, b2 = preprocess.particionar(datos)
    assert len(a1) == 1200 and len(b1) == 300
    assert a1.customer_id.tolist() == a2.customer_id.tolist()
    assert not set(a1.customer_id) & set(b1.customer_id)


@pytest.mark.parametrize("conjunto", ["A", "B", "C"])
def test_transformacion_ajustada_solo_con_entrenamiento(datos, conjunto):
    train, test = preprocess.particionar(datos)
    pre = preprocess.Preprocesador(conjunto).fit(train)
    Z = pre.transform(test)
    assert Z.shape[0] == len(test) and Z.shape[1] == pre.pca.n_components_
    assert np.isfinite(Z).all()
    # El escalador se ajustó con el entrenamiento: su media coincide con la de train, no con la de test.
    X_train, _ = preprocess.construir_features(train, conjunto)
    assert np.allclose(pre.scaler.mean_, X_train.mean().to_numpy())


def test_el_conjunto_c_pondera_los_bloques_categoricos(datos):
    pre = preprocess.Preprocesador("C").fit(datos)
    ancho = len(pre.columnas)
    assert ancho > 40
    Z = pre.escalar(datos)
    var_numericas = Z[:, : len(cfg.FEATURES_B)].var(axis=0).sum()
    var_categoricas = Z[:, len(cfg.FEATURES_B):].var(axis=0).sum()
    assert var_categoricas < 5 * var_numericas  # sin ponderar serían ~40 veces más


def test_esquema_incorrecto_se_rechaza(tmp_path):
    malo = tmp_path / "malo.csv"
    pd.DataFrame({"a": [1]}).to_csv(malo, index=False)
    with pytest.raises(ValueError):
        preprocess.cargar_y_validar(malo)


def test_faltan_campos_en_el_registro(datos):
    with pytest.raises(ValueError):
        preprocess.construir_features(datos.drop(columns=["satisfaction_score"]), "B")


@pytest.mark.skipif(not RAW.exists(), reason="falta el dataset original")
def test_dataset_original_cumple_el_esquema_y_no_se_modifica():
    antes = RAW.stat().st_mtime
    df = preprocess.cargar_y_validar(RAW)
    limpio, informe = preprocess.limpiar(df)
    assert df.shape == (50000, 53) and informe["nulos_restantes"] == 0
    assert RAW.stat().st_mtime == antes
