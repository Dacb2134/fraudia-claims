# GUÍA 2 — Implementación de Mejoras UX · FraudIA Claims
## Documento para Claude Code · Leer completo antes de editar

---

## CONTEXTO

- Stack: React 19 + Vite + TypeScript + Tailwind + CSS custom
- Rutas: `frontend/src/views/{Login,Dashboard,AgenteIA,GestionCasos,Reportes,Detalle,Configuracion}/`
- Sidebar compartido: `components/shared/Sidebar.tsx`
- Auth: `import { obtenerSesion } from '../../services/authService'`
- API: `import { apiFetch, API_URL } from '../../services/api'`

## REGLA TRANSVERSAL (aplica a TODO)
Respetar los 10 heurísticos de Nielsen, en especial:
- **#8 Minimalismo:** no duplicar controles ni mostrar ruido visual
- **#4 Consistencia:** mismo header/sidebar/footer en todas las vistas
- **#1 Visibilidad de estado:** loaders y estados activos siempre visibles

Ya se aplicaron las fases previas (login campo oscuro, chat centrado). NO repetir esas.

---

## FASE A — Reportes: eliminar duplicación de Exportar (Nielsen #8)

**Archivo:** `views/Reportes/Reportes.tsx`

**PROBLEMA:** Los botones de exportar aparecen DOS veces: en el header (arriba) y en la sección azul (abajo). Esto es redundante y viola el principio de minimalismo.

**DECISIÓN:** Mantener SOLO la sección de abajo (más descriptiva, con contexto de "para auditoría"). Eliminar los del header y reemplazar por un único botón de menú o nada.

**Paso 1** — En el header, buscar el bloque que mapea los 3 enlaces de exportar:
```tsx
<div className="flex items-center gap-2">
  {([
    { nivel: 'ROJO',     label: '🔴 Alto Riesgo',  color: '#ba1a1a' },
    { nivel: 'AMARILLO', label: '🟡 Medio Riesgo', color: '#f97316' },
    { nivel: 'todos',    label: '📋 Todos',         color: '#002662' },
  ] as const).map(({ nivel, label, color }) => (
    <a key={nivel} href={...}>...</a>
  ))}
</div>
```
Reemplazar TODO ese `<div>` por un solo botón que hace scroll a la sección de exportar:
```tsx
<button
  onClick={() => document.getElementById('export-section')?.scrollIntoView({ behavior: 'smooth' })}
  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border border-primary text-primary bg-white hover:bg-primary hover:text-white transition-colors cursor-pointer">
  <span className="material-symbols-outlined text-[18px]">download</span>
  Exportar Reporte
</button>
```

**Paso 2** — En la sección de exportar de abajo, agregar el `id`:
```tsx
<section id="export-section" className="...">
```

---

## FASE B — Reportes: arreglar contraste de la sección Exportar (Nielsen #4, accesibilidad)

**Archivo:** `views/Reportes/Reportes.tsx`

**PROBLEMA:** La sección usa `bg-primary-container` con `text-white`, pero `primary-container` en el theme es un azul claro, dejando texto blanco sobre fondo claro (ilegible). En la captura el título "Exportar reporte para auditoría" se ve cortado/desvanecido.

**FIX** — Buscar:
```tsx
<section id="export-section" className="bg-primary-container rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
  <div>
    <h3 className="font-medium text-white mb-1">Exportar reporte para auditoría</h3>
    <p className="text-sm text-primary-fixed-dim">Descarga un CSV...</p>
  </div>
```
Reemplazar el `className` de la section y los textos por:
```tsx
<section id="export-section" className="rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4"
  style={{ background: 'linear-gradient(135deg, #002662 0%, #003a8f 100%)' }}>
  <div>
    <h3 className="font-medium mb-1" style={{ color: '#fff' }}>Exportar reporte para auditoría</h3>
    <p className="text-sm" style={{ color: '#b9c9ed' }}>Descarga un CSV con todos los casos del nivel seleccionado, listo para revisión externa.</p>
  </div>
```

---

## FASE C — Reportes: tabla Top 10 vacía (Nielsen #1 visibilidad)

**Archivo:** `views/Reportes/Reportes.tsx`

**PROBLEMA:** En las capturas la tabla "Top 10 Casos Críticos" aparece sin filas. Con el dataset actual (0 casos ROJO, 21 AMARILLO) el endpoint `/api/v1/reporte/ejecutivo` puede estar devolviendo `top_10_casos_criticos` vacío porque filtra solo ROJO.

**FIX FRONTEND** — Agregar un estado vacío visible. Buscar el `<tbody>` de la tabla Top 10 y envolver el map con un fallback:
```tsx
<tbody className="divide-y divide-outline-variant/15">
  {data.top_10_casos_criticos.length === 0 ? (
    <tr>
      <td colSpan={6} className="px-4 py-12 text-center text-on-surface-variant">
        <span className="material-symbols-outlined text-[40px] block mb-2 opacity-40">inbox</span>
        No hay casos críticos en el nivel actual.
        <br/>
        <span className="text-xs">Los 21 casos de riesgo medio se pueden revisar en Gestión de Casos.</span>
      </td>
    </tr>
  ) : (
    data.top_10_casos_criticos.map((caso, i) => (
      // ... el map existente sin cambios
    ))
  )}
</tbody>
```

**NOTA PARA EL BACKEND (separado):** El endpoint `/api/v1/reporte/ejecutivo` debería incluir también casos AMARILLO cuando no hay ROJO, ordenados por score. Si el equipo backend puede, que cambie el filtro de `nivel_riesgo = 'ROJO'` a `nivel_riesgo IN ('ROJO','AMARILLO') ORDER BY score DESC LIMIT 10`.

---

## FASE D — Reportes: tarjetas de ramo "0% riesgo" poco informativas (Nielsen #2)

**Archivo:** `views/Reportes/Reportes.tsx`

**PROBLEMA:** Todos los ramos muestran "0% riesgo" en verde, lo que se ve vacío. Aunque es correcto (no hay ROJO), conviene mostrar también el % de AMARILLO para dar señal de actividad.

**FIX** — En el bloque `riesgo_por_ramo`, cambiar el texto inferior:
```tsx
<p className="text-[11px] text-on-surface-variant mt-0.5">{r.total} total · {r.rojos} rojos</p>
```
Por:
```tsx
<p className="text-[11px] text-on-surface-variant mt-0.5">
  {r.total} siniestros · {r.rojos} alto riesgo
  {r.rojos === 0 && <span className="text-green-600"> · sin alertas críticas</span>}
</p>
```

---

## FASE E — Agente IA: verificar alineación final del input (Nielsen #4)

**Archivo:** `views/AgenteIA/AgenteIA.css`

**PROBLEMA REPORTADO:** "la barra de texto no está bien ajustada a la pantalla".

El CSS ya tiene `.input-wrap { max-width: 820px; margin: 0 auto }` y `.chat-row { max-width: 760px; margin: 0 auto }`. El desfase es que **820 ≠ 760**: el input es 60px más ancho que los mensajes, creando un escalón visual.

**FIX** — Igualar los anchos. Buscar:
```css
.input-wrap {
  max-width: 820px;
```
Cambiar a:
```css
.input-wrap {
  max-width: 760px;
```

Así el input queda exactamente alineado con la columna de mensajes.

---

## FASE F — Dashboard y GestionCasos: verificar campana funcional (Nielsen #1)

**Archivos:** `views/Dashboard/Dashboard.tsx`, `views/GestionCasos/GestionCasos.tsx`

Verificar que las campanas de notificaciones abren su dropdown (se implementó en fases previas). Si NO está, aplicar el patrón:
- Estado `const [showNotif, setShowNotif] = useState(false)`
- Botón con `onClick={() => setShowNotif(v => !v)}`
- Dropdown con casos ROJO; si no hay ROJO, mostrar casos AMARILLO con mensaje "No hay casos críticos, mostrando riesgo medio".

**IMPORTANTE:** Como el dataset tiene 0 ROJO, el dropdown de notificaciones se vería vacío. Cambiar el filtro a:
```tsx
{(() => {
  const criticos = casos.filter(c => c.nivel_riesgo === 'ROJO')
  const mostrar = criticos.length > 0 ? criticos : casos.filter(c => c.nivel_riesgo === 'AMARILLO')
  return mostrar.slice(0, 5).map(c => (/* ... item ... */))
})()}
```

---

## FASE G — Animaciones suaves (motion principles)

**Aplicar en todos los dropdowns nuevos (notificaciones, ayuda, modales):**

Agregar al CSS global o inline una animación de entrada:
```css
@keyframes dropdownIn {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}
```
Y en cada dropdown agregar:
```tsx
style={{ animation: 'dropdownIn 0.18s ease-out', /* resto de estilos */ }}
```

**Regla de motion:** todas las transiciones de hover/focus deben durar 150-200ms. Verificar que los botones tengan `transition: ... 0.15s`.

**Accesibilidad:** agregar al CSS global:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## FASE H — Consistencia de footer (Nielsen #4)

Revisar que TODOS los footers digan `© 2026` (no 2024) y tengan los mismos links navegables (no `href="#"`).

Archivos a revisar: `Dashboard.tsx`, `Detalle.tsx`, `GestionCasos.tsx`, `Reportes.tsx`, `Configuracion.tsx`.

---

## CHECKLIST FINAL

- [ ] Reportes: exportar aparece UNA sola vez (header lleva a la sección de abajo)
- [ ] Reportes: sección exportar tiene fondo azul oscuro con texto blanco legible
- [ ] Reportes: tabla Top 10 muestra mensaje de estado vacío cuando no hay casos
- [ ] Reportes: tarjetas de ramo muestran "sin alertas críticas" cuando rojos = 0
- [ ] AgenteIA: input alineado exactamente con el ancho de los mensajes (760px ambos)
- [ ] Dashboard/GestionCasos: campana muestra casos AMARILLO si no hay ROJO
- [ ] Todos los dropdowns tienen animación de entrada suave (0.18s)
- [ ] Existe regla prefers-reduced-motion en CSS global
- [ ] Todos los footers dicen © 2026
- [ ] Compila sin errores de TypeScript (npm run dev)

---

## ORDEN DE EJECUCIÓN

```
1. Fase A — quitar exportar duplicado (5 min)
2. Fase B — contraste sección exportar (3 min)
3. Fase C — estado vacío tabla Top 10 (5 min)
4. Fase E — alinear input chat a 760px (1 min)
5. Fase F — campana con fallback AMARILLO (5 min)
6. Fase D — texto ramos (3 min)
7. Fase G — animaciones dropdowns + reduced-motion (8 min)
8. Fase H — consistencia footers (5 min)
```
