// Predicción de un cliente en el navegador: la misma cuenta que `predecir()` de src/models/predict.py.
// Usa solo los parámetros exportados en public/data/model.json (escalador, PCA y centroides), sin servidor.
// Si cambia el modelo, `python -m src.models.exportar_dashboard` regenera model.json y `npm test` comprueba
// que el navegador sigue dando el mismo resultado que Python.

// Mismos rangos que valida predict.py: lo que Python rechaza, aquí también.
const MINIMOS = {
  days_since_last_purchase: 0,
  total_purchases: 0,
  tenure_months: 1,
  avg_order_value_usd: 0,
  return_count: 0,
  complaint_count: 0,
  satisfaction_score: 1,
}

export function validarEntrada(modelo, entrada) {
  const errores = {}
  const avisos = {}
  for (const campo of modelo.campos) {
    const bruto = entrada?.[campo.id]
    if (typeof bruto === 'boolean' || bruto === '' || bruto === null || bruto === undefined) {
      errores[campo.id] = 'Obligatorio.'
      continue
    }
    const valor = Number(bruto)
    if (!Number.isFinite(valor)) {
      errores[campo.id] = 'Debe ser un número.'
    } else if (valor < MINIMOS[campo.id]) {
      errores[campo.id] = `Debe ser ≥ ${MINIMOS[campo.id]}.`
    } else if (campo.id === 'satisfaction_score' && valor > 5) {
      errores[campo.id] = 'Debe estar entre 1 y 5.'
    } else if (valor > campo.max) {
      avisos[campo.id] = `Fuera del rango observado en el dataset (máx. ${campo.max}); el resultado es menos confiable.`
    }
  }
  return { errores, avisos }
}

export function estatusAlerta(regla, satisfaccion, dias, quejas) {
  if (dias >= regla.alertaDias || (satisfaccion <= regla.alertaSatisfaccion && quejas >= regla.alertaQuejas)) return 'Alerta'
  if (dias >= regla.atencionDias || satisfaccion <= regla.alertaSatisfaccion || quejas >= regla.atencionQuejas) return 'Atención'
  return 'Normal'
}

// Cuenta del modelo sobre un cliente ya validado: variables B -> estandarizar y ponderar -> PCA -> centroide más cercano.
// Devuelve también la proyección `y` (espacio donde se mide la silueta).
export function proyectar(modelo, entrada) {
  const n = (id) => Number(entrada[id])
  const compras = n('total_purchases')
  // Variables del conjunto B, igual que preprocess.construir_features
  const x = [
    n('days_since_last_purchase'),
    Math.log1p(compras / Math.max(n('tenure_months'), 1)),
    n('avg_order_value_usd'),
    Math.log1p(n('return_count') / (compras + 5)),
    n('complaint_count'),
    n('satisfaction_score'),
  ]
  const z = x.map((v, i) => ((v - modelo.scaler.mean[i]) / modelo.scaler.scale[i]) * modelo.pesos[i])
  const y = modelo.pca.components.map((fila) => fila.reduce((suma, c, j) => suma + c * (z[j] - modelo.pca.mean[j]), 0))
  const distancias = modelo.centroides.map((c) => Math.hypot(...c.map((v, i) => v - y[i])))
  const orden = distancias.map((d, i) => [d, i]).sort((a, b) => a[0] - b[0])
  const [d1, grupo] = orden[0]
  const d2 = orden[1][0]
  return { y, distancias, grupo, d1, confianza: d1 + d2 === 0 ? 1 : d2 / Math.max(d1 + d2, 1e-12) }
}

export function predecir(modelo, entrada) {
  const { errores, avisos } = validarEntrada(modelo, entrada)
  if (Object.keys(errores).length) {
    return { status: 'error', mensaje: 'Datos inválidos.', errores }
  }
  const { distancias, grupo, d1, confianza } = proyectar(modelo, entrada)
  const inversas = distancias.map((d) => 1 / Math.max(d, 1e-9))
  const total = inversas.reduce((a, b) => a + b, 0)
  return {
    status: 'success',
    cluster_id: grupo,
    distancia_centroide: d1,
    confianza,
    cercania: inversas.map((v) => v / total),
    estatus_alerta: estatusAlerta(modelo.reglaAlerta, Number(entrada.satisfaction_score), Number(entrada.days_since_last_purchase), Number(entrada.complaint_count)),
    avisos,
  }
}
