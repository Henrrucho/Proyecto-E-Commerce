import { useState } from 'react'
import { ArrowLeft, Globe, TrendingUp } from 'lucide-react'
import { BOTON_VOLVER, TARJETA } from './iconos'

const signo = (n) => (n >= 0 ? `+${n.toFixed(2)}` : n.toFixed(2))

// Comparador de categorías por zona (RF-05) y resumen por país. No hay filtro por temporada: el dataset no tiene fechas.
export default function TrendsView({ zonas, paises, onVolver, titulo = 'Detalle de Tendencias por Categoría, Zona y País' }) {
  const [zona, setZona] = useState('Todas las zonas')
  const categorias = zonas[zona] || zonas['Todas las zonas']
  const maximo = Math.max(...categorias.map((c) => c.share))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <TrendingUp size={20} className="text-emerald-500" /> {titulo}
          </h2>
          <p className="text-xs text-slate-400">Preferencia de compra (categoría principal de cada cliente) en las 12 categorías del catálogo</p>
        </div>
        {onVolver && <button onClick={onVolver} className={BOTON_VOLVER}><ArrowLeft size={14} /> Volver al Panel Principal</button>}
      </div>

      <div className={`${TARJETA} p-6 space-y-5`}>
        <div className="flex flex-wrap items-center gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
          <label className="flex items-center gap-2 text-xs font-semibold text-slate-500">
            Zona:
            <select value={zona} onChange={(e) => setZona(e.target.value)} className="bg-[#F4F5F7] dark:bg-slate-800 text-xs font-bold px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100">
              {Object.keys(zonas).map((z) => <option key={z}>{z}</option>)}
            </select>
          </label>
        </div>
        <div>
          <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-1">Categorías que más y menos pesan en la zona ({zona})</h3>
          <p className="text-[11px] text-slate-400 mb-4">Diferencia en puntos porcentuales (pp) frente al promedio global.</p>
          <div className="space-y-3">
            {categorias.map((c) => (
              <div key={c.name} className="grid grid-cols-12 items-center gap-3 text-xs">
                <div className="col-span-4 sm:col-span-3 flex flex-col">
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{c.name}</span>
                  {c.status !== 'Estable' && (
                    <span className={`inline-block w-fit text-[10px] font-bold px-2 py-0.5 rounded-full mt-0.5 ${c.status === 'Tendencia' ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400' : 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400'}`}>{c.status}</span>
                  )}
                </div>
                <div className="col-span-6 sm:col-span-7 h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-500 ${c.diff >= 0 ? 'bg-teal-500' : 'bg-amber-500'}`} style={{ width: `${(c.share / maximo) * 100}%` }} />
                </div>
                <div className="col-span-2 text-right font-bold text-slate-900 dark:text-white">
                  {c.share.toFixed(1)}% <span className={`text-[11px] ${c.diff >= 0 ? 'text-emerald-600' : 'text-amber-600'}`}>({signo(c.diff)} pp)</span>
                </div>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-slate-400 mt-4 leading-snug">
            Nota: en este dataset las preferencias están casi repartidas por igual (cada categoría ronda el 8.3 %), así que las diferencias son de menos de un punto
            y las etiquetas «Reforzar / Activar» son una guía ilustrativa, no una señal fuerte.
          </p>
        </div>
      </div>

      <div className={`${TARJETA} p-6`}>
        <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-4 flex items-center gap-2">
          <Globe size={16} className="text-blue-500" /> Resumen por país ({paises.length} mercados)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="text-[11px] font-bold text-white">
                {['País', 'Clientes', 'Categoría líder', 'Categoría más baja', 'Gasto promedio', '% en riesgo', 'Satisfacción'].map((t, i, a) => (
                  <th key={t} className={`py-3 px-3 ${['bg-teal-500', 'bg-indigo-500', 'bg-amber-500', 'bg-emerald-500', 'bg-teal-600', 'bg-indigo-400', 'bg-orange-400'][i]} ${i === 0 ? 'rounded-tl-xl' : ''} ${i === a.length - 1 ? 'rounded-tr-xl' : ''}`}>{t}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {paises.map((p) => (
                <tr key={p.country} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition">
                  <td className="py-3 px-3 font-bold text-slate-900 dark:text-white">{p.country}</td>
                  <td className="py-3 px-3 text-slate-600 dark:text-slate-300">{p.clients}</td>
                  <td className="py-3 px-3 font-semibold text-emerald-700 dark:text-emerald-400">{p.topCat}</td>
                  <td className="py-3 px-3 text-slate-500 dark:text-slate-400">{p.lowCat}</td>
                  <td className="py-3 px-3 font-bold text-slate-900 dark:text-white">{p.avgSpent}</td>
                  <td className="py-3 px-3 text-rose-600 dark:text-rose-400 font-semibold">{p.riskPct}</td>
                  <td className="py-3 px-3 font-semibold text-slate-800 dark:text-slate-200">{p.sat}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
