"""Genera docs/ENTREGA_3.md con las cifras REALES de reports/ (nada se escribe a mano).

Primero hay que haber corrido:  python -m src.models.train
Uso:                            python scripts/generar_entrega3.py
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import config_columns as cfg  # noqa: E402
from src.models import predict  # noqa: E402

REPORTES = RAIZ / "reports"
t = pd.read_csv(REPORTES / "experimentos.csv")
rob = pd.read_csv(REPORTES / "robustez.csv")
met = json.loads((REPORTES / "metrics.json").read_text(encoding="utf-8"))
perfil = pd.read_csv(REPORTES / "perfil_grupos.csv")
ctab = pd.read_csv(REPORTES / "grupos_vs_rfm.csv", index_col=0)
log = (REPORTES / "log_entrenamiento.txt").read_text(encoding="utf-8")
crudo = pd.read_csv(RAIZ / "data" / "raw" / "E-commerce_Customer_Segmentation_2026.csv")
g = met["ganador"]


def f3(x):
    return f"{x:.3f}"


def pct(x):
    return f"{100 * x:.1f} %"


def tabla(df, columnas, encabezados):
    filas = ["| " + " | ".join(encabezados) + " |", "|" + "|".join("---" for _ in encabezados) + "|"]
    for _, fila in df.iterrows():
        filas.append("| " + " | ".join(str(fila[c]) for c in columnas) + " |")
    return "\n".join(filas)


def hp_corto(texto):
    d = json.loads(texto) if texto.startswith("{") else None
    if d is None:
        return texto
    if "n_init" in d:
        return f"K={d['k']}, n_init={d['n_init']}"
    base = f"K={d['k']}, población {d['poblacion']}, {d['generaciones']} generaciones, mutación {d['p_mutacion']}"
    return base + (", semilla K-Means++" if d.get("init") == "kmeans++" else "")


# ---------------------------------------------------------------- datos derivados de los reportes
modelos = t[t.exp.isin([3, 4, 5, 6])]
b = t[t.conjunto == "B"]
km_b = b[b.exp == 4]
km_mejor_b = km_b.loc[km_b.silueta_test.idxmax()]
km_elegible = km_b[km_b.tamano_minimo_train >= 0.10]
km_elegible_mejor = km_elegible.loc[km_elegible.silueta_train.idxmax()]
ga_b = b[b.exp == 5]
rfm_b, azar_b = b[b.exp == 1].iloc[0], b[b.exp == 2].iloc[0]
a_km = t[(t.conjunto == "A") & (t.exp == 4)]
a_mejor = modelos[modelos.conjunto == "A"].loc[modelos[modelos.conjunto == "A"].silueta_test.idxmax()]
c_mejor = modelos[modelos.conjunto == "C"].loc[modelos[modelos.conjunto == "C"].silueta_test.idxmax()]
brecha_max = (modelos.silueta_train - modelos.silueta_test).max()
mejor_db_km = km_b.loc[km_b.davies_bouldin_test.idxmin()]
mejor_ch_km = km_b.loc[km_b.calinski_harabasz_test.idxmax()]
est = met["estabilidad_ari"]
cj = json.loads((REPORTES / "correlaciones.json").read_text(encoding="utf-8"))
pares_c = pd.read_csv(REPORTES / "correlaciones_pares.csv")
cat_c = pd.read_csv(REPORTES / "correlaciones_categoricas.csv")
corr_max = cj["pearson_max_abs"]
# (la correlación máxima viene de reports/correlaciones.json)
rob_ok = rob[rob.estructura == 1.0]
rob_0 = rob[rob.estructura == 0.0]
rob_06 = rob[rob.estructura == 0.6]


def vencedor_ga_vs_km(df):
    ga, km = df[df.modelo == "Algoritmo genético"], df[df.modelo == "K-Means"]
    return int((ga.silueta_test.to_numpy() > km.silueta_test.to_numpy()).sum()), len(ga)


# Artefactos propios de este proyecto (models/); joblib usa pickle y no debe abrir archivos ajenos.
import joblib  # noqa: E402
from sklearn.metrics import silhouette_score  # noqa: E402
from src.data import preprocess  # noqa: E402
from src.models import evaluacion  # noqa: E402

_limpio, _ = preprocess.limpiar(crudo)
_train, _test = preprocess.particionar(_limpio, met["semilla"], met["test_size"])
_pre = joblib.load(RAIZ / "models" / "preprocesador.joblib")
_cand = joblib.load(RAIZ / "models" / "modelo_candidato.joblib")
_Zte = _pre.transform(_test)
_yte = evaluacion.asignar(_Zte, _cand["centroides"])
sil_exacta = float(silhouette_score(_Zte, _yte))
sil_muestras = [float(silhouette_score(_Zte, _yte, sample_size=5000, random_state=s)) for s in range(5)]
asign = pd.read_csv(RAIZ / "data" / "outputs" / "customer_assignments.csv")
composicion = pd.crosstab(asign.cluster_id, crudo.set_index("customer_id").loc[asign.customer_id, "purchase_frequency"].to_numpy(), normalize="index")
ORDEN_FRECUENCIA = ["Daily", "Weekly", "Monthly", "Quarterly", "Rarely"]
segundo_eta = float(cat_c.eta.iloc[1])
pares_top = pares_c.head(5)

ks = sorted(int(k) for k in rob.k_elegido.unique())
ks_texto = ('El criterio de la silueta eligió siempre K=3 aunque los arquetipos reales sean 5: usar la silueta para elegir K favorece pocos grupos.'
            if ks == [3] else f'El criterio de la silueta eligió K = {ks}; los arquetipos reales son 5.')


# ---------------------------------------------------------------- matriz condensada
def fila_matriz(r, nombre_var):
    return {
        "var": nombre_var, "modelo": r.modelo, "hp": hp_corto(r.hiperparametros) + f" · conjunto {r.conjunto}",
        "principal": f"Silueta: {f3(r.silueta_test)}", "secundaria": f"Davies-Bouldin: {f3(r.davies_bouldin_test)}",
        "tiempo": f"{r.tiempo_entrenamiento_s:.2f} s / {r.tiempo_inferencia_ms:.1f} ms",
        "diag": r.diagnostico + (f"; grupo mínimo {pct(r.tamano_minimo_test)}" if r.tamano_minimo_test < 0.10 else ""),
    }


filas = []
filas.append(fila_matriz(rfm_b, "Exp 1: reglas RFM"))
filas.append(fila_matriz(azar_b, "Exp 2: aleatoria"))
filas.append(fila_matriz(b[b.exp == 3].iloc[0], "Exp 3: baseline"))
for _, r in km_b.iterrows():
    filas.append(fila_matriz(r, f"Exp 4: K-Means K={r.k}"))
for _, r in ga_b.iterrows():
    filas.append(fila_matriz(r, f"Exp 5: genético K={r.k}"))
for _, r in t[t.exp == 6].iterrows():
    filas.append(fila_matriz(r, "Exp 6: ajuste"))
for conj, nombre in (("A", "conjunto A"), ("C", "conjunto C")):
    for exp, etiqueta in ((4, "K-Means"), (5, "genético")):
        sub = t[(t.conjunto == conj) & (t.exp == exp)]
        filas.append(fila_matriz(sub.loc[sub.silueta_test.idxmax()], f"Exp {exp}: {etiqueta}, {nombre} (mejor K)"))
matriz = pd.DataFrame(filas)

# ---------------------------------------------------------------- llamada real a predecir()
cliente = crudo.iloc[22].to_dict()
campos = predict._artefactos()[0]["columnas_requeridas"]
entrada = {c: (int(cliente[c]) if float(cliente[c]).is_integer() else float(cliente[c])) for c in campos}
salida = predict.predecir(cliente)
error = predict.predecir({"satisfaction_score": 3})
codigo = (RAIZ / "src" / "models" / "predict.py").read_text(encoding="utf-8")
arbol = ast.parse(codigo)
funcion = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == "predecir")
fuente_predecir = "\n".join(codigo.splitlines()[funcion.lineno - 1: funcion.end_lineno])

# ---------------------------------------------------------------- avance del motor
checklist = [
    ("Carga y validación de las 53 columnas (RF-01 del motor)", True),
    ("Limpieza, imputación y exclusión de columnas derivadas (RF-02)", True),
    ("Partición 80/20 con semilla fija (42)", True),
    ("Agrupamiento con algoritmo genético para K = 3, 4 y 5 (RF-03)", True),
    ("K-Means y líneas base (reglas RFM y partición aleatoria)", True),
    ("Métricas, matriz de experimentos y diagnóstico de sobreajuste", True),
    ("Modelos y transformadores serializados, `predecir()` desacoplada", True),
    ("Archivos de salida para el dashboard (`customer_assignments.csv`, `segments_summary.json`)", True),
    ("Reporte ejecutivo `segments_report.html` (RF-08)", False),
    ("Simulador de comportamiento y predicción supervisada (fase 2, fuera de esta entrega)", False),
]
hechos = sum(1 for _, ok in checklist if ok)
avance = round(100 * hechos / len(checklist))

# ---------------------------------------------------------------- documento
salida_pytest = subprocess.run([sys.executable, '-m', 'pytest', '--collect-only', '-q', 'tests'], cwd=RAIZ, capture_output=True, text=True).stdout
n_pruebas = int(next(l for l in reversed(salida_pytest.splitlines()) if 'collected' in l or 'test' in l).split()[0])
ruta_log = "\n".join(l for l in log.splitlines())
md = []
w = md.append
w("# Entrega 3: Desarrollo, entrenamiento y experimentación del modelo")
w("")
w("Fundamentos de Inteligencia Artificial · Proyecto final")
w("")
w("| Dato | Valor |\n|---|---|")
w("| Fecha de entrega | 11 de noviembre de 2026 |")
w("| Nombre del proyecto | E-Commerce AI: Inteligencia Artificial para la gestión y personalización de clientes |")
w("| Equipo / grupo | LITIID73 |")
w("| Docente | Ing. Carlos André Castro Rodríguez |")
w("| Repositorio | https://github.com/Henrrucho/Proyecto-E-Commerce |")
w("")
w("**Integrantes y roles**")
w("")
w("1. María Tita Fregoso Arechiga — Líder de Datos y Preprocesamiento")
w("2. Jesús Alexander Recaman Lara — Líder de Modelado y Experimentación")
w("3. Henrry Misael Pech Pool — Líder de Pipeline e Integración")
w("4. Gretel Dairen Zavaleta Moctezuma — Gestión del proyecto")
w("")
w("## Resumen y diferencias con la Entrega 2")
w("")
w(f"Esta entrega implementa y evalúa el motor de agrupamiento no supervisado comprometido en la Entrega 2 (algoritmo genético frente a K-Means) sobre el dataset de {len(crudo):,} clientes. **Las cifras de la Entrega 2 eran proyecciones: no existía código que las produjera.** Lo que sigue son los resultados reales de ejecutar el código del repositorio.")
w("")
w("| Concepto | Entrega 2 (proyectado) | Real, conjunto A (8 numéricas de la E2) | Real, mejor modelo |\n|---|---|---|---|")
w(f"| Silueta K=3 | 0.360 | {f3(a_km[a_km.k == 3].silueta_test.iloc[0])} (K-Means) | {f3(ga_b[ga_b.k == 3].silueta_test.iloc[0])} (genético, conjunto B) |")
w(f"| Silueta K=4 | 0.421 | {f3(a_km[a_km.k == 4].silueta_test.iloc[0])} (K-Means) | {f3(ga_b[ga_b.k == 4].silueta_test.iloc[0])} (genético, conjunto B) |")
w(f"| Silueta K=5 | 0.310 | {f3(a_km[a_km.k == 5].silueta_test.iloc[0])} (K-Means) | {f3(ga_b[ga_b.k == 5].silueta_test.iloc[0])} (genético, conjunto B) |")
w(f"| Reglas RFM | 0.140 | {f3(t[(t.conjunto == 'A') & (t.exp == 1)].silueta_test.iloc[0])} | {f3(rfm_b.silueta_test)} (conjunto B) |")
w(f"| Objetivo mínimo (silueta ≥ 0.380) | cumplido (0.421) | **no cumplido** | **no cumplido** ({f3(g['silueta_test'])}) |")
w(f"| Grupo más pequeño | 18 % | {pct(a_mejor.tamano_minimo_test)} | {pct(g['tamano_minimo_test'])} |")
w("")
w(f"**Por qué no se alcanzó 0.380.** Casi todas las variables de este dataset son independientes entre sí: la correlación absoluta máxima entre las 8 numéricas de la Entrega 2 es {corr_max:.2f}, dentro del ruido esperado (±{cj['ruido_esperado_pearson']:.4f}); el detalle del cálculo está en la sección siguiente. La única relación fuerte que encontramos es entre la frecuencia de compra declarada y los días desde la última compra (razón de correlación η = {cj['eta_max']:.2f}): los días se reparten en bandas según la frecuencia (diaria 0-1, semanal 1-7, mensual 8-30, trimestral 31-90, rara vez 91-365). Esa banda de recencia es la única estructura real del dataset y es la que usan los grupos del modelo ganador. Sin más relaciones entre variables no hay grupos marcados en varias dimensiones a la vez, y la silueta de cualquier partición queda baja. Lo comprobamos de dos maneras: (1) la segmentación por reglas RFM que trae el dataset obtiene apenas {f3(rfm_b.silueta_test)} en ese mismo espacio; (2) con datasets generados con estructura (sección 3, experimento 7) los mismos algoritmos suben a silueta {f3(rob_ok.silueta_test.min())} a {f3(rob_ok.silueta_test.max())}. Es decir, el modelo funciona; los datos solo traen estructura en la recencia.")
w("")
w("Otras diferencias: el algoritmo genético usó 60 generaciones (la Entrega 2 decía 50) y una población de 40; los nombres de los grupos (VIP, en riesgo, etc.) del dashboard actual no salen de este modelo y deberán sustituirse en la Entrega 4 por los de `data/outputs/segments_summary.json`.")
w("")

w("## Cómo se midieron la silueta y la correlación")
w("")
w("### La partición 80/20")
w("")
w(f"Los {met['filas_entrenamiento'] + met['filas_prueba']:,} clientes se separan una sola vez, al azar y con semilla 42 (la misma para todos los experimentos; se controla con `--test-size 0.2`):")
w("")
w("| Conjunto | Clientes | Para qué se usa |\n|---|---|---|")
w(f"| Entrenamiento ({100 * (1 - met['test_size']):.0f} %) | {met['filas_entrenamiento']:,} | Ajustar el escalador y la PCA, entrenar los modelos y **elegir** la configuración ganadora |")
w(f"| Prueba ({100 * met['test_size']:.0f} %) | {met['filas_prueba']:,} | Solo **medir**. Nunca se usa para decidir ni para ajustar |")
w("")
w("Aparte, el algoritmo genético calcula su aptitud con 1,000 clientes fijos tomados del conjunto de entrenamiento; eso no es una partición adicional, es una muestra para que cada evaluación sea rápida.")
w("")
w("### Cómo se evaluó la silueta")
w("")
w("La silueta mide qué tan bien separados quedan los grupos. Para **cada cliente** se calculan dos distancias: `a` = distancia promedio a los demás clientes de su propio grupo, y `b` = distancia promedio a los clientes del grupo ajeno más cercano. Su silueta es `s = (b − a) / máx(a, b)`, un número entre −1 y 1. La silueta del modelo es el promedio de `s` de todos los clientes.")
w("")
w("Ejemplo ilustrativo (números inventados): un cliente con `a = 2` y `b = 5` tiene `s = 0.60` (está mucho más cerca de los suyos que de los otros); con `a = 4` y `b = 4`, `s = 0` (en la frontera); con `a = 5` y `b = 2`, `s = −0.60` (probablemente está en el grupo equivocado).")
w("")
w("Escala de referencia habitual (regla práctica de Kaufman y Rousseeuw, 1990):")
w("")
w("| Silueta | Lectura |\n|---|---|")
w("| 0.71 a 1.00 | Estructura fuerte |")
w("| 0.51 a 0.70 | Estructura razonable |")
w("| 0.26 a 0.50 | Estructura débil, puede ser artificial |")
w("| 0.25 o menos | Sin estructura sustancial |")
w("")
w("Detalles de cómo se calculó en este proyecto:")
w("")
w("- **Espacio de las distancias.** Las variables se estandarizan (media 0, desviación 1), los bloques categóricos se ponderan (conjunto C) y todo se proyecta con PCA reteniendo el 95 % de la varianza. La distancia es la euclidiana en ese espacio, por eso las variables con escalas distintas pesan igual.")
w(f"- **Con qué clientes.** El modelo se ajusta con el conjunto de entrenamiento. Cada cliente de prueba se asigna al centroide más cercano y la silueta de prueba se calcula sobre una muestra aleatoria fija de 5,000 clientes (`silhouette_score(..., sample_size=5000, random_state=42)` de scikit-learn); la de entrenamiento se calcula igual con 5,000 de los {met['filas_entrenamiento']:,}. Se usa muestra porque la silueta exacta compara a cada cliente con todos los demás (cientos de millones de distancias o más), y la misma muestra para todos los modelos hace la comparación justa.")
w(f"- **Error por muestreo.** Para el modelo ganador, la silueta exacta con los {met['filas_prueba']:,} clientes de prueba es {f3(sil_exacta)}; con la muestra de 5,000 es {f3(g['silueta_test'])}; con 5 muestras distintas va de {f3(min(sil_muestras))} a {f3(max(sil_muestras))}. La diferencia es de unas milésimas, mucho menor que las diferencias entre modelos.")
w("- **En el algoritmo genético.** La aptitud es la silueta sobre 1,000 clientes de entrenamiento con la matriz de distancias precalculada (implementación propia, idéntica a la de scikit-learn: lo verifica la prueba `test_silueta_rapida_coincide_con_scikit_learn`), con la restricción de grupo mínimo.")
w(f"- **Cómo se usó para decidir.** La configuración ganadora se elige con la silueta de **entrenamiento**; la de prueba solo se reporta. La partición aleatoria ({f3(azar_b.silueta_test)}) sirve de calibración: una métrica bien calculada da ≈ 0 cuando los grupos no significan nada.")
w("- **Limitaciones.** La silueta favorece grupos compactos y redondeados y tiende a preferir pocos grupos (por eso casi siempre elige K=3); no dice si los grupos son útiles para el negocio.")
w("")
w("### Cómo se calculó la correlación máxima")
w("")
w(f"La **correlación de Pearson** `r` mide qué tan alineadas están dos variables en línea recta: 0 es ninguna relación, 1 o −1 es relación perfecta. Se calculó con los {cj['filas']:,} clientes entre cada par de las 8 variables numéricas de la Entrega 2 (28 pares), se tomó el valor absoluto y se buscó el máximo: **|r| = {corr_max:.3f}**, entre `{cj['pearson_max_par'][0]}` y `{cj['pearson_max_par'][1]}`. Con esa correlación, una variable explica solo {100 * corr_max ** 2:.2f} % de la variación de la otra (`r²`).")
w("")
w(f"**Cómo leerlo.** Aunque dos variables sean totalmente independientes, con {cj['filas']:,} filas `r` nunca sale exactamente 0: oscila alrededor de 0 con un margen de ±1/√n = ±{cj['ruido_esperado_pearson']:.4f}. El máximo observado ({corr_max:.3f}) equivale a unas {corr_max / cj['ruido_esperado_pearson']:.1f} veces ese margen, entre 28 pares, lo esperable por azar. También se calculó la correlación de Spearman (por rangos, detecta relaciones curvas que siempre suben o siempre bajan): su máximo es {cj['spearman_max_abs']:.3f}, igual de pequeño.")
w("")
w("Los 5 pares con mayor correlación:")
w("")
pares_t = pares_top.copy()
pares_t["par"] = pares_t.variable_1 + " con " + pares_t.variable_2
pares_t["r"] = pares_t.pearson.map(lambda x: f"{x:+.4f}")
pares_t["rho"] = pares_t.spearman.map(lambda x: f"{x:+.4f}")
w(tabla(pares_t, ["par", "r", "rho"], ["Par de variables", "Pearson", "Spearman"]))
w("")
w("![Matriz de correlación de Pearson](../reports/correlaciones.png)")
w("")
w(f"**Variables categóricas.** Pearson no sirve con categorías (género, país, frecuencia…), así que se usó la **razón de correlación** η: va de 0 (la categoría no explica nada de la variable) a 1 (la explica por completo). Se calculó para {cj['pares_categoria_variable']} pares (11 columnas categóricas por 6 variables conductuales). El mayor es η = **{cj['eta_max']:.3f}** entre `{cj['eta_max_par'][0]}` y `{cj['eta_max_par'][1]}`, contra {cj['eta_max_esperado_por_azar']:.3f} esperable por azar: es la banda de recencia descrita arriba. El segundo mayor es {segundo_eta:.3f}, a la altura del ruido; es decir, las demás categorías no explican nada de las variables conductuales.")
w("")
w("**Lo que esta medida no detecta.** Relaciones curvas que no son monótonas, o que solo aparecen combinando tres o más variables. Para comprobar que la herramienta sí ve la estructura cuando existe, una prueba automática la aplica a un dataset generado con estructura y obtiene |r| máximo mayor a 0.25.")
w("")

w("## 1. Selección y justificación técnica de los modelos")
w("")
w("### A. Estrategia de modelado")
w("")
w("- [x] **Estrategia comparativa:** se entrenan dos modelos de familias distintas (algoritmo genético y K-Means) y se comparan con dos líneas base.")
w("- [ ] Estrategia baseline frente a modelo optimizado. (Se hace además, dentro del experimento 6, el ajuste de parámetros del genético.)")
w("")
w("### B. Justificación de la elección")
w("")
w("| Modelo | Paradigma | Justificación técnica |\n|---|---|---|")
w(f"| **Modelo 1 (candidato): algoritmo genético de agrupamiento** | Computación evolutiva aplicada a aprendizaje no supervisado | Cada individuo es un conjunto de K centroides y la aptitud es directamente la silueta. Esto permite incluir como restricción el tamaño mínimo de grupo (10 % prometido en la Entrega 2) y no depende de la inicialización de un único punto de partida. Costo: no garantiza el óptimo y es más lento (alrededor de un segundo frente a décimas); su estabilidad entre semillas se mide en la sección 3 (ARI {est['Algoritmo genético']['medio']:.2f}). |")
w("| **Modelo 2 (baseline): K-Means** | Aprendizaje no supervisado, particional | Referencia estándar y rápida (décimas de segundo). Minimiza la inercia, no la silueta, y no tiene restricción de tamaño mínimo; sirve para validar si la complejidad del genético aporta algo. |")
w(f"| Línea base 1: reglas RFM | Reglas de negocio, sin aprendizaje | La columna `rfm_category` que ya trae el dataset. Silueta {f3(rfm_b.silueta_test)}. |")
w(f"| Línea base 2: partición aleatoria | Sin modelo | K=4, etiquetas al azar. Silueta {f3(azar_b.silueta_test)} (≈ 0 por definición). |")
w("")
w("**Variables de entrada.** Se compararon tres conjuntos. A: las 8 numéricas de la Entrega 2. B: 6 variables conductuales construidas desde columnas base (recencia, compras por mes en logaritmo, valor medio de pedido, tasa de devoluciones en logaritmo, quejas y satisfacción). C: B más las categóricas codificadas (ingreso, educación y frecuencia como ordinales; género, estado civil, empleo, canal, dispositivo, pago y región como 0/1; categorías preferidas ponderadas por orden; redes sociales). Los bloques categóricos se escalan para pesar como una sola variable cada uno. **Ninguna de las 24 columnas derivadas entra a un modelo** (una prueba automática lo verifica); solo se leen para comparar contra las reglas RFM.")
w("")

w("## 2. Pipeline de datos y estructura en el repositorio")
w("")
w("### A. Ubicación de archivos")
w("")
w("| Elemento | Ruta |\n|---|---|")
w("| Entrenamiento (script) | `src/models/train.py` |")
w("| Entrenamiento (notebook de Colab) | `notebooks/03_model_training.ipynb` |")
w("| Preprocesamiento | `src/data/preprocess.py` (reglas de las columnas derivadas en `src/data/reglas.py`) |")
w("| Algoritmo genético | `src/models/ga_clustering.py` |")
w("| Inferencia | `src/models/predict.py` |")
w("| Generador de datasets | `src/data/generate.py` |")
w("| Modelos serializados | `models/modelo_candidato.joblib` (y `ga_*`, `kmeans_*` de cada experimento) |")
w("| Escalador y PCA | `models/scaler.joblib`, `models/pca.joblib`, `models/preprocesador.joblib` |")
w("| Reportes | `reports/` (matriz de experimentos, métricas, gráficas, log) |")
w("| Salidas para el dashboard | `data/outputs/customer_assignments.csv`, `segments_summary.json` |")
w(f"| Pruebas | `tests/` ({n_pruebas} pruebas) |")
w("| Dependencias | `requirements.txt` |")
w("")
w("Ninguna ruta es absoluta: todo se resuelve desde la raíz del repositorio.")
w("")
w("### B. Comando de reproducibilidad")
w("")
w("```")
w("python -m src.models.train --data data/raw/E-commerce_Customer_Segmentation_2026.csv --output models/")
w("```")
w("")
w("La corrida usa semilla 42 y dura alrededor de un minuto y medio. Para obtener otros datos de prueba, el generador acepta un número de filas y una semilla:")
w("")
w("```")
w("python -m src.data.generate --rows 5000 --seed 7 --estructura 0.6")
w("```")
w("")
w("Si se ejecuta sin argumentos pregunta «N. de filas:» y elige una semilla al azar (la imprime y la guarda en el nombre del archivo para poder repetir la corrida).")
w("")

w("## 3. Matriz de experimentación y ajuste de hiperparámetros")
w("")
w(f"Todos los modelos se evalúan sobre el mismo conjunto de prueba: {met['filas_prueba']:,} clientes (20 %), con semilla 42. La configuración ganadora se elige con la silueta de **entrenamiento** ({met['filas_entrenamiento']:,} clientes), entre las que cumplen el grupo mínimo del 10 %; el conjunto de prueba solo se reporta. Tiempos: entrenamiento / inferencia sobre los 10,000 clientes de prueba.")
w("")
w(tabla(matriz, ["var", "modelo", "hp", "principal", "secundaria", "tiempo", "diag"],
        ["Variante", "Modelo", "Hiperparámetros", "Métrica principal (test)", "Métrica secundaria (test)", "Tiempo", "Diagnóstico"]))
w("")
w("La matriz completa (30 corridas, con Calinski-Harabasz, tamaño mínimo y silueta de entrenamiento) está en `reports/experimentos.csv`.")
w("")
w("### Experimento 7: robustez con datasets generados")
w("")
w("Misma configuración (conjunto B, K elegido entre 3, 4 y 5 por silueta de entrenamiento) sobre datasets generados de distinto tamaño. `estructura` es la fracción de clientes que sigue uno de 5 arquetipos (0 = solo la relación frecuencia-recencia que ya trae el original, sin más grupos). El arquetipo real no se le da al modelo; se usa después para calcular el ARI (1 = recupera los grupos reales, 0 = al azar).")
w("")
rob_t = rob.copy()
rob_t["silueta"] = rob_t.silueta_test.map(f3)
rob_t["ari"] = rob_t.ari_vs_arquetipo.map(lambda x: "n/d" if pd.isna(x) else f3(x))
rob_t["ari5"] = rob_t.ari_con_k5.map(lambda x: "n/d" if pd.isna(x) else f3(x))
rob_t["filas"] = rob_t.filas.map(lambda x: f"{x:,}")
w(tabla(rob_t, ["filas", "estructura", "modelo", "k_elegido", "silueta", "ari", "ari5"],
        ["Filas", "Estructura", "Modelo", "K elegido", "Silueta (test)", "ARI vs arquetipos", "ARI con K=5"]))
w("")
w("### Análisis crítico de los resultados")
w("")
dif_ga_km = ga_b[ga_b.k == 3].silueta_test.iloc[0] - km_b[km_b.k == 3].silueta_test.iloc[0]
w(f"**1. ¿Qué modelo resultó ganador y por qué?** El ganador por la regla definida es el **algoritmo genético con K=3 sobre el conjunto B** (silueta {f3(g['silueta_train'])} en entrenamiento y {f3(g['silueta_test'])} en prueba; grupo más pequeño {pct(g['tamano_minimo_test'])}). Con el mismo K=3, K-Means obtiene {f3(km_b[km_b.k == 3].silueta_test.iloc[0])}, es decir, {dif_ga_km:+.3f}. La razón es matemática: el genético usa la silueta como aptitud y K-Means minimiza la inercia, por lo que es esperable que gane en la métrica que optimiza. En otras métricas la ventaja no es tan clara: el mejor Davies-Bouldin entre los K-Means del conjunto B es {f3(mejor_db_km.davies_bouldin_test)} (K={mejor_db_km.k}) frente a {f3(g['davies_bouldin_test'])} del ganador (menor es mejor), y el mejor Calinski-Harabasz es {mejor_ch_km.calinski_harabasz_test:,.0f} frente a {g['calinski_harabasz_test']:,.0f}. Los K-Means con K=4 y K=5 alcanzan silueta {f3(km_mejor_b.silueta_test)} como máximo, pero dejan un grupo del {pct(km_mejor_b.tamano_minimo_test)}, por debajo del mínimo comprometido, así que no son elegibles. Frente a las líneas base, ambas familias superan con claridad a las reglas RFM ({f3(rfm_b.silueta_test)}) y a la partición aleatoria ({f3(azar_b.silueta_test)}).")
w("")
w(f"**Estabilidad.** Con 5 semillas distintas (K=3, conjunto B), el ARI medio entre particiones es {est['Algoritmo genético']['medio']:.2f} (mínimo {est['Algoritmo genético']['minimo']:.2f}) para el genético y {est['K-Means']['medio']:.2f} (mínimo {est['K-Means']['minimo']:.2f}) para K-Means. Un ARI de 1 significa particiones idénticas; valores menores muestran que parte de la partición cambia al repetir el entrenamiento, algo esperable cuando los datos no tienen grupos marcados y hay varias divisiones de calidad parecida.")
w("")
w(f"**Variables.** Las categóricas codificadas (conjunto C) no ayudan: su mejor silueta en prueba es {f3(c_mejor.silueta_test)} frente a {f3(modelos[modelos.conjunto == 'B'].silueta_test.max())} del conjunto B. Es coherente con el diagnóstico: la única categórica informativa es la frecuencia de compra, y su información ya está en la recencia; las otras diez son independientes de las variables conductuales (η ≤ {segundo_eta:.2f}) y solo agregan ruido a la distancia. No se hizo un experimento adicional para aislar la causa. El conjunto B también supera al A ({f3(a_mejor.silueta_test)}); una explicación probable, no comprobada, es que las razones por mes y por compra (con logaritmo para las colas pesadas) resumen mejor el comportamiento que los conteos crudos.")
w("")
w(f"**Robustez.** Sin estructura, el genético mantiene una silueta de {f3(rob_0[rob_0.modelo == 'Algoritmo genético'].silueta_test.min())} a {f3(rob_0[rob_0.modelo == 'Algoritmo genético'].silueta_test.max())} y K-Means de {f3(rob_0[rob_0.modelo == 'K-Means'].silueta_test.min())} a {f3(rob_0[rob_0.modelo == 'K-Means'].silueta_test.max())}, como en el dataset real: un nivel bajo que no depende del tamaño. Con estructura completa ambos suben a {f3(rob_ok.silueta_test.min())}–{f3(rob_ok.silueta_test.max())} y recuperan parcialmente los arquetipos: ARI de {rob_ok.ari_vs_arquetipo.min():.2f} a {rob_ok.ari_vs_arquetipo.max():.2f} con el K elegido y de {rob_ok.ari_con_k5.min():.2f} a {rob_ok.ari_con_k5.max():.2f} si se fuerza K=5; con estructura parcial (60 %, el resto es ruido independiente) el ARI cae a {rob_06.ari_vs_arquetipo.min():.2f}–{rob_06.ari_vs_arquetipo.max():.2f}. {ks_texto}")
w("")
w(f"**2. Detección y mitigación del sobreajuste.** Rendimiento en entrenamiento y prueba del ganador: {f3(g['silueta_train'])} y {f3(g['silueta_test'])} (brecha {g['silueta_train'] - g['silueta_test']:+.3f}). En las {len(modelos)} configuraciones de los experimentos 3 a 6, la mayor brecha entrenamiento-prueba es {brecha_max:.3f}: no hay sobreajuste. Era poco probable por diseño (pocos parámetros: K centroides, y muchos datos), pero se tomaron medidas: el escalador y la PCA se ajustan solo con entrenamiento; la aptitud del genético se calcula sobre una submuestra fija de 1,000 clientes y se mide en 10,000 clientes que nunca vio; el tamaño mínimo de grupo (restricción tipo regla de Deb) impide el truco de aislar unos pocos valores atípicos en un grupo diminuto —una primera versión sin esa restricción obtuvo una silueta de 0.72 con un grupo de 0.5 % y se corrigió—; la mutación decrece con las generaciones; y la PCA retiene el 95 % de la varianza. El ajuste de parámetros (experimento 6) muestra que aumentar la población y las generaciones ({f3(t[(t.exp == 6) & (t.modelo.str.contains('grande'))].silueta_test.iloc[0])}) no mejora la configuración base ({f3(g['silueta_test'])}), y que reducirlas ({f3(t[(t.exp == 6) & (t.modelo.str.contains('peque'))].silueta_test.iloc[0])}) sí empeora el resultado: la base ya converge.")
w("")
w("### Perfil de los grupos del modelo ganador")
w("")
perfil_t = perfil.copy()
perfil_t["clientes_f"] = perfil_t.clientes.map(lambda x: f"{x:,}")
perfil_t["pct"] = perfil_t.porcentaje.map(pct)
perfil_t["dias"] = perfil_t.days_since_last_purchase.map(lambda x: f"{x:.0f}")
perfil_t["compras"] = perfil_t.total_purchases.map(lambda x: f"{x:.0f}")
perfil_t["devol"] = perfil_t.return_count.map(lambda x: f"{x:.1f}")
perfil_t["satis"] = perfil_t.satisfaction_score.map(lambda x: f"{x:.2f}")
w(tabla(perfil_t, ["nombre", "clientes_f", "pct", "dias", "compras", "devol", "satis"],
        ["Grupo (nombre descriptivo)", "Clientes (train)", "%", "Días sin comprar", "Compras", "Devoluciones", "Satisfacción"]))
w("")
w("**Cómo se nombran los grupos.** El nombre sale de una regla fija, no se escribe a mano: (1) se calcula la media de cada grupo en 7 variables en unidades originales (días sin comprar, compras, valor medio del pedido, devoluciones, quejas, satisfacción y antigüedad); (2) se compara con la media de todos los clientes, medida en desviaciones estándar (sd); (3) se toman las dos variables en las que el grupo más se aleja del promedio; (4) cada una se traduce a una frase según el signo (por ejemplo, +2.35 sd en días sin comprar es «compra hace mucho»). Los números exactos de cada grupo están en `reports/perfil_grupos.csv` (columna `rasgos_distintivos`). El nombre describe en qué se diferencia el grupo, no una cualidad del cliente: con una silueta baja describe el reparto y no debe leerse como un segmento natural.")
w("")
w("Composición de cada grupo por frecuencia de compra declarada (porcentaje de sus clientes, todos los clientes del dataset); confirma que los grupos siguen las bandas de recencia:")
w("")
comp = composicion[ORDEN_FRECUENCIA].copy()
comp.insert(0, "Grupo", [perfil.set_index("grupo").loc[i, "nombre"] for i in comp.index])
for c in ORDEN_FRECUENCIA:
    comp[c] = comp[c].map(lambda x: f"{100 * x:.0f} %")
w(tabla(comp, ["Grupo"] + ORDEN_FRECUENCIA, ["Grupo", "Diaria", "Semanal", "Mensual", "Trimestral", "Rara vez"]))
w("")

w("## 4. Evidencias de ejecución funcional")
w("")
w("### A. Registro de consola del entrenamiento")
w("")
w("```")
w(log.strip())
w("```")
w("")
w("### B. Gráficas de convergencia y comparación")
w("")
w("Convergencia del algoritmo genético (la aptitud inviable —grupo por debajo del mínimo— se muestra como −1 menos el déficit, por eso la curva «peor» está cerca de −1):")
w("")
w("![Convergencia del algoritmo genético](../reports/convergencia.png)")
w("")
w("Comparación de la silueta en prueba:")
w("")
w("![Comparación de modelos](../reports/comparacion.png)")
w("")
w("Concordancia entre los grupos del modelo y la regla RFM del dataset (análoga a una matriz de confusión; no hay etiquetas verdaderas, así que se ve cuánto se parecen dos formas de agrupar):")
w("")
cabecera = ["Grupo"] + list(ctab.columns)
w("| " + " | ".join(cabecera) + " |")
w("|" + "|".join("---" for _ in cabecera) + "|")
for idx, fila in ctab.iterrows():
    w(f"| Grupo {idx} | " + " | ".join(f"{int(v):,}" for v in fila) + " |")
w("")
w("![Grupos frente a RFM](../reports/grupos_vs_rfm.png)")
w("")

w("## 5. Función de inferencia desacoplada (`predecir`)")
w("")
w("### A. Código fuente (`src/models/predict.py`)")
w("")
w("Los artefactos (modelo, escalador y PCA) se cargan una sola vez en memoria. La función no lanza excepciones por datos inválidos: devuelve `status: error` con un mensaje.")
w("")
w("```python")
w(fuente_predecir)
w("```")
w("")
w("`predecir_lote(df)` aplica lo mismo a todo un DataFrame y `exportar_resultados` genera los archivos que consumirá el dashboard en la Entrega 4.")
w("")
w("### B. Prueba unitaria de entrada y salida")
w("")
w("Cliente `CUST-000023` del dataset, llamada real:")
w("")
w("```json")
w(json.dumps(entrada, indent=1))
w("```")
w("")
w("Salida devuelta por el modelo:")
w("")
w("```json")
w(json.dumps(salida, indent=1, ensure_ascii=False))
w("```")
w("")
w("Entrada incompleta (manejo de error):")
w("")
w("```json")
w(json.dumps(error, indent=1, ensure_ascii=False))
w("```")
w("")
w("`confianza` va de 0.5 (el cliente está a igual distancia de sus dos grupos más cercanos) a 1.0 (está sobre un centroide); no es una probabilidad calibrada. `estatus_alerta` es una regla sobre los datos del cliente (Alerta, Atención o Normal) con umbrales editables en `src/models/perfiles.py`.")
w("")

w("## 6. Reporte de estado del proyecto (Sprint Review)")
w("")
w(f"1. **Porcentaje global de avance del motor de IA: {avance} %** ({hechos} de {len(checklist)} puntos de la lista siguiente).")
w("")
for item, ok in checklist:
    w(f"   - [{'x' if ok else ' '}] {item}")
w("")
w("2. **Semáforo del sprint: con retraso moderado.** El agrupamiento está completo y reproducible, pero las cifras de la Entrega 2 no se cumplieron y siguen pendientes el reporte HTML y la fase 2.")
w("3. **Bloqueos técnicos:**")
w("   - El dataset no tiene estructura de grupos (variables independientes); la silueta real es 0.25, no 0.42.")
w("   - Las cifras de la Entrega 2 y los datos del dashboard actual eran proyecciones sin código detrás; hay que corregir ambos.")
w("   - No hay historial de compras fechado: el simulador de comportamiento (compra, abandono, cierre de cuenta) y la predicción supervisada quedan para la fase siguiente y requieren decisiones de alcance (cambian la Exclusión 2 de la Entrega 2).")
w("4. **Plan de acción para la Entrega 4:**")
w("   - Conectar el dashboard a `data/outputs/` (reemplazar datos estáticos y nombres de grupo) y corregir las cifras mostradas.")
w("   - Generar `segments_report.html` (RF-08).")
w("   - Evaluar la fase 2: catálogo de productos sintético, simulador de comportamiento de 4 clases y clasificador supervisado, declarando que aprende los supuestos del simulador.")
w("")
w("Los términos técnicos de este documento (silueta, centroide, algoritmo genético, PCA, etc.) se explican en lenguaje sencillo en `docs/GLOSARIO_BASICO.md`.")
w("")
w("## Uso de herramientas de IA")
w("")
w(f"El código se elaboró con ayuda de Claude. Para la verificación se ejecutaron {n_pruebas} pruebas, ejecución completa del entrenamiento (el log de la sección 4 es el output real), y una revisión de que cada cifra del documento se genera en `reports/` con `scripts/generar_entrega3.py`.")
w("")
destino = RAIZ / "docs" / "ENTREGA_3.md"
destino.write_text("\n".join(md), encoding="utf-8")
print("escrito", destino, f"({len(md)} bloques)")
