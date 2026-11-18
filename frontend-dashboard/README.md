# Dashboard de E-Commerce AI

React 19 + Vite + Tailwind 3 + Recharts. Es una página estática: no hay servidor ni variables de entorno.

Todo lo que muestra sale de `public/data/*.json`, que genera el motor de IA con `python -m src.models.exportar_dashboard` (desde la raíz del repositorio). La predicción de clientes nuevos corre en el navegador (`src/lib/predict.js`) con los parámetros de `public/data/model.json`.

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # genera dist/
npm test         # paridad de la predicción contra Python (300 clientes)
npm run lint
```

Requiere Node 24.19 y npm 11.
