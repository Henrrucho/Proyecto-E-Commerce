"""Métricas de agrupamiento y utilidades de asignación."""
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score


def asignar(Z, centroides):
    """Etiqueta cada punto con el centroide más cercano (distancia euclidiana)."""
    return cdist(Z, centroides).argmin(axis=1)


def metricas(Z, etiquetas, semilla=42, muestra=5000):
    """Silueta (sobre una muestra fija), Davies-Bouldin, Calinski-Harabasz y tamaño mínimo de grupo."""
    etiquetas = np.asarray(etiquetas)
    grupos, cuentas = np.unique(etiquetas, return_counts=True)
    salida = {"n_grupos": int(len(grupos)), "tamano_minimo_pct": float(cuentas.min() / len(etiquetas))}
    if len(grupos) < 2:
        return {**salida, "silueta": float("nan"), "davies_bouldin": float("nan"), "calinski_harabasz": float("nan")}
    salida["silueta"] = float(silhouette_score(Z, etiquetas, sample_size=min(muestra, len(Z)), random_state=semilla))
    salida["davies_bouldin"] = float(davies_bouldin_score(Z, etiquetas))
    salida["calinski_harabasz"] = float(calinski_harabasz_score(Z, etiquetas))
    return salida


def silueta_con_distancias(D, etiquetas, k):
    """Silueta media usando una matriz de distancias ya calculada (sirve de aptitud del algoritmo genético).

    Devuelve (silueta, fraccion_del_grupo_mas_pequeno). Si algún grupo queda con menos de 2 puntos
    la partición es degenerada y devuelve (-1, 0).
    """
    n = len(etiquetas)
    pertenencia = np.zeros((n, k))
    pertenencia[np.arange(n), etiquetas] = 1.0
    cuentas = pertenencia.sum(axis=0)
    if cuentas.min() < 2:
        return -1.0, 0.0
    sumas = D @ pertenencia
    propio = etiquetas
    a = sumas[np.arange(n), propio] / (cuentas[propio] - 1)
    medias = sumas / cuentas
    medias[np.arange(n), propio] = np.inf
    b = medias.min(axis=1)
    s = (b - a) / np.maximum(a, b)
    return float(np.nan_to_num(s).mean()), float(cuentas.min() / n)


def diagnostico(silueta_train, silueta_test):
    """Etiqueta de diagnóstico para la matriz de experimentos."""
    brecha = silueta_train - silueta_test
    if np.isnan(silueta_test):
        return "Sin partición válida"
    if silueta_test < 0.10:
        return "Estructura débil (casi sin grupos naturales)"
    if brecha > 0.03:
        return f"Sobreajuste (brecha {brecha:.3f})"
    return f"Estable (brecha {brecha:+.3f})"
