import React, { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import {
  Home, PieChart, Users, GitCompare, Download, FileSpreadsheet,
  Sparkles, ChevronRight, Bell, CheckCircle2, Moon, Sun
} from 'lucide-react';

export default function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState('Summary');
  const [selectedSegment, setSelectedSegment] = useState('all');

  // Datos de perfiles descubiertos por IA vs Reglas (RF-IA-04, RF-IA-05)
  const clusterAnalytics = [
    {
      name: 'Clúster 0 (VIP)',
      shortName: 'VIP Leales',
      clientes: 17000,
      porcentaje: 34,
      gastoPromedio: 4250,
      reglaRFM: 3800,
      satisfaccion: 4.8,
      color: '#2563EB',
      desc: 'Alta frecuencia y ticket elevado'
    },
    {
      name: 'Clúster 1 (Ocasional)',
      shortName: 'Ocasionales',
      clientes: 14500,
      porcentaje: 29,
      gastoPromedio: 1850,
      reglaRFM: 2100,
      satisfaccion: 3.9,
      color: '#3B82F6',
      desc: 'Compras estacionales, sensibilidad a promos'
    },
    {
      name: 'Clúster 2 (En Riesgo)',
      shortName: 'En Riesgo',
      clientes: 9500,
      porcentaje: 19,
      gastoPromedio: 1120,
      reglaRFM: 1650,
      satisfaccion: 2.1,
      color: '#F97316',
      desc: 'Altas devoluciones y quejas registradas'
    },
    {
      name: 'Clúster 3 (Nuevos)',
      shortName: 'Nuevos',
      clientes: 9000,
      porcentaje: 18,
      gastoPromedio: 490,
      reglaRFM: 520,
      satisfaccion: 3.5,
      color: '#10B981',
      desc: 'Poca antigüedad, primera o segunda compra'
    }
  ];

  // Evaluación de las 3 configuraciones de K-Means (RF-IA-03)
  const modelConfigs = [
    { k: 'K = 3', silhouette: 0.36, status: 'Evaluado' },
    { k: 'K = 4', silhouette: 0.42, status: 'Seleccionado' },
    { k: 'K = 5', silhouette: 0.31, status: 'Evaluado' },
  ];

  // Clientes para la tabla interactiva y filtro (RF-IA-06, RF-IA-07)
  const customersData = [
    { id: 'CUST-10021', segment: '0', name: 'Segmento 0: VIP Leales', spent: '$4,250.00', orders: 38, satisfaction: 4.8, rfm: 'Champion', status: 'Activo' },
    { id: 'CUST-10022', segment: '1', name: 'Segmento 1: Ocasionales', spent: '$1,850.00', orders: 12, satisfaction: 3.9, rfm: 'Potential', status: 'Activo' },
    { id: 'CUST-10023', segment: '2', name: 'Segmento 2: En Riesgo', spent: '$1,120.00', orders: 5, satisfaction: 1.8, rfm: 'At Risk', status: 'Alerta' },
    { id: 'CUST-10024', segment: '0', name: 'Segmento 0: VIP Leales', spent: '$5,100.00', orders: 44, satisfaction: 4.9, rfm: 'Champion', status: 'Activo' },
    { id: 'CUST-10025', segment: '3', name: 'Segmento 3: Nuevos', spent: '$490.00', orders: 2, satisfaction: 3.5, rfm: 'New', status: 'Nuevo' },
    { id: 'CUST-10026', segment: '2', name: 'Segmento 2: En Riesgo', spent: '$1,400.00', orders: 8, satisfaction: 2.1, rfm: 'Loyal (Falso)', status: 'Alerta' },
  ];

  const filteredCustomers = selectedSegment === 'all'
    ? customersData
    : customersData.filter(c => c.segment === selectedSegment);

  // Tooltip personalizado adaptable a modo claro/oscuro
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700 text-xs">
          <p className="text-slate-400 font-medium mb-2">{label}</p>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-4">
              <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                Gasto IA (K-Means)
              </span>
              <span className="font-bold text-slate-900 dark:text-white">${payload[0]?.value?.toLocaleString()} USD</span>
            </div>
            {payload[1] && (
              <div className="flex items-center justify-between gap-4">
                <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                  <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                  Regla Clásica RFM
                </span>
                <span className="font-bold text-slate-900 dark:text-white">${payload[1]?.value?.toLocaleString()} USD</span>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-[#F4F5F7] dark:bg-[#0B0F19] text-slate-900 dark:text-slate-100 flex font-sans transition-colors duration-300">
        
        {/* SIDEBAR MINIMALISTA */}
        <aside className="w-60 bg-[#F4F5F7] dark:bg-[#0B0F19] p-6 hidden lg:flex flex-col justify-between border-r border-slate-200/60 dark:border-slate-800/80 transition-colors duration-300">
          <div>
            {/* Logo */}
            <div className="flex items-center gap-3 px-2 mb-10">
              <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
                <Sparkles size={18} />
              </div>
              <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">E-Commerce AI</span>
            </div>

            {/* Navegación */}
            <nav className="space-y-2">
              <button
                onClick={() => setActiveTab('Summary')}
                className={`w-full flex items-center gap-3.5 px-3 py-2.5 rounded-full text-sm font-medium transition-all ${
                  activeTab === 'Summary'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <span className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  activeTab === 'Summary'
                    ? 'bg-slate-900 dark:bg-blue-600 text-white'
                    : 'bg-slate-200/70 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                }`}>
                  <Home size={15} />
                </span>
                Resumen IA
              </button>

              <button
                onClick={() => setActiveTab('Segments')}
                className={`w-full flex items-center gap-3.5 px-3 py-2.5 rounded-full text-sm font-medium transition-all ${
                  activeTab === 'Segments'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <span className="w-8 h-8 rounded-full bg-slate-200/70 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center">
                  <PieChart size={15} />
                </span>
                Perfiles K-Means
              </button>

              <button
                onClick={() => setActiveTab('Comparison')}
                className={`w-full flex items-center gap-3.5 px-3 py-2.5 rounded-full text-sm font-medium transition-all ${
                  activeTab === 'Comparison'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <span className="w-8 h-8 rounded-full bg-slate-200/70 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center">
                  <GitCompare size={15} />
                </span>
                IA vs. Reglas
              </button>

              <button
                onClick={() => document.getElementById('tabla-clientes')?.scrollIntoView({ behavior: 'smooth' })}
                className="w-full flex items-center gap-3.5 px-3 py-2.5 rounded-full text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-all"
              >
                <span className="w-8 h-8 rounded-full bg-slate-200/70 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center">
                  <Users size={15} />
                </span>
                Filtro Clientes
              </button>
            </nav>
          </div>

          {/* Estado del Dataset */}
          <div className="bg-white dark:bg-slate-900 p-4 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 mb-1">
              <CheckCircle2 size={14} /> Dataset Validado
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              50,000 registros y 53 columnas cargadas sin fuga de datos (R-02).
            </p>
          </div>
        </aside>

        {/* CONTENIDO PRINCIPAL */}
        <main className="flex-1 p-6 lg:p-10 max-w-7xl mx-auto w-full space-y-6">
          
          {/* HEADER ESTILO BRIGHT AI + BOTÓN MODO OSCURO */}
          <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
            <div className="flex items-center gap-4 flex-wrap">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                Hola, Henrry
              </h1>
              <span className="inline-flex items-center gap-1.5 bg-slate-900 dark:bg-blue-600 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-sm">
                <Sparkles size={13} className="text-orange-400 dark:text-amber-300" />
                PCA + K-Means Activo
              </span>
            </div>

            {/* Controles de Exportación (RF-IA-08) y Botón Dark Mode */}
            <div className="flex items-center gap-2.5">
              <button
                onClick={() => alert('Exportando customer_assignments.csv (50,000 clientes)...')}
                className="flex items-center gap-2 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200/80 dark:border-slate-800 text-xs font-semibold px-4 py-2.5 rounded-full shadow-sm transition-all"
              >
                <FileSpreadsheet size={15} className="text-blue-600 dark:text-blue-400" />
                + Exportar CSV
              </button>
              <button
                onClick={() => alert('Generando reporte ejecutivo segments_report.html...')}
                className="flex items-center gap-2 bg-slate-900 dark:bg-blue-600 hover:bg-slate-800 dark:hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2.5 rounded-full shadow-sm transition-all"
              >
                <Download size={15} />
                Reporte HTML
              </button>

              {/* BOTÓN DE MODO OSCURO / CLARO */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                title={darkMode ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
                className="w-10 h-10 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-700 dark:text-amber-400 shadow-sm hover:scale-105 transition-all"
              >
                {darkMode ? <Sun size={18} /> : <Moon size={18} />}
              </button>

              <div className="w-10 h-10 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-400 shadow-sm">
                <Bell size={16} />
              </div>
            </div>
          </header>

          {/* BENTO GRID PRINCIPAL */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* COLUMNA IZQUIERDA (8 COLUMNAS) */}
            <div className="lg:col-span-8 space-y-6">
              
              {/* TARJETA GRANDE: GRÁFICA ANALÍTICA DE SEGMENTOS */}
              <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-100 dark:border-slate-800 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                    Analítica de Segmentación (IA vs. Reglas RFM)
                  </h2>
                  <span className="text-xs text-slate-400 font-medium">
                    Gasto promedio (USD) por grupo descubierto
                  </span>
                </div>

                {/* Pestañas */}
                <div className="flex items-center gap-6 border-b border-slate-100 dark:border-slate-800 pb-3 mb-6 text-xs font-semibold overflow-x-auto">
                  {['Summary', 'Gasto Promedio', 'Frecuencia', 'Satisfacción', 'Reglas RFM'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`pb-3 -mb-3.5 transition-all whitespace-nowrap ${
                        activeTab === tab
                          ? 'text-slate-900 dark:text-white border-b-2 border-slate-900 dark:border-blue-500 font-bold'
                          : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
                      }`}
                    >
                      {tab === 'Summary' ? 'Resumen General' : tab}
                    </button>
                  ))}
                </div>

                {/* Gráfica de Barras Comparativa */}
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={clusterAnalytics} barGap={8}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                        stroke={darkMode ? '#1E293B' : '#F1F5F9'}
                      />
                      <XAxis
                        dataKey="name"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#94A3B8', fontSize: 12 }}
                        dy={10}
                      />
                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#94A3B8', fontSize: 12 }}
                        tickFormatter={(val) => `$${val}`}
                      />
                      <Tooltip
                        content={<CustomTooltip />}
                        cursor={{ fill: darkMode ? '#1E293B' : '#F8FAFC', radius: 12 }}
                      />
                      <Bar
                        dataKey="gastoPromedio"
                        name="Gasto IA (K-Means)"
                        fill="#2563EB"
                        radius={[10, 10, 10, 10]}
                        barSize={38}
                      />
                      <Bar
                        dataKey="reglaRFM"
                        name="Regla Clásica RFM"
                        fill="#FB923C"
                        radius={[10, 10, 10, 10]}
                        barSize={38}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* FILA INFERIOR IZQUIERDA: DOS TARJETAS EN PARALELO */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* TARJETA 1: PERFILES DE CLÚSTERES */}
                <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-sm border border-slate-100 dark:border-slate-800 flex flex-col justify-between transition-colors">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-bold text-slate-900 dark:text-white">Perfiles de Clúster</h3>
                      <button
                        onClick={() => setSelectedSegment('all')}
                        className="text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-3 py-1 rounded-full transition"
                      >
                        Ver todos
                      </button>
                    </div>
                    <p className="text-xs text-slate-400 mb-4">Haz clic en un grupo para filtrar la tabla</p>

                    <div className="space-y-3.5">
                      {clusterAnalytics.map((c, index) => (
                        <div
                          key={c.name}
                          onClick={() => setSelectedSegment(String(index))}
                          className={`flex items-center justify-between p-2.5 rounded-2xl cursor-pointer transition-all ${
                            selectedSegment === String(index)
                              ? 'bg-blue-50/80 dark:bg-blue-950/50 ring-1 ring-blue-500/30'
                              : 'hover:bg-slate-50 dark:hover:bg-slate-800/60'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className="w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-sm"
                              style={{ backgroundColor: c.color }}
                            >
                              C{index}
                            </div>
                            <div>
                              <div className="text-xs font-bold text-slate-900 dark:text-white">{c.shortName}</div>
                              <div className="text-[11px] text-slate-400">{c.desc}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xs font-bold text-slate-900 dark:text-white">
                              {c.clientes.toLocaleString()}
                            </div>
                            <div className={`text-[11px] font-semibold ${
                              c.satisfaccion >= 4.0 ? 'text-emerald-600 dark:text-emerald-400' : c.satisfaccion < 2.5 ? 'text-rose-500' : 'text-slate-400'
                            }`}>
                              ★ {c.satisfaccion} / 5
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* TARJETA 2: EVALUACIÓN DE 3 CONFIGURACIONES (RF-IA-03) */}
                <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-sm border border-slate-100 dark:border-slate-800 flex flex-col justify-between transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold text-slate-900 dark:text-white">Evaluación K-Means</h3>
                    <span className="text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-3 py-1 rounded-full">
                      3 Configs (RF-IA-03)
                    </span>
                  </div>

                  <div className="my-2">
                    <p className="text-xs text-slate-400">Mejor Índice Silhouette</p>
                    <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-1">0.421</div>
                    <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium mt-0.5">
                      ✓ Configuración K=4 óptima seleccionada
                    </p>
                  </div>

                  {/* Mini gráfico de barras */}
                  <div className="grid grid-cols-3 gap-3 items-end pt-4 h-36">
                    {modelConfigs.map((cfg) => {
                      const isWinner = cfg.k === 'K = 4';
                      return (
                        <div key={cfg.k} className="flex flex-col items-center h-full justify-end">
                          {isWinner && (
                            <span className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-[10px] font-bold px-2.5 py-1 rounded-full mb-1.5 shadow">
                              {cfg.silhouette}
                            </span>
                          )}
                          <div
                            className={`w-full rounded-2xl transition-all ${
                              isWinner
                                ? 'bg-orange-500 h-20 shadow-md shadow-orange-500/20'
                                : 'bg-slate-100 dark:bg-slate-800 h-12'
                            }`}
                          ></div>
                          <span className="text-[11px] text-slate-400 font-medium mt-2">{cfg.k}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>
            </div>

            {/* COLUMNA DERECHA (4 COLUMNAS) */}
            <div className="lg:col-span-4 space-y-6">
              
              {/* WIDGET OSCURO SUPERIOR */}
              <div className="bg-slate-900 dark:bg-blue-950/60 dark:border dark:border-blue-800/40 text-white rounded-3xl p-5 shadow-md flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="relative w-12 h-12 rounded-full border-4 border-orange-500 flex items-center justify-center text-xs font-bold">
                    100%
                  </div>
                  <div>
                    <h4 className="text-sm font-bold">Clientes Segmentados</h4>
                    <p className="text-xs text-slate-400">50,000 válidos procesados con PCA</p>
                  </div>
                </div>
                <ChevronRight size={18} className="text-slate-400" />
              </div>

              {/* WIDGET MEDIO: HALLAZGO IA VS REGLAS */}
              <div className="bg-slate-200/70 dark:bg-slate-800/70 rounded-3xl p-6 border border-slate-200/80 dark:border-slate-700/60 relative overflow-hidden transition-colors">
                <h4 className="font-bold text-slate-900 dark:text-white text-base mb-1.5">
                  Hallazgo IA vs. Reglas RFM
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
                  K-Means detectó <strong>9,500 clientes en riesgo</strong> por altas quejas y devoluciones que la regla RFM clásica clasificaba erróneamente como "Leales".
                </p>
                <button
                  onClick={() => setSelectedSegment('2')}
                  className="bg-slate-900 dark:bg-orange-500 hover:bg-slate-800 dark:hover:bg-orange-400 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-sm transition"
                >
                  Inspeccionar Clúster 2
                </button>
              </div>

              {/* WIDGET INFERIOR: DISTRIBUCIÓN POBLACIONAL */}
              <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-sm border border-slate-100 dark:border-slate-800 space-y-5 transition-colors">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-slate-900 dark:text-white">Universo Analizado</h3>
                  <span className="w-7 h-7 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400">
                    <ChevronRight size={14} />
                  </span>
                </div>

                <div>
                  <p className="text-xs text-slate-400">Base activa E-Commerce 2026</p>
                  <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-1">50,000</div>
                </div>

                {/* Barra segmentada multicolor */}
                <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-slate-800 flex overflow-hidden gap-0.5">
                  <div className="bg-blue-600 h-full" style={{ width: '34%' }} title="VIP (34%)"></div>
                  <div className="bg-sky-400 h-full" style={{ width: '29%' }} title="Ocasionales (29%)"></div>
                  <div className="bg-orange-500 h-full" style={{ width: '19%' }} title="En Riesgo (19%)"></div>
                  <div className="bg-emerald-500 h-full" style={{ width: '18%' }} title="Nuevos (18%)"></div>
                </div>

                {/* Desglose de porcentajes */}
                <div className="grid grid-cols-3 gap-2 pt-1">
                  <div>
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                      <span className="w-2 h-2 rounded-full bg-blue-600"></span> VIP
                    </div>
                    <div className="font-bold text-sm text-slate-900 dark:text-white mt-0.5">17.0K</div>
                    <div className="text-[11px] text-slate-400">34%</div>
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                      <span className="w-2 h-2 rounded-full bg-sky-400"></span> Ocasional
                    </div>
                    <div className="font-bold text-sm text-slate-900 dark:text-white mt-0.5">14.5K</div>
                    <div className="text-[11px] text-slate-400">29%</div>
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                      <span className="w-2 h-2 rounded-full bg-orange-500"></span> Riesgo
                    </div>
                    <div className="font-bold text-sm text-slate-900 dark:text-white mt-0.5">9.5K</div>
                    <div className="text-[11px] text-slate-400">19%</div>
                  </div>
                </div>

                <button
                  onClick={() => document.getElementById('tabla-clientes')?.scrollIntoView({ behavior: 'smooth' })}
                  className="w-full py-2.5 rounded-full border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
                >
                  Ver tabla de clientes detallada
                </button>
              </div>

            </div>
          </div>

          {/* SECCIÓN INFERIOR: FILTRO Y TABLA DE CLIENTES (RF-IA-06 y RF-IA-07) */}
          <section id="tabla-clientes" className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-100 dark:border-slate-800 space-y-5 transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  Explorador y Filtrado de Clientes por Segmento
                </h3>
                <p className="text-xs text-slate-400">
                  Consulta individual sin ejecutar código (RF-IA-06) y conteo dinámico por segmento (RF-IA-07)
                </p>
              </div>

              <div className="flex items-center gap-3">
                <select
                  value={selectedSegment}
                  onChange={(e) => setSelectedSegment(e.target.value)}
                  className="bg-[#F4F5F7] dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold px-4 py-2.5 rounded-full border border-slate-200 dark:border-slate-700 focus:outline-none"
                >
                  <option value="all">Todos los segmentos (50,000)</option>
                  <option value="0">Clúster 0: VIP Leales (17,000)</option>
                  <option value="1">Clúster 1: Ocasionales (14,500)</option>
                  <option value="2">Clúster 2: En Riesgo / Quejas (9,500)</option>
                  <option value="3">Clúster 3: Nuevos (9,000)</option>
                </select>

                <span className="bg-slate-900 dark:bg-blue-600 text-white text-xs font-semibold px-4 py-2 rounded-full">
                  Mostrando: {filteredCustomers.length}
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                    <th className="py-3.5 px-4">Customer ID</th>
                    <th className="py-3.5 px-4">Segmento IA (K-Means)</th>
                    <th className="py-3.5 px-4">Clasificación Regla RFM</th>
                    <th className="py-3.5 px-4">Gasto Total</th>
                    <th className="py-3.5 px-4">Compras</th>
                    <th className="py-3.5 px-4">Satisfacción</th>
                    <th className="py-3.5 px-4 text-right">Estatus</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                  {filteredCustomers.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition">
                      <td className="py-3.5 px-4 font-mono font-bold text-slate-900 dark:text-white">{c.id}</td>
                      <td className="py-3.5 px-4">
                        <span className="inline-flex items-center gap-1.5 font-semibold text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-3 py-1 rounded-full">
                          {c.name}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 dark:text-slate-400 font-medium">{c.rfm}</td>
                      <td className="py-3.5 px-4 font-bold text-slate-900 dark:text-white">{c.spent}</td>
                      <td className="py-3.5 px-4 text-slate-600 dark:text-slate-300">{c.orders} órdenes</td>
                      <td className="py-3.5 px-4">
                        <span className={`font-bold ${c.satisfaction < 2.5 ? 'text-rose-500' : 'text-emerald-600 dark:text-emerald-400'}`}>
                          ★ {c.satisfaction} / 5
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <span className={`inline-block px-3 py-1 rounded-full text-[11px] font-semibold ${
                          c.status === 'Activo'
                            ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400'
                            : c.status === 'Alerta'
                            ? 'bg-orange-50 dark:bg-orange-950/60 text-orange-700 dark:text-orange-400'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                        }`}>
                          {c.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

        </main>
      </div>
    </div>
  );
}