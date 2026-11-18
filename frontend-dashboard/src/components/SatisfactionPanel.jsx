import { useState } from 'react'
import { ArrowRight, CheckCircle2, Sparkles } from 'lucide-react'
import { TARJETA } from './iconos'

// KPIs de satisfacción + simulador de meta (RF-07): cuántos clientes neutrales o insatisfechos hay que recuperar.
export default function SatisfactionPanel({ insights, compacto = false, onAbrirDetalle }) {
  const { satisfaction: s } = insights
  const [meta, setMeta] = useState(75)
  const total = s.dist.reduce((a, d) => a + d.count, 0)
  const satisfechos = (s.dist[3]?.count || 0) + (s.dist[4]?.count || 0)
  const actual = total > 0 ? (satisfechos / total) * 100 : 0
  const porMejorar = (s.dist[0]?.count || 0) + (s.dist[1]?.count || 0) + (s.dist[2]?.count || 0)
  const objetivo = Math.ceil((meta / 100) * total)
  const recuperar = Math.max(0, objetivo - satisfechos)
  const alcanzable = Math.min(recuperar, porMejorar)
  const pctRecuperar = porMejorar > 0 ? Math.min(100, Math.round((recuperar / porMejorar) * 100)) : 0
  const maximo = Math.max(...s.dist.map((d) => d.count))

  const kpis = [
    ['Promedio', `${s.avg} de 5`, 'border-t-teal-400'],
    ['Satisfechos (4-5)', s.satisfiedPct, 'border-t-indigo-400'],
    ['Neutrales (3)', s.neutralPct, 'border-t-amber-400'],
    ['Insatisfechos (1-2)', s.unsatisfiedPct, 'border-t-rose-400'],
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-1">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Satisfacción del Cliente y Simulador de Meta</h3>
          <p className="text-xs text-slate-400">Estado de lealtad del grupo seleccionado</p>
        </div>
        {compacto && onAbrirDetalle && (
          <button onClick={onAbrirDetalle} className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
            Ver desglose y suscripciones <ArrowRight size={13} />
          </button>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {kpis.map(([nombre, valor, borde]) => (
          <div key={nombre} className={`bg-white dark:bg-slate-900 rounded-2xl p-4 shadow-sm border border-slate-100 dark:border-slate-800 border-t-4 ${borde}`}>
            <span className="text-[11px] text-slate-400">{nombre}</span>
            <div className="text-xl font-extrabold text-slate-900 dark:text-white mt-0.5">{valor}</div>
          </div>
        ))}
      </div>
      <div className={`${TARJETA} p-5 space-y-3`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <Sparkles size={14} />
            </span>
            <h4 className="font-bold text-slate-900 dark:text-white text-xs">Simulador de Meta de Satisfacción ({actual.toFixed(1)}% actual)</h4>
          </div>
          <span className="text-sm font-extrabold text-blue-600 dark:text-blue-400">Meta: {meta}%</span>
        </div>
        <input
          type="range" min="45" max="95" step="1" value={meta} aria-label="Meta de satisfacción"
          onChange={(e) => setMeta(Number(e.target.value))}
          className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-200 dark:bg-slate-700 rounded-lg"
        />
        <div className="text-xs text-slate-600 dark:text-slate-300 flex items-center gap-2">
          <CheckCircle2 size={15} className="text-emerald-500 shrink-0" />
          {recuperar === 0 ? (
            <span>Este segmento <strong>ya supera el {meta}%</strong> de satisfacción.</span>
          ) : (
            <span>
              Para llegar al <strong>{meta}%</strong>, necesitas recuperar a{' '}
              <strong className="text-emerald-600 dark:text-emerald-400">{alcanzable.toLocaleString()} clientes</strong> ({pctRecuperar}% de los neutrales e insatisfechos).
              {recuperar > porMejorar && ' La meta no es alcanzable con este segmento.'}
            </span>
          )}
        </div>
      </div>
      {!compacto && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
          <div className={`${TARJETA} p-6`}>
            <h4 className="font-bold text-slate-900 dark:text-white mb-5">Cuántos clientes dan cada calificación</h4>
            <div className="space-y-4">
              {s.dist.map((d) => (
                <div key={d.label} className="grid grid-cols-12 items-center gap-3 text-xs">
                  <span className="col-span-5 text-slate-600 dark:text-slate-300 font-medium">{d.label}</span>
                  <div className="col-span-5 h-5 bg-slate-100 dark:bg-slate-800 rounded-lg overflow-hidden">
                    <div className={`h-full rounded-lg transition-all duration-500 ${d.color}`} style={{ width: `${Math.max((d.count / maximo) * 100, 6)}%` }} />
                  </div>
                  <span className="col-span-2 text-right font-extrabold text-slate-900 dark:text-white">{d.count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
          <div className={`${TARJETA} p-6 overflow-x-auto`}>
            <h4 className="font-bold text-slate-900 dark:text-white mb-4">Por nivel de suscripción</h4>
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-[11px] font-bold">
                  <th className="py-2.5 px-3 bg-teal-400/20 text-teal-800 dark:text-teal-300 rounded-tl-xl">Nivel</th>
                  <th className="py-2.5 px-3 bg-indigo-400/20 text-indigo-800 dark:text-indigo-300">Clientes</th>
                  <th className="py-2.5 px-3 bg-purple-400/20 text-purple-800 dark:text-purple-300">Promedio</th>
                  <th className="py-2.5 px-3 bg-amber-400/20 text-amber-800 dark:text-amber-300">% Satisfechos</th>
                  <th className="py-2.5 px-3 bg-emerald-400/20 text-emerald-800 dark:text-emerald-300 rounded-tr-xl">Gasto Prom.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {s.tiers.map((t) => (
                  <tr key={t.tier} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition">
                    <td className="py-3 px-3 font-bold text-slate-900 dark:text-white">{t.tier}</td>
                    <td className="py-3 px-3 text-slate-600 dark:text-slate-300">{t.count}</td>
                    <td className="py-3 px-3 font-semibold text-slate-800 dark:text-slate-200">{t.avg}</td>
                    <td className="py-3 px-3 text-emerald-600 dark:text-emerald-400 font-semibold">{t.sat}</td>
                    <td className="py-3 px-3 font-bold text-slate-900 dark:text-white">{t.spent}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
