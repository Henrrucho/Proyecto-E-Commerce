import { ArrowRight, Share2, TrendingUp } from 'lucide-react'
import { ICONOS, TARJETA } from './iconos'

export default function CategoryTrends({ insights, onAbrirTendencias }) {
  const { label, categories, socialConversion, funnel, unitEconomics } = insights
  const maxRate = Math.max(...socialConversion.map((r) => r.rate))
  return (
    <div className="space-y-3">
      <div className="px-1">
        <h3 className="text-base font-bold text-slate-900 dark:text-white">Tendencias de Categorías y Canales de Marketing</h3>
        <p className="text-xs text-slate-400">
          Segmento activo: <strong className="text-blue-600 dark:text-blue-400">{label}</strong>
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className={`${TARJETA} p-5 flex flex-col justify-between`}>
          <div>
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                <TrendingUp size={16} className="text-emerald-500" /> Categorías Preferidas
              </h4>
              <button onClick={onAbrirTendencias} className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
                Ver más detalles <ArrowRight size={13} />
              </button>
            </div>
            <div className="space-y-3.5">
              {categories.map((c) => {
                const Icono = ICONOS[c.iconKey] || ICONOS.sparkles
                return (
                  <div key={c.name} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span className="w-9 h-9 rounded-2xl bg-blue-50 dark:bg-slate-800 text-blue-600 dark:text-blue-400 flex items-center justify-center shadow-sm">
                        <Icono size={17} />
                      </span>
                      <div>
                        <div className="text-xs font-bold text-slate-900 dark:text-white">{c.name}</div>
                        <div className="text-[11px] text-slate-400">Ticket prom: {c.avgTicket}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-extrabold text-emerald-600 dark:text-emerald-400">{c.share}</div>
                      <div className="text-[10px] text-slate-400">{c.topZone}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
          <button
            onClick={onAbrirTendencias}
            className="mt-4 w-full py-2 rounded-2xl bg-slate-50 dark:bg-slate-800/70 hover:bg-blue-50 dark:hover:bg-slate-800 text-xs font-bold text-blue-600 dark:text-blue-400 transition flex items-center justify-center gap-1.5"
          >
            Abrir tendencias por zona y país <ArrowRight size={13} />
          </button>
        </div>
        <div className={`${TARJETA} p-5`}>
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
              <Share2 size={16} className="text-indigo-500" /> Marketing: Conversión por Canal
            </h4>
            <span className="text-[11px] text-slate-400 font-medium">Redes y Correo</span>
          </div>
          <div className="space-y-2.5">
            {socialConversion.map((r) => (
              <div key={r.net} className="grid grid-cols-12 items-center gap-2 text-xs">
                <span className="col-span-4 font-medium text-slate-700 dark:text-slate-300">{r.net}</span>
                <div className="col-span-5 h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 rounded-full transition-all duration-500" style={{ width: `${Math.min((r.rate / maxRate) * 100, 100)}%` }} />
                </div>
                <span className="col-span-3 text-right font-bold text-slate-900 dark:text-white">{r.rate}%</span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-3 gap-2 text-center">
            {[['Apertura Email', `${funnel.emailOpen}%`], ['Clics (CTR)', `${funnel.ctr}%`], ['Conversión', `${funnel.conversion}%`]].map(([nombre, valor], i) => (
              <div key={nombre} className="bg-slate-50 dark:bg-slate-800/60 p-2 rounded-2xl">
                <div className="text-[10px] text-slate-400">{nombre}</div>
                <div className={`text-xs font-bold ${i === 2 ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-900 dark:text-white'}`}>{valor}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            {[['CAC', unitEconomics.cac], ['CLV', unitEconomics.clv], ['Devoluciones', unitEconomics.returnsAvg]].map(([nombre, valor]) => (
              <div key={nombre} className="rounded-2xl border border-slate-100 dark:border-slate-800 p-2">
                <div className="text-[10px] text-slate-400">{nombre}</div>
                <div className="text-[11px] font-bold text-slate-900 dark:text-white">{valor}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
