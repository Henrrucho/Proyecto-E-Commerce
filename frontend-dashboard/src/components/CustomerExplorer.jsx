import { useMemo, useState } from 'react'
import { Download, Search, Star } from 'lucide-react'
import { TARJETA } from './iconos'

const POR_PAGINA = 25
const ESTATUS = {
  Normal: 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400',
  Atención: 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400',
  Alerta: 'bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400',
}

function descargarCsv(filas, nombre) {
  const encabezado = 'customer_id,grupo,segmento_rfm,gasto_total_usd,compras,satisfaccion,estatus,pais'
  const cuerpo = filas.map((c) => [c.id, c.cluster, c.rfm, c.spent, c.orders, c.satisfaction, c.status, c.country].join(','))
  const url = URL.createObjectURL(new Blob([[encabezado, ...cuerpo].join('\n')], { type: 'text/csv;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: nombre })
  a.click()
  URL.revokeObjectURL(url)
}

// Explorador de clientes con filtro por grupo (RF-05), búsqueda por ID y contador dinámico.
export default function CustomerExplorer({ clientes, grupos, segmento, setSegmento }) {
  const [busqueda, setBusqueda] = useState('')
  const [pagina, setPagina] = useState(0)
  const nombres = useMemo(() => Object.fromEntries(grupos.map((g) => [g.id, g.name])), [grupos])
  const filtrados = useMemo(() => {
    const q = busqueda.trim().toUpperCase()
    return clientes.filter((c) => (segmento === 'all' || c.cluster === Number(segmento)) && (!q || c.id.includes(q)))
  }, [clientes, segmento, busqueda])
  const paginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA))
  const actual = Math.min(pagina, paginas - 1)
  const visibles = filtrados.slice(actual * POR_PAGINA, (actual + 1) * POR_PAGINA)

  return (
    <section id="tabla-clientes" className={`${TARJETA} p-6 space-y-4`}>
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Explorador y Filtrado de Clientes por Grupo</h3>
          <p className="text-xs text-slate-400">Consulta individual de clientes y conteo dinámico por grupo</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={busqueda} onChange={(e) => { setBusqueda(e.target.value); setPagina(0) }} placeholder="Buscar ID (CUST-000123)" aria-label="Buscar cliente por ID"
              className="bg-[#F4F5F7] dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold pl-8 pr-3 py-2 rounded-full border border-slate-200 dark:border-slate-700 w-52"
            />
          </label>
          <select
            value={segmento} onChange={(e) => { setSegmento(e.target.value); setPagina(0) }} aria-label="Filtrar por grupo"
            className="bg-[#F4F5F7] dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold px-4 py-2 rounded-full border border-slate-200 dark:border-slate-700"
          >
            <option value="all">Todos los grupos ({clientes.length.toLocaleString()})</option>
            {grupos.map((g) => <option key={g.id} value={String(g.id)}>{g.name} ({g.clientes.toLocaleString()})</option>)}
          </select>
          <span className="bg-slate-900 dark:bg-blue-600 text-white text-xs font-semibold px-3.5 py-2 rounded-full">
            Mostrando: {filtrados.length.toLocaleString()} de {clientes.length.toLocaleString()}
          </span>
          <button
            onClick={() => descargarCsv(filtrados, 'clientes_filtrados.csv')}
            className="flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-full border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
          >
            <Download size={13} /> Exportar vista
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-100 dark:border-slate-800 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
              {['ID Cliente', 'Grupo del modelo', 'Segmento RFM', 'Gasto Total', 'Compras', 'Satisfacción', 'País', 'Estatus'].map((t, i, a) => (
                <th key={t} className={`py-3 px-4 ${i === a.length - 1 ? 'text-right' : ''}`}>{t}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
            {visibles.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition">
                <td className="py-3 px-4 font-mono font-bold text-slate-900 dark:text-white">{c.id}</td>
                <td className="py-3 px-4">
                  <span className="inline-flex font-semibold text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-3 py-1 rounded-full">{nombres[c.cluster]}</span>
                </td>
                <td className="py-3 px-4 text-slate-500 dark:text-slate-400 font-medium">{c.rfm}</td>
                <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">${c.spent.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                <td className="py-3 px-4 text-slate-600 dark:text-slate-300">{c.orders} órdenes</td>
                <td className="py-3 px-4">
                  <span className={`inline-flex items-center gap-1 font-bold ${c.satisfaction < 3 ? 'text-rose-500' : 'text-emerald-600 dark:text-emerald-400'}`}>
                    <Star size={12} className="fill-current" /> {c.satisfaction} / 5
                  </span>
                </td>
                <td className="py-3 px-4 text-slate-500 dark:text-slate-400">{c.country}</td>
                <td className="py-3 px-4 text-right">
                  <span className={`inline-block px-3 py-1 rounded-full text-[11px] font-semibold ${ESTATUS[c.status]}`}>{c.status}</span>
                </td>
              </tr>
            ))}
            {visibles.length === 0 && (
              <tr><td colSpan="8" className="py-8 text-center text-slate-400">Ningún cliente coincide con el filtro.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>Página {actual + 1} de {paginas.toLocaleString()}</span>
        <div className="flex gap-2">
          <button disabled={actual === 0} onClick={() => setPagina(actual - 1)} className="px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800">Anterior</button>
          <button disabled={actual >= paginas - 1} onClick={() => setPagina(actual + 1)} className="px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800">Siguiente</button>
        </div>
      </div>
    </section>
  )
}
