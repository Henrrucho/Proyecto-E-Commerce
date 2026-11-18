import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { TARJETA } from './iconos'

// Comparativa del modelo con la segmentación por reglas RFM (RF-06).
export default function ComparisonChart({ grupos, evaluacion, darkMode }) {
  const datos = grupos.map((g) => ({ ...g, nombre: `G${g.id}` }))
  const { baselines, ganador } = evaluacion
  return (
    <div className={`${TARJETA} p-5 flex flex-col justify-between h-full`}>
      <div className="mb-2">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white">Analítica de Segmentación</h3>
        <p className="text-[11px] text-slate-400">Gasto promedio (USD): grupos del modelo vs. categoría RFM dominante en cada grupo</p>
      </div>
      <div className="h-44 w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={datos} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? '#1E293B' : '#F1F5F9'} />
            <XAxis dataKey="nombre" axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 11 }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 11 }} tickFormatter={(v) => `$${Math.round(v / 1000)}k`} width={45} />
            <Tooltip
              cursor={{ fill: darkMode ? '#1E293B' : '#F8FAFC', radius: 8 }}
              contentStyle={{ borderRadius: '12px', fontSize: '11px', border: 'none' }}
              formatter={(v) => `$${Number(v).toLocaleString()}`}
            />
            <Bar dataKey="gastoPromedio" name="Grupo del modelo" fill="#2563EB" radius={[6, 6, 6, 6]} barSize={18} />
            <Bar dataKey="reglaRFM" name="Categoría RFM dominante" fill="#FB923C" radius={[6, 6, 6, 6]} barSize={18} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center justify-center gap-4 text-[11px] text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800">
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-600" /> Grupo del modelo</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-orange-400" /> Categoría RFM dominante</span>
      </div>
      <p className="text-[11px] text-slate-400 mt-2 leading-snug">
        Calidad de la separación (silueta, mayor es mejor): modelo <strong className="text-slate-700 dark:text-slate-200">{ganador.silueta_test}</strong>, reglas RFM{' '}
        <strong className="text-slate-700 dark:text-slate-200">{baselines['Reglas RFM']}</strong>, azar {baselines['Partición aleatoria']}.
      </p>
    </div>
  )
}
