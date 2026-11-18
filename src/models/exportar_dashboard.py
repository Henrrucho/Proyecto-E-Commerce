"""Genera los archivos que consume el dashboard (frontend-dashboard/public/).

    python -m src.models.exportar_dashboard

Lee el dataset original y el modelo ganador (models/), asigna un grupo a cada cliente con el mismo código
que usa `predecir()` y escribe:
  data/dashboard.json        agregados por grupo y por segmento, alertas, recomendaciones, zonas y países
  data/customers.json        tabla del explorador (una fila por cliente)
  data/model.json            parámetros del modelo para ejecutar `predecir` en el navegador
  data/parity_sample.json    clientes con su resultado en Python, para probar que el navegador da lo mismo
  exports/customer_assignments.csv y exports/segments_report.html   descargas de la cabecera
Todo es un resultado calculado del modelo y del dataset; nada se escribe a mano.
"""
import html
import json
import time
from pathlib import Path

# joblib (pickle): solo se cargan los artefactos de models/, generados por este proyecto y revisados en el PR 2.
import joblib
import numpy as np
import pandas as pd

from src import config_columns as cfg
from src.data import generate, preprocess, reglas
from src.models import perfiles, predict

RAIZ = Path(__file__).resolve().parents[2]
PUBLIC = RAIZ / "frontend-dashboard" / "public"
RAW = RAIZ / "data" / "raw" / "E-commerce_Customer_Segmentation_2026.csv"

COLORES = ["#2563EB", "#6366F1", "#F97316", "#10B981", "#EC4899", "#14B8A6"]
CATEGORIAS_ES = {
    "Automotive": "Automotriz", "Beauty": "Belleza", "Books": "Libros", "Electronics": "Electrónica", "Fashion": "Moda",
    "Grocery": "Despensa", "Home & Kitchen": "Hogar y cocina", "Office Supplies": "Oficina", "Pet Supplies": "Mascotas",
    "Sports & Fitness": "Deporte y fitness", "Toys": "Juguetes", "Health & Personal Care": "Salud y cuidado personal",
}
ICONOS = {"Automotriz": "car", "Belleza": "sparkles", "Libros": "bookOpen", "Electrónica": "laptop", "Moda": "shirt",
          "Despensa": "coffee", "Hogar y cocina": "home", "Oficina": "bookOpen", "Mascotas": "heart", "Deporte y fitness": "dumbbell",
          "Juguetes": "gift", "Salud y cuidado personal": "heart"}
PAISES_ES = {
    "Germany": "Alemania", "Saudi Arabia": "Arabia Saudita", "Australia": "Australia", "Brazil": "Brasil", "Canada": "Canadá",
    "Spain": "España", "United States": "Estados Unidos", "France": "Francia", "India": "India", "Italy": "Italia", "Japan": "Japón",
    "Mexico": "México", "Netherlands": "Países Bajos", "Pakistan": "Pakistán", "United Kingdom": "Reino Unido", "Singapore": "Singapur",
    "United Arab Emirates": "Emiratos Árabes Unidos",
}
TIERS = [("Diamond", "Diamante"), ("Platinum", "Platino"), ("Gold", "Oro"), ("Silver", "Plata"), ("Bronze", "Bronce"), ("No Tier", "Sin nivel")]
ETIQUETAS_SATISFACCION = [("1 ★ Muy Insatisfecho", "bg-rose-500"), ("2 ★ Insatisfecho", "bg-orange-400"), ("3 ★ Neutral", "bg-amber-400"),
                          ("4 ★ Satisfecho", "bg-indigo-500"), ("5 ★ Muy Satisfecho", "bg-emerald-500")]
# Acción sugerida según el rasgo más distintivo de un grupo (regla, no aprendida).
ACCIONES = {
    ("days_since_last_purchase", 1): "Campaña de regreso con un beneficio directo en su categoría favorita.",
    ("days_since_last_purchase", -1): "Ventas cruzadas y recordatorios de reposición mientras compran con frecuencia.",
    ("total_purchases", 1): "Programa de fidelidad con acceso anticipado para sostener la frecuencia.",
    ("total_purchases", -1): "Incentivar la segunda y tercera compra con una oferta de bienvenida.",
    ("avg_order_value_usd", 1): "Ofertas premium y envíos prioritarios para proteger el ticket alto.",
    ("avg_order_value_usd", -1): "Paquetes y descuentos por volumen para subir el ticket promedio.",
    ("return_count", 1): "Revisar las causas de devolución y mejorar la guía de producto antes de ofrecer descuentos.",
    ("return_count", -1): "Mantener la experiencia actual; no requiere intervención.",
    ("complaint_count", 1): "Contacto de atención al cliente y resolución prioritaria de reclamos abiertos.",
    ("complaint_count", -1): "Mantener la experiencia actual; no requiere intervención.",
    ("satisfaction_score", 1): "Invitar a reseñas y referidos: son los clientes más propensos a recomendar.",
    ("satisfaction_score", -1): "Encuesta breve para conocer el motivo y seguimiento por atención al cliente.",
    ("tenure_months", 1): "Reconocer la antigüedad con beneficios de cliente de largo plazo.",
    ("tenure_months", -1): "Acompañar la incorporación con contenido y soporte durante los primeros meses.",
}


# ---------------------------------------------------------------- datos
def cargar(ruta_csv=RAW):
    df, _ = preprocess.limpiar(preprocess.cargar_y_validar(ruta_csv))
    asign = predict.predecir_lote(df)
    df = df.reset_index(drop=True)
    df["cluster"] = asign["cluster_id"].to_numpy()
    df["estatus"] = asign["estatus_alerta"].to_numpy()
    df["distancia"] = asign["distancia_centroide"].to_numpy()
    df["confianza"] = asign["confianza"].to_numpy()
    df["categoria"] = df["preferred_category_1"].map(CATEGORIAS_ES)
    df["region"] = df["country"].map(cfg.REGION_BY_COUNTRY).fillna("Otra")
    return df, asign


def r1(x):
    return round(float(x), 1)


def pct(x, d=1):
    return round(100 * float(x), d)


def millones(x):
    return f"${x / 1e6:,.0f}M" if x >= 1e6 else f"${x:,.0f}"


# ---------------------------------------------------------------- piezas del dashboard
def _clave_rasgo(texto):
    """'days_since_last_purchase (+2.35 sd)' -> ('days_since_last_purchase', 1)."""
    return texto.split(" (")[0], (1 if "(+" in texto else -1)


def grupos(df, modelo):
    perfil = pd.DataFrame(modelo["perfil_grupos"]).set_index("grupo")
    total_gasto = df["total_spent_usd"].sum()
    salida = []
    for g in sorted(df["cluster"].unique()):
        sub = df[df["cluster"] == g]
        nombre = perfil.loc[g, "nombre"]
        corto = nombre.split(": ", 1)[1]
        rfm_dom = sub["rfm_category"].mode().iloc[0]
        rasgos = perfil.loc[g, "rasgos_distintivos"].split(", ")
        salida.append({
            "id": int(g), "name": nombre, "shortName": corto[0].upper() + corto[1:], "color": COLORES[int(g) % len(COLORES)],
            "clientes": int(len(sub)), "porcentaje": pct(len(sub) / len(df)),
            "porcentajeGasto": pct(sub["total_spent_usd"].sum() / total_gasto), "gastoTotalM": millones(sub["total_spent_usd"].sum()),
            "gastoPromedio": round(float(sub["total_spent_usd"].mean())),
            "reglaRFM": round(float(df[df["rfm_category"] == rfm_dom]["total_spent_usd"].mean())), "rfmDominante": rfm_dom,
            "satisfaccion": round(float(sub["satisfaction_score"].mean()), 2),
            "desc": f"{sub['days_since_last_purchase'].mean():.0f} días sin comprar, {sub['total_purchases'].mean():.0f} compras, "
                    f"satisfacción {sub['satisfaction_score'].mean():.1f}",
            "rasgos": rasgos,
            "accion": " ".join(list(dict.fromkeys(ACCIONES[k] for k in map(_clave_rasgo, rasgos) if k in ACCIONES))[:1]) or "Seguimiento regular.",
            "perfil": {v: round(float(sub[v].mean()), 2) for v in perfiles.VARIABLES},
        })
    return salida


def insights(sub, etiqueta):
    cat = sub["categoria"].value_counts(normalize=True)
    categorias = []
    for nombre, share in cat.head(3).items():
        s = sub[sub["categoria"] == nombre]
        zonas = s["region"].value_counts().head(2).index.tolist()
        categorias.append({"name": nombre, "iconKey": ICONOS[nombre], "avgTicket": f"${s['avg_order_value_usd'].mean():,.0f} USD",
                           "share": f"{100 * share:.1f}%", "topZone": " / ".join(zonas)})
    redes = []
    for red in cfg.SOCIAL_NETWORKS:
        usa = sub["social_media_presence"].astype(str).str.contains(red, regex=False)
        redes.append({"net": red, "rate": r1(100 * sub.loc[usa, "conversion_rate"].mean())})
    sin = sub["social_media_presence"].astype(str) == "None"
    redes.append({"net": "Directo / Email", "rate": r1(100 * sub.loc[sin, "conversion_rate"].mean())})
    redes.sort(key=lambda r: -r["rate"])
    sat = sub["satisfaction_score"]
    dist = [{"label": ETIQUETAS_SATISFACCION[i][0], "count": int((sat == i + 1).sum()), "color": ETIQUETAS_SATISFACCION[i][1]} for i in range(5)]
    tiers = []
    for clave, es in TIERS:
        t = sub[sub["loyalty_tier"] == clave]
        if len(t):
            tiers.append({"tier": es, "count": f"{len(t):,}", "avg": f"{t['satisfaction_score'].mean():.1f} ★",
                          "sat": f"{100 * (t['satisfaction_score'] >= 4).mean():.0f}%", "spent": f"${t['total_spent_usd'].mean():,.0f}"})
    return {
        "label": etiqueta,
        "unitEconomics": {"cac": f"${sub['customer_acquisition_cost_usd'].mean():,.0f} USD", "clv": f"${sub['customer_lifetime_value_usd'].mean():,.0f} USD",
                          "returnsAvg": f"{sub['return_count'].mean():.1f} devoluciones"},
        "categories": categorias, "socialConversion": redes,
        "funnel": {"emailOpen": r1(100 * sub["email_open_rate"].mean()), "ctr": r1(100 * sub["click_through_rate"].mean()),
                   "conversion": r1(100 * sub["conversion_rate"].mean())},
        "satisfaction": {"avg": f"{sat.mean():.2f}", "satisfiedPct": f"{100 * (sat >= 4).mean():.1f}%", "neutralPct": f"{100 * (sat == 3).mean():.1f}%",
                         "unsatisfiedPct": f"{100 * (sat <= 2).mean():.1f}%", "dist": dist, "tiers": tiers},
    }


def alertas(df, gs):
    alto = df[df["loyalty_tier"].isin(["Diamond", "Platinum"]) & (df["estatus"] == "Alerta")]
    g_riesgo = int(alto["cluster"].value_counts().idxmax()) if len(alto) else 0
    top = max(gs, key=lambda g: g["porcentajeGasto"])
    sin = df[df["loyalty_tier"] == "No Tier"]
    con = df[df["loyalty_tier"] != "No Tier"]
    g_sin = int(sin["cluster"].value_counts().idxmax())
    redes = insights(df, "")["socialConversion"]
    dif = max(r["rate"] for r in redes) - min(r["rate"] for r in redes)
    sin_red = (df["social_media_presence"].astype(str) == "None").mean()
    return [
        {"id": "alert-vip-risk", "iconKey": "shieldAlert", "priority": "Crítica", "title": "Clientes de alto valor en alerta",
         "metric": f"{len(alto):,} clientes Diamante/Platino", "detail": f"{millones(alto['customer_lifetime_value_usd'].sum())} USD en CLV en juego · Promedio {alto['complaint_count'].mean():.1f} quejas",
         "actionLabel": f"Inspeccionar Grupo {g_riesgo}", "targetSegment": str(g_riesgo), "accent": "rose"},
        {"id": "alert-pareto", "iconKey": "gem", "priority": "Estratégica", "title": "Concentración de valor",
         "metric": f"{top['porcentajeGasto']:.0f}% del ingreso en el Grupo {top['id']}", "detail": f"Generado por el {top['porcentaje']:.0f}% de la base ({top['clientes']:,} clientes)",
         "actionLabel": f"Enfocar Grupo {top['id']}", "targetSegment": str(top["id"]), "accent": "blue"},
        {"id": "alert-no-tier", "iconKey": "userPlus", "priority": "Oportunidad", "title": "Brecha de suscripción detectada",
         "metric": f"{len(sin):,} clientes sin nivel", "detail": f"Gastan ${sin['total_spent_usd'].mean():,.0f} USD vs. ${con['total_spent_usd'].mean():,.0f} USD de clientes con nivel",
         "actionLabel": f"Ver Grupo {g_sin}", "targetSegment": str(g_sin), "accent": "amber"},
        {"id": "alert-channels", "iconKey": "split", "priority": "Táctica", "title": "Conversión por canal",
         "metric": f"Diferencia entre canales: {dif:.1f} pp", "detail": f"{100 * sin_red:.1f}% sin red social registrada requieren contacto vía Email",
         "actionLabel": "Ver todo el universo", "targetSegment": "all", "accent": "indigo"},
    ]


def recomendaciones(df, alerts):
    alto = df[df["loyalty_tier"].isin(["Diamond", "Platinum"])]
    en_alerta = alto[alto["estatus"] == "Alerta"]
    inact = df[df["activity_status"] == "Inactive"]
    insat = alto[alto["satisfaction_score"] <= 2]
    redes = insights(df, "")["socialConversion"]
    g_alerta = alerts[0]["targetSegment"]
    g_inact = str(int(inact["cluster"].value_counts().idxmax()))
    return [
        {"id": "rec-vip", "title": "Proteger a los clientes de alto valor en alerta", "priority": "Alta",
         "fact": f"{len(en_alerta):,} clientes Diamante y Platino están en alerta (medio año sin comprar, o insatisfechos con muchas quejas). Valor del cliente en juego: {millones(en_alerta['customer_lifetime_value_usd'].sum())}.",
         "action": "Contacto personal de un ejecutivo y oferta exclusiva. Revisar por qué están insatisfechos.",
         "buttonLabel": "Ver clientes en alerta", "targetSegment": g_alerta, "targetView": "dashboard"},
        {"id": "rec-inactive", "title": "Reactivar clientes inactivos", "priority": "Alta",
         "fact": f"{len(inact):,} clientes inactivos (90 días o más sin comprar), con {inact['days_since_last_purchase'].mean():.1f} días sin comprar en promedio.",
         "action": "Campaña de regreso con un beneficio directo en su categoría favorita.",
         "buttonLabel": "Ver perfiles de clientes", "targetSegment": g_inact, "targetView": "dashboard"},
        {"id": "rec-unsat", "title": "Atender a los insatisfechos de alto valor", "priority": "Media",
         "fact": f"{len(insat):,} clientes Diamante y Platino dieron una calificación de 1 o 2.",
         "action": "Encuesta breve para conocer el motivo y seguimiento por atención al cliente.",
         "buttonLabel": "Ver satisfacción", "targetSegment": "all", "targetView": "satisfaction"},
        {"id": "rec-channels", "title": "Probar canales de marketing", "priority": "Media",
         "fact": f"Ninguna red destaca: la conversión va de {min(r['rate'] for r in redes):.2f}% a {max(r['rate'] for r in redes):.2f}%.",
         "action": "Hacer pruebas A/B por red antes de concentrar la inversión en una sola.",
         "buttonLabel": "Ver canales en inicio", "targetSegment": "all", "targetView": "dashboard"},
    ]


def zonas(df):
    base = 100 / len(CATEGORIAS_ES)
    glob = df["categoria"].value_counts(normalize=True) * 100
    salida = {}
    for zona, sub in [("Todas las zonas", df)] + [(r, df[df["region"] == r]) for r in sorted(df["region"].unique())]:
        share = sub["categoria"].value_counts(normalize=True) * 100
        filas = []
        for cat in share.index:
            ref = base if zona == "Todas las zonas" else glob[cat]
            diff = share[cat] - ref
            filas.append({"name": cat, "share": r1(share[cat]), "diff": round(float(diff), 2),
                          "status": "Tendencia" if diff >= 0.15 else "Baja" if diff <= -0.15 else "Estable"})
        salida[zona] = filas
    return salida


def paises(df):
    filas = []
    for pais, sub in df.groupby("country"):
        share = sub["categoria"].value_counts(normalize=True) * 100
        filas.append({"country": PAISES_ES.get(pais, pais), "clients": f"{len(sub):,}",
                      "topCat": f"{share.index[0]} ({share.iloc[0]:.1f}%)", "lowCat": f"{share.index[-1]} ({share.iloc[-1]:.1f}%)",
                      "avgSpent": f"${sub['total_spent_usd'].mean():,.0f}",
                      "riskPct": f"{100 * sub['churn_risk_category'].isin(['High', 'Very High']).mean():.1f}%",
                      "sat": f"{sub['satisfaction_score'].mean():.2f}"})
    return sorted(filas, key=lambda f: f["country"])


def evaluacion():
    t = pd.read_csv(RAIZ / "reports" / "experimentos.csv")
    met = json.loads((RAIZ / "reports" / "metrics.json").read_text(encoding="utf-8"))
    g = met["ganador"]
    filas = []
    for exp, nombre in ((4, "K-Means"), (5, "Algoritmo genético")):
        for _, r in t[(t.exp == exp) & (t.conjunto == g["conjunto"])].iterrows():
            filas.append({"modelo": nombre, "k": int(r.k), "silueta_train": round(float(r.silueta_train), 3), "silueta_test": round(float(r.silueta_test), 3),
                          "davies_bouldin": round(float(r.davies_bouldin_test), 3)})
    base = {nombre: round(float(t[(t.exp == e) & (t.conjunto == g["conjunto"])].silueta_test.iloc[0]), 3) for e, nombre in ((1, "Reglas RFM"), (2, "Partición aleatoria"))}
    return {"configuraciones": filas, "baselines": base,
            "ganador": {"modelo": g["modelo"], "k": int(g["k"]), "conjunto": g["conjunto"], "silueta_train": round(g["silueta_train"], 3),
                        "silueta_test": round(g["silueta_test"], 3), "tamano_minimo": round(g["tamano_minimo_test"], 3), "tamano_maximo": round(g["tamano_maximo_test"], 3)},
            "estabilidad": {k: round(v["medio"], 3) for k, v in met["estabilidad_ari"].items()}}


# ---------------------------------------------------------------- modelo para el navegador
def modelo_navegador(modelo, pre, gs, df):
    if pre.conjunto != "B":
        raise SystemExit("El exportador del navegador solo implementa el conjunto de variables B.")
    return {
        "conjunto": pre.conjunto, "familia": modelo["familia"], "k": int(modelo["k"]),
        "campos": [
            {"id": "days_since_last_purchase", "etiqueta": "Días desde la última compra", "min": 0, "max": 365, "paso": 1, "ejemplo": 12},
            {"id": "total_purchases", "etiqueta": "Compras totales", "min": 0, "max": 500, "paso": 1, "ejemplo": 40},
            {"id": "tenure_months", "etiqueta": "Antigüedad (meses)", "min": 1, "max": 240, "paso": 1, "ejemplo": 30},
            {"id": "avg_order_value_usd", "etiqueta": "Valor promedio del pedido (USD)", "min": 0, "max": 5000, "paso": 0.01, "ejemplo": 250},
            {"id": "return_count", "etiqueta": "Devoluciones", "min": 0, "max": 100, "paso": 1, "ejemplo": 3},
            {"id": "complaint_count", "etiqueta": "Quejas", "min": 0, "max": 100, "paso": 1, "ejemplo": 1},
            {"id": "satisfaction_score", "etiqueta": "Satisfacción (1 a 5)", "min": 1, "max": 5, "paso": 1, "ejemplo": 4},
        ],
        "scaler": {"mean": pre.scaler.mean_.tolist(), "scale": pre.scaler.scale_.tolist()},
        "pesos": pre.pesos.tolist(),
        "pca": {"mean": pre.pca.mean_.tolist(), "components": pre.pca.components_.tolist()},
        "centroides": np.asarray(modelo["centroides"]).tolist(),
        "grupos": [{k: g[k] for k in ("id", "name", "shortName", "color", "porcentaje", "satisfaccion", "desc", "accion", "perfil", "rasgos")} for g in gs],
        "catalogos": catalogos(),
        "ejemplos": [{"grupo": int(g), **{c: float(r[c]) for c in predict_campos()}} for g, r in
                     ((g, df[df["cluster"] == g].nsmallest(1, "distancia").iloc[0]) for g in sorted(df["cluster"].unique()))],
        "reglaAlerta": {"alertaDias": 180, "alertaQuejas": 10, "alertaSatisfaccion": 2, "atencionDias": 90, "atencionQuejas": 12},
        "simulador": parametros_simulador(),
    }


def catalogos():
    """Textos y mapas que el navegador necesita para armar las mismas vistas con clientes simulados."""
    return {
        "categoriasEs": CATEGORIAS_ES, "iconos": ICONOS, "paisesEs": PAISES_ES, "tiers": TIERS,
        "etiquetasSatisfaccion": ETIQUETAS_SATISFACCION, "colores": COLORES,
        "acciones": {f"{variable}|{signo}": texto for (variable, signo), texto in ACCIONES.items()},
        "regiones": cfg.REGION_BY_COUNTRY, "redes": cfg.SOCIAL_NETWORKS,
    }


def parametros_simulador():
    """Parámetros de src/data/generate.py (las proporciones salen del dataset real) para simular clientes en el navegador."""
    perfil = generate.cargar_perfil()
    paises = {}
    for pais, _ciudad, p in perfil["country_city"]:
        paises[pais] = paises.get(pais, 0) + p
    return {
        "frecuencia": perfil["purchase_frequency"],
        "pais": paises, "categoria": perfil["preferred_category_1"], "pSocial": perfil["p_social"],
        "coefChurn": list(reglas.COEF_CHURN), "sdChurn": reglas.SD_CHURN,
        "bandas": generate.FRECUENCIA_DIAS,
        # Rangos enteros inclusivos del generador cuando estructura = 0 (aov es continuo: uniforme entre los dos valores)
        "base": {"tenure": [1, 119], "purchases": [0, 199], "aov": [10, 1000], "returns": [0, 19], "complaints": [0, 14], "satisfaction": [1, 5]},
        "arquetipos": generate.ARQUETIPOS,
    }


def muestra_paridad(df, n=300):
    m = df.sample(n, random_state=7)
    campos = predict_campos()
    return [{**{c: float(r[c]) for c in campos}, "cluster": int(r["cluster"]), "confianza": float(r["confianza"]),
             "distancia": float(r["distancia"]), "estatus": r["estatus"]} for _, r in m.iterrows()]


def predict_campos():
    return ["days_since_last_purchase", "total_purchases", "tenure_months", "avg_order_value_usd", "return_count", "complaint_count", "satisfaction_score"]


# ---------------------------------------------------------------- reporte HTML
def reporte_html(resumen):
    def fila(celdas, th=False):
        etiqueta = "th" if th else "td"
        return "<tr>" + "".join(f"<{etiqueta}>{html.escape(str(c))}</{etiqueta}>" for c in celdas) + "</tr>"

    g = resumen["evaluacion"]["ganador"]
    cuerpo = "".join(fila([x["name"], f"{x['clientes']:,}", f"{x['porcentaje']}%", f"${x['gastoPromedio']:,}", x["satisfaccion"], x["accion"]]) for x in resumen["clusters"])
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Reporte ejecutivo de segmentos</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#0f172a}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #cbd5e1;padding:.45rem .6rem;text-align:left;font-size:.9rem}}th{{background:#0f172a;color:#fff}}h1{{font-size:1.5rem}}small{{color:#64748b}}</style></head><body>
<h1>Reporte ejecutivo de segmentos</h1><p><small>Generado el {html.escape(resumen['meta']['generado'])} con {resumen['meta']['clientes']:,} clientes.</small></p>
<p>Modelo: {html.escape(g['modelo'])}, K={g['k']}, conjunto {g['conjunto']}. Silueta de entrenamiento {g['silueta_train']} y de prueba {g['silueta_test']}.
Con una silueta baja los grupos describen el reparto y no son segmentos naturales de clientes.</p>
<table>{fila(['Grupo', 'Clientes', '% de la base', 'Gasto promedio', 'Satisfacción', 'Acción sugerida'], True)}{cuerpo}</table>
<h2>Alertas</h2><ul>{''.join(f"<li><b>{html.escape(a['title'])}:</b> {html.escape(a['metric'])}. {html.escape(a['detail'])}</li>" for a in resumen['alertas'])}</ul>
</body></html>"""


# ---------------------------------------------------------------- principal
def main():
    inicio = time.perf_counter()
    modelo = joblib.load(RAIZ / "models" / "modelo_candidato.joblib")
    pre = joblib.load(RAIZ / "models" / "preprocesador.joblib")
    df, asign = cargar()
    gs = grupos(df, modelo)
    segmentos = {"all": insights(df, f"Universo Global ({len(df):,} clientes)")}
    for g in gs:
        segmentos[str(g["id"])] = insights(df[df["cluster"] == g["id"]], f"{g['name']} ({g['clientes']:,} clientes)")
    alerts = alertas(df, gs)
    resumen = {
        "meta": {"generado": time.strftime("%Y-%m-%d %H:%M"), "clientes": int(len(df)), "columnas": 53, "tiempo_asignacion_ms": None},
        "clusters": gs, "insights": segmentos, "alertas": alerts, "recomendaciones": recomendaciones(df, alerts),
        "zonas": zonas(df), "paises": paises(df), "evaluacion": evaluacion(),
        "columnasEsperadas": cfg.EXPECTED_COLUMNS,
        "comparacionRFM": pd.crosstab(df["cluster"], df["rfm_category"]).to_dict(orient="index"),
    }
    datos = PUBLIC / "data"
    exports = PUBLIC / "exports"
    datos.mkdir(parents=True, exist_ok=True)
    exports.mkdir(parents=True, exist_ok=True)
    (datos / "dashboard.json").write_text(json.dumps(resumen, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    columnas = ["id", "cluster", "rfm", "spent", "orders", "satisfaction", "status", "country"]
    filas = [[a, int(b), c, round(float(d), 2), int(e), int(f), s, PAISES_ES.get(p, p)] for a, b, c, d, e, f, s, p in zip(
        df["customer_id"], df["cluster"], df["rfm_category"], df["total_spent_usd"], df["total_purchases"], df["satisfaction_score"], df["estatus"], df["country"])]
    (datos / "customers.json").write_text(json.dumps({"columns": columnas, "rows": filas}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (datos / "model.json").write_text(json.dumps(modelo_navegador(modelo, pre, gs, df), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (datos / "parity_sample.json").write_text(json.dumps(muestra_paridad(df), separators=(",", ":")), encoding="utf-8")
    asign.to_csv(exports / "customer_assignments.csv", index=False)
    (exports / "segments_report.html").write_text(reporte_html(resumen), encoding="utf-8")
    print(f"dashboard.json, customers.json, model.json, parity_sample.json y descargas escritos en {PUBLIC} ({time.perf_counter() - inicio:.1f} s)")
    print("grupos:", [(g["id"], g["name"], g["clientes"]) for g in gs])


if __name__ == "__main__":
    main()
