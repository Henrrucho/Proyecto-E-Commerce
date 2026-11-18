import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { ari, csvSimulado, evaluarSimulacion, silueta, simularClientes, aleatorio } from '../src/lib/simular.js'

const modelo = JSON.parse(readFileSync(new URL('../public/data/model.json', import.meta.url), 'utf8'))
const sim = modelo.simulador
const media = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length

test('la misma semilla da los mismos clientes y otra semilla, otros', () => {
  const a = simularClientes(modelo, 500, 0.5, 7)
  assert.deepEqual(a, simularClientes(modelo, 500, 0.5, 7))
  assert.notDeepEqual(a, simularClientes(modelo, 500, 0.5, 8))
})

test('sin estructura respeta los rangos y la distribución del generador original', () => {
  const clientes = simularClientes(modelo, 20000, 0, 1)
  assert.ok(clientes.every((c) => c.arquetipo === 'ruido'))
  const dentro = (campo, [lo, hi]) => clientes.every((c) => c[campo] >= lo && c[campo] <= hi)
  assert.ok(dentro('tenure_months', sim.base.tenure) && dentro('total_purchases', sim.base.purchases) && dentro('avg_order_value_usd', sim.base.aov))
  assert.ok(dentro('return_count', sim.base.returns) && dentro('complaint_count', sim.base.complaints) && dentro('satisfaction_score', sim.base.satisfaction))
  assert.ok(dentro('days_since_last_purchase', [0, 365]))
  const punto = (rango) => (rango[0] + rango[1]) / 2
  assert.ok(Math.abs(media(clientes.map((c) => c.tenure_months)) - punto(sim.base.tenure)) < 1.5)
  assert.ok(Math.abs(media(clientes.map((c) => c.avg_order_value_usd)) - punto(sim.base.aov)) < 8)
  // Días sin comprar esperados = suma de (proporción de cada frecuencia x punto medio de su banda)
  const esperado = Object.entries(sim.frecuencia).reduce((s, [f, p]) => s + p * punto(sim.bandas[f]), 0)
  assert.ok(Math.abs(media(clientes.map((c) => c.days_since_last_purchase)) - esperado) < 3)
})

test('con estructura 1 cada cliente cae en el rango de su arquetipo y los 5 aparecen por igual', () => {
  const clientes = simularClientes(modelo, 10000, 1, 2)
  const conteo = {}
  for (const c of clientes) {
    const a = sim.arquetipos[c.arquetipo]
    assert.ok(a, `arquetipo desconocido ${c.arquetipo}`)
    assert.ok(c.tenure_months >= a.tenure[0] && c.tenure_months <= a.tenure[1])
    assert.ok(c.days_since_last_purchase >= a.days[0] && c.days_since_last_purchase <= a.days[1])
    assert.ok(a.satisfaction.includes(c.satisfaction_score))
    conteo[c.arquetipo] = (conteo[c.arquetipo] || 0) + 1
  }
  assert.equal(Object.keys(conteo).length, Object.keys(sim.arquetipos).length)
  for (const v of Object.values(conteo)) assert.ok(Math.abs(v / clientes.length - 0.2) < 0.02)
})

test('con clientes fabricados sin estructura el modelo los reparte como a los reales', () => {
  const r = evaluarSimulacion(modelo, simularClientes(modelo, 20000, 0, 3), 3)
  assert.equal(r.n, 20000)
  assert.equal(r.conteos.reduce((a, b) => a + b, 0), 20000)
  assert.ok(r.diferenciaMaxima < 3, `diferencia ${r.diferenciaMaxima}`)
  assert.ok(r.silueta > 0.13 && r.silueta < 0.23, `silueta ${r.silueta}`) // referencia real 0.178; en Python salen 0.17 a 0.19
  assert.equal(r.ari, null)
})

test('con estructura el modelo recupera los arquetipos solo en parte (ARI parecido al de Python, 0.21)', () => {
  const r = evaluarSimulacion(modelo, simularClientes(modelo, 10000, 0.6, 4), 4)
  assert.ok(r.ari > 0.12 && r.ari < 0.35, `ARI ${r.ari}`)
  assert.equal(r.matriz.length, 5)
  assert.ok(r.conArquetipo > 5500 && r.conArquetipo < 6500)
})

test('ari: 1 para particiones iguales (aunque cambien los nombres) y cerca de 0 para el azar', () => {
  assert.equal(ari(['a', 'a', 'b', 'b', 'c'], [3, 3, 1, 1, 2]), 1)
  const r = aleatorio(5)
  const x = Array.from({ length: 20000 }, () => Math.floor(r() * 4))
  const y = Array.from({ length: 20000 }, () => Math.floor(r() * 4))
  assert.ok(Math.abs(ari(x, y)) < 0.01)
})

test('silueta: dos nubes muy separadas dan casi 1 y un solo grupo no se puede medir', () => {
  const r = aleatorio(9)
  const puntos = Array.from({ length: 400 }, (_, i) => [(i < 200 ? 0 : 50) + r(), r()])
  const etiquetas = puntos.map((_, i) => (i < 200 ? 0 : 1))
  assert.ok(silueta(puntos, etiquetas, aleatorio(1)) > 0.95)
  assert.equal(silueta(puntos, etiquetas.map(() => 0), aleatorio(1)), null)
})

test('el CSV simulado trae encabezado, una fila por cliente y el grupo asignado', () => {
  const clientes = simularClientes(modelo, 50, 0.5, 6)
  const r = evaluarSimulacion(modelo, clientes, 6)
  const filas = csvSimulado(clientes, r.grupos).split('\n')
  assert.equal(filas.length, 51)
  assert.ok(filas[0].endsWith('cluster_id'))
  assert.equal(filas[1].split(',').length, filas[0].split(',').length)
})
