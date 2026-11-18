import { ArrowLeft, ArrowRight, Lightbulb } from 'lucide-react'
import { BOTON_VOLVER, TARJETA } from './iconos'
import TrendsView from './TrendsView'

// Acciones priorizadas a partir de los datos (RF-04); cada botón filtra el tablero hacia el grupo afectado.
export default function RecommendationsView({ recomendaciones, zonas, paises, onSeleccionar, onVolver }) {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Lightbulb size={20} className="text-blue-600 dark:text-blue-400" /> Recomendaciones de la IA
          </h2>
          <p className="text-xs text-slate-400">Acciones priorizadas por valor en juego, inactividad, satisfacción y preferencias por zona</p>
        </div>
        <button onClick={onVolver} className={BOTON_VOLVER}><ArrowLeft size={14} /> Volver al Panel Principal</button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {recomendaciones.map((r) => (
          <div key={r.id} className={`${TARJETA} p-6 flex flex-col justify-between`}>
            <div className="space-y-3">
              <h3 className="font-bold text-slate-900 dark:text-white text-sm leading-snug">{r.title}</h3>
              <span className={`inline-block text-[11px] font-bold px-3 py-0.5 rounded-full ${r.priority === 'Alta' ? 'bg-amber-100/80 dark:bg-amber-950/70 text-amber-800 dark:text-amber-300' : 'bg-blue-100/80 dark:bg-blue-950/70 text-blue-800 dark:text-blue-300'}`}>
                Prioridad {r.priority}
              </span>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed"><strong className="text-slate-900 dark:text-white">Dato:</strong> {r.fact}</p>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed"><strong className="text-slate-900 dark:text-white">Acción sugerida:</strong> {r.action}</p>
            </div>
            <button
              onClick={() => onSeleccionar(r.targetSegment, r.targetView)}
              className="mt-5 w-fit px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5 transition"
            >
              {r.buttonLabel} <ArrowRight size={13} />
            </button>
          </div>
        ))}
      </div>
      <TrendsView zonas={zonas} paises={paises} />
    </div>
  )
}
