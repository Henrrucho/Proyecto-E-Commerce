import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Dices, Download, FlaskConical } from 'lucide-react'
import { resumir } from '../lib/resumen'
import { csvSimulado, evaluarSimulacion, simularClientes } from '../lib/simular'
import { TARJETA } from './iconos'
import PaginaDatos from './PaginaDatos'

const NOMBRES = {
  leal_frecuente: 'Leal y frecuente',
  ocasional_gastador: 'Ocasional gastador',
  en_riesgo: 'En riesgo',
  nuevo: 'Nuevo',
  ahorrador_regular: 'Ahorrador regular',
}
const PRESETS = [1000, 5000, 20000, 50000]
const MIN = 100
const MAX = 50000
const PESTANAS = [
  ['evaluacion', 'Evaluación'],
  ['dashboard', 'Panel'],
  ['trends', 'Tendencias y zonas'],
  ['recommendations', 'Recomendaciones'],
  ['satisfaction', 'Satisfacción'],
]
const FUENTES = [['simulados', 'Simulados'], ['originales', 'Originales'], ['ambos', 'Ambos']]

const entrada = 'mt-1 w-full bg-[#F4F5F7] dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700'
const pildora = (activa) => `text-xs font-bold px-3.5 py-2 rounded-full transition ${activa ? 'bg-slate-900 dark:bg-blue-600 text-white' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800'}`

function Kpi({ titulo, valor, nota }) {
  return (
    <div className={`${TARJETA} p-4`}>
      <p className="text-[11px] font-semibold text-slate-400">{titulo}</p>
      <p className="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">{valor}</p>
      <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{nota}</p>
    </div>
  )
}

const calidadARI = (v) => (v < 0.3 ? 'baja' : v < 0.6 ? 'media' : 'alta')

function Evaluacion({ modelo, datos, simulacion, darkMode }) {
  const { resultado: r, resumen, estructura, clientes, semilla } = simulacion
  const referencia = datos.evaluacion.ganador.silueta_test
  const grafica = modelo.grupos.map((g, i) => ({ nombre: `Grupo ${g.id}`, 'Clientes reales': Number(r.reales[i].toFixed(1)), 'Clientes simulados': Number(r.porcentajes[i].toFixed(1)) }))
  const descargar = () => {
    const url = URL.createObjectURL(new Blob([csvSimulado(clientes, r.grupos)], { type: 'text/csv;charset=utf-8' }))
    const enlace = Object.assign(document.createElement('a'), { href: url, download: `clientes_simulados_${r.n}_s${semilla}_e${estructura}.csv` })
    enlace.click()
    URL.revokeObjectURL(url)
  }
  const par = (real, sim, formato = (x) => x) => <><span className="text-slate-400">{formato(real)}</span> → <span className="font-bold text-slate-900 dark:text-white">{formato(sim)}</span></>

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Kpi titulo="Clientes simulados" valor={r.n.toLocaleString()} nota={`asignados en ${r.ms.toFixed(0)} ms`} />
        <Kpi titulo="Silueta (muestra)" valor={r.silueta === null ? '—' : r.silueta.toFixed(3)} nota={`con los clientes reales: ${referencia}`} />
        <Kpi titulo="Mayor diferencia de reparto" valor={`${r.diferenciaMaxima.toFixed(1)} pp`} nota={estructura === 0 ? 'frente al reparto real' : 'esperada: los arquetipos no existen en los datos reales'} />
        <Kpi titulo="Recupera arquetipos (ARI)" valor={r.ari === null ? '—' : r.ari.toFixed(2)} nota={r.ari === null ? 'sin estructura no hay arquetipos' : `1 = perfecto, 0 = azar · ${r.conArquetipo.toLocaleString()} clientes`} />
      </div>

      <div className={`${TARJETA} p-6 space-y-3`}>
        <h4 className="font-bold text-sm text-slate-900 dark:text-white">Reparto por grupo: clientes reales frente a simulados (%)</h4>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={grafica} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? '#1E293B' : '#F1F5F9'} />
              <XAxis dataKey="nombre" axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 11 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 11 }} width={36} unit="%" />
              <Tooltip contentStyle={{ borderRadius: '12px', fontSize: '11px', border: 'none' }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="Clientes reales" fill="#94A3B8" radius={[6, 6, 6, 6]} barSize={22} />
              <Bar dataKey="Clientes simulados" fill="#2563EB" radius={[6, 6, 6, 6]} barSize={22} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1.5">
          {estructura === 0 && (
            <li>
              <strong>Generalización:</strong>{' '}
              {r.diferenciaMaxima <= 3
                ? `con clientes fabricados sin estructura, el modelo los reparte casi igual que a los reales (diferencia máxima ${r.diferenciaMaxima.toFixed(1)} pp), así que no depende de los 50,000 registros concretos.`
                : `el reparto se aleja del real (${r.diferenciaMaxima.toFixed(1)} pp). Con pocos clientes simulados es normal; prueba con más.`}
            </li>
          )}
          {r.silueta !== null && (
            <li>
              <strong>Separación:</strong> la silueta de los clientes simulados es {r.silueta.toFixed(3)} frente a {referencia} con los reales
              {Math.abs(r.silueta - referencia) <= 0.03 ? ': comportamiento parecido.' : r.silueta > referencia ? ': los grupos salen mejor separados porque los arquetipos sí tienen estructura.' : ': los grupos salen más mezclados.'}
            </li>
          )}
          {r.ari !== null && (
            <li>
              <strong>Recuperación de arquetipos:</strong> ARI {r.ari.toFixed(2)} ({calidadARI(r.ari)}).{' '}
              {r.ari < 0.3 && 'El modelo se entrenó con datos casi sin estructura, así que sus grupos no coinciden con estos arquetipos; es una limitación real del modelo, no del simulador.'}
            </li>
          )}
          <li><strong>Confianza media:</strong> {(100 * r.confianzaMedia).toFixed(1)} % · <strong>clientes en estatus Alerta:</strong> {r.porcentajeAlerta.toFixed(1)} %</li>
        </ul>
      </div>

      <div className={`${TARJETA} p-6 space-y-3 overflow-x-auto`}>
        <h4 className="font-bold text-sm text-slate-900 dark:text-white">Perfil de cada grupo: dataset original → clientes simulados</h4>
        <table className="w-full text-xs text-left">
          <thead>
            <tr className="text-[11px] text-slate-400">
              <th className="py-1.5">Grupo</th><th>% de clientes</th><th>% del gasto</th><th>Gasto promedio</th><th>Satisfacción</th><th>Días sin comprar</th><th>Compras</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {datos.clusters.map((g, i) => {
              const s = resumen.clusters[i]
              return (
                <tr key={g.id}>
                  <td className="py-1.5 font-medium text-slate-700 dark:text-slate-200"><span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ backgroundColor: g.color }} />{g.shortName}</td>
                  <td>{par(g.porcentaje, s.porcentaje, (x) => `${x.toFixed(1)}%`)}</td>
                  <td>{par(g.porcentajeGasto, s.porcentajeGasto, (x) => `${x.toFixed(1)}%`)}</td>
                  <td>{par(g.gastoPromedio, s.gastoPromedio, (x) => `$${x.toLocaleString()}`)}</td>
                  <td>{par(g.satisfaccion, s.satisfaccion, (x) => x.toFixed(2))}</td>
                  <td>{par(g.perfil.days_since_last_purchase, s.perfil.days_since_last_purchase, (x) => x.toFixed(0))}</td>
                  <td>{par(g.perfil.total_purchases, s.perfil.total_purchases, (x) => x.toFixed(0))}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {r.matriz.length > 0 && (
        <div className={`${TARJETA} p-6 space-y-3 overflow-x-auto`}>
          <h4 className="font-bold text-sm text-slate-900 dark:text-white">Arquetipo fabricado frente al grupo que asigna el modelo (% de cada fila)</h4>
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="text-[11px] text-slate-400">
                <th className="py-1.5">Arquetipo</th>
                {modelo.grupos.map((g) => <th key={g.id} className="text-center">Grupo {g.id}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {r.matriz.map((fila) => {
                const total = fila.conteos.reduce((a, b) => a + b, 0)
                return (
                  <tr key={fila.arquetipo}>
                    <td className="py-1.5 font-medium text-slate-700 dark:text-slate-200">{NOMBRES[fila.arquetipo] ?? fila.arquetipo}</td>
                    {fila.conteos.map((c, i) => {
                      const p = total ? c / total : 0
                      return (
                        <td key={i} className="text-center font-bold text-slate-900 dark:text-white" style={{ backgroundColor: `${modelo.grupos[i].color}${Math.round(p * 80 + 8).toString(16).padStart(2, '0')}` }}>
                          {(100 * p).toFixed(0)}%
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <button onClick={descargar} className="flex items-center gap-2 text-xs font-bold px-4 py-2.5 rounded-full border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition">
        <Download size={14} /> Descargar clientes simulados (CSV)
      </button>
    </div>
  )
}

// Fabrica clientes con el procedimiento del generador (src/data/generate.py), los pasa por el modelo y arma las mismas
// vistas que el dataset original para poder compararlas lado a lado.
export default function SimulationView({ modelo, datos, tabla, darkMode, simulacion, setSimulacion }) {
  const [cantidad, setCantidad] = useState(String(simulacion?.resultado.n ?? 5000))
  const [estructura, setEstructura] = useState(simulacion?.estructura ?? 0)
  const [semilla, setSemilla] = useState(String(simulacion?.semilla ?? 42))
  const [error, setError] = useState(null)
  const [pestana, setPestana] = useState('evaluacion')
  const [fuente, setFuente] = useState('ambos')
  const [segmento, setSegmento] = useState('all')

  const simular = (e) => {
    e.preventDefault()
    const n = Number(cantidad)
    const s = Number(semilla)
    if (!Number.isInteger(n) || n < MIN || n > MAX) return setError(`La cantidad debe ser un entero entre ${MIN.toLocaleString()} y ${MAX.toLocaleString()}.`)
    if (!Number.isInteger(s) || s < 0) return setError('La semilla debe ser un entero mayor o igual a 0.')
    setError(null)
    const clientes = simularClientes(modelo, n, estructura / 100, s)
    const resultado = evaluarSimulacion(modelo, clientes, s)
    const filas = clientes.map((c, i) => ({ ...c, cluster: resultado.grupos[i], estatus: resultado.estatus[i] }))
    setSegmento('all')
    setSimulacion({ clientes, resultado, resumen: resumir(filas, modelo), estructura: estructura / 100, semilla: s })
  }

  const sim = simulacion && { ...simulacion.resumen, evaluacion: datos.evaluacion }
  const pagina = (cual) => (
    <PaginaDatos
      key={cual} vista={pestana} datos={cual === 'simulados' ? sim : datos} tabla={cual === 'simulados' ? simulacion.resumen.tabla : tabla}
      evaluacion={datos.evaluacion} segmento={segmento} setSegmento={setSegmento} darkMode={darkMode} onIr={setPestana} validacion={false}
    />
  )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
          <FlaskConical size={20} className="text-blue-600 dark:text-blue-400" /> Simulación de clientes
        </h2>
        <p className="text-xs text-slate-400 max-w-3xl">
          El modelo buscó sus {modelo.k} grupos en los {datos.meta.clientes.toLocaleString()} clientes reales. Aquí se fabrican clientes nuevos con el mismo procedimiento del generador del proyecto
          (<code>src/data/generate.py</code>, con las proporciones del dataset real), se pasan por el modelo y se dibujan las mismas vistas que las del dataset original, para compararlas.
        </p>
      </div>

      <form onSubmit={simular} className={`${TARJETA} p-6 space-y-4`} noValidate>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <label className="block text-xs">
            <span className="font-semibold text-slate-700 dark:text-slate-200">Cantidad de clientes a fabricar</span>
            <input type="number" inputMode="numeric" min={MIN} max={MAX} step={100} value={cantidad} onChange={(e) => setCantidad(e.target.value)} className={entrada} />
            <span className="flex flex-wrap gap-1.5 mt-2">
              {PRESETS.map((p) => (
                <button key={p} type="button" onClick={() => setCantidad(String(p))} className="text-[11px] font-bold px-2.5 py-1 rounded-full border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800">{p.toLocaleString()}</button>
              ))}
            </span>
          </label>
          <label className="block text-xs">
            <span className="flex items-center justify-between font-semibold text-slate-700 dark:text-slate-200">Estructura <span className="font-extrabold text-blue-600 dark:text-blue-400">{estructura} %</span></span>
            <input type="range" min="0" max="100" step="10" value={estructura} onChange={(e) => setEstructura(Number(e.target.value))} className="w-full mt-3 accent-blue-600" aria-label="Estructura de los clientes simulados" />
            <span className="block text-[11px] text-slate-400 leading-snug mt-1">0 % reproduce el dataset original (variables independientes). Con más, esa fracción sigue uno de 5 arquetipos y se puede medir si el modelo los recupera.</span>
          </label>
          <label className="block text-xs">
            <span className="font-semibold text-slate-700 dark:text-slate-200">Semilla (misma semilla, mismos clientes)</span>
            <span className="flex gap-2 mt-1">
              <input type="number" inputMode="numeric" min={0} step={1} value={semilla} onChange={(e) => setSemilla(e.target.value)} className={`${entrada} mt-0 flex-1`} />
              <button type="button" onClick={() => setSemilla(String(Math.floor(Math.random() * 1000000)))} className="flex items-center gap-1.5 text-[11px] font-bold px-3 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800">
                <Dices size={14} /> Al azar
              </button>
            </span>
          </label>
        </div>
        {error && <p className="text-rose-500 text-xs" role="alert">{error}</p>}
        <div className="flex flex-wrap items-center gap-4">
          <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-6 py-3 rounded-2xl transition">Simular y evaluar</button>
          <p className="text-[11px] text-slate-400 leading-snug flex-1 min-w-[260px]">
            El navegador usa otro generador de números aleatorios que numpy, así que con la misma semilla no salen los mismos clientes que en Python; lo que se conserva es la distribución (se verifica con pruebas automáticas).
          </p>
        </div>
      </form>

      {!simulacion && <div className={`${TARJETA} p-8 text-center text-xs text-slate-400`}>Elige cuántos clientes fabricar y pulsa «Simular y evaluar».</div>}
      {simulacion && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2" role="tablist" aria-label="Vistas de la simulación">
              {PESTANAS.map(([id, nombre]) => <button key={id} role="tab" aria-selected={pestana === id} onClick={() => setPestana(id)} className={pildora(pestana === id)}>{nombre}</button>)}
            </div>
            {pestana !== 'evaluacion' && (
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                Datos:
                {FUENTES.map(([id, nombre]) => <button key={id} onClick={() => setFuente(id)} className={pildora(fuente === id)}>{nombre}</button>)}
              </div>
            )}
          </div>

          {pestana === 'evaluacion' && <Evaluacion modelo={modelo} datos={datos} simulacion={simulacion} darkMode={darkMode} />}
          {pestana !== 'evaluacion' && (
            <div className="space-y-10">
              {(fuente === 'simulados' || fuente === 'ambos') && (
                <section aria-label="Clientes simulados" className="space-y-6">
                  <h3 className="text-sm font-extrabold text-blue-700 dark:text-blue-400 border-l-4 border-blue-600 pl-3">Clientes simulados ({simulacion.resultado.n.toLocaleString()}) · estructura {Math.round(100 * simulacion.estructura)} % · semilla {simulacion.semilla}</h3>
                  {pagina('simulados')}
                </section>
              )}
              {(fuente === 'originales' || fuente === 'ambos') && (
                <section aria-label="Dataset original" className="space-y-6">
                  <h3 className="text-sm font-extrabold text-slate-600 dark:text-slate-300 border-l-4 border-slate-400 pl-3">Dataset original, referencia ({datos.meta.clientes.toLocaleString()} clientes)</h3>
                  {pagina('originales')}
                </section>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
