import { Gem, Star } from 'lucide-react'
import { TARJETA } from './iconos'

// Selector de perfiles (RF-05): al elegir un grupo se filtra todo el tablero.
export function ClusterProfiles({ grupos, segmento, setSegmento }) {
  return (
    <div className={`${TARJETA} p-5 flex flex-col justify-between h-full`}>
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-bold text-sm text-slate-900 dark:text-white">Perfiles de Grupo</h3>
          <button
            onClick={() => setSegmento('all')}
            className="text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-2.5 py-1 rounded-full transition"
          >
            Ver todos
          </button>
        </div>
        <p className="text-[11px] text-slate-400 mb-3">Selecciona un grupo para filtrar el tablero</p>
        <div className="space-y-2">
          {grupos.map((g) => (
            <div
              key={g.id}
              onClick={() => setSegmento(String(g.id))}
              className={`flex items-center justify-between p-2 rounded-2xl cursor-pointer transition-all ${
                segmento === String(g.id) ? 'bg-blue-50/80 dark:bg-blue-950/50 ring-1 ring-blue-500/30' : 'hover:bg-slate-50 dark:hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-sm shrink-0" style={{ backgroundColor: g.color }}>
                  G{g.id}
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">{g.shortName}</div>
                  <div className="text-[10px] text-slate-400">{g.desc}</div>
                </div>
              </div>
              <div className="text-right shrink-0 pl-2">
                <div className="text-xs font-bold text-slate-900 dark:text-white">{g.clientes.toLocaleString()}</div>
                <div
                  className={`inline-flex items-center justify-end gap-1 text-[10px] font-semibold ${
                    g.satisfaccion >= 4 ? 'text-emerald-600 dark:text-emerald-400' : g.satisfaccion < 2.5 ? 'text-rose-500' : 'text-slate-400'
                  }`}
                >
                  <Star size={10} className="fill-current" /> {g.satisfaccion}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Concentración de valor (Pareto): % de clientes frente a % de ingresos por grupo.
export function ValueChart({ grupos, segmento, setSegmento, gastoTotal }) {
  return (
    <div className={`${TARJETA} p-5 flex flex-col justify-between h-full`}>
      <div>
        <div className="mb-3">
          <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-1.5">
            <Gem size={15} className="text-blue-600 dark:text-blue-400" /> Dónde está el valor
          </h3>
          <p className="text-[11px] text-slate-400">% Clientes vs. % Ingresos ({gastoTotal})</p>
        </div>
        <div className="space-y-2.5">
          {grupos.map((g) => (
            <div
              key={g.id}
              onClick={() => setSegmento(String(g.id))}
              className={`p-2 rounded-2xl cursor-pointer transition ${segmento === String(g.id) ? 'bg-blue-50/70 dark:bg-blue-950/40 ring-1 ring-blue-500/30' : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'}`}
            >
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: g.color }} />G{g.id} · {g.shortName}
                </span>
                <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400">{g.gastoTotalM}</span>
              </div>
              {[['Clientes', g.porcentaje, ''], ['Ingresos', g.porcentajeGasto, 'opacity-60']].map(([nombre, valor, opacidad]) => (
                <div key={nombre} className="grid grid-cols-12 items-center gap-1.5 text-[10px] mb-0.5">
                  <span className="col-span-3 text-slate-400">{nombre}</span>
                  <div className="col-span-7 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${opacidad}`} style={{ width: `${valor}%`, backgroundColor: g.color }} />
                  </div>
                  <span className="col-span-2 text-right font-semibold text-slate-700 dark:text-slate-200">{valor}%</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
