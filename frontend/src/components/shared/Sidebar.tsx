import { obtenerSesion } from '../../services/authService'

type Vista = 'dashboard' | 'casos' | 'agente' | 'reportes' | 'configuracion'

interface SidebarProps {
  vistaActiva: Vista | string
  onNav:       (v: string) => void
  onLogout:    () => void
}

const ALL_NAV_ITEMS = [
  { icon: 'dashboard',  label: 'Dashboard',       vista: 'dashboard',      roles: ['admin','analista','supervisor'] },
  { icon: 'assignment', label: 'Gestión de Casos', vista: 'casos',          roles: ['admin','analista']              },
  { icon: 'analytics',  label: 'Reportes',         vista: 'reportes',       roles: ['admin','supervisor']            },
  { icon: 'smart_toy',  label: 'Agente IA',        vista: 'agente',         roles: ['admin','analista','supervisor'] },
  { icon: 'settings',   label: 'Configuración',    vista: 'configuracion',  roles: ['admin','supervisor']            },
]

const ROL_LABEL: Record<string, string> = {
  admin:      'Administrador',
  analista:   'Analista de Riesgos',
  supervisor: 'Supervisor',
}

const ROL_COLOR: Record<string, string> = {
  admin:      '#ef4444',
  analista:   '#3b82f6',
  supervisor: '#f59e0b',
}

export default function Sidebar({ vistaActiva, onNav, onLogout }: SidebarProps) {
  const usuario = obtenerSesion()
  const rol     = usuario?.rol ?? 'analista'

  const navItems = ALL_NAV_ITEMS.filter(item => item.roles.includes(rol))

  const inicial = usuario?.nombre?.charAt(0).toUpperCase() ?? 'U'

  return (
    <aside className="hidden md:flex flex-col h-full py-6 px-4 gap-4 bg-surface-container w-64 flex-shrink-0 z-50 border-r border-surface-container-high"
      style={{ minHeight: '100vh' }}>

      {/* Logo */}
      <div className="px-2 mb-4">
        <div className="flex items-center gap-2 mb-1">
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #1a4aab 0%, #0069ff 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#fff', fontVariationSettings: "'FILL' 1" }}>security</span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-primary" style={{ fontSize: 18, fontWeight: 800 }}>FraudIA Claims</h1>
        </div>
        <p className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-widest opacity-70" style={{ fontSize: 10, paddingLeft: 40 }}>
          Detector de Riesgos v1.0
        </p>
      </div>

      {/* Usuario actual */}
      <div style={{
        background: 'rgba(0,83,207,0.08)',
        borderRadius: 12,
        padding: '10px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        marginBottom: 4,
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'linear-gradient(135deg, #0041a8, #0069ff)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 700, fontSize: 15, flexShrink: 0,
        }}>
          {inicial}
        </div>
        <div style={{ overflow: 'hidden' }}>
          <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#002662', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {usuario?.nombre ?? 'Usuario'}
          </p>
          <span style={{
            fontSize: 10, fontWeight: 600, color: ROL_COLOR[rol] ?? '#3b82f6',
            background: `${ROL_COLOR[rol] ?? '#3b82f6'}18`,
            padding: '1px 6px', borderRadius: 4,
            textTransform: 'uppercase', letterSpacing: '0.05em',
          }}>
            {ROL_LABEL[rol] ?? rol}
          </span>
        </div>
      </div>

      {/* Navegación filtrada por rol */}
      <nav className="flex flex-col gap-1" style={{ flex: 1 }}>
        {navItems.map(({ icon, label, vista }) => {
          const active = vistaActiva === vista
          return (
            <button key={label}
              onClick={() => onNav(vista)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors w-full text-left border-none cursor-pointer ${
                active
                  ? 'text-primary font-bold bg-surface-container-high'
                  : 'text-on-surface-variant bg-transparent hover:bg-surface-container-high'
              }`}
              style={active ? { background: 'rgba(0,83,207,0.1)', color: '#002662' } : {}}>
              <span
                className="material-symbols-outlined"
                style={active ? { fontVariationSettings: "'FILL' 1", color: '#002662' } : { fontSize: 20 }}>
                {icon}
              </span>
              <span className="font-title-md text-title-md" style={{ fontSize: 14 }}>{label}</span>
              {active && <span style={{ marginLeft: 'auto', width: 4, height: 4, borderRadius: '50%', background: '#002662' }} />}
            </button>
          )
        })}

        <div style={{ borderTop: '1px solid rgba(0,0,0,0.08)', marginTop: 8, paddingTop: 8 }}>
          <button
            onClick={onLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl transition-colors w-full text-left border-none cursor-pointer bg-transparent"
            style={{ color: '#ba1a1a' }}>
            <span className="material-symbols-outlined">logout</span>
            <span className="font-title-md text-title-md" style={{ fontSize: 14 }}>Cerrar Sesión</span>
          </button>
        </div>
      </nav>

      {/* Status IA */}
      <div className="p-4 rounded-xl text-white" style={{ background: 'linear-gradient(135deg, #0041a8, #0069ff)' }}>
        <div className="flex items-center gap-2 mb-1">
          <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1", fontSize: 16 }}>auto_awesome</span>
          <span style={{ fontSize: 11, fontFamily: 'JetBrains Mono', letterSpacing: '0.05em' }}>AI STATUS</span>
          <span style={{ marginLeft: 'auto', width: 6, height: 6, borderRadius: '50%', background: '#4ade80', boxShadow: '0 0 6px #4ade80' }} />
        </div>
        <p style={{ fontSize: 12, lineHeight: 1.4, margin: 0, opacity: 0.9 }}>
          Gemini activo. Analizando siniestros en tiempo real.
        </p>
      </div>
    </aside>
  )
}
