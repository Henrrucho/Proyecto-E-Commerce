"""Función de inferencia desacoplada: contrato entre el motor de IA y el dashboard (Entrega 4).

    from src.models.predict import predecir
    predecir({"days_since_last_purchase": 267, ...})

Los artefactos se cargan una sola vez, al primer uso. Se cargan con joblib (pickle): solo deben ser
los generados por `src.models.train` en la carpeta models/; no cargar archivos de fuentes ajenas.
"""
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.data import preprocess
from src.models import evaluacion, perfiles

RAIZ = Path(__file__).resolve().parents[2]
RUTA_MODELO = RAIZ / "models" / "modelo_candidato.joblib"
RUTA_PRE = RAIZ / "models" / "preprocesador.joblib"
_CACHE = {}


def _artefactos(ruta_modelo=RUTA_MODELO, ruta_pre=RUTA_PRE):
    clave = (str(ruta_modelo), str(ruta_pre))
    if clave not in _CACHE:
        _CACHE[clave] = (joblib.load(ruta_modelo), joblib.load(ruta_pre))
    return _CACHE[clave]


def _confianza(distancias):
    """0.5 si el cliente está a igual distancia de sus dos grupos más cercanos, 1.0 si está en un centroide."""
    orden = np.sort(distancias, axis=1)
    d1, d2 = orden[:, 0], orden[:, 1]
    return np.where(d1 + d2 == 0, 1.0, d2 / np.maximum(d1 + d2, 1e-12))


def predecir_lote(df, ruta_modelo=RUTA_MODELO, ruta_pre=RUTA_PRE):
    """Asigna grupo a todos los clientes de un DataFrame con las columnas base. Devuelve un DataFrame."""
    modelo, pre = _artefactos(ruta_modelo, ruta_pre)
    Z = pre.transform(df)
    from scipy.spatial.distance import cdist
    d = cdist(Z, modelo["centroides"])
    grupo = d.argmin(axis=1)
    nombres = {p["grupo"]: p["nombre"] for p in modelo["perfil_grupos"]}
    salida = pd.DataFrame({
        "customer_id": df["customer_id"].to_numpy() if "customer_id" in df else np.arange(len(df)),
        "cluster_id": grupo,
        "cluster_etiqueta": [nombres.get(int(g), f"Grupo {g}") for g in grupo],
        "distancia_centroide": d.min(axis=1).round(4),
        "confianza": _confianza(d).round(4),
        "estatus_alerta": [perfiles.estatus_alerta(s, dias, q) for s, dias, q in
                           zip(df["satisfaction_score"], df["days_since_last_purchase"], df["complaint_count"])],
    })
    if "rfm_category" in df:
        salida["regla_rfm_original"] = df["rfm_category"].to_numpy()
    return salida


def predecir(entrada, ruta_modelo=RUTA_MODELO, ruta_pre=RUTA_PRE):
    """Recibe un cliente como diccionario plano y devuelve la inferencia estructurada.

    Nunca lanza excepciones por datos inválidos: devuelve {"status": "error", "mensaje": ...}.
    """
    try:
        modelo, _ = _artefactos(ruta_modelo, ruta_pre)
    except FileNotFoundError:
        return {"status": "error", "mensaje": "No hay modelo entrenado. Ejecute: python -m src.models.train"}
    requeridas = modelo["columnas_requeridas"]
    if not isinstance(entrada, dict):
        return {"status": "error", "mensaje": "La entrada debe ser un diccionario."}
    faltan = [c for c in requeridas if c not in entrada]
    if faltan:
        return {"status": "error", "mensaje": f"Faltan campos: {faltan}", "campos_requeridos": requeridas}
    registro = {**{c: entrada.get(c) for c in ("preferred_category_2", "preferred_category_3", "social_media_presence")}, **entrada}
    for c in ("preferred_category_2", "preferred_category_3", "social_media_presence"):
        registro[c] = registro[c] if registro[c] else "None"
    df = pd.DataFrame([registro])
    try:
        inicio = time.perf_counter()
        tabla = predecir_lote(df, ruta_modelo, ruta_pre)
        ms = (time.perf_counter() - inicio) * 1000
    except (ValueError, KeyError, TypeError) as e:
        return {"status": "error", "mensaje": f"Datos inválidos: {e}"}
    f = tabla.iloc[0]
    return {
        "cluster_id": int(f.cluster_id),
        "clase_etiqueta": f.cluster_etiqueta,
        "distancia_centroide": float(f.distancia_centroide),
        "confianza": float(f.confianza),
        "estatus_alerta": f.estatus_alerta,
        "modelo": f"{modelo['familia']} (conjunto {modelo['conjunto']}, K={modelo['k']})",
        "silueta_modelo_test": round(modelo["silueta_test"], 4),
        "tiempo_ms": round(ms, 2),
        "status": "success",
    }


def exportar_resultados(df, carpeta, ruta_modelo=RUTA_MODELO, ruta_pre=RUTA_PRE, reportes=None):
    """Genera los archivos que consumirá el dashboard: customer_assignments.csv y segments_summary.json."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    modelo, _ = _artefactos(ruta_modelo, ruta_pre)
    inicio = time.perf_counter()
    asignaciones = predecir_lote(df, ruta_modelo, ruta_pre)
    ms = (time.perf_counter() - inicio) * 1000
    asignaciones.to_csv(carpeta / "customer_assignments.csv", index=False)
    perfil = perfiles.perfil_de_grupos(df, asignaciones["cluster_id"].to_numpy())
    resumen = {
        "modelo": {k: modelo[k] for k in ("familia", "conjunto", "k", "silueta_train", "silueta_test", "semilla")},
        "clientes": int(len(df)),
        "tiempo_inferencia_ms": round(ms, 1),
        "aviso": "Los nombres de grupo describen el reparto; con silueta baja no son grupos naturales de clientes.",
        "grupos": json.loads(perfil.to_json(orient="records")),
        "alertas": asignaciones["estatus_alerta"].value_counts().to_dict(),
    }
    (carpeta / "segments_summary.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    return resumen
