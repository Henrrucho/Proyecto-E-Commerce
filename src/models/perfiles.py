"""Perfil descriptivo de cada grupo y regla de alerta.

Los nombres salen de comparar la media de cada grupo con la del total (en unidades originales);
no se asignan a mano antes de ver los centroides.
"""
import numpy as np
import pandas as pd

# variable -> (frase si el grupo está por encima del total, frase si está por debajo)
FRASES = {
    "days_since_last_purchase": ("compra hace mucho", "compra reciente"),
    "total_purchases": ("muchas compras", "pocas compras"),
    "avg_order_value_usd": ("pedido promedio alto", "pedido promedio bajo"),
    "return_count": ("muchas devoluciones", "pocas devoluciones"),
    "complaint_count": ("muchas quejas", "pocas quejas"),
    "satisfaction_score": ("satisfecho", "insatisfecho"),
    "tenure_months": ("cliente antiguo", "cliente reciente"),
}
VARIABLES = list(FRASES)


def perfil_de_grupos(df, etiquetas):
    """Tabla con tamaño, medias por grupo y nombre descriptivo. `df` trae las columnas base."""
    datos = df[VARIABLES].copy()
    datos["grupo"] = np.asarray(etiquetas)
    medias = datos.groupby("grupo")[VARIABLES].mean()
    global_media, global_sd = datos[VARIABLES].mean(), datos[VARIABLES].std().replace(0, 1)
    z = (medias - global_media) / global_sd
    filas = []
    for g in medias.index:
        top = z.loc[g].abs().sort_values(ascending=False).index[:2]
        frases = [FRASES[v][0] if z.loc[g, v] > 0 else FRASES[v][1] for v in top]
        filas.append({
            "grupo": int(g),
            "nombre": f"Grupo {g}: " + " y ".join(frases),
            "clientes": int((datos["grupo"] == g).sum()),
            "porcentaje": float((datos["grupo"] == g).mean()),
            **{v: float(medias.loc[g, v]) for v in VARIABLES},
            "rasgos_distintivos": ", ".join(f"{v} ({z.loc[g, v]:+.2f} sd)" for v in top),
        })
    return pd.DataFrame(filas)


def estatus_alerta(satisfaccion, dias_sin_comprar, quejas):
    """Regla sobre los datos del propio cliente: 'Alerta', 'Atención' o 'Normal'.

    Alerta: medio año sin comprar, o insatisfecho con muchas quejas. Atención: tres meses sin comprar,
    insatisfecho o con muchas quejas. Los umbrales son una decisión de negocio editable.
    """
    if dias_sin_comprar >= 180 or (satisfaccion <= 2 and quejas >= 10):
        return "Alerta"
    if dias_sin_comprar >= 90 or satisfaccion <= 2 or quejas >= 12:
        return "Atención"
    return "Normal"
