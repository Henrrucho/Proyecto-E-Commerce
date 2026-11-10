# E-Commerce AI: Inteligencia Artificial para la gestión y personalización de clientes

Prototipo de sistema inteligente de segmentación de clientes (50,000 registros y 53 variables) con aprendizaje no supervisado: un **algoritmo genético de agrupamiento** comparado con **K-Means** y con reglas de negocio (RFM), más un dashboard web interactivo. Proyecto final de Fundamentos de Inteligencia Artificial (LITIID73, UT Cancún).

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Henrrucho/Proyecto-E-Commerce/blob/main/notebooks/03_model_training.ipynb)

> **Estado:** Entrega 3 (motor de IA, sin interfaz). Las cifras reales y su explicación están en [`docs/ENTREGA_3.md`](docs/ENTREGA_3.md); los términos técnicos, en [`docs/GLOSARIO_BASICO.md`](docs/GLOSARIO_BASICO.md). El dashboard se conecta a las salidas del modelo en la Entrega 4.

## Reproducir el entrenamiento (una línea)

```bash
pip install -r requirements.txt
python -m src.models.train --data data/raw/E-commerce_Customer_Segmentation_2026.csv --output models/
```

Tarda alrededor de un minuto y medio, usa semilla 42 y partición 80/20 (`--test-size 0.2`). Deja los modelos en `models/`, los reportes en `reports/` y los archivos del dashboard en `data/outputs/`. También se puede correr en Colab con [`notebooks/03_model_training.ipynb`](notebooks/03_model_training.ipynb).

## Estructura del proyecto

```
data/raw/             Dataset original intacto (solo lectura)
data/processed/       clean_customers.csv (se regenera) y data_quality_report.json
data/outputs/         customer_assignments.csv, segments_summary.json, clustering_metrics.json (contrato con el dashboard)
src/data/             preprocess.py, reglas.py, diagnostico.py, generate.py
src/models/           train.py, ga_clustering.py, evaluacion.py, perfiles.py, predict.py
models/               Modelos, escaladores y PCA serializados (.joblib)
reports/              Matriz de experimentos, correlaciones, gráficas y log del entrenamiento
notebooks/            03_model_training.ipynb (Colab)
tests/                Pruebas con pytest
docs/                 Entrega 3 (md, docx, pdf) y glosario básico
scripts/              Generación del notebook y del documento
frontend-dashboard/   Dashboard web (React + Vite + Recharts + Tailwind)
ai-engine/            Reservada: el motor de IA vive en src/ por la estructura que pide la plantilla de la Entrega 3
backend-api/          Sin uso: la Entrega 2 eliminó el servidor intermedio (los datos pasan por archivos en data/outputs/)
Proyecto_IA_E_Commerce.ipynb   Notebook inicial del equipo
```

## Inferencia

```python
from src.models.predict import predecir

predecir({"days_since_last_purchase": 12, "total_purchases": 194, "tenure_months": 118,
          "avg_order_value_usd": 872.32, "return_count": 12, "complaint_count": 2, "satisfaction_score": 5})
# {'cluster_id': 2, 'clase_etiqueta': 'Grupo 2: compra reciente y muchas compras', 'confianza': 0.58, ..., 'status': 'success'}
```

Con datos inválidos o incompletos no lanza excepciones: devuelve `{"status": "error", "mensaje": ...}`.

## Generador de datos

```bash
python -m src.data.generate                                  # pregunta "N. de filas:"
python -m src.data.generate --rows 5000 --seed 7 --estructura 0.6
```

Crea un CSV con las mismas 53 columnas. Sin `--seed` elige una al azar y la imprime (queda en el nombre del archivo). `--estructura` (0 a 1) es la fracción de clientes que sigue un arquetipo; con 0 reproduce el dataset original (variables numéricas independientes y una sola relación fuerte: frecuencia de compra → días sin comprar). El arquetipo real se guarda aparte (`*_arquetipos.csv`) para evaluar al modelo, nunca en el CSV de entrada.

## Decisiones importantes

- **Sin fuga de datos:** las 24 columnas derivadas del dataset (por ejemplo `activity_status`, `rfm_category`) nunca entran como variables de entrada; una prueba lo verifica.
- **Tamaño mínimo de grupo:** el algoritmo genético trata como inviable cualquier partición con un grupo menor al 12 % (el compromiso es 10 %). Sin esa restricción aprendía a aislar unos pocos valores atípicos.
- **Elección del modelo:** con la silueta de entrenamiento (80 %); el conjunto de prueba (20 %) solo se reporta.
- **Los datos casi no tienen grupos:** las variables numéricas son independientes y la única relación fuerte es frecuencia de compra → días sin comprar, por lo que la silueta real es baja. Con datasets generados con estructura, el mismo código sí detecta grupos (experimento 7).

## Pruebas

```bash
python -m pytest tests -q
```

## Nota de seguridad

Los modelos se guardan con `joblib` (basado en `pickle`). Solo carguen los `.joblib` generados por este proyecto; no abran archivos de fuentes desconocidas.

## Equipo

María Tita Fregoso Arechiga, Henrry Misael Pech Pool, Jesús Alexander Recaman Lara y Gretel Dairen Zavaleta Moctezuma. Docente: Ing. Carlos André Castro Rodríguez.
