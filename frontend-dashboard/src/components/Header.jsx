import { CheckCircle2, Download, FileSpreadsheet, Moon, Sun } from 'lucide-react'
import { DESCARGAS } from '../services/api'

export default function Header({ darkMode, setDarkMode, clientes }) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">Panel de Inteligencia Comercial</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">Estrategias de segmentación, tendencias de consumo y fidelización de clientes</p>
      </div>
      <div className="flex flex-wrap items-center gap-2.5">
        <div className="bg-slate-900 dark:bg-blue-950/80 text-white px-3.5 py-2 rounded-full flex items-center gap-2.5 shadow-sm border border-slate-800 dark:border-blue-800/50">
          <span className="w-5 h-5 rounded-full border-2 border-orange-500 flex items-center justify-center text-[9px] font-extrabold">100%</span>
          <span className="text-xs font-bold">{clientes.toLocaleString()} Clientes Segmentados</span>
          <CheckCircle2 size={14} className="text-emerald-400" />
        </div>
        <a
          href={DESCARGAS.csv}
          download="customer_assignments.csv"
          className="bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-semibold px-3.5 py-2 rounded-full border border-slate-200 dark:border-slate-800 flex items-center gap-1.5 shadow-sm transition"
        >
          <FileSpreadsheet size={14} /> Exportar CSV
        </a>
        <a
          href={DESCARGAS.reporte}
          target="_blank"
          rel="noreferrer"
          className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3.5 py-2 rounded-full flex items-center gap-1.5 shadow-sm transition"
        >
          <Download size={14} /> Reporte Ejecutivo
        </a>
        <button
          onClick={() => setDarkMode(!darkMode)}
          title="Cambiar tema"
          className="w-9 h-9 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition shadow-sm"
        >
          {darkMode ? <Sun size={16} className="text-amber-400" /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  )
}
