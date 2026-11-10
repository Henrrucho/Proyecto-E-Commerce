import numpy as np
import pytest
from sklearn.metrics import adjusted_rand_score, silhouette_score

from src.data import generate, preprocess
from src.models import evaluacion
from src.models.ga_clustering import AGClustering


def test_silueta_rapida_coincide_con_scikit_learn():
    rng = np.random.default_rng(0)
    Z = np.vstack([rng.normal(0, 1, (80, 3)), rng.normal(4, 1, (70, 3)), rng.normal([0, 5, 0], 1, (60, 3))])
    etiquetas = np.repeat([0, 1, 2], [80, 70, 60])
    from scipy.spatial.distance import cdist
    propia, minimo = evaluacion.silueta_con_distancias(cdist(Z, Z), etiquetas, 3)
    assert propia == pytest.approx(silhouette_score(Z, etiquetas), abs=1e-9)
    assert minimo == pytest.approx(60 / 210)


def test_particion_degenerada_se_penaliza():
    D = np.ones((10, 10)) - np.eye(10)
    assert evaluacion.silueta_con_distancias(D, np.array([0] * 9 + [1]), 2) == (-1.0, 0.0)


def test_ga_encuentra_grupos_obvios_y_es_reproducible():
    rng = np.random.default_rng(1)
    Z = np.vstack([rng.normal(c, 0.6, (300, 2)) for c in ([0, 0], [6, 0], [0, 6], [6, 6])])
    verdad = np.repeat(range(4), 300)
    a = AGClustering(k=4, poblacion=30, generaciones=40, semilla=3).fit(Z)
    b = AGClustering(k=4, poblacion=30, generaciones=40, semilla=3).fit(Z)
    assert np.allclose(a.centroides_, b.centroides_)
    assert adjusted_rand_score(verdad, a.predict(Z)) > 0.9
    h = a.historial_
    assert h["mejor"].iloc[-1] >= h["mejor"].iloc[0] and (h["mejor"].diff().dropna() >= -1e-12).all()  # el elitismo no pierde al mejor


def test_ga_no_acepta_grupos_menores_al_minimo():
    rng = np.random.default_rng(2)
    Z = rng.normal(0, 1, (500, 3))
    ga = AGClustering(k=4, poblacion=20, generaciones=20, semilla=1).fit(Z)
    cuentas = np.bincount(ga.predict(Z), minlength=4) / 500
    assert cuentas.min() > 0.08  # el mínimo es 10 % sobre la submuestra de aptitud


def test_ga_recupera_arquetipos_en_datos_con_estructura():
    df, arq = generate.generar(4000, semilla=21, estructura=1.0)
    df = preprocess.limpiar(df)[0]
    pre = preprocess.Preprocesador("B").fit(df)
    Z = pre.transform(df)
    ga = AGClustering(k=5, poblacion=30, generaciones=50, semilla=0).fit(Z)
    assert adjusted_rand_score(arq.loc[df.customer_id].to_numpy(), ga.predict(Z)) > 0.5
