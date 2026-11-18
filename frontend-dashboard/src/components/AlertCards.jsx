import { ArrowRight, Sparkles } from 'lucide-react'
import { ACENTOS, ICONOS } from './iconos'

export default function AlertCards({ alertas, segmento, setSegmento, clientes }) {
  return (
    <section className="space-y-2.5">
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <Sparkles size={15} className="text-blue-600 dark:text-blue-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Lo más importante hoy · Hallazgos Ejecutivos</h3>
        </div>
        {segmento !== 'all' && (
          <button onClick={() => setSegmento('all')} className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline">
            Restablecer vista global ({clientes.toLocaleString()})
          </button>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {alertas.map((a) => {
          const Icono = ICONOS[a.iconKey] || Sparkles
          const acento = ACENTOS[a.accent] || ACENTOS.blue
          const activa = segmento === a.targetSegment
          return (
            <div
              key={a.id}
              onClick={() => setSegmento(a.targetSegment)}
              className={`bg-white dark:bg-slate-900 rounded-3xl p-4 shadow-sm border border-slate-100 dark:border-slate-800 border-t-4 ${acento.borderTop} cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-md flex flex-col justify-between ${activa ? 'ring-2 ring-blue-500/50' : ''}`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${acento.iconBox}`}>
                    <Icono size={16} />
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${acento.badge}`}>Prioridad {a.priority}</span>
                </div>
                <p className="text-[11px] font-semibold text-slate-400">{a.title}</p>
                <h4 className="text-sm font-extrabold text-slate-900 dark:text-white mt-0.5">{a.metric}</h4>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-snug">{a.detail}</p>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-bold text-slate-800 dark:text-slate-200 group">
                <span>{a.actionLabel}</span>
                <ArrowRight size={13} className="text-blue-600 dark:text-blue-400 transition-transform group-hover:translate-x-1" />
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
