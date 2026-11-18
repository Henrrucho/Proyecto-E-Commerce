// Prueba de paridad: los agregados que el navegador calcula (src/lib/resumen.js) con los 50,000 clientes REALES
// deben ser idénticos a los que escribió Python en public/data/dashboard.json. Si lo son, las mismas vistas
// dibujadas con clientes simulados son comparables con las del dataset original.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { resumir } from '../src/lib/resumen.js'
import { categoriaRfm, estatusActividad, evaluarSimulacion, nivelLealtad, simularClientes } from '../src/lib/simular.js'

const leer = (ruta) => JSON.parse(readFileSync(new URL(ruta, import.meta.url), 'utf8'))
const modelo = leer('../public/data/model.json')
const dashboard = leer('../public/data/dashboard.json')
const clientes = leer('../public/data/customers.json')
const CSV = new URL('../../data/raw/E-commerce_Customer_Segmentation_2026.csv', import.meta.url)

// Lector de CSV mínimo (campos entre comillas con comas dentro, como social_media_presence)
function leerCsv(texto) {
  const filas = []
  let fila = []
  let campo = ''
  let comillas = false
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i]
    if (comillas) {
      if (c === '"' && texto[i + 1] === '"') { campo += '"'; i++ } else if (c === '"') comillas = false
      else campo += c
    } else if (c === '"') comillas = true
    else if (c === ',') { fila.push(campo); campo = '' } else if (c === '\n') { fila.push(campo.replace(/\r$/, '')); filas.push(fila); fila = []; campo = '' } else campo += c
  }
  if (campo || fila.length) { fila.push(campo); filas.push(fila) }
  const [encabezado, ...resto] = filas
  return resto.filter((f) => f.length === encabezado.length).map((f) => Object.fromEntries(encabezado.map((h, i) => [h, f[i]])))
}

const cat = modelo.catalogos
// En el CSV el cliente sin nivel viene como «None» (pandas lo lee como vacío y el motor lo imputa como «No Tier»)
const nivel = (r) => (['', 'None'].includes(r.loyalty_tier) ? 'No Tier' : r.loyalty_tier)
const crudos = leerCsv(readFileSync(CSV, 'utf8'))
const asignado = new Map(clientes.rows.map((f) => [f[0], { cluster: f[1], estatus: f[6] }]))
const reales = crudos.map((r) => ({
  customer_id: r.customer_id, country: r.country, categoria: cat.categoriasEs[r.preferred_category_1],
  social_media_presence: r.social_media_presence || 'None', conversion_rate: +r.conversion_rate, email_open_rate: +r.email_open_rate,
  click_through_rate: +r.click_through_rate, customer_acquisition_cost_usd: +r.customer_acquisition_cost_usd,
  customer_lifetime_value_usd: +r.customer_lifetime_value_usd, loyalty_tier: nivel(r), total_spent_usd: +r.total_spent_usd,
  rfm_category: r.rfm_category, activity_status: r.activity_status, churn_risk_category: r.churn_risk_category,
  return_count: +r.return_count, complaint_count: +r.complaint_count, satisfaction_score: +r.satisfaction_score,
  days_since_last_purchase: +r.days_since_last_purchase, total_purchases: +r.total_purchases, tenure_months: +r.tenure_months,
  avg_order_value_usd: +r.avg_order_value_usd, ...asignado.get(r.customer_id),
}))

function diferencias(a, b, ruta = '') {
  if (typeof a !== typeof b || a === null || b === null) return a === b ? [] : [`${ruta}: ${JSON.stringify(a)} != ${JSON.stringify(b)}`]
  if (typeof a === 'object') {
    const claves = new Set([...Object.keys(a), ...Object.keys(b)])
    return [...claves].flatMap((k) => diferencias(a[k], b[k], `${ruta}.${k}`))
  }
  return a === b ? [] : [`${ruta}: ${a} != ${b}`]
}

test('el CSV real se leyó completo y cada cliente tiene su grupo', () => {
  assert.equal(reales.length, 50000)
  assert.ok(reales.every((f) => Number.isInteger(f.cluster)))
})

test('las reglas del simulador reproducen las columnas derivadas del dataset original', () => {
  const malas = crudos.filter((r) => categoriaRfm(+r.rfm_score) !== r.rfm_category || estatusActividad(+r.days_since_last_purchase) !== r.activity_status
    || nivelLealtad(+r.total_spent_usd) !== nivel(r))
  assert.equal(malas.length, 0, `${malas.length} clientes no coinciden`)
})

for (const parte of ['clusters', 'alertas', 'recomendaciones', 'zonas', 'paises']) {
  test(`el navegador reproduce «${parte}» de dashboard.json con los clientes reales`, () => {
    const resumen = resumir(reales, modelo)
    const dif = diferencias(resumen[parte], dashboard[parte], parte)
    assert.deepEqual(dif.slice(0, 8), [], `${dif.length} diferencias`)
  })
}

test('el navegador reproduce «insights» (global y por grupo) con los clientes reales', () => {
  const resumen = resumir(reales, modelo)
  const dif = diferencias(resumen.insights, dashboard.insights, 'insights')
  assert.deepEqual(dif.slice(0, 8), [], `${dif.length} diferencias`)
})

test('los clientes simulados sin estructura se parecen a los reales en las columnas derivadas', () => {
  const sim = simularClientes(modelo, 20000, 0, 21)
  const fr = (filas, f) => filas.filter(f).length / filas.length
  const media = (filas, c) => filas.reduce((s, x) => s + x[c], 0) / filas.length
  const comparar = (nombre, f, tolerancia) => assert.ok(Math.abs(fr(sim, f) - fr(reales, f)) < tolerancia, `${nombre}: ${fr(sim, f)} frente a ${fr(reales, f)}`)
  comparar('riesgo de fuga alto', (x) => ['High', 'Very High'].includes(x.churn_risk_category), 0.02)
  comparar('sin nivel de lealtad', (x) => x.loyalty_tier === 'No Tier', 0.01)
  comparar('Diamante', (x) => x.loyalty_tier === 'Diamond', 0.01)
  comparar('Champions', (x) => x.rfm_category === 'Champions', 0.015)
  comparar('inactivos', (x) => x.activity_status === 'Inactive', 0.015)
  comparar('sin red social', (x) => x.social_media_presence === 'None', 0.015)
  for (const campo of ['customer_lifetime_value_usd', 'total_spent_usd', 'customer_acquisition_cost_usd']) {
    assert.ok(Math.abs(media(sim, campo) / media(reales, campo) - 1) < 0.05, campo)
  }
})

test('las vistas de la simulación se arman con la misma función que las del dataset original', () => {
  const sim = simularClientes(modelo, 3000, 0.4, 5)
  const evaluacion = evaluarSimulacion(modelo, sim, 5)
  const filas = sim.map((c, i) => ({ ...c, cluster: evaluacion.grupos[i], estatus: evaluacion.estatus[i] }))
  const r = resumir(filas, modelo)
  assert.equal(r.clusters.reduce((s, g) => s + g.clientes, 0), 3000)
  assert.equal(r.tabla.length, 3000)
  assert.equal(r.alertas.length, 4)
  assert.equal(r.recomendaciones.length, 4)
  assert.equal(Object.keys(r.insights).length, 1 + modelo.k)
  assert.ok(Object.keys(r.zonas).includes('Todas las zonas'))
})
