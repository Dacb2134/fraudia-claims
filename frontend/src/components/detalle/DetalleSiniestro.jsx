import { useState, useEffect } from 'react';
import {
  getSiniestroDetalle,
  getRedProveedor,
  getExplicacionIA,
} from '../../services/detalle/DetalleSiniestroService';

// ─── Configuración de semáforo ──────────────────────────────────────────────
const CIRCUMFERENCE = 440; // 2π × r(70)

const NIVEL = {
  ROJO: {
    badge:         'bg-error text-on-error',
    label:         'ALTO RIESGO',
    stroke:        '#ba1a1a',
    track:         '#ffdad6',
    text:          'text-error',
    borderCard:    'border-error-container',
    glow:          '0 0 20px rgba(186,26,26,0.2)',
    accionPrimaria:'Iniciar Auditoría',
    accionSecundaria: 'Suspender Pago',
    sugerencias: [
      'Escalar inmediatamente a la Unidad Especializada de Antifraude.',
      'Suspender el pago de forma preventiva hasta completar la revisión.',
      'Solicitar inspección de campo con perito certificado.',
      'Verificar identidad del asegurado y documentos originales.',
    ],
  },
  AMARILLO: {
    badge:         'bg-[#f97316] text-white',
    label:         'RIESGO MEDIO',
    stroke:        '#f97316',
    track:         '#ffedd5',
    text:          'text-[#f97316]',
    borderCard:    'border-orange-200',
    glow:          'none',
    accionPrimaria:'Escalar a Revisión',
    accionSecundaria: 'Solicitar Documentación',
    sugerencias: [
      'Solicitar documentación adicional al asegurado en 5 días hábiles.',
      'Escalar a supervisor para revisión documental detallada.',
      'Verificar historial del proveedor beneficiario.',
      'Marcar caso para seguimiento en 15 días.',
    ],
  },
  VERDE: {
    badge:         'bg-[#16a34a] text-white',
    label:         'BAJO RIESGO',
    stroke:        '#16a34a',
    track:         '#dcfce7',
    text:          'text-[#16a34a]',
    borderCard:    'border-green-200',
    glow:          'none',
    accionPrimaria:'Aprobar Pago',
    accionSecundaria: 'Archivar Caso',
    sugerencias: [
      'Continuar con el flujo de pago normal.',
      'Archivar caso una vez completado el proceso.',
      'No se requieren acciones adicionales de revisión.',
    ],
  },
};

// ─── Helpers de alertas ─────────────────────────────────────────────────────
function parseAlertas(alertasStr) {
  if (!alertasStr?.trim()) return [];
  return alertasStr
    .split(' | ')
    .filter(Boolean)
    .map((raw, i) => {
      // Extrae puntos del final: "→ 8 pts)" o "(3 pts)"
      const match = raw.match(/(\d+)\s*pts\)/);
      const pts = match ? parseInt(match[1]) : 0;
      // Muestra texto sin la anotación de puntos al final
      const texto = raw.replace(/\s*\([^(]*pts\)\s*$/, '').trim();
      return { id: i, texto, pts };
    });
}

function getAlertaIcon(texto) {
  const t = texto.toLowerCase();
  if (t.includes('tardío') || t.includes('tardio') || t.includes('retraso')) return 'timer_off';
  if (t.includes('demora') || t.includes('denuncia')) return 'schedule';
  if (t.includes('proveedor') || t.includes('prov-')) return 'hub';
  if (t.includes('monto') || t.includes('suma asegurada')) return 'payments';
  if (t.includes('document') || t.includes('inconsistente')) return 'folder_off';
  if (t.includes('frecuencia') || t.includes('siniestros previos')) return 'repeat';
  if (t.includes('narrativa') || t.includes('similar') || t.includes('idéntica')) return 'content_copy';
  if (t.includes('borde') || t.includes('vigencia')) return 'event_busy';
  if (t.includes('dinámica') || t.includes('dinamica') || t.includes('pérdida total')) return 'directions_car';
  if (t.includes('tercero') || t.includes('rastro')) return 'person_off';
  return 'warning';
}

function alertaStyle(pts) {
  if (pts >= 7) return { bg: 'rgba(255,218,214,0.25)', border: '#ba1a1a', textColor: '#ba1a1a' };
  if (pts >= 4) return { bg: 'rgba(255,237,213,0.5)',  border: '#f97316', textColor: '#f97316' };
  return             { bg: 'rgba(230,238,255,0.3)',     border: '#747783', textColor: '#747783' };
}

// ─── Helpers de timeline ────────────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return null;
  try {
    return new Date(dateStr).toLocaleDateString('es-EC', {
      day: 'numeric', month: 'short', year: 'numeric',
    });
  } catch { return dateStr; }
}

function buildTimeline(s) {
  const events = [];

  if (s.fecha_ocurrencia) events.push({
    titulo:      'Ocurrencia del Siniestro',
    fecha:       s.fecha_ocurrencia,
    descripcion: s.descripcion?.substring(0, 110) || 'Evento reportado por el asegurado.',
    tipo:        'normal',
  });

  if (s.fecha_reporte) {
    const dias = s.dias_reporte || 0;
    events.push({
      titulo:      'Reporte a la Aseguradora',
      fecha:       s.fecha_reporte,
      descripcion: dias > 7
        ? `Alerta: retraso de ${dias} días en la notificación.`
        : `Notificado ${dias} día${dias !== 1 ? 's' : ''} después del evento.`,
      tipo: dias > 7 ? 'alerta' : 'normal',
    });
  }

  if (s.proveedor?.id) {
    const obs = s.proveedor.pct_casos_observados;
    events.push({
      titulo:      `Ingreso a proveedor ${s.proveedor.id}`,
      fecha:       null,
      descripcion: s.proveedor.en_lista_restrictiva
        ? 'Proveedor en lista restrictiva. Requiere revisión.'
        : obs > 0.3
          ? `Proveedor con ${Math.round(obs * 100)}% de casos observados.`
          : 'Proveedor asignado al caso.',
      tipo: s.proveedor.en_lista_restrictiva ? 'error' : obs > 0.3 ? 'alerta' : 'normal',
    });
  }

  if (s.score?.calculado_en) events.push({
    titulo:      'Análisis de Riesgo FraudIA',
    fecha:       s.score.calculado_en,
    descripcion: `Score ${s.score.valor}/100 — ${s.score.nivel}. ${
      s.score.nivel === 'ROJO'     ? 'Requiere revisión especializada de campo.' :
      s.score.nivel === 'AMARILLO' ? 'Escalar a Unidad Antifraude.' :
      'Continuar flujo normal.'
    }`,
    tipo: s.score.nivel === 'ROJO' ? 'error' : 'normal',
  });

  return events;
}

// ─── Documentos por ramo ────────────────────────────────────────────────────
const DOCS_POR_RAMO = {
  'Vehículos': ['Factura de Reparación', 'Fotografías del Siniestro', 'Declaración Jurada', 'Reporte Policial'],
  'Hogar':     ['Factura de Reparación', 'Fotografías del Siniestro', 'Declaración Jurada', 'Informe de Perito'],
  'Salud':     ['Historia Clínica',      'Facturas Médicas',          'Diagnóstico Médico', 'Recetas'],
  'Vida':      ['Acta de Defunción',     'Docs. de Beneficiario',     'Certificado Médico', 'Declaración Jurada'],
  'Generales': ['Factura',               'Fotografías del Daño',      'Declaración Jurada', 'Informe de Perito'],
};

function getDocumentos(s) {
  const lista = DOCS_POR_RAMO[s.ramo] || DOCS_POR_RAMO['Generales'];
  return lista.map((nombre, i) => {
    // Marcar el segundo documento como inconsistente si tiene_doc_inconsistente=true
    if (s.tiene_doc_inconsistente && i === 1) return { nombre, estado: 'inconsistente' };
    // Marcar el último como pendiente si documentos_completos=false
    if (!s.documentos_completos && i === lista.length - 1) return { nombre, estado: 'pendiente' };
    return { nombre, estado: 'completo' };
  });
}

// ─── Componente principal ───────────────────────────────────────────────────
/**
 * Props:
 *   siniestroId  {string}    - ID del siniestro a mostrar (ej: "SIN-00001")
 *   onBack       {function}  - Callback para volver al listado
 *
 * Con react-router puedes hacer:
 *   const { id } = useParams();
 *   <DetalleSiniestro siniestroId={id} onBack={() => navigate('/casos')} />
 */
export default function DetalleSiniestro({ siniestroId, onBack }) {
  const [siniestro,  setSiniestro]  = useState(null);
  const [redData,    setRedData]    = useState(null);
  const [explicacion,setExplicacion]= useState('');
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState(null);
  const [showModal,  setShowModal]  = useState(false);

  useEffect(() => {
    if (!siniestroId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    getSiniestroDetalle(siniestroId)
      .then(data => {
        if (cancelled) return;
        setSiniestro(data);

        // Carga en paralelo: red del proveedor + explicación IA
        if (data.proveedor?.id) {
          getRedProveedor(data.proveedor.id)
            .then(r => { if (!cancelled) setRedData(r); })
            .catch(() => {}); // no bloquea si falla
        }
        getExplicacionIA(siniestroId)
          .then(r => { if (!cancelled) setExplicacion(r.respuesta || ''); })
          .catch(() => {}); // no bloquea si falta GEMINI_API_KEY
      })
      .catch(e => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [siniestroId]);

  // ── Estados de carga / error ──
  if (loading) return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <span className="material-symbols-outlined text-primary text-[48px] animate-spin">autorenew</span>
        <p className="text-on-surface-variant font-body-md">Cargando siniestro {siniestroId}…</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="bg-error-container text-error p-8 rounded-xl max-w-md text-center space-y-3">
        <span className="material-symbols-outlined text-[48px]" style={{ fontVariationSettings: "'FILL' 1" }}>error</span>
        <h2 className="font-title-md text-title-md">No se pudo cargar el siniestro</h2>
        <p className="font-body-md">{error}</p>
        <button onClick={onBack} className="mt-4 bg-primary text-on-primary px-6 py-2 rounded-lg font-medium">
          Volver al listado
        </button>
      </div>
    </div>
  );

  if (!siniestro) return null;

  // ── Derivados del siniestro ──
  const nivel       = siniestro.score?.nivel || 'VERDE';
  const score       = siniestro.score?.valor || 0;
  const cfg         = NIVEL[nivel] || NIVEL.VERDE;
  const dashOffset  = CIRCUMFERENCE * (1 - score / 100);
  const alertas     = parseAlertas(siniestro.score?.alertas);
  const timeline    = buildTimeline(siniestro);
  const documentos  = getDocumentos(siniestro);
  const reglasCrit  = Array.isArray(siniestro.score?.reglas_criticas)
                        ? siniestro.score.reglas_criticas
                        : [];

  // Explicación de respaldo si Gemini no está configurado
  const textoIA = explicacion || (
    alertas.length > 0
      ? `El siniestro ${siniestroId} presenta ${alertas.length} señal${alertas.length > 1 ? 'es' : ''} que requieren revisión: ${alertas.slice(0, 2).map(a => a.texto).join('; ')}${alertas.length > 2 ? ', entre otras.' : '.'}`
      : 'No se detectaron señales de alerta significativas. Se recomienda continuar el flujo normal.'
  );

  return (
    <div className="bg-background text-on-surface font-body-md overflow-x-hidden">

      {/* ══ TopAppBar ══════════════════════════════════════════════════════ */}
      <header className="bg-surface-container-lowest shadow-sm flex justify-between items-center w-full px-margin-desktop h-16 z-50 sticky top-0">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="material-symbols-outlined text-primary cursor-pointer hover:opacity-70 transition-opacity"
            title="Volver al listado">
            arrow_back
          </button>
          <span className="text-title-md font-title-md font-black text-primary">FraudIA Claims</span>
        </div>

        <div className="flex items-center gap-6">
          <div className="hidden md:flex gap-4">
            <button className="text-on-surface-variant hover:bg-surface-container-high transition-colors font-label-sm text-label-sm px-2 py-1 rounded">Dashboard</button>
            <button className="text-primary font-bold border-b-2 border-primary pb-1 font-label-sm text-label-sm">Gestión de Casos</button>
            <button className="text-on-surface-variant hover:bg-surface-container-high transition-colors font-label-sm text-label-sm px-2 py-1 rounded">Reportes</button>
          </div>
          <div className="flex items-center gap-2 border-l border-outline-variant pl-6">
            <span className="material-symbols-outlined text-on-surface-variant">notifications</span>
            <span className="material-symbols-outlined text-on-surface-variant">help</span>
            <div className="flex items-center gap-2 ml-2">
              <span className="text-label-sm font-label-sm text-on-surface-variant">Analista de Riesgos</span>
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary text-xs font-bold">AR</div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex min-h-screen">

        {/* ══ Sidebar ════════════════════════════════════════════════════════ */}
        <aside className="hidden lg:flex flex-col h-auto py-8 px-4 gap-4 bg-surface-container w-64 border-r border-outline-variant">
          <div className="flex flex-col gap-2 mb-8">
            <span className="font-headline-lg text-headline-lg text-primary">FraudIA</span>
            <span className="text-label-sm font-label-sm text-on-surface-variant">Intelligent Detector</span>
          </div>
          <nav className="flex flex-col gap-2">
            {[
              { icon: 'dashboard',  label: 'Dashboard',        active: false },
              { icon: 'assignment', label: 'Gestión de Casos', active: true  },
              { icon: 'analytics',  label: 'Reportes',         active: false },
              { icon: 'settings',   label: 'Configuración',    active: false },
            ].map(({ icon, label, active }) => (
              <a key={label} href="#"
                className={`flex items-center gap-3 p-3 rounded-xl transition-colors ${
                  active
                    ? 'text-primary font-bold bg-surface-container-high'
                    : 'text-on-surface-variant hover:bg-surface-container-high'
                }`}>
                <span className="material-symbols-outlined">{icon}</span>
                <span className="font-label-sm text-label-sm">{label}</span>
              </a>
            ))}
          </nav>
        </aside>

        {/* ══ Contenido principal ════════════════════════════════════════════ */}
        <main className="flex-1 p-6 md:p-10 space-y-8 max-w-7xl mx-auto w-full">

          {/* Breadcrumbs */}
          <nav className="flex items-center gap-2 text-on-surface-variant font-label-sm text-label-sm">
            <button onClick={onBack} className="hover:text-primary transition-colors">Casos</button>
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            <span className="text-primary font-bold">Siniestro #{siniestro.id_siniestro}</span>
          </nav>

          {/* ── Reglas críticas (banner urgente si las hay) ── */}
          {reglasCrit.length > 0 && (
            <div className="bg-error-container border border-error rounded-xl p-4 flex items-center gap-3">
              <span className="material-symbols-outlined text-error" style={{ fontVariationSettings: "'FILL' 1" }}>gpp_bad</span>
              <div>
                <span className="font-medium text-error">Reglas críticas activadas: </span>
                <span className="font-label-sm text-label-sm text-error">{reglasCrit.join(' · ')}</span>
              </div>
            </div>
          )}

          {/* ══ Hero: Score + Explicación IA ═══════════════════════════════ */}
          <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Tarjeta principal con score */}
            <div
              className={`lg:col-span-2 bg-surface-container-lowest rounded-xl p-8 border relative overflow-hidden flex flex-col sm:flex-row items-center justify-between gap-6 ${cfg.borderCard}`}
              style={{ boxShadow: cfg.glow }}>
              <div className="space-y-4 flex-1">
                <div className="flex flex-wrap items-center gap-3">
                  <span className={`${cfg.badge} px-3 py-1 rounded-full font-label-sm text-label-sm flex items-center gap-1`}>
                    <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>warning</span>
                    {cfg.label}
                  </span>
                  <h1 className="font-headline-lg text-headline-lg text-on-surface">Detalle de Siniestro</h1>
                </div>

                {/* Datos clave */}
                <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-body-md">
                  <span className="text-on-surface-variant">Asegurado:</span>
                  <span className="font-medium">{siniestro.id_asegurado}</span>
                  <span className="text-on-surface-variant">Póliza:</span>
                  <span className="font-medium">{siniestro.id_poliza}</span>
                  <span className="text-on-surface-variant">Ramo / Cobertura:</span>
                  <span className="font-medium">{siniestro.ramo} — {siniestro.cobertura}</span>
                  <span className="text-on-surface-variant">Monto reclamado:</span>
                  <span className="font-medium">
                    ${siniestro.monto_reclamado?.toLocaleString('es-EC', { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-on-surface-variant">Estado:</span>
                  <span className="font-medium">{siniestro.estado}</span>
                  <span className="text-on-surface-variant">Sucursal:</span>
                  <span className="font-medium">{siniestro.sucursal}</span>
                </div>

                <div className="flex flex-wrap gap-3 pt-2">
                  <button
                    onClick={() => setShowModal(true)}
                    className="bg-primary text-on-primary px-6 py-2 rounded-lg font-title-md text-title-md hover:opacity-90 transition-opacity">
                    {cfg.accionPrimaria}
                  </button>
                  <button className="border border-outline text-on-surface px-6 py-2 rounded-lg font-title-md text-title-md hover:bg-surface-container-high transition-colors">
                    {cfg.accionSecundaria}
                  </button>
                </div>
              </div>

              {/* Gauge circular de score */}
              <div className="flex flex-col items-center flex-shrink-0">
                <div className="relative w-40 h-40 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
                    <circle cx="80" cy="80" fill="transparent" r="70"
                      stroke={cfg.track} strokeWidth="12"/>
                    <circle cx="80" cy="80" fill="transparent" r="70"
                      stroke={cfg.stroke}
                      strokeDasharray={CIRCUMFERENCE}
                      strokeDashoffset={dashOffset}
                      strokeLinecap="round"
                      strokeWidth="12"
                      style={{ transition: 'stroke-dashoffset 1s ease' }}/>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className={`text-[48px] leading-none font-bold font-display-lg ${cfg.text}`}>{score}</span>
                    <span className="font-label-sm text-label-sm text-on-surface-variant">/ 100</span>
                  </div>
                </div>
                <span className={`mt-4 font-title-md text-title-md ${cfg.text}`}>Puntuación de Riesgo</span>
              </div>
            </div>

            {/* Tarjeta explicación IA */}
            <div className="bg-tertiary-container text-on-tertiary-container rounded-xl p-6 flex flex-col justify-between shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-on-tertiary-container">auto_awesome</span>
                <h3 className="font-title-md text-title-md text-on-tertiary">Explicación IA</h3>
              </div>
              <p className="font-body-md text-body-md italic leading-relaxed text-tertiary-fixed">
                "{textoIA}"
              </p>
              <div className="mt-4 pt-4 border-t border-on-tertiary-fixed-variant/30 flex justify-between items-center">
                <span className="text-label-sm font-label-sm opacity-80 text-tertiary-fixed">
                  Motor: Reglas + XGBoost + Gemini
                </span>
                <span
                  className="material-symbols-outlined text-[18px] cursor-help text-tertiary-fixed"
                  title="Score calculado: 60% motor de reglas + 40% modelo ML">
                  info
                </span>
              </div>
            </div>
          </section>

          {/* ══ Factores de Riesgo + Línea de Tiempo ══════════════════════ */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

            {/* Factores de riesgo */}
            <div className="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/30">
              <h2 className="font-title-md text-title-md text-on-surface mb-6 flex items-center gap-2">
                <span className="material-symbols-outlined text-error">list_alt</span>
                Factores de Riesgo Detectados
                <span className="ml-auto bg-surface-container text-primary font-label-sm text-label-sm px-2 py-0.5 rounded-full">
                  {alertas.length} alerta{alertas.length !== 1 ? 's' : ''}
                </span>
              </h2>

              {alertas.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-on-surface-variant gap-3">
                  <span className="material-symbols-outlined text-[48px] text-[#16a34a]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                  <p className="font-body-md">Sin alertas detectadas</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {alertas.map(alerta => {
                    const st = alertaStyle(alerta.pts);
                    return (
                      <div key={alerta.id}
                        className="flex items-center justify-between p-4 rounded-lg border-l-4"
                        style={{ backgroundColor: st.bg, borderLeftColor: st.border }}>
                        <div className="flex items-center gap-3">
                          <span
                            className="material-symbols-outlined"
                            style={{ color: st.border }}>
                            {getAlertaIcon(alerta.texto)}
                          </span>
                          <span className="font-body-md text-body-md text-on-surface">{alerta.texto}</span>
                        </div>
                        {alerta.pts > 0 && (
                          <span
                            className="font-label-sm text-label-sm font-bold ml-4 whitespace-nowrap"
                            style={{ color: st.textColor }}>
                            +{alerta.pts} pts
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Línea de tiempo */}
            <div className="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/30">
              <h2 className="font-title-md text-title-md text-on-surface mb-6 flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">timeline</span>
                Línea de Tiempo del Evento
              </h2>
              <div className="relative pl-8 space-y-7 before:content-[''] before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[2px] before:bg-outline-variant">
                {timeline.map((ev, i) => {
                  const dotColor =
                    ev.tipo === 'error'  ? '#ba1a1a' :
                    ev.tipo === 'alerta' ? '#f97316' :
                    i === 0              ? '#002662' : '#002662aa';
                  const titleColor =
                    ev.tipo === 'error' ? 'text-error' : 'text-on-surface';
                  const descColor =
                    ev.tipo === 'error'  ? 'text-error font-medium' :
                    ev.tipo === 'alerta' ? 'text-[#f97316] font-medium' :
                    'text-on-surface-variant';

                  return (
                    <div key={i} className="relative">
                      <span
                        className="absolute -left-[27px] top-1 w-4 h-4 rounded-full border-4 border-surface-container-lowest"
                        style={{ backgroundColor: dotColor }}/>
                      <div>
                        <h4 className={`font-title-md text-title-md ${titleColor}`}>{ev.titulo}</h4>
                        {ev.fecha && (
                          <p className="text-label-sm font-label-sm text-on-surface-variant">{formatDate(ev.fecha)}</p>
                        )}
                        <p className={`mt-1 text-body-md ${descColor}`}>{ev.descripcion}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* ══ Red de Relaciones + Estado Documental ══════════════════════ */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

            {/* Grafo de relaciones */}
            <div className="lg:col-span-2 bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/30 flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <h2 className="font-title-md text-title-md text-on-surface flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">account_tree</span>
                  Red de Relaciones (Grafo)
                </h2>
                {redData && (
                  <span className="text-label-sm font-label-sm text-on-surface-variant">
                    {redData.total} siniestros vinculados
                  </span>
                )}
              </div>

              <div className="flex-1 bg-surface-container rounded-lg relative overflow-hidden min-h-[280px]">
                {/* Fondo punteado decorativo */}
                <div className="absolute inset-0 opacity-10 pointer-events-none"
                  style={{ backgroundImage: 'radial-gradient(#002662 1px, transparent 1px)', backgroundSize: '20px 20px' }}/>

                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                  {siniestro.proveedor?.id && (
                    <line stroke="#002662" strokeWidth="2" x1="50%" x2="72%" y1="50%" y2="38%"/>
                  )}
                  {redData?.siniestros?.slice(0, 2).map((_, i) => (
                    <line key={i}
                      stroke={siniestro.proveedor.en_lista_restrictiva ? '#ba1a1a' : '#f97316'}
                      strokeWidth="1.5"
                      x1="72%" x2={`${76 + i * 6}%`}
                      y1="38%" y2={`${62 + i * 12}%`}/>
                  ))}
                </svg>

                {/* Nodo Asegurado */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center">
                  <div className="w-16 h-16 rounded-full bg-primary border-4 border-surface-container-lowest flex items-center justify-center text-on-primary shadow-lg z-10">
                    <span className="material-symbols-outlined">person</span>
                  </div>
                  <span className="bg-surface-container-lowest px-2 py-0.5 rounded mt-2 text-label-sm font-label-sm shadow-sm">
                    {siniestro.id_asegurado}
                  </span>
                </div>

                {/* Nodo Proveedor */}
                {siniestro.proveedor?.id && (
                  <div className="absolute flex flex-col items-center group" style={{ top: '30%', left: '68%' }}>
                    <div className={`w-14 h-14 rounded-full border-2 flex items-center justify-center shadow-md transition-transform group-hover:scale-110 ${
                      siniestro.proveedor.en_lista_restrictiva
                        ? 'bg-error-container border-error text-error'
                        : siniestro.proveedor.pct_casos_observados > 0.3
                          ? 'bg-orange-50 border-[#f97316] text-[#f97316]'
                          : 'bg-surface-container-lowest border-primary text-primary'
                    }`}>
                      <span className="material-symbols-outlined">build</span>
                    </div>
                    <span className={`text-label-sm font-label-sm font-bold mt-1 ${
                      siniestro.proveedor.en_lista_restrictiva ? 'text-error' : 'text-on-surface-variant'
                    }`}>
                      {siniestro.proveedor.id}
                    </span>
                    {siniestro.proveedor.en_lista_restrictiva && (
                      <span className="text-[10px] bg-error text-on-error px-1.5 py-0.5 rounded mt-0.5">
                        Lista restrictiva
                      </span>
                    )}
                    {/* Tooltip hover */}
                    <div className="hidden group-hover:block absolute top-full mt-2 w-52 p-2 bg-inverse-surface text-inverse-on-surface rounded-lg text-[11px] z-20 shadow-xl">
                      Tipo: {siniestro.proveedor.tipo || 'No especificado'}<br/>
                      Casos observados: {Math.round((siniestro.proveedor.pct_casos_observados || 0) * 100)}%
                      {redData ? ` | ${redData.total} siniestros vinculados` : ''}
                    </div>
                  </div>
                )}

                {/* Nodos de siniestros relacionados */}
                {redData?.siniestros?.slice(0, 2).map((rel, i) => (
                  <div key={rel.id_siniestro}
                    className="absolute flex flex-col items-center"
                    style={{ top: `${58 + i * 14}%`, left: `${74 + i * 5}%` }}>
                    <div className="w-10 h-10 rounded-full bg-surface-container-lowest border border-outline-variant flex items-center justify-center text-on-surface-variant shadow">
                      <span className="material-symbols-outlined text-[18px]">assignment</span>
                    </div>
                    <span className="text-[10px] text-on-surface-variant mt-0.5">{rel.id_siniestro}</span>
                  </div>
                ))}

                {!siniestro.proveedor?.id && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-on-surface-variant gap-2">
                    <span className="material-symbols-outlined text-[40px]">hub</span>
                    <p className="text-body-md">Sin proveedor vinculado</p>
                  </div>
                )}
              </div>
            </div>

            {/* Estado documental */}
            <div className="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/30 flex flex-col">
              <h2 className="font-title-md text-title-md text-on-surface mb-6 flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">task_alt</span>
                Estatus Documental
              </h2>

              <div className="space-y-4 flex-1">
                {documentos.map(({ nombre, estado }) => (
                  <div key={nombre} className="flex items-center justify-between p-3 border-b border-outline-variant/20">
                    <div className="flex items-center gap-3">
                      {estado === 'completo' && (
                        <span className="material-symbols-outlined text-secondary"
                          style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                      )}
                      {estado === 'inconsistente' && (
                        <span className="material-symbols-outlined text-error"
                          style={{ fontVariationSettings: "'FILL' 1" }}>error</span>
                      )}
                      {estado === 'pendiente' && (
                        <span className="material-symbols-outlined text-outline"
                          style={{ fontVariationSettings: "'FILL' 1" }}>pending</span>
                      )}
                      <span className="font-body-md text-body-md text-on-surface">{nombre}</span>
                    </div>
                    <span className={`font-label-sm text-label-sm ${
                      estado === 'inconsistente' ? 'text-error font-bold' :
                      estado === 'pendiente'     ? 'text-on-surface-variant italic' :
                      'text-on-surface-variant'
                    }`}>
                      {estado === 'completo'     ? 'Completo' :
                       estado === 'inconsistente'? 'Inconsistente' :
                       'Pendiente'}
                    </span>
                  </div>
                ))}
              </div>

              {siniestro.tiene_doc_inconsistente && (
                <div className="mt-6 p-4 bg-surface-container rounded-lg">
                  <p className="font-label-sm text-label-sm text-on-surface mb-1 font-bold">Nota del Sistema:</p>
                  <p className="text-body-md text-body-md text-on-surface-variant italic leading-tight">
                    Se detectaron inconsistencias en la documentación. Requiere verificación manual por el analista.
                  </p>
                </div>
              )}
            </div>
          </div>

        </main>
      </div>

      {/* ══ Botón flotante del agente IA ══════════════════════════════════ */}
      <button
        onClick={() => setShowModal(true)}
        className="fixed bottom-8 right-8 w-14 h-14 bg-primary text-on-primary rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform group z-50">
        <span className="material-symbols-outlined">smart_toy</span>
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-error rounded-full border-2 border-background animate-pulse"/>
        <div className="absolute right-full mr-4 bg-inverse-surface text-inverse-on-surface px-4 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap text-label-sm font-label-sm pointer-events-none">
          Sugerencias para este caso
        </div>
      </button>

      {/* ══ Modal: Sugerir acción al analista ════════════════════════════ */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
          onClick={() => setShowModal(false)}>
          <div
            className="bg-surface-container-lowest rounded-xl p-8 max-w-lg w-full shadow-2xl"
            onClick={e => e.stopPropagation()}>

            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary">smart_toy</span>
                <h2 className="font-title-md text-title-md text-on-surface">Sugerencias del Analista</h2>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="material-symbols-outlined text-on-surface-variant hover:text-on-surface transition-colors">
                close
              </button>
            </div>

            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full font-label-sm text-label-sm font-bold mb-4 ${cfg.badge}`}>
              <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>warning</span>
              {cfg.label} — Score {score}/100
            </div>

            <p className="text-body-md text-on-surface-variant mb-5">
              Basado en el análisis de riesgo, se recomiendan las siguientes acciones.
              La decisión final corresponde exclusivamente al analista.
            </p>

            <ul className="space-y-3 mb-6">
              {cfg.sugerencias.map((s, i) => (
                <li key={i} className="flex items-start gap-3 p-3 bg-surface-container-low rounded-lg">
                  <span className="material-symbols-outlined text-primary text-[18px] mt-0.5">check_circle</span>
                  <span className="text-body-md text-on-surface">{s}</span>
                </li>
              ))}
            </ul>

            <p className="text-label-sm font-label-sm text-on-surface-variant italic border-t border-outline-variant pt-4">
              ⚠️ Este sistema sugiere revisión, no determina fraude. Toda acción debe ser validada por el analista responsable.
            </p>
          </div>
        </div>
      )}

      {/* ══ Footer ══════════════════════════════════════════════════════ */}
      <footer className="bg-surface-dim w-full py-4 px-margin-desktop flex flex-col md:flex-row justify-between items-center gap-4 border-t border-outline-variant mt-20">
        <span className="font-title-md text-title-md text-on-surface">FraudIA Claims</span>
        <p className="font-body-md text-body-md text-on-surface-variant text-center">
          Este sistema sugiere revisión, no determina fraude. © 2026 FraudIA Claims.
        </p>
        <div className="flex gap-6">
          {['Ética AI', 'Soporte Técnico', 'Documentación'].map(link => (
            <a key={link} className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary transition-colors" href="#">
              {link}
            </a>
          ))}
        </div>
      </footer>
    </div>
  );
}
