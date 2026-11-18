import { useState } from 'react'
import { AlertTriangle, Wand2 } from 'lucide-react'
import { predecir } from '../lib/predict'
import { TARJETA } from './iconos'

const ALERTA = {
  Normal: 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400',
  Atención: 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400',
  Alerta: 'bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400',
}

// Asigna un cliente nuevo a uno de los grupos del modelo (predecir en el navegador, sin servidor).
export default function PredictionView({ modelo }) {
  const vacio = Object.fromEntries(modelo.campos.map((c) => [c.id, '']))
  const [valores, setValores] = useState(vacio)
  const [resultado, setResultado] = useState(null)
  const grupos = modelo.grupos

  const enviar = (e) => {
    e.preventDefault()
    setResultado(predecir(modelo, valores))
  }
  const cargarEjemplo = (ejemplo) => {
    const nuevos = Object.fromEntries(modelo.campos.map((c) => [c.id, String(ejemplo[c.id])]))
    setValores(nuevos)
    setResultado(predecir(modelo, nuevos))
  }
  const grupo = resultado?.status === 'success' ? grupos.find((g) => g.id === resultado.cluster_id) : null

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
          <Wand2 size={20} className="text-blue-600 dark:text-blue-400" /> Predicción de cliente
        </h2>
        <p className="text-xs text-slate-400">
          Captura los datos de un cliente y el modelo ({modelo.familia}, K = {modelo.k}) lo asigna al grupo más cercano. El cálculo corre en tu navegador, igual que la función <code>predecir()</code> de Python.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6 items-start">
        <form onSubmit={enviar} className={`${TARJETA} p-6 space-y-4 xl:col-span-2`} noValidate>
          <div className="flex flex-wrap gap-2">
            <span className="text-[11px] text-slate-400 w-full">Cargar un cliente típico de cada grupo:</span>
            {modelo.ejemplos.map((ej) => (
              <button key={ej.grupo} type="button" onClick={() => cargarEjemplo(ej)} className="text-[11px] font-bold px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                <span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ backgroundColor: grupos[ej.grupo].color }} />Grupo {ej.grupo}
              </button>
            ))}
            <button type="button" onClick={() => { setValores(vacio); setResultado(null) }} className="text-[11px] font-bold px-3 py-1.5 rounded-full text-slate-500 hover:text-slate-800 dark:hover:text-slate-200">Limpiar</button>
          </div>
          {modelo.campos.map((c) => {
            const error = resultado?.errores?.[c.id]
            const aviso = resultado?.avisos?.[c.id]
            return (
              <label key={c.id} className="block text-xs">
                <span className="font-semibold text-slate-700 dark:text-slate-200">{c.etiqueta}</span>
                <input
                  type="number" inputMode="decimal" step={c.paso} min={c.min} value={valores[c.id]} placeholder={`Ej. ${c.ejemplo}`}
                  onChange={(e) => setValores({ ...valores, [c.id]: e.target.value })}
                  className={`mt-1 w-full bg-[#F4F5F7] dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm px-3.5 py-2 rounded-xl border ${error ? 'border-rose-400' : 'border-slate-200 dark:border-slate-700'}`}
                />
                {error && <span className="text-rose-500 text-[11px]">{error}</span>}
                {!error && aviso && <span className="text-amber-600 text-[11px]">{aviso}</span>}
              </label>
            )
          })}
          <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-4 py-3 rounded-2xl transition">Predecir grupo</button>
        </form>

        <div className="xl:col-span-3 space-y-4">
          {!resultado && (
            <div className={`${TARJETA} p-8 text-center text-xs text-slate-400`}>Captura un cliente (o carga un ejemplo) para ver a qué grupo pertenece.</div>
          )}
          {resultado?.status === 'error' && (
            <div className="rounded-3xl p-6 bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 text-xs flex items-start gap-2.5">
              <AlertTriangle size={16} className="shrink-0" />
              <div><strong>{resultado.mensaje}</strong> Corrige los campos marcados e inténtalo de nuevo.</div>
            </div>
          )}
          {grupo && (
            <>
              <div className={`${TARJETA} p-6 space-y-4`} style={{ borderTop: `4px solid ${grupo.color}` }}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-[11px] font-semibold text-slate-400">Grupo asignado</p>
                    <h3 className="text-lg font-extrabold text-slate-900 dark:text-white">{grupo.name}</h3>
                    <p className="text-[11px] text-slate-400">{grupo.porcentaje}% de los clientes · {grupo.desc}</p>
                  </div>
                  <span className={`text-xs font-bold px-3 py-1 rounded-full ${ALERTA[resultado.estatus_alerta]}`}>Estatus: {resultado.estatus_alerta}</span>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-700 dark:text-slate-200">Confianza de la asignación</span>
                    <span className="font-extrabold text-slate-900 dark:text-white">{(100 * resultado.confianza).toFixed(1)}%</span>
                  </div>
                  <div className="h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${100 * resultado.confianza}%`, backgroundColor: grupo.color }} />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">50 % = a igual distancia de dos grupos; 100 % = justo en el centro del grupo. No es la probabilidad de comprar ni de abandonar.</p>
                </div>
                <div className="rounded-2xl bg-slate-50 dark:bg-slate-800/60 p-4 text-xs text-slate-700 dark:text-slate-200">
                  <strong>Acción sugerida:</strong> {grupo.accion}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className={`${TARJETA} p-5`}>
                  <h4 className="font-bold text-sm text-slate-900 dark:text-white mb-3">Cercanía a cada grupo</h4>
                  <div className="space-y-2.5">
                    {grupos.map((g, i) => (
                      <div key={g.id} className="grid grid-cols-12 items-center gap-2 text-xs">
                        <span className="col-span-3 font-medium text-slate-700 dark:text-slate-300">Grupo {g.id}</span>
                        <div className="col-span-7 h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${100 * resultado.cercania[i]}%`, backgroundColor: g.color }} />
                        </div>
                        <span className="col-span-2 text-right font-bold text-slate-900 dark:text-white">{(100 * resultado.cercania[i]).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className={`${TARJETA} p-5 overflow-x-auto`}>
                  <h4 className="font-bold text-sm text-slate-900 dark:text-white mb-3">Tu cliente frente al grupo</h4>
                  <table className="w-full text-xs text-left">
                    <thead><tr className="text-[11px] text-slate-400"><th className="py-1.5">Dato</th><th>Cliente</th><th>Promedio del grupo</th></tr></thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {modelo.campos.map((c) => (
                        <tr key={c.id}>
                          <td className="py-1.5 text-slate-600 dark:text-slate-300">{c.etiqueta}</td>
                          <td className="font-bold text-slate-900 dark:text-white">{Number(valores[c.id])}</td>
                          <td className="text-slate-500">{grupo.perfil[c.id] ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
