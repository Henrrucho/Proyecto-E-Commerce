import { useMemo } from 'react'
import { ArrowLeft } from 'lucide-react'
import AlertCards from './AlertCards'
import CategoryTrends from './CategoryTrends'
import { ClusterProfiles, ValueChart } from './ClusterCards'
import ComparisonChart from './ComparisonChart'
import CustomerExplorer from './CustomerExplorer'
import { BOTON_VOLVER } from './iconos'
import ModelValidation from './ModelValidation'
import RecommendationsView from './RecommendationsView'
import SatisfactionPanel from './SatisfactionPanel'
import TrendsView from './TrendsView'

// Una de las 4 vistas de datos (panel, tendencias, recomendaciones, satisfacción). Se usa igual con los clientes
// reales (pestañas principales) y con los simulados (pestaña Simulación), para que las gráficas sean comparables.
export default function PaginaDatos({ vista, datos, tabla, evaluacion, columnasEsperadas, segmento, setSegmento, darkMode, onIr, validacion = true }) {
  const insights = useMemo(() => datos.insights[segmento] || datos.insights.all, [datos, segmento])
  const volver = () => onIr('dashboard')
  const gastoTotal = `$${(datos.clusters.reduce((s, g) => s + g.gastoPromedio * g.clientes, 0) / 1e6).toFixed(0)}M`

  if (vista === 'trends') return <TrendsView zonas={datos.zonas} paises={datos.paises} onVolver={volver} />
  if (vista === 'recommendations') {
    return (
      <RecommendationsView
        recomendaciones={datos.recomendaciones} zonas={datos.zonas} paises={datos.paises}
        onSeleccionar={(seg, destino) => { setSegmento(seg); onIr(destino) }} onVolver={volver}
      />
    )
  }
  if (vista === 'satisfaction') {
    return (
      <div className="space-y-6">
        <div className="flex justify-end"><button onClick={volver} className={BOTON_VOLVER}><ArrowLeft size={14} /> Volver al Panel Principal</button></div>
        <SatisfactionPanel key={segmento} insights={insights} />
        {validacion && <ModelValidation evaluacion={evaluacion} esperadas={columnasEsperadas} darkMode={darkMode} />}
      </div>
    )
  }
  return (
    <>
      <AlertCards alertas={datos.alertas} segmento={segmento} setSegmento={setSegmento} clientes={datos.meta.clientes} />
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div className="xl:col-span-7"><CategoryTrends insights={insights} onAbrirTendencias={() => onIr('trends')} /></div>
        <div className="xl:col-span-5"><SatisfactionPanel key={segmento} insights={insights} compacto onAbrirDetalle={() => onIr('satisfaction')} /></div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-4"><ClusterProfiles grupos={datos.clusters} segmento={segmento} setSegmento={setSegmento} /></div>
        <div className="lg:col-span-4"><ValueChart grupos={datos.clusters} segmento={segmento} setSegmento={setSegmento} gastoTotal={gastoTotal} /></div>
        <div className="lg:col-span-4"><ComparisonChart grupos={datos.clusters} evaluacion={evaluacion} darkMode={darkMode} /></div>
      </div>
      <CustomerExplorer clientes={tabla} grupos={datos.clusters} segmento={segmento} setSegmento={setSegmento} />
    </>
  )
}
