import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { CheckCircle2, FileCheck, Upload, XCircle } from 'lucide-react'
import { TARJETA } from './iconos'

// Lee solo el encabezado del CSV (primeros 64 KB) y lo compara con las 53 columnas esperadas (RF-01, sin servidor).
async function validarArchivo(archivo, esperadas) {
  const texto = await archivo.slice(0, 65536).text()
  const encabezado = texto.split(/\r?\n/, 1)[0] || ''
  const columnas = encabezado.split(',').map((c) => c.trim().replace(/^"|"$/g, '')).filter(Boolean)
  return {
    nombre: archivo.name, columnas: columnas.length,
    faltan: esperadas.filter((c) => !columnas.includes(c)),
    sobran: columnas.filter((c) => !esperadas.includes(c)),
  }
}

export default function ModelValidation({ evaluacion, esperadas, darkMode }) {
  const [resultado, setResultado] = useState(null)
  const { configuraciones, ganador, baselines, estabilidad } = evaluacion
  const ks = [...new Set(configuraciones.map((c) => c.k))].sort()
  const datos = ks.map((k) => ({
    k: `K = ${k}`,
    'K-Means': configuraciones.find((c) => c.k === k && c.modelo === 'K-Means')?.silueta_train,
    'Algoritmo genético': configuraciones.find((c) => c.k === k && c.modelo === 'Algoritmo genético')?.silueta_train,
  }))
  const valido = resultado && resultado.faltan.length === 0 && resultado.sobran.length === 0

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className={`${TARJETA} p-6 space-y-4`}>
        <div>
          <h4 className="font-bold text-slate-900 dark:text-white">Validación del modelo</h4>
          <p className="text-xs text-slate-400">Silueta en entrenamiento por número de grupos (mayor es mejor; con el conjunto de variables {ganador.conjunto}).</p>
        </div>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={datos} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? '#1E293B' : '#F1F5F9'} />
              <XAxis dataKey="k" axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 11 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 11 }} width={40} domain={[0, 0.3]} />
              <Tooltip contentStyle={{ borderRadius: '12px', fontSize: '11px', border: 'none' }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="K-Means" fill="#FB923C" radius={[6, 6, 6, 6]} barSize={22} />
              <Bar dataKey="Algoritmo genético" fill="#2563EB" radius={[6, 6, 6, 6]} barSize={22} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1.5">
          <li><strong>Modelo elegido:</strong> {ganador.modelo}, K = {ganador.k} (silueta {ganador.silueta_train} en entrenamiento y {ganador.silueta_test} en prueba).</li>
          <li><strong>Tamaño de los grupos:</strong> de {(100 * ganador.tamano_minimo).toFixed(1)} % a {(100 * ganador.tamano_maximo).toFixed(1)} % de los clientes.</li>
          <li><strong>Referencias:</strong> reglas RFM {baselines['Reglas RFM']} · partición aleatoria {baselines['Partición aleatoria']}.</li>
          <li><strong>Estabilidad entre semillas</strong> (1 = idéntico): genético {estabilidad['Algoritmo genético']}, K-Means {estabilidad['K-Means']}.</li>
        </ul>
        <p className="text-[11px] text-slate-400 leading-snug">
          Una silueta baja significa que el dataset casi no tiene grupos naturales: los grupos describen el reparto de los clientes, no segmentos separados con claridad.
        </p>
      </div>

      <div className={`${TARJETA} p-6 space-y-4`}>
        <div>
          <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2"><FileCheck size={16} className="text-blue-500" /> Validador de CSV</h4>
          <p className="text-xs text-slate-400">Comprueba en tu navegador que un archivo trae las {esperadas.length} columnas esperadas. No se sube nada a ningún servidor.</p>
        </div>
        <label
          onDragOver={(e) => e.preventDefault()}
          onDrop={async (e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) setResultado(await validarArchivo(f, esperadas)) }}
          className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-2xl py-8 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition text-xs text-slate-500"
        >
          <Upload size={20} className="text-blue-500" />
          Arrastra un .csv aquí o haz clic para elegirlo
          <input type="file" accept=".csv,text/csv" className="hidden" aria-label="Archivo CSV a validar" onChange={async (e) => { const f = e.target.files[0]; if (f) setResultado(await validarArchivo(f, esperadas)) }} />
        </label>
        {resultado && (
          <div className={`rounded-2xl p-4 text-xs space-y-2 ${valido ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300' : 'bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300'}`}>
            <div className="flex items-center gap-2 font-bold">
              {valido ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
              {resultado.nombre}: {valido ? `✔ Lista (${resultado.columnas} columnas)` : `✖ No cumple el esquema (${resultado.columnas} columnas)`}
            </div>
            {resultado.faltan.length > 0 && <p><strong>Faltan:</strong> {resultado.faltan.join(', ')}</p>}
            {resultado.sobran.length > 0 && <p><strong>Sobran:</strong> {resultado.sobran.join(', ')}</p>}
          </div>
        )}
      </div>
    </div>
  )
}
