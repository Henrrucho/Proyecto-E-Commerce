// Comprueba que predecir() del navegador coincide con el resultado de Python para 300 clientes reales.
// Ejecutar con:  npm test
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { predecir, validarEntrada } from '../src/lib/predict.js'

const leer = (ruta) => JSON.parse(readFileSync(new URL(`../public/data/${ruta}`, import.meta.url), 'utf8'))
const modelo = leer('model.json')
const muestra = leer('parity_sample.json')

test('el navegador asigna el mismo grupo que Python en los 300 clientes de la muestra', () => {
  let distintos = 0
  for (const fila of muestra) {
    const r = predecir(modelo, fila)
    assert.equal(r.status, 'success')
    if (r.cluster_id !== fila.cluster) distintos += 1
    assert.ok(Math.abs(r.confianza - fila.confianza) < 1e-3, `confianza ${r.confianza} vs ${fila.confianza}`)
    assert.ok(Math.abs(r.distancia_centroide - fila.distancia) < 1e-3, `distancia ${r.distancia_centroide} vs ${fila.distancia}`)
    assert.equal(r.estatus_alerta, fila.estatus)
  }
  assert.equal(distintos, 0)
})

test('rechaza los valores que Python rechaza', () => {
  const base = { days_since_last_purchase: 10, total_purchases: 5, tenure_months: 12, avg_order_value_usd: 100, return_count: 0, complaint_count: 0, satisfaction_score: 3 }
  assert.equal(predecir(modelo, base).status, 'success')
  for (const [campo, malo] of [['days_since_last_purchase', -5], ['total_purchases', -1], ['tenure_months', 0], ['satisfaction_score', 99], ['satisfaction_score', true], ['return_count', 'texto'], ['avg_order_value_usd', NaN]]) {
    assert.equal(predecir(modelo, { ...base, [campo]: malo }).status, 'error', `${campo}=${malo}`)
  }
  assert.equal(predecir(modelo, {}).status, 'error')
})

test('un valor fuera del rango observado solo genera un aviso', () => {
  const { errores, avisos } = validarEntrada(modelo, { days_since_last_purchase: 900, total_purchases: 5, tenure_months: 12, avg_order_value_usd: 100, return_count: 0, complaint_count: 0, satisfaction_score: 3 })
  assert.deepEqual(errores, {})
  assert.ok(avisos.days_since_last_purchase)
})

test('la cercanía a los grupos suma 1', () => {
  const r = predecir(modelo, muestra[0])
  assert.ok(Math.abs(r.cercania.reduce((a, b) => a + b, 0) - 1) < 1e-9)
})
