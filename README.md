# E-Commerce AI: Inteligencia Artificial para la gestión y personalización de clientes

Prototipo de sistema inteligente de segmentación de clientes (50,000 registros y 53 variables) mediante PCA y K-Means, con comparación frente a reglas de negocio y dashboard web interactivo.

## Estructura del Proyecto
- `data/raw/`: Dataset original intacto (Solo lectura - RNF-IA-02).
- `data/processed/`: Datos limpios y reportes de diagnóstico (Actividad A3).
- `data/outputs/`: Salidas del modelo (JSON, CSV y HTML) para integración con el Dashboard (Mitigación R-07).
- `ai-engine/`: Cuadernos de Google Colab y scripts en Python (PCA + K-Means).
- `backend-api/`: API REST en Node.js para comunicación de datos.
- `frontend-dashboard/`: Interfaz web interactiva (Consulta, filtrado y exportación).
- `docs/`: Diccionario de datos, manual de usuario y evidencias de pruebas.
