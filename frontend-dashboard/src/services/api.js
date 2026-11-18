// Carga de los archivos que genera el motor de IA (src/models/exportar_dashboard.py).
// Contrato de datos: el dashboard no calcula nada del modelo, solo lee y presenta estos archivos.
const BASE = import.meta.env.BASE_URL

async function cargarJson(ruta) {
  const respuesta = await fetch(`${BASE}data/${ruta}`)
  if (!respuesta.ok) throw new Error(`No se pudo cargar ${ruta} (${respuesta.status}). Ejecute: python -m src.models.exportar_dashboard`)
  return respuesta.json()
}

export const cargarDashboard = () => cargarJson('dashboard.json')
export const cargarModelo = () => cargarJson('model.json')

// customers.json viene en columnas + filas para pesar menos; aquí se convierte a objetos.
export async function cargarClientes() {
  const { columns, rows } = await cargarJson('customers.json')
  return rows.map((fila) => Object.fromEntries(columns.map((c, i) => [c, fila[i]])))
}

export const DESCARGAS = {
  csv: `${BASE}exports/customer_assignments.csv`,
  reporte: `${BASE}exports/segments_report.html`,
}
