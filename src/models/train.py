"""Entrena y compara los modelos de agrupamiento y guarda artefactos, métricas y gráficas.

    python -m src.models.train --data data/raw/E-commerce_Customer_Segmentation_2026.csv --output models/

Experimentos (todos sobre el mismo conjunto de prueba del 20 %, semilla 42):
  1  reglas RFM del dataset (línea base sin aprendizaje)
  2  partición aleatoria (línea base ingenua)
  3  K-Means con configuración por defecto
  4  K-Means ajustado (K = 3, 4, 5; 10 inicializaciones)
  5  algoritmo genético (K = 3, 4, 5)
  6  algoritmo genético con ajuste de parámetros
  7  robustez con datasets generados de distinto tamaño y estructura
La configuración se elige con la silueta de ENTRENAMIENTO; el conjunto de prueba solo se reporta.
"""
import argparse
import itertools
import json
import logging
import time
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

from src import config_columns as cfg
from src.data import generate, preprocess
from src.models import evaluacion, perfiles
from src.models.ga_clustering import AGClustering

RAIZ = Path(__file__).resolve().parents[2]
LOG = logging.getLogger("train")
CONJUNTOS = ["A", "B", "C"]
DESCRIPCION_CONJUNTO = {"A": "8 numéricas de la Entrega 2", "B": "6 conductuales", "C": "conductuales + categóricas codificadas"}


def configurar_log(carpeta):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    LOG.handlers.clear()
    LOG.setLevel(logging.INFO)
    formato = logging.Formatter("[%(levelname)s] %(message)s")
    for h in (logging.StreamHandler(), logging.FileHandler(carpeta / "log_entrenamiento.txt", mode="w", encoding="utf-8")):
        h.setFormatter(formato)
        LOG.addHandler(h)


# ---------------------------------------------------------------- ajuste de modelos
class ModeloCentroides:
    """Envoltura común: cualquier modelo queda como un conjunto de centroides en el espacio de entrada."""

    def __init__(self, familia, k, centroides, tiempo, parametros, extra=None):
        self.familia, self.k, self.centroides_ = familia, k, centroides
        self.tiempo_entrenamiento_, self.parametros, self.extra = tiempo, parametros, extra

    def predict(self, Z):
        return evaluacion.asignar(Z, self.centroides_)


def ajustar_kmeans(Z, k, semilla, n_init):
    inicio = time.perf_counter()
    km = KMeans(n_clusters=k, n_init=n_init, random_state=semilla).fit(Z)
    return ModeloCentroides("K-Means", k, km.cluster_centers_, time.perf_counter() - inicio,
                            {"k": k, "n_init": n_init, "semilla": semilla}, extra={"inercia": float(km.inertia_)})


def ajustar_ga(Z, k, semilla, **params):
    ga = AGClustering(k=k, semilla=semilla, **params).fit(Z)
    return ModeloCentroides("Algoritmo genético", k, ga.centroides_, ga.tiempo_entrenamiento_, ga.parametros(),
                            extra={"historial": ga.historial_})


def evaluar_modelo(exp, nombre, conjunto, modelo, Ztr, Zte, semilla):
    ytr, yte = modelo.predict(Ztr), modelo.predict(Zte)
    mtr, mte = evaluacion.metricas(Ztr, ytr, semilla), evaluacion.metricas(Zte, yte, semilla)
    inicio = time.perf_counter()
    modelo.predict(Zte)
    infer_ms = (time.perf_counter() - inicio) * 1000
    return {
        "exp": exp, "modelo": nombre, "conjunto": conjunto, "k": modelo.k,
        "hiperparametros": json.dumps({k: v for k, v in modelo.parametros.items() if k != "semilla"}, ensure_ascii=False),
        "silueta_train": mtr["silueta"], "silueta_test": mte["silueta"], "davies_bouldin_test": mte["davies_bouldin"],
        "calinski_harabasz_test": mte["calinski_harabasz"], "tamano_minimo_train": mtr["tamano_minimo_pct"], "tamano_minimo_test": mte["tamano_minimo_pct"],
        "tiempo_entrenamiento_s": modelo.tiempo_entrenamiento_, "tiempo_inferencia_ms": infer_ms,
        "diagnostico": evaluacion.diagnostico(mtr["silueta"], mte["silueta"]),
    }


def evaluar_etiquetas(exp, nombre, conjunto, ytr, yte, Ztr, Zte, semilla, detalle):
    """Línea base sin modelo: ya trae sus etiquetas."""
    mtr, mte = evaluacion.metricas(Ztr, ytr, semilla), evaluacion.metricas(Zte, yte, semilla)
    return {
        "exp": exp, "modelo": nombre, "conjunto": conjunto, "k": mte["n_grupos"], "hiperparametros": detalle,
        "silueta_train": mtr["silueta"], "silueta_test": mte["silueta"], "davies_bouldin_test": mte["davies_bouldin"],
        "calinski_harabasz_test": mte["calinski_harabasz"], "tamano_minimo_train": mtr["tamano_minimo_pct"], "tamano_minimo_test": mte["tamano_minimo_pct"],
        "tiempo_entrenamiento_s": 0.0, "tiempo_inferencia_ms": 0.0,
        "diagnostico": evaluacion.diagnostico(mtr["silueta"], mte["silueta"]),
    }


def estabilidad(ajustar, Ztr, Zte, semillas=range(5)):
    """ARI medio entre las particiones de prueba obtenidas con semillas distintas."""
    etiquetas = [ajustar(Ztr, s).predict(Zte) for s in semillas]
    pares = [adjusted_rand_score(a, b) for a, b in itertools.combinations(etiquetas, 2)]
    return float(np.mean(pares)), float(np.min(pares))


# ---------------------------------------------------------------- experimentos 1 a 6
def experimentos_principales(train, test, rapido, semilla):
    filas, modelos, espacios = [], {}, {}
    ga_base = dict(poblacion=15, generaciones=12) if rapido else {}
    for conjunto in CONJUNTOS:
        pre = preprocess.Preprocesador(conjunto).fit(train)
        Ztr, Zte = pre.transform(train), pre.transform(test)
        espacios[conjunto] = (pre, Ztr, Zte)
        LOG.info("Conjunto %s (%s): %d variables -> %d componentes PCA (%.0f %% de la varianza)", conjunto,
                 DESCRIPCION_CONJUNTO[conjunto], len(pre.columnas), pre.pca.n_components_, 100 * pre.pca.explained_variance_ratio_.sum())

        codigos = {c: i for i, c in enumerate(sorted(train["rfm_category"].unique()))}
        filas.append(evaluar_etiquetas(1, "Reglas RFM (rfm_category)", conjunto, train["rfm_category"].map(codigos).to_numpy(),
                                       test["rfm_category"].map(codigos).to_numpy(), Ztr, Zte, semilla, "5 categorías del dataset"))
        rng = np.random.default_rng(semilla)
        filas.append(evaluar_etiquetas(2, "Partición aleatoria", conjunto, rng.integers(0, 4, len(Ztr)), rng.integers(0, 4, len(Zte)),
                                       Ztr, Zte, semilla, "K=4, etiquetas al azar"))
        m = ajustar_kmeans(Ztr, 4, semilla, n_init=1)
        filas.append(evaluar_modelo(3, "K-Means por defecto", conjunto, m, Ztr, Zte, semilla))
        for k in (3, 4, 5):
            m = ajustar_kmeans(Ztr, k, semilla, n_init=10)
            modelos[("K-Means", conjunto, k)] = m
            filas.append(evaluar_modelo(4, "K-Means ajustado", conjunto, m, Ztr, Zte, semilla))
            LOG.info("  K-Means K=%d: silueta train %.3f | test %.3f", k, filas[-1]["silueta_train"], filas[-1]["silueta_test"])
        for k in (3, 4, 5):
            m = ajustar_ga(Ztr, k, semilla, **ga_base)
            modelos[("GA", conjunto, k)] = m
            filas.append(evaluar_modelo(5, "Algoritmo genético", conjunto, m, Ztr, Zte, semilla))
            LOG.info("  Genético  K=%d: silueta train %.3f | test %.3f (%.1f s)", k, filas[-1]["silueta_train"],
                     filas[-1]["silueta_test"], m.tiempo_entrenamiento_)

    tabla = pd.DataFrame(filas)
    ga5 = tabla[tabla.exp == 5]
    mejor = ga5.loc[ga5.silueta_train.idxmax()]  # el algoritmo genético ya garantiza el tamaño mínimo
    conjunto, k = mejor.conjunto, int(mejor.k)
    LOG.info("Mejor genético por silueta de entrenamiento: conjunto %s, K=%d. Se usa para el ajuste del experimento 6.", conjunto, k)
    _, Ztr, Zte = espacios[conjunto]
    variantes = {
        "pequeño": dict(poblacion=10 if rapido else 20, generaciones=8 if rapido else 30),
        "grande": dict(poblacion=20 if rapido else 80, generaciones=15 if rapido else 100, p_mutacion=0.3),
        "híbrido (semilla K-Means++)": {**ga_base, "init": "kmeans++"},
    }
    for nombre, params in variantes.items():
        m = ajustar_ga(Ztr, k, semilla, **params)
        modelos[("GA " + nombre, conjunto, k)] = m
        fila = evaluar_modelo(6, f"Genético {nombre}", conjunto, m, Ztr, Zte, semilla)
        filas.append(fila)
        LOG.info("  Genético %-28s silueta train %.3f | test %.3f (%.1f s)", nombre, fila["silueta_train"], fila["silueta_test"], m.tiempo_entrenamiento_)
    return pd.DataFrame(filas), modelos, espacios


# ---------------------------------------------------------------- experimento 7
def robustez(rapido, semilla):
    tamanos = [500] if rapido else [1000, 10000, 50000]
    ga_base = dict(poblacion=15, generaciones=12) if rapido else {}
    filas = []
    for (n, estructura), i in zip(itertools.product(tamanos, [0.0, 0.6, 1.0]), itertools.count()):
        df, arq = generate.generar(n, semilla=1000 + i, estructura=estructura)
        df = preprocess.limpiar(df)[0]
        tr, te = preprocess.particionar(df, semilla)
        pre = preprocess.Preprocesador("B").fit(tr)
        Ztr, Zte = pre.transform(tr), pre.transform(te)
        verdad = arq.loc[te.customer_id].to_numpy()
        for familia in ("K-Means", "Algoritmo genético"):
            candidatos = []
            for k in (3, 4, 5):
                m = ajustar_kmeans(Ztr, k, semilla, 10) if familia == "K-Means" else ajustar_ga(Ztr, k, semilla, **ga_base)
                mt = evaluacion.metricas(Ztr, m.predict(Ztr), semilla)
                candidatos.append((mt["silueta"] if mt["tamano_minimo_pct"] >= 0.10 else -1.0, m))
            _, m = max(candidatos, key=lambda x: x[0])
            yte = m.predict(Zte)
            m5 = next(c[1] for c in candidatos if c[1].k == 5)
            estruct = estructura > 0
            filas.append({
                "filas": n, "estructura": estructura, "modelo": familia, "k_elegido": m.k,
                "silueta_test": evaluacion.metricas(Zte, yte, semilla)["silueta"],
                "ari_vs_arquetipo": adjusted_rand_score(verdad, yte) if estruct else float("nan"),
                "ari_sin_ruido": adjusted_rand_score(verdad[verdad != "ruido"], yte[verdad != "ruido"]) if estruct else float("nan"),
                "ari_con_k5": adjusted_rand_score(verdad, m5.predict(Zte)) if estruct else float("nan"),
                "tiempo_s": m.tiempo_entrenamiento_,
            })
            LOG.info("  %6d filas, estructura %.1f, %-18s K=%d silueta %.3f ARI %s", n, estructura, familia, m.k, filas[-1]["silueta_test"],
                     f"{filas[-1]['ari_vs_arquetipo']:.3f}" if estruct else "n/d")
    return pd.DataFrame(filas)


# ---------------------------------------------------------------- gráficas y artefactos
def graficar(tabla, ga_modelo, k_ga, ctab, carpeta):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    h = ga_modelo.extra["historial"]
    ax.plot(h.generacion, h.mejor, lw=2, label="mejor")
    ax.plot(h.generacion, h.media, label="media")
    ax.plot(h.generacion, h.peor, alpha=0.5, label="peor")
    ax.set(xlabel="generación", ylabel="aptitud (silueta con penalización)", title=f"Convergencia del algoritmo genético (K={k_ga})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(carpeta / "convergencia.png", dpi=130)
    plt.close(fig)

    reales = tabla[tabla.exp.isin([1, 2, 3, 4, 5, 6])].copy()
    mejores = reales.sort_values("silueta_test").groupby(["exp", "modelo"]).tail(1).sort_values("exp")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh([f"{m} ({c}, K={k})" for m, c, k in zip(mejores.modelo, mejores.conjunto, mejores.k)], mejores.silueta_test)
    ax.set(xlabel="silueta en prueba (mejor conjunto de cada modelo)", title="Comparación de modelos")
    fig.tight_layout()
    fig.savefig(carpeta / "comparacion.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    im = ax.imshow(ctab.to_numpy(), cmap="Blues")
    ax.set_xticks(range(ctab.shape[1]), ctab.columns, rotation=30, ha="right")
    ax.set_yticks(range(ctab.shape[0]), [f"Grupo {g}" for g in ctab.index])
    for i, j in itertools.product(range(ctab.shape[0]), range(ctab.shape[1])):
        ax.text(j, i, ctab.iat[i, j], ha="center", va="center", fontsize=8)
    ax.set_title("Grupos del modelo frente a la regla RFM (prueba)")
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(carpeta / "grupos_vs_rfm.png", dpi=130)
    plt.close(fig)


def main(argv=None):
    p = argparse.ArgumentParser(description="Entrena y compara los modelos de agrupamiento.")
    p.add_argument("--data", default=str(RAIZ / "data" / "raw" / "E-commerce_Customer_Segmentation_2026.csv"))
    p.add_argument("--output", default=str(RAIZ / "models"), help="carpeta de modelos")
    p.add_argument("--reports", default=str(RAIZ / "reports"))
    p.add_argument("--outputs", default=str(RAIZ / "data" / "outputs"), help="carpeta con los archivos para el dashboard")
    p.add_argument("--seed", type=int, default=cfg.SEED)
    p.add_argument("--quick", action="store_true", help="corrida reducida para pruebas")
    a = p.parse_args(argv)
    salida, reportes = Path(a.output), Path(a.reports)
    salida.mkdir(parents=True, exist_ok=True)
    configurar_log(reportes)
    inicio = time.perf_counter()

    df = preprocess.cargar_y_validar(a.data)
    LOG.info("Cargando dataset: %s (%s registros, %d columnas)", a.data, f"{len(df):,}", df.shape[1])
    if a.quick:
        df = df.sample(min(len(df), 4000), random_state=a.seed)
        LOG.info("Modo rápido: submuestra de %d registros", len(df))
    df, informe = preprocess.limpiar(df)
    LOG.info("Limpieza: %d duplicados, nulos imputados %s, nulos restantes %d", informe["duplicados_eliminados"],
             informe["nulos_imputados"], informe["nulos_restantes"])
    LOG.info("Se excluyen %d columnas derivadas y %d sin valor para el modelo", len(cfg.DERIVED_COLUMNS), len(cfg.IGNORED_COLUMNS))
    train, test = preprocess.particionar(df, a.seed)
    LOG.info("Conjunto Train: %s muestras | Conjunto Test: %s muestras | semilla %d", f"{len(train):,}", f"{len(test):,}", a.seed)

    LOG.info("== Experimentos 1 a 6 ==")
    tabla, modelos, espacios = experimentos_principales(train, test, a.quick, a.seed)

    candidatos = tabla[tabla.exp.isin([3, 4, 5, 6])]
    elegibles = candidatos[candidatos.tamano_minimo_train >= 0.10]  # mínimo por grupo prometido en la Entrega 2
    LOG.info("%d de %d configuraciones cumplen el tamaño mínimo del 10 %% por grupo y pueden ser ganadoras", len(elegibles), len(candidatos))
    candidatos = elegibles if len(elegibles) else candidatos
    ganador = candidatos.loc[candidatos.silueta_train.idxmax()]
    LOG.info("Modelo ganador por silueta de entrenamiento: %s, conjunto %s, K=%d (silueta train %.3f, test %.3f)", ganador.modelo,
             ganador.conjunto, ganador.k, ganador.silueta_train, ganador.silueta_test)
    clave = next(k for k, m in modelos.items() if m.k == ganador.k and k[1] == ganador.conjunto and
                 ((k[0] == "K-Means" and ganador.modelo == "K-Means ajustado") or
                  (k[0] == "GA" and ganador.modelo == "Algoritmo genético") or
                  (k[0] != "GA" and k[0] != "K-Means" and ganador.modelo == "Genético " + k[0].replace("GA ", ""))))
    modelo = modelos[clave]
    pre, Ztr, Zte = espacios[ganador.conjunto]

    # estabilidad entre semillas (ARI) del ganador y de la otra familia
    ga_base = dict(poblacion=15, generaciones=12) if a.quick else {}
    est = {}
    for familia, ajustar in (("K-Means", lambda Z, s: ajustar_kmeans(Z, int(ganador.k), s, 10)),
                             ("Algoritmo genético", lambda Z, s: ajustar_ga(Z, int(ganador.k), s, **ga_base))):
        est[familia] = estabilidad(ajustar, Ztr, Zte, range(3 if a.quick else 5))
        LOG.info("Estabilidad %s (K=%d, %s): ARI medio %.3f, mínimo %.3f", familia, ganador.k, ganador.conjunto, *est[familia])

    LOG.info("== Experimento 7: robustez con datasets generados ==")
    rob = robustez(a.quick, a.seed)

    # artefactos
    for (fam, conjunto, k), m in modelos.items():
        if fam in ("K-Means", "GA"):
            nombre = ("kmeans" if fam == "K-Means" else "ga") + f"_{conjunto}_k{k}.joblib"
            joblib.dump({"familia": m.familia, "k": k, "conjunto": conjunto, "centroides": m.centroides_, "parametros": m.parametros}, salida / nombre)
    for conjunto, (p_, _, _) in espacios.items():
        p_.guardar(salida, f"_{conjunto}")
    pre.guardar(salida)
    etiquetas_train = modelo.predict(Ztr)
    perfil = perfiles.perfil_de_grupos(train, etiquetas_train)
    candidato = {
        "familia": modelo.familia, "conjunto": ganador.conjunto, "k": int(ganador.k), "centroides": modelo.centroides_,
        "parametros": modelo.parametros, "perfil_grupos": perfil.to_dict(orient="records"),
        "silueta_train": float(ganador.silueta_train), "silueta_test": float(ganador.silueta_test), "semilla": a.seed,
        "columnas_requeridas": preprocess.columnas_requeridas(ganador.conjunto),
    }
    joblib.dump(candidato, salida / "modelo_candidato.joblib")
    LOG.info("[SUCCESS] Modelo serializado en: %s", salida / "modelo_candidato.joblib")
    LOG.info("[SUCCESS] Escalador y PCA guardados en: %s", salida / "scaler.joblib")

    # reportes
    reportes.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(reportes / "experimentos.csv", index=False)
    rob.to_csv(reportes / "robustez.csv", index=False)
    yte = modelo.predict(Zte)
    ctab = pd.crosstab(yte, test["rfm_category"])
    ctab.to_csv(reportes / "grupos_vs_rfm.csv")
    ga_k = next(m for (f, c, k), m in modelos.items() if f == "GA" and c == ganador.conjunto and k == int(ganador.k)) \
        if ("GA", ganador.conjunto, int(ganador.k)) in modelos else next(m for (f, c, k), m in modelos.items() if f == "GA")
    graficar(tabla, ga_k, ga_k.k, ctab, reportes)
    perfil.to_csv(reportes / "perfil_grupos.csv", index=False)
    resumen = {
        "semilla": a.seed, "filas_entrenamiento": len(train), "filas_prueba": len(test), "limpieza": informe,
        "ganador": json.loads(ganador.to_json()), "estabilidad_ari": {k: {"medio": v[0], "minimo": v[1]} for k, v in est.items()},
        "tiempo_total_s": time.perf_counter() - inicio,
    }
    (reportes / "metrics.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

    from src.models import predict
    predict.exportar_resultados(df, Path(a.outputs), salida / "modelo_candidato.joblib", salida / "preprocesador.joblib", reportes)
    mte = evaluacion.metricas(Zte, yte, a.seed)
    LOG.info("[RESULTADOS EN TEST SET] silueta %.3f | Davies-Bouldin %.3f | Calinski-Harabasz %.0f | grupo más pequeño %.1f %%",
             mte["silueta"], mte["davies_bouldin"], mte["calinski_harabasz"], 100 * mte["tamano_minimo_pct"])
    LOG.info("[SUCCESS] Entrenamiento terminado en %.1f segundos.", time.perf_counter() - inicio)


if __name__ == "__main__":
    main()
