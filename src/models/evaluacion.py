"""Métricas de agrupamiento y utilidades de asignación."""
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score


def asignar(Z, centroides):
    """Etiqueta cada punto con el centroide más cercano (distancia euclidiana)."""
    return cdist(Z, centroides).argmin(axis=1)


def metricas(Z, etiquetas, semilla=42, muestra=10000):
    """Silueta (completa en test de 10k, muestreada en datasets mas grandes), Davies-Bouldin, Calinski-Harabasz y balance de tamaños."""
    etiquetas = np.asarray(etiquetas)
    grupos, cuentas = np.unique(etiquetas, return_counts=True)
    salida = {
        "n_grupos": int(len(grupos)),
        "tamano_minimo_pct": float(cuentas.min() / len(etiquetas)),
        "tamano_maximo_pct": float(cuentas.max() / len(etiquetas)),
    }
    if len(grupos) < 2:
        return {**salida, "silueta": float("nan"), "davies_bouldin": float("nan"), "calinski_harabasz": float("nan")}
    # Cambio de mejora: subir muestra a 10,000 permite medir la silueta exacta sobre todo el conjunto de prueba
    # (sin variacion por azar del muestreo) y con mayor estabilidad en entrenamiento.
    salida["silueta"] = float(silhouette_score(Z, etiquetas, sample_size=min(muestra, len(Z)), random_state=semilla))
    salida["davies_bouldin"] = float(davies_bouldin_score(Z, etiquetas))
    salida["calinski_harabasz"] = float(calinski_harabasz_score(Z, etiquetas))
    return salida


def _normalizar_columna(s, mayor_es_mejor=True):
    rango = float(s.max() - s.min())
    if rango <= 1e-12:
        return pd.Series(0.5, index=s.index)
    return (s - s.min()) / rango if mayor_es_mejor else (s.max() - s) / rango


def seleccionar_mejor_candidato(tabla, min_pct=0.10, max_pct=0.60):
    """Elige al mejor candidato usando solo metricas de entrenamiento y equilibrio de grupos.

    Cambio de mejora: antes se elegia solo con la silueta mas alta, lo que premiaba dividir en pocos grupos (K=3)
    o juntar ~78 % de clientes en un solo bloque incluso cuando K=4 o K=5 separaban mucho mejor los perfiles reales.
    Aqui se filtran particiones balanceadas (10 % a 60 % por grupo) y se combinan las tres metricas de entrenamiento:
    40 % silueta (separacion), 30 % Davies-Bouldin invertido (compacidad) y 30 % Calinski-Harabasz (contraste).
    """
    validos = tabla.dropna(subset=["silueta_train", "davies_bouldin_train", "calinski_harabasz_train"])
    elegibles = validos[(validos["tamano_minimo_train"] >= min_pct) & (validos["tamano_maximo_train"] <= max_pct)]
    if len(elegibles) == 0:
        elegibles = validos[validos["tamano_minimo_train"] >= min_pct]
    if len(elegibles) == 0:
        elegibles = validos
    puntaje = (
        0.40 * _normalizar_columna(elegibles["silueta_train"], mayor_es_mejor=True)
        + 0.30 * _normalizar_columna(elegibles["davies_bouldin_train"], mayor_es_mejor=False)
        + 0.30 * _normalizar_columna(elegibles["calinski_harabasz_train"], mayor_es_mejor=True)
    )
    elegibles = elegibles.copy()
    elegibles["indice_compuesto_train"] = puntaje
    return elegibles.loc[puntaje.idxmax()]


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
