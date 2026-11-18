// Clientes simulados: el mismo procedimiento que src/data/generate.py (proporciones tomadas del dataset real),
// pasados por el mismo modelo que los clientes reales para medir cómo se comporta con datos que no estaban en el entrenamiento.
// Los parámetros (frecuencias, rangos, arquetipos, países, categorías) vienen de public/data/model.json -> "simulador".
// Las reglas que derivan columnas (RFM, nivel de lealtad, estatus de actividad, riesgo de fuga) son las de src/data/reglas.py;
// tests/resumen.test.mjs comprueba que reproducen las columnas del dataset original.
//
// Ojo: el generador de números aleatorios del navegador no es el de numpy; con la misma semilla NO salen los mismos
// clientes que en Python, pero sí la misma distribución (src/data/generate.py sigue siendo la referencia).
import { estatusAlerta, proyectar } from './predict.js'

// mulberry32: generador pequeño y repetible (misma semilla -> mismos clientes en el navegador)
export function aleatorio(semilla) {
  let a = semilla >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const entero = (r, [minimo, maximo]) => minimo + Math.floor(r() * (maximo - minimo + 1))
const uniforme = (r, [minimo, maximo], decimales = 2) => {
  const f = 10 ** decimales
  return Math.round((minimo + r() * (maximo - minimo)) * f) / f
}
const normal = (r) => Math.sqrt(-2 * Math.log(1 - r())) * Math.cos(2 * Math.PI * r())

function elegir(r, tabla) {
  const claves = Object.keys(tabla)
  let u = r() * claves.reduce((s, c) => s + tabla[c], 0)
  for (const c of claves) {
    u -= tabla[c]
    if (u < 0) return c
  }
  return claves[claves.length - 1]
}

// ---- Reglas de src/data/reglas.py (cuántos límites quedan por debajo del valor)
const bajo = (limites, v) => limites.filter((l) => l < v).length // el límite pertenece al grupo inferior
const hasta = (limites, v) => limites.filter((l) => l <= v).length
const recencia = (dias) => 5 - bajo([30, 60, 90, 180], dias)
const frecuencia = (compras) => 1 + bajo([4, 19, 49, 99], compras)
const monetario = (gasto) => 1 + hasta([5000, 10000, 25000, 50000], gasto)
export const categoriaRfm = (puntaje) => ['Need Attention', 'At Risk', 'Potential Loyalists', 'Loyal', 'Champions'][bajo([5, 8, 10, 12], puntaje)]
export const estatusActividad = (dias) => ['Active', 'At Risk', 'Dormant', 'Inactive'][bajo([29, 59, 89], dias)]
export const nivelLealtad = (gasto) => ['No Tier', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'][bajo([999.99, 4999.99, 9999.99, 24999.99, 49999.99], gasto)]
const categoriaRiesgo = (puntaje) => ['Very Low', 'Low', 'Medium', 'High', 'Very High'][bajo([20, 40, 60, 80], puntaje)]
const limitar = (v, minimo, maximo) => Math.min(maximo, Math.max(minimo, v))

// Columnas que se calculan a partir de las base (igual que reglas.derivar)
function derivar(c, sim, r) {
  c.total_spent_usd = Math.round(c.total_purchases * c.avg_order_value_usd * 100) / 100
  c.rfm_category = categoriaRfm(recencia(c.days_since_last_purchase) + frecuencia(c.total_purchases) + monetario(c.total_spent_usd))
  c.activity_status = estatusActividad(c.days_since_last_purchase)
  c.loyalty_tier = nivelLealtad(c.total_spent_usd)
  const x = [c.days_since_last_purchase, c.return_count, c.complaint_count, c.satisfaction_score, 1]
  const riesgo = x.reduce((s, v, i) => s + v * sim.coefChurn[i], 0) + sim.sdChurn * normal(r)
  c.churn_risk_category = categoriaRiesgo(limitar(Math.round(riesgo), 0, 100))
  c.customer_lifetime_value_usd = Math.round(c.total_spent_usd * (0.8 + 0.7 * r()) * 100) / 100
}

// estructura = fracción de clientes que sigue un arquetipo (0 reproduce el dataset original: variables independientes)
export function simularClientes(modelo, cantidad, estructura, semilla) {
  const { simulador: sim, catalogos: cat } = modelo
  const r = aleatorio(semilla)
  const nombres = Object.keys(sim.arquetipos)
  const clientes = new Array(cantidad)
  for (let i = 0; i < cantidad; i++) {
    // En el original los días desde la última compra salen de bandas según la frecuencia declarada
    const banda = sim.bandas[elegir(r, sim.frecuencia)]
    const pais = elegir(r, sim.pais)
    const categoria = elegir(r, sim.categoria)
    let social = 'None'
    if (r() < sim.pSocial) {
      const redes = [...cat.redes]
      const cuantas = 1 + Math.floor(r() * 3)
      const elegidas = []
      for (let k = 0; k < cuantas; k++) elegidas.push(redes.splice(Math.floor(r() * redes.length), 1)[0])
      social = elegidas.join(', ')
    }
    let c = {
      customer_id: `SIM-${String(i + 1).padStart(6, '0')}`,
      country: pais,
      region: cat.regiones[pais] || 'Otra',
      categoria: cat.categoriasEs[categoria],
      social_media_presence: social,
      email_open_rate: uniforme(r, [0, 1], 3),
      click_through_rate: uniforme(r, [0, 0.5], 3),
      conversion_rate: uniforme(r, [0, 0.3], 3),
      customer_acquisition_cost_usd: uniforme(r, [5, 200]),
      days_since_last_purchase: entero(r, banda),
      total_purchases: entero(r, sim.base.purchases),
      tenure_months: entero(r, sim.base.tenure),
      avg_order_value_usd: uniforme(r, sim.base.aov),
      return_count: entero(r, sim.base.returns),
      complaint_count: entero(r, sim.base.complaints),
      satisfaction_score: entero(r, sim.base.satisfaction),
      arquetipo: 'ruido',
    }
    if (estructura > 0 && r() < estructura) {
      const nombre = nombres[Math.floor(r() * nombres.length)]
      const a = sim.arquetipos[nombre]
      c = {
        ...c,
        tenure_months: entero(r, a.tenure),
        total_purchases: entero(r, a.purchases),
        avg_order_value_usd: uniforme(r, a.aov),
        days_since_last_purchase: entero(r, a.days),
        return_count: entero(r, a.returns),
        complaint_count: entero(r, a.complaints),
        satisfaction_score: a.satisfaction[Math.floor(r() * a.satisfaction.length)],
        arquetipo: nombre,
      }
      // 70 % de los clientes de un arquetipo prefiere sus categorías típicas (igual que generate.py)
      if (r() < 0.7) c.categoria = cat.categoriasEs[a.categorias[Math.floor(r() * a.categorias.length)]]
    }
    derivar(c, sim, r)
    clientes[i] = c
  }
  return clientes
}

// Silueta en el espacio de la PCA, sobre una muestra (es O(m²)); misma definición que sklearn.silhouette_score
export function silueta(puntos, etiquetas, r) {
  const total = puntos.length
  if (new Set(etiquetas).size < 2) return null
  const indices = Array.from({ length: total }, (_, i) => i)
  const m = Math.min(total, 1500)
  for (let i = 0; i < m; i++) {
    const j = i + Math.floor(r() * (total - i))
    ;[indices[i], indices[j]] = [indices[j], indices[i]]
  }
  const muestra = indices.slice(0, m)
  let suma = 0
  for (const i of muestra) {
    const suma_por_grupo = new Map()
    const cuenta = new Map()
    for (const j of muestra) {
      if (i === j) continue
      const d = Math.hypot(...puntos[i].map((v, k) => v - puntos[j][k]))
      const g = etiquetas[j]
      suma_por_grupo.set(g, (suma_por_grupo.get(g) || 0) + d)
      cuenta.set(g, (cuenta.get(g) || 0) + 1)
    }
    const propio = etiquetas[i]
    if (!cuenta.get(propio)) continue // grupo de un solo cliente: silueta 0
    const a = suma_por_grupo.get(propio) / cuenta.get(propio)
    let b = Infinity
    for (const [g, s] of suma_por_grupo) if (g !== propio) b = Math.min(b, s / cuenta.get(g))
    suma += (b - a) / Math.max(a, b)
  }
  return suma / m
}

const pares = (n) => (n * (n - 1)) / 2

// Índice de Rand ajustado entre dos asignaciones (1 = idénticas, 0 = como el azar)
export function ari(a, b) {
  const tabla = new Map()
  const filas = new Map()
  const columnas = new Map()
  for (let i = 0; i < a.length; i++) {
    const clave = `${a[i]}|${b[i]}`
    tabla.set(clave, (tabla.get(clave) || 0) + 1)
    filas.set(a[i], (filas.get(a[i]) || 0) + 1)
    columnas.set(b[i], (columnas.get(b[i]) || 0) + 1)
  }
  const suma = (mapa) => [...mapa.values()].reduce((s, v) => s + pares(v), 0)
  const indice = suma(tabla)
  const esperado = (suma(filas) * suma(columnas)) / pares(a.length)
  const maximo = (suma(filas) + suma(columnas)) / 2
  return maximo === esperado ? null : (indice - esperado) / (maximo - esperado)
}

export function evaluarSimulacion(modelo, clientes, semilla = 1) {
  const k = modelo.k
  const inicio = performance.now()
  const grupos = new Array(clientes.length)
  const estatus = new Array(clientes.length)
  const puntos = new Array(clientes.length)
  const conteos = new Array(k).fill(0)
  let confianza = 0
  let enAlerta = 0
  clientes.forEach((c, i) => {
    const p = proyectar(modelo, c)
    grupos[i] = p.grupo
    puntos[i] = p.y
    conteos[p.grupo]++
    confianza += p.confianza
    estatus[i] = estatusAlerta(modelo.reglaAlerta, c.satisfaction_score, c.days_since_last_purchase, c.complaint_count)
    if (estatus[i] === 'Alerta') enAlerta++
  })
  const ms = performance.now() - inicio
  const n = clientes.length
  const porcentajes = conteos.map((v) => (100 * v) / n)
  const reales = modelo.grupos.map((g) => g.porcentaje)
  const arquetipos = [...new Set(clientes.map((c) => c.arquetipo))].filter((x) => x !== 'ruido').sort()
  const conArquetipo = clientes.map((c, i) => i).filter((i) => clientes[i].arquetipo !== 'ruido')
  const matriz = arquetipos.map((nombre) => {
    const fila = new Array(k).fill(0)
    conArquetipo.forEach((i) => { if (clientes[i].arquetipo === nombre) fila[grupos[i]]++ })
    return { arquetipo: nombre, conteos: fila }
  })
  return {
    n, ms, conteos, porcentajes, reales,
    diferenciaMaxima: Math.max(...porcentajes.map((p, i) => Math.abs(p - reales[i]))),
    silueta: silueta(puntos, grupos, aleatorio(semilla)),
    confianzaMedia: confianza / n,
    porcentajeAlerta: (100 * enAlerta) / n,
    ari: conArquetipo.length > 1 ? ari(conArquetipo.map((i) => clientes[i].arquetipo), conArquetipo.map((i) => grupos[i])) : null,
    conArquetipo: conArquetipo.length,
    matriz,
    grupos,
    estatus,
  }
}

export function csvSimulado(clientes, grupos) {
  const columnas = ['customer_id', 'country', 'days_since_last_purchase', 'total_purchases', 'tenure_months', 'avg_order_value_usd', 'return_count', 'complaint_count', 'satisfaction_score', 'total_spent_usd', 'loyalty_tier', 'rfm_category', 'arquetipo']
  const filas = clientes.map((c, i) => [...columnas.map((col) => c[col]), grupos[i]].join(','))
  return [[...columnas, 'cluster_id'].join(','), ...filas].join('\n')
}
