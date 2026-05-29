// Sidebar compartido — mismo diseño en todas las vistas
type Vista = 'dashboard' | 'casos' | 'agente' | 'reportes' | 'configuracion'

interface SidebarProps {
  vistaActiva: Vista | string
  onNav:       (v: string) => void
  onLogout:    () => void
}

const NAV_ITEMS = [
  { icon: 'dashboard',  label: 'Dashboard',        vista: 'dashboard'     },
  { icon: 'assignment', label: 'Gestión de Casos',  vista: 'casos'         },
  { icon: 'analytics',  label: 'Reportes',          vista: 'reportes'      },
  { icon: 'smart_toy',  label: 'Agente IA',         vista: 'agente'        },
  { icon: 'settings',   label: 'Configuración',     vista: 'configuracion' },
]

export default function Sidebar({ vistaActiva, onNav, onLogout }: SidebarProps) {
  return (
    <aside className="hidden md:flex flex-col h-full py-8 px-4 gap-4 bg-surface-container w-64 flex-shrink-0 z-50">
      <div className="px-2 mb-8">
        <h1 className="font-headline-lg text-headline-lg text-primary">FraudIA Claims</h1>
        <p className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-widest opacity-70">
          Intelligent Detector
        </p>
      </div>

      <nav className="flex flex-col gap-2">
        {NAV_ITEMS.map(({ icon, label, vista }) => {
          const active = vistaActiva === vista
          return (
            <button key={label}
              onClick={() => onNav(vista)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors w-full text-left border-none cursor-pointer ${
                active
                  ? 'text-primary font-bold bg-surface-container-high opacity-80'
                  : 'text-on-surface-variant bg-transparent hover:bg-surface-container-high'
              }`}>
              <span
                className="material-symbols-outlined"
                style={active ? { fontVariationSettings: "'FILL' 1" } : {}}>
                {icon}
              </span>
              <span className="font-title-md text-title-md">{label}</span>
            </button>
          )
        })}

        <button
          onClick={onLogout}
          className="flex items-center gap-3 px-4 py-3 rounded-xl transition-colors w-full text-left border-none cursor-pointer text-error hover:bg-error-container mt-2 bg-transparent">
          <span className="material-symbols-outlined">logout</span>
          <span className="font-title-md text-title-md">Cerrar Sesión</span>
        </button>
      </nav>

      <div className="mt-auto p-4 bg-primary-container rounded-xl text-white">
        <div className="flex items-center gap-2 mb-2">
          <span
            className="material-symbols-outlined text-[20px]"
            style={{ fontVariationSettings: "'FILL' 1" }}>
            auto_awesome
          </span>
          <span className="font-label-sm text-label-sm">AI STATUS</span>
        </div>
        <p className="font-body-md text-[13px] leading-tight">
          Motor Gemini activo. Analizando siniestros en tiempo real.
        </p>
      </div>
    </aside>
  )
}
