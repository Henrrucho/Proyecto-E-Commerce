"""Genera notebooks/03_model_training.ipynb (la misma corrida de train.py, para Colab o Jupyter)."""
from pathlib import Path

import nbformat as nbf

RAIZ = Path(__file__).resolve().parents[1]
REPO = "https://github.com/Henrrucho/Proyecto-E-Commerce"

celdas = [
    nbf.v4.new_markdown_cell(
        "# Ecommerce AI: entrenamiento y experimentación (Entrega 3)\n\n"
        "Fundamentos de Inteligencia Artificial · LITIID73\n\n"
        "Este notebook ejecuta **el mismo código del repositorio** (`src/`): no tiene lógica propia. "
        "Corre el entrenamiento completo, muestra la matriz de experimentos, las gráficas y una llamada real a `predecir()`.\n\n"
        "- En **Colab**: *Entorno de ejecución → Ejecutar todo*. Clona el repositorio solo.\n"
        "- En **local**: abrirlo desde `notebooks/` con el repositorio ya clonado."
    ),
    nbf.v4.new_code_cell(
        "import os, subprocess, sys\n\n"
        "# Ubica la raíz del repositorio; si no está (Colab), lo clona.\n"
        "if not os.path.exists('src'):\n"
        "    if os.path.exists('../src'):\n"
        "        os.chdir('..')\n"
        "    else:\n"
        f"        subprocess.run(['git', 'clone', '{REPO}'], check=True)\n"
        "        os.chdir('Proyecto-E-Commerce')\n"
        "if 'google.colab' in sys.modules:\n"
        "    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', 'requirements.txt'], check=True)\n"
        "print('Directorio de trabajo:', os.getcwd())"
    ),
    nbf.v4.new_markdown_cell("## 1. Entrenamiento\n\nComando de reproducibilidad (una línea):\n\n```\npython -m src.models.train --data data/raw/E-commerce_Customer_Segmentation_2026.csv --output models/\n```"),
    nbf.v4.new_code_cell(
        "r = subprocess.run([sys.executable, '-m', 'src.models.train', '--data', 'data/raw/E-commerce_Customer_Segmentation_2026.csv',\n"
        "                    '--output', 'models/'], capture_output=True, text=True, encoding='utf-8')\n"
        "print(r.stdout)\nprint(r.stderr)\n"
        "assert r.returncode == 0, 'el entrenamiento falló'"
    ),
    nbf.v4.new_markdown_cell("## 2. Matriz de experimentos\n\nSilueta y Davies-Bouldin sobre el conjunto de prueba (20 %). Conjuntos: A = 8 numéricas de la Entrega 2, B = 6 conductuales, C = B + categóricas codificadas."),
    nbf.v4.new_code_cell(
        "import pandas as pd\n"
        "pd.set_option('display.width', 200); pd.set_option('display.max_columns', 20)\n"
        "t = pd.read_csv('reports/experimentos.csv')\n"
        "t[['exp', 'modelo', 'conjunto', 'k', 'silueta_train', 'silueta_test', 'davies_bouldin_test', 'tamano_minimo_test',\n"
        "   'tiempo_entrenamiento_s', 'diagnostico']].round(3)"
    ),
    nbf.v4.new_markdown_cell("## 3. Gráficas"),
    nbf.v4.new_code_cell(
        "from IPython.display import Image, display\n"
        "for archivo in ['convergencia', 'comparacion', 'grupos_vs_rfm']:\n"
        "    display(Image(f'reports/{archivo}.png'))"
    ),
    nbf.v4.new_markdown_cell("## 4. Robustez con datasets generados\n\n`src/data/generate.py` crea datasets con el mismo esquema; `estructura` es la fracción de clientes que sigue un arquetipo (0 = variables independientes, como en el original)."),
    nbf.v4.new_code_cell("pd.read_csv('reports/robustez.csv').round(3)"),
    nbf.v4.new_markdown_cell("## 5. Inferencia: `predecir()`\n\nUna llamada real con un cliente del dataset y un caso de error."),
    nbf.v4.new_code_cell(
        "import json\n"
        "from src.models.predict import predecir\n\n"
        "cliente = pd.read_csv('data/raw/E-commerce_Customer_Segmentation_2026.csv').iloc[22].to_dict()\n"
        "campos = ['days_since_last_purchase', 'total_purchases', 'tenure_months', 'avg_order_value_usd', 'return_count', 'complaint_count', 'satisfaction_score']\n"
        "print('Entrada:', json.dumps({c: cliente[c] for c in campos}))\n"
        "print('Salida:', json.dumps(predecir(cliente), ensure_ascii=False, indent=1))\n"
        "print('Entrada incompleta:', json.dumps(predecir({'satisfaction_score': 3}), ensure_ascii=False))"
    ),
    nbf.v4.new_markdown_cell("## 6. Pruebas\n\n`pytest` verifica geometría, preprocesamiento sin fuga de datos, generador, algoritmo genético, contrato de `predecir()` y reproducibilidad."),
    nbf.v4.new_code_cell(
        "r = subprocess.run([sys.executable, '-m', 'pytest', 'tests', '-q'], capture_output=True, text=True, encoding='utf-8')\n"
        "print(r.stdout[-1500:])"
    ),
]
nb = nbf.v4.new_notebook(cells=celdas)
nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}, "language_info": {"name": "python"}}
for i, c in enumerate(nb.cells):
    c["id"] = f"c{i:02d}"
destino = RAIZ / "notebooks" / "03_model_training.ipynb"
nbf.write(nb, destino)
print("escrito", destino)
