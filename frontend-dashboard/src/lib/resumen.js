// Arma, a partir de una lista de clientes con grupo asignado, los mismos agregados que el motor de Python
// escribe en public/data/dashboard.json (src/models/exportar_dashboard.py: grupos, insights, alertas,
// recomendaciones, zonas y países). Así las vistas del dashboard se pueden dibujar igual con los clientes
// reales y con los simulados. Un test (tests/resumen.test.mjs) aplica esta misma función a los 50,000 clientes
// reales y comprueba que el resultado coincide con el dashboard.json que generó Python.
//
// Cada cliente ("fila") trae: customer_id, country, categoria (en español), avg_order_value_usd, social_media_presence,
// conversion_rate, email_open_rate, click_through_rate, customer_acquisition_cost_usd, customer_lifetime_value_usd,
// loyalty_tier, total_spent_usd, rfm_category, activity_status, churn_risk_category, return_count, complaint_count,
// satisfaction_score, days_since_last_purchase, total_purchases, tenure_months, cluster y estatus.

const num = (x, decimales) => x.toLocaleString('en-US', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
const media = (filas, campo) => (filas.length ? filas.reduce((s, f) => s + Number(f[campo]), 0) / filas.length : 0)
const fraccion = (filas, condicion) => (filas.length ? filas.filter(condicion).length / filas.length : 0)
const r1 = (x) => Math.round(x * 10) / 10
const r2 = (x) => Math.round(x * 100) / 100
const pct = (x) => r1(100 * x)
const millones = (x) => (x >= 1e6 ? `$${num(x / 1e6, 0)}M` : `$${num(x, 0)}`)

// Conteo por clave ordenado de mayor a menor (en empate, la clave que aparece primero)
function contar(filas, clave) {
  const mapa = new Map()
  for (const f of filas) mapa.set(clave(f), (mapa.get(clave(f)) || 0) + 1)
  return [...mapa.entries()].sort((a, b) => b[1] - a[1])
}
const moda = (filas, clave, predeterminado) => {
  const c = contar(filas, clave)
  return c.length ? c[0][0] : predeterminado
}

function grupos(filas, modelo) {
  const gastoTotal = filas.reduce((s, f) => s + f.total_spent_usd, 0)
  const variables = Object.keys(modelo.grupos[0].perfil)
  return modelo.grupos.map((g) => {
    const sub = filas.filter((f) => f.cluster === g.id)
    const gastoGrupo = sub.reduce((s, f) => s + f.total_spent_usd, 0)
    // Categoría RFM más frecuente del grupo (en empate, la primera por orden alfabético, como pandas.mode)
    const conteo = contar(sub, (f) => f.rfm_category)
    const maximo = conteo.length ? conteo[0][1] : 0
    const rfmDominante = conteo.filter(([, c]) => c === maximo).map(([k]) => k).sort()[0] ?? '—'
    return {
      id: g.id, name: g.name, shortName: g.shortName, color: g.color,
      clientes: sub.length, porcentaje: pct(sub.length / filas.length), porcentajeGasto: pct(gastoTotal ? gastoGrupo / gastoTotal : 0),
      gastoTotalM: millones(gastoGrupo), gastoPromedio: Math.round(media(sub, 'total_spent_usd')),
      reglaRFM: Math.round(media(filas.filter((f) => f.rfm_category === rfmDominante), 'total_spent_usd')), rfmDominante,
      satisfaccion: r2(media(sub, 'satisfaction_score')),
      desc: `${media(sub, 'days_since_last_purchase').toFixed(0)} días sin comprar, ${media(sub, 'total_purchases').toFixed(0)} compras, satisfacción ${media(sub, 'satisfaction_score').toFixed(1)}`,
      rasgos: g.rasgos, accion: g.accion,
      perfil: Object.fromEntries(variables.map((v) => [v, r2(media(sub, v))])),
    }
  })
}

function insights(sub, etiqueta, cat) {
  const categorias = contar(sub, (f) => f.categoria).slice(0, 3).map(([nombre, n]) => {
    const s = sub.filter((f) => f.categoria === nombre)
    const zonas = contar(s, (f) => cat.regiones[f.country] || 'Otra').slice(0, 2).map(([z]) => z)
    return { name: nombre, iconKey: cat.iconos[nombre], avgTicket: `$${num(media(s, 'avg_order_value_usd'), 0)} USD`, share: `${((100 * n) / sub.length).toFixed(1)}%`, topZone: zonas.join(' / ') }
  })
  const tasa = (grupo) => r1(100 * media(grupo, 'conversion_rate'))
  const redes = cat.redes.map((red) => ({ net: red, rate: tasa(sub.filter((f) => String(f.social_media_presence).includes(red))) }))
  redes.push({ net: 'Directo / Email', rate: tasa(sub.filter((f) => String(f.social_media_presence) === 'None')) })
  redes.sort((a, b) => b.rate - a.rate)
  const dist = cat.etiquetasSatisfaccion.map(([label, color], i) => ({ label, count: sub.filter((f) => f.satisfaction_score === i + 1).length, color }))
  const tiers = []
  for (const [clave, es] of cat.tiers) {
    const t = sub.filter((f) => f.loyalty_tier === clave)
    if (t.length) tiers.push({ tier: es, count: num(t.length, 0), avg: `${media(t, 'satisfaction_score').toFixed(1)} ★`, sat: `${(100 * fraccion(t, (f) => f.satisfaction_score >= 4)).toFixed(0)}%`, spent: `$${num(media(t, 'total_spent_usd'), 0)}` })
  }
  const s = (condicion) => `${(100 * fraccion(sub, condicion)).toFixed(1)}%`
  return {
    label: etiqueta,
    unitEconomics: { cac: `$${num(media(sub, 'customer_acquisition_cost_usd'), 0)} USD`, clv: `$${num(media(sub, 'customer_lifetime_value_usd'), 0)} USD`, returnsAvg: `${media(sub, 'return_count').toFixed(1)} devoluciones` },
    categories: categorias, socialConversion: redes,
    funnel: { emailOpen: r1(100 * media(sub, 'email_open_rate')), ctr: r1(100 * media(sub, 'click_through_rate')), conversion: r1(100 * media(sub, 'conversion_rate')) },
    satisfaction: { avg: media(sub, 'satisfaction_score').toFixed(2), satisfiedPct: s((f) => f.satisfaction_score >= 4), neutralPct: s((f) => f.satisfaction_score === 3), unsatisfiedPct: s((f) => f.satisfaction_score <= 2), dist, tiers },
  }
}

const ALTO = ['Diamond', 'Platinum']

function alertas(filas, gs, cat) {
  const alto = filas.filter((f) => ALTO.includes(f.loyalty_tier) && f.estatus === 'Alerta')
  const gRiesgo = moda(alto, (f) => f.cluster, 0)
  const top = gs.reduce((a, g) => (g.porcentajeGasto > a.porcentajeGasto ? g : a), gs[0])
  const sin = filas.filter((f) => f.loyalty_tier === 'No Tier')
  const con = filas.filter((f) => f.loyalty_tier !== 'No Tier')
  const gSin = moda(sin, (f) => f.cluster, 0)
  const redes = insights(filas, '', cat).socialConversion
  const dif = Math.max(...redes.map((r) => r.rate)) - Math.min(...redes.map((r) => r.rate))
  const sinRed = fraccion(filas, (f) => String(f.social_media_presence) === 'None')
  return [
    { id: 'alert-vip-risk', iconKey: 'shieldAlert', priority: 'Crítica', title: 'Clientes de alto valor en alerta', metric: `${num(alto.length, 0)} clientes Diamante/Platino`,
      detail: `${millones(alto.reduce((s, f) => s + f.customer_lifetime_value_usd, 0))} USD en CLV en juego · Promedio ${media(alto, 'complaint_count').toFixed(1)} quejas`,
      actionLabel: `Inspeccionar Grupo ${gRiesgo}`, targetSegment: String(gRiesgo), accent: 'rose' },
    { id: 'alert-pareto', iconKey: 'gem', priority: 'Estratégica', title: 'Concentración de valor', metric: `${top.porcentajeGasto.toFixed(0)}% del ingreso en el Grupo ${top.id}`,
      detail: `Generado por el ${top.porcentaje.toFixed(0)}% de la base (${num(top.clientes, 0)} clientes)`, actionLabel: `Enfocar Grupo ${top.id}`, targetSegment: String(top.id), accent: 'blue' },
    { id: 'alert-no-tier', iconKey: 'userPlus', priority: 'Oportunidad', title: 'Brecha de suscripción detectada', metric: `${num(sin.length, 0)} clientes sin nivel`,
      detail: `Gastan $${num(media(sin, 'total_spent_usd'), 0)} USD vs. $${num(media(con, 'total_spent_usd'), 0)} USD de clientes con nivel`, actionLabel: `Ver Grupo ${gSin}`, targetSegment: String(gSin), accent: 'amber' },
    { id: 'alert-channels', iconKey: 'split', priority: 'Táctica', title: 'Conversión por canal', metric: `Diferencia entre canales: ${dif.toFixed(1)} pp`,
      detail: `${(100 * sinRed).toFixed(1)}% sin red social registrada requieren contacto vía Email`, actionLabel: 'Ver todo el universo', targetSegment: 'all', accent: 'indigo' },
  ]
}

function recomendaciones(filas, alerts, cat) {
  const alto = filas.filter((f) => ALTO.includes(f.loyalty_tier))
  const enAlerta = alto.filter((f) => f.estatus === 'Alerta')
  const inact = filas.filter((f) => f.activity_status === 'Inactive')
  const insat = alto.filter((f) => f.satisfaction_score <= 2)
  const redes = insights(filas, '', cat).socialConversion
  const tasas = redes.map((r) => r.rate)
  return [
    { id: 'rec-vip', title: 'Proteger a los clientes de alto valor en alerta', priority: 'Alta',
      fact: `${num(enAlerta.length, 0)} clientes Diamante y Platino están en alerta (medio año sin comprar, o insatisfechos con muchas quejas). Valor del cliente en juego: ${millones(enAlerta.reduce((s, f) => s + f.customer_lifetime_value_usd, 0))}.`,
      action: 'Contacto personal de un ejecutivo y oferta exclusiva. Revisar por qué están insatisfechos.', buttonLabel: 'Ver clientes en alerta', targetSegment: alerts[0].targetSegment, targetView: 'dashboard' },
    { id: 'rec-inactive', title: 'Reactivar clientes inactivos', priority: 'Alta',
      fact: `${num(inact.length, 0)} clientes inactivos (90 días o más sin comprar), con ${media(inact, 'days_since_last_purchase').toFixed(1)} días sin comprar en promedio.`,
      action: 'Campaña de regreso con un beneficio directo en su categoría favorita.', buttonLabel: 'Ver perfiles de clientes', targetSegment: String(moda(inact, (f) => f.cluster, 0)), targetView: 'dashboard' },
    { id: 'rec-unsat', title: 'Atender a los insatisfechos de alto valor', priority: 'Media', fact: `${num(insat.length, 0)} clientes Diamante y Platino dieron una calificación de 1 o 2.`,
      action: 'Encuesta breve para conocer el motivo y seguimiento por atención al cliente.', buttonLabel: 'Ver satisfacción', targetSegment: 'all', targetView: 'satisfaction' },
    { id: 'rec-channels', title: 'Probar canales de marketing', priority: 'Media', fact: `Ninguna red destaca: la conversión va de ${Math.min(...tasas).toFixed(2)}% a ${Math.max(...tasas).toFixed(2)}%.`,
      action: 'Hacer pruebas A/B por red antes de concentrar la inversión en una sola.', buttonLabel: 'Ver canales en inicio', targetSegment: 'all', targetView: 'dashboard' },
  ]
}

function zonas(filas) {
  const base = 100 / 12
  const global = new Map(contar(filas, (f) => f.categoria).map(([k, n]) => [k, (100 * n) / filas.length]))
  const salida = {}
  const regiones = [...new Set(filas.map((f) => f.region))].sort()
  for (const [zona, sub] of [['Todas las zonas', filas], ...regiones.map((r) => [r, filas.filter((f) => f.region === r)])]) {
    salida[zona] = contar(sub, (f) => f.categoria).map(([nombre, n]) => {
      const share = (100 * n) / sub.length
      const diff = share - (zona === 'Todas las zonas' ? base : global.get(nombre))
      return { name: nombre, share: r1(share), diff: r2(diff), status: diff >= 0.15 ? 'Tendencia' : diff <= -0.15 ? 'Baja' : 'Estable' }
    })
  }
  return salida
}

function paises(filas, cat) {
  const porPais = new Map()
  for (const f of filas) porPais.set(f.country, [...(porPais.get(f.country) || []), f])
  return [...porPais.entries()].map(([pais, sub]) => {
    const share = contar(sub, (f) => f.categoria).map(([k, n]) => [k, (100 * n) / sub.length])
    return {
      country: cat.paisesEs[pais] || pais, clients: num(sub.length, 0), topCat: `${share[0][0]} (${share[0][1].toFixed(1)}%)`, lowCat: `${share.at(-1)[0]} (${share.at(-1)[1].toFixed(1)}%)`,
      avgSpent: `$${num(media(sub, 'total_spent_usd'), 0)}`, riskPct: `${(100 * fraccion(sub, (f) => ['High', 'Very High'].includes(f.churn_risk_category))).toFixed(1)}%`, sat: media(sub, 'satisfaction_score').toFixed(2),
    }
  }).sort((a, b) => (a.country < b.country ? -1 : a.country > b.country ? 1 : 0))
}

export function resumir(filas, modelo) {
  const cat = modelo.catalogos
  const conRegion = filas.map((f) => (f.region ? f : { ...f, region: cat.regiones[f.country] || 'Otra' }))
  const gs = grupos(conRegion, modelo)
  const segmentos = { all: insights(conRegion, `Universo Global (${num(conRegion.length, 0)} clientes)`, cat) }
  for (const g of gs) segmentos[String(g.id)] = insights(conRegion.filter((f) => f.cluster === g.id), `${g.name} (${num(g.clientes, 0)} clientes)`, cat)
  const alerts = alertas(conRegion, gs, cat)
  return {
    meta: { clientes: conRegion.length },
    clusters: gs, insights: segmentos, alertas: alerts, recomendaciones: recomendaciones(conRegion, alerts, cat),
    zonas: zonas(conRegion), paises: paises(conRegion, cat),
    tabla: conRegion.map((f) => ({ id: f.customer_id, cluster: f.cluster, rfm: f.rfm_category, spent: Math.round(f.total_spent_usd * 100) / 100, orders: f.total_purchases, satisfaction: f.satisfaction_score, status: f.estatus, country: cat.paisesEs[f.country] || f.country })),
  }
}
