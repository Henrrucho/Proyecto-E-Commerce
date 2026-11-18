import { CheckCircle2, FlaskConical, Globe, LayoutDashboard, Lightbulb, Smile, Wand2 } from 'lucide-react'

const VISTAS = [
  { id: 'dashboard', label: 'Panel Principal', icono: LayoutDashboard },
  { id: 'trends', label: 'Tendencias y Zonas', icono: Globe },
  { id: 'recommendations', label: 'Recomendaciones IA', icono: Lightbulb },
  { id: 'satisfaction', label: 'Satisfacción y Modelo', icono: Smile },
  { id: 'predict', label: 'Predicción de cliente', icono: Wand2 },
  { id: 'simulate', label: 'Simulación de clientes', icono: FlaskConical },
]

export default function Sidebar({ vistaActiva, setVistaActiva, clientes }) {
  return (
    <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-100 dark:border-slate-800 p-6 hidden xl:flex flex-col justify-between shrink-0 transition-colors">
      <div className="space-y-8">
        <div className="flex items-center gap-3 px-2">
          <div className="w-9 h-9 rounded-2xl bg-blue-600 flex items-center justify-center text-white font-extrabold text-sm shadow-md shadow-blue-600/20">EC</div>
          <div>
            <span className="font-extrabold text-slate-900 dark:text-white tracking-tight block leading-none">E-Commerce AI</span>
            <span className="text-[11px] text-slate-400 font-medium">Customer Intelligence</span>
          </div>
        </div>
        <nav className="space-y-1.5">
          {VISTAS.map(({ id, label, icono: Icono }) => (
            <button
              key={id}
              onClick={() => setVistaActiva(id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-xs font-bold transition-all ${
                vistaActiva === id
                  ? 'bg-slate-900 dark:bg-blue-600 text-white shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60'
              }`}
            >
              <Icono size={16} />
              {label}
            </button>
          ))}
        </nav>
      </div>
      <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-2xl border border-slate-100 dark:border-slate-800 space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-slate-200">
          <CheckCircle2 size={14} className="text-emerald-500" />
          Base Activa Verificada
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          {clientes.toLocaleString()} clientes y 53 variables validadas; los valores faltantes se imputan en el preprocesamiento.
        </p>
      </div>
    </aside>
  )
}
