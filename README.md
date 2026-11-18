# E-Commerce AI: Inteligencia Artificial para la gestión y personalización de clientes

Prototipo de sistema inteligente de segmentación de clientes (50,000 registros y 53 variables) con aprendizaje no supervisado: un **algoritmo genético de agrupamiento** comparado con **K-Means** y con reglas de negocio (RFM), más un dashboard web interactivo. Proyecto final de Fundamentos de Inteligencia Artificial (LITIID73, UT Cancún).

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Henrrucho/Proyecto-E-Commerce/blob/main/notebooks/03_model_training.ipynb)

> **Estado:** Entrega 4, sistema funcional. El dashboard lee las salidas reales del modelo y permite predecir clientes nuevos en el navegador. [`docs/ENTREGA_3.md`](docs/ENTREGA_3.md) es el informe histórico de la Entrega 3: el modelo se mejoró después (K = 4, silueta de prueba 0.178), así que sus cifras ya no coinciden con las de `reports/`.

**Modelo vigente:** algoritmo genético híbrido (semilla K-Means++), conjunto B de 6 variables de comportamiento, K = 4 grupos de 11.5 % a 44.6 % de los clientes, silueta 0.177 en entrenamiento y 0.178 en prueba.

## Guía rápida de despliegue y ejecución

**Versiones probadas:** Python 3.14.7 (numpy 2.5.3, pandas 3.0.6, scikit-learn 1.9.1, scipy 1.18.1, joblib 1.6.0, matplotlib 3.11.2, pytest 9.2.0; están fijadas en `requirements.txt`) y Node 24.19.0 con npm 11.17.0 (React 19, Vite 8, Tailwind 3, Recharts 3; fijadas en `package-lock.json`). No hay variables de entorno ni inicio de sesión (ver `.env.example`).

```bash
# 1. Motor de IA (opcional: los resultados ya vienen en el repositorio)
pip install -r requirements.txt
python -m src.models.train --data data/raw/E-commerce_Customer_Segmentation_2026.csv --output models/
python -m src.models.exportar_dashboard        # regenera frontend-dashboard/public/data y exports

# 2. Dashboard
cd frontend-dashboard
npm install
npm run dev                                    # http://localhost:5173
npm run build                                  # genera dist/ (lo que publica Netlify)
```

El entrenamiento tarda alrededor de un minuto y medio, usa semilla 42 y partición 80/20 (`--test-size 0.2`). Deja los modelos en `models/`, los reportes en `reports/` y los archivos del dashboard en `data/outputs/`. También se puede correr en Colab con [`notebooks/03_model_training.ipynb`](notebooks/03_model_training.ipynb).

**Despliegue en Netlify:** `netlify.toml` ya define la carpeta base (`frontend-dashboard`), el comando (`npm ci && npm run build`) y la carpeta publicada (`dist`). Basta con conectar el repositorio a un sitio de Netlify y elegir la rama `main`.

**Pruebas:** `python -m pytest tests -q` (motor y exportación) y `cd frontend-dashboard && npm test` (la predicción del navegador da el mismo grupo que Python en 300 clientes).

## Estructura del proyecto

```
data/raw/             Dataset original intacto (solo lectura)
data/processed/       clean_customers.csv (se regenera) y data_quality_report.json
data/outputs/         customer_assignments.csv, segments_summary.json, clustering_metrics.json (contrato con el dashboard)
src/data/             preprocess.py, reglas.py, diagnostico.py, generate.py
src/models/           train.py, ga_clustering.py, evaluacion.py, perfiles.py, predict.py, exportar_dashboard.py
models/               Modelos, escaladores y PCA serializados (.joblib)
reports/              Matriz de experimentos, correlaciones, gráficas y log del entrenamiento
notebooks/            03_model_training.ipynb (Colab)
tests/                Pruebas con pytest
docs/                 ENTREGA_3.md (informe con las cifras reales)
scripts/              Generación del notebook y del informe
frontend-dashboard/   Dashboard web (React + Vite + Recharts + Tailwind); public/data/ lo genera el motor
netlify.toml          Configuración de despliegue en Netlify
ai-engine/            Reservada: el motor de IA vive en src/ por la estructura que pide la plantilla de la Entrega 3
Proyecto_IA_E_Commerce.ipynb   Notebook inicial del equipo
```

## Inferencia

```python
from src.models.predict import predecir

predecir({"days_since_last_purchase": 12, "total_purchases": 194, "tenure_months": 118,
          "avg_order_value_usd": 872.32, "return_count": 12, "complaint_count": 2, "satisfaction_score": 5})
# {'cluster_id': 0, 'clase_etiqueta': 'Grupo 0: satisfecho y compra reciente', 'confianza': 0.6824, 'estatus_alerta': 'Normal', ..., 'status': 'success'}
```

Con datos inválidos o incompletos no lanza excepciones: devuelve `{"status": "error", "mensaje": ...}`. El dashboard (vista "Predicción de cliente") hace lo mismo en el navegador.

La vista "Simulación de clientes" fabrica N clientes nuevos con el procedimiento de `src/data/generate.py` (proporciones del dataset real), los pasa por el modelo y mide cuánto se parece su reparto al real, la silueta y, con estructura, si recupera los arquetipos (ARI). Además dibuja las mismas vistas del dashboard (panel, tendencias, recomendaciones y satisfacción) con los clientes simulados, junto a las del dataset original como referencia. El navegador usa otro generador de números aleatorios que numpy, así que con la misma semilla no salen los mismos clientes que en Python; lo que se conserva es la distribución, y las pruebas lo comprueban (los agregados que calcula el navegador con los 50,000 clientes reales son idénticos a los de `dashboard.json`). Con 0 % de estructura el modelo reparte a los clientes fabricados casi igual que a los reales (diferencia máxima < 1 pp con 5,000); con estructura recupera los arquetipos solo en parte (ARI ≈ 0.21), porque se entrenó con datos casi sin estructura.

## Generador de datos

```bash
python -m src.data.generate                                  # pregunta "N. de filas:"
python -m src.data.generate --rows 5000 --seed 7 --estructura 0.6
```

Crea un CSV con las mismas 53 columnas. Sin `--seed` elige una al azar y la imprime (queda en el nombre del archivo). `--estructura` (0 a 1) es la fracción de clientes que sigue un arquetipo; con 0 reproduce el dataset original (variables numéricas independientes y una sola relación fuerte: frecuencia de compra → días sin comprar). El arquetipo real se guarda aparte (`*_arquetipos.csv`) para evaluar al modelo, nunca en el CSV de entrada.

## Decisiones importantes

- **Sin fuga de datos:** las 24 columnas derivadas del dataset (por ejemplo `activity_status`, `rfm_category`) nunca entran como variables de entrada; una prueba lo verifica.
- **Tamaño de grupo:** el algoritmo genético trata como inviable cualquier partición con un grupo menor al 12 % o mayor al 55 % (el compromiso de la Entrega 2 es 10 % a 60 %). Sin esa restricción aprendía a aislar unos pocos valores atípicos.
- **Elección del modelo:** entre las configuraciones con grupos de 10 % a 60 %, gana la mejor combinación de silueta (40 %), Davies-Bouldin (30 %) y Calinski-Harabasz (30 %) en entrenamiento (80 %); el conjunto de prueba (20 %) solo se reporta.
- **Los datos casi no tienen grupos:** las variables numéricas son independientes y la única relación fuerte es frecuencia de compra → días sin comprar, por lo que la silueta real es baja. Con datasets generados con estructura, el mismo código sí detecta grupos (experimento 7).

## Pruebas

```bash
python -m pytest tests -q
```

## Nota de seguridad

Los modelos se guardan con `joblib` (basado en `pickle`). Solo carguen los `.joblib` generados por este proyecto; no abran archivos de fuentes desconocidas.

## Equipo

María Tita Fregoso Arechiga, Henrry Misael Pech Pool, Jesús Alexander Recaman Lara y Gretel Dairen Zavaleta Moctezuma. Docente: Ing. Carlos André Castro Rodríguez.
