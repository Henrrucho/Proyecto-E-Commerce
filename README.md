# Ecommerce AI

Motor de inteligencia artificial para segmentar clientes de comercio electrónico. Proyecto final de Fundamentos de Inteligencia Artificial (LITIID73, UT Cancún).

El sistema agrupa a los clientes sin etiquetas previas (aprendizaje no supervisado) con dos modelos que se comparan: un **algoritmo genético de agrupamiento** y **K-Means**, frente a dos líneas base (reglas RFM y partición aleatoria). Expone una función `predecir()` que asigna un cliente a un grupo y genera los archivos que consumirá el dashboard.

> **Estado:** Entrega 3 (motor de IA, sin interfaz). El dashboard se conecta en la Entrega 4. Las cifras de la Entrega 2 eran proyecciones; las reales están en [`docs/ENTREGA_3.md`](docs/ENTREGA_3.md).

## Reproducir en una línea

```bash
pip install -r requirements.txt
python -m src.models.train --data data/raw/E-commerce_Customer_Segmentation_2026.csv --output models/
```

Tarda alrededor de un minuto y medio, usa semilla 42 y deja modelos en `models/`, reportes en `reports/` y los archivos del dashboard en `data/outputs/`. También se puede correr en Colab con [`notebooks/03_model_training.ipynb`](notebooks/03_model_training.ipynb).

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

Crea un CSV con las mismas 53 columnas. Sin `--seed` elige una al azar y la imprime (queda en el nombre del archivo). `--estructura` (0 a 1) es la fracción de clientes que sigue un arquetipo; con 0 las variables son independientes, como en el dataset original. El arquetipo real se guarda aparte (`*_arquetipos.csv`) para evaluar al modelo, nunca en el CSV de entrada.

## Estructura

```
data/raw/        dataset original (solo lectura)
data/outputs/    customer_assignments.csv, segments_summary.json (para el dashboard)
src/data/        preprocess.py, reglas.py (columnas derivadas), generate.py
src/models/      train.py, ga_clustering.py, evaluacion.py, perfiles.py, predict.py
models/          modelos, escaladores y PCA serializados (.joblib)
reports/         matriz de experimentos, métricas, gráficas y log del entrenamiento
notebooks/       03_model_training.ipynb
tests/           pruebas con pytest
docs/            Entrega 3 (md, docx, pdf)
scripts/         generación del notebook y del documento
```

## Decisiones importantes

- **Sin fuga de datos:** las 24 columnas derivadas del dataset (por ejemplo `activity_status`, `rfm_category`) nunca entran como variables de entrada; una prueba lo verifica.
- **Tamaño mínimo de grupo:** el algoritmo genético trata como inviable cualquier partición con un grupo menor al 12 % (el compromiso es 10 %). Sin esa restricción aprendía a aislar unos pocos valores atípicos.
- **Elección del modelo:** con la silueta de entrenamiento; el conjunto de prueba (20 %) solo se reporta.
- **Los datos no tienen grupos marcados:** las variables son independientes, por lo que la silueta real es baja (≈ 0.25). Con datasets generados con estructura, el mismo código sí detecta grupos (experimento 7).

## Pruebas

```bash
python -m pytest tests -q
```

## Nota de seguridad

Los modelos se guardan con `joblib` (basado en `pickle`). Solo carguen los `.joblib` generados por este proyecto; no abran archivos de fuentes desconocidas.

## Equipo

María Tita Fregoso Arechiga, Henrry Misael Pech Pool, Jesús Alexander Recaman Lara y Gretel Dairen Zavaleta Moctezuma. Docente: Ing. Carlos André Castro Rodríguez.
