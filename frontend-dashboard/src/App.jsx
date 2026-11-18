import { useEffect, useState } from 'react'
import Header from './components/Header'
import PaginaDatos from './components/PaginaDatos'
import PredictionView from './components/PredictionView'
import SimulationView from './components/SimulationView'
import Sidebar from './components/Sidebar'
import { cargarClientes, cargarDashboard, cargarModelo } from './services/api'

function Mensaje({ texto, error = false }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F4F5F7] dark:bg-[#0B0F19] p-8">
      <p className={`text-sm font-semibold ${error ? 'text-rose-600' : 'text-slate-500'}`} role={error ? 'alert' : 'status'}>{texto}</p>
    </div>
  )
}

const VISTAS_DATOS = ['dashboard', 'trends', 'recommendations', 'satisfaction']

export default function App() {
  const [darkMode, setDarkMode] = useState(() => {
    try { return localStorage.getItem('tema') === 'oscuro' } catch { return false }
  })
  const [vista, setVista] = useState('dashboard')
  const [segmento, setSegmento] = useState('all')
  const [datos, setDatos] = useState(null)
  const [clientes, setClientes] = useState(null)
  const [modelo, setModelo] = useState(null)
  const [error, setError] = useState(null)
  // La simulación vive aquí para que no se pierda al cambiar de pestaña
  const [simulacion, setSimulacion] = useState(null)

  useEffect(() => {
    // dashboard.json y model.json son pequeños; la tabla de clientes (3 MB) se descarga en paralelo.
    Promise.all([cargarDashboard(), cargarModelo(), cargarClientes()])
      .then(([d, m, c]) => { setDatos(d); setModelo(m); setClientes(c) })
      .catch((e) => setError(e.message))
  }, [])
  useEffect(() => {
    try { localStorage.setItem('tema', darkMode ? 'oscuro' : 'claro') } catch { /* sin almacenamiento */ }
  }, [darkMode])

  if (error) return <Mensaje texto={`No se pudieron cargar los datos del modelo. ${error}`} error />
  if (!datos || !clientes || !modelo) return <Mensaje texto="Cargando resultados del modelo…" />

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-[#F4F5F7] dark:bg-[#0B0F19] text-slate-900 dark:text-slate-100 flex font-sans transition-colors duration-300">
        <Sidebar vistaActiva={vista} setVistaActiva={setVista} clientes={datos.meta.clientes} />
        <main className="flex-1 p-5 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
          <Header darkMode={darkMode} setDarkMode={setDarkMode} clientes={datos.meta.clientes} />
          <nav className="xl:hidden flex flex-wrap gap-2" aria-label="Vistas">
            {[['dashboard', 'Panel'], ['trends', 'Tendencias'], ['recommendations', 'Recomendaciones'], ['satisfaction', 'Satisfacción'], ['predict', 'Predicción'], ['simulate', 'Simulación']].map(([id, nombre]) => (
              <button key={id} onClick={() => setVista(id)} className={`text-xs font-bold px-3.5 py-2 rounded-full ${vista === id ? 'bg-slate-900 dark:bg-blue-600 text-white' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800'}`}>{nombre}</button>
            ))}
          </nav>

          {VISTAS_DATOS.includes(vista) && (
            <PaginaDatos
              vista={vista} datos={datos} tabla={clientes} evaluacion={datos.evaluacion} columnasEsperadas={datos.columnasEsperadas}
              segmento={segmento} setSegmento={setSegmento} darkMode={darkMode} onIr={setVista}
            />
          )}
          {vista === 'predict' && <PredictionView modelo={modelo} />}
          {vista === 'simulate' && (
            <SimulationView
              modelo={modelo} datos={datos} tabla={clientes} darkMode={darkMode}
              simulacion={simulacion} setSimulacion={setSimulacion}
            />
          )}
        </main>
      </div>
    </div>
  )
}
