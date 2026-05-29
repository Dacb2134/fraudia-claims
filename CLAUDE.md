# FraudIA Claims — Guía para Claude Code

## Contexto
Detector de posibles fraudes en siniestros para hackIAthon 2026.
Frontend: React 19 + Vite + TypeScript + Tailwind + CSS custom.

## Principios de diseño OBLIGATORIOS

### Heurísticos de Nielsen (aplicar en cada cambio de UI)
1. Visibilidad del estado del sistema — loaders, toasts, estados activos visibles
2. Correspondencia con el mundo real — lenguaje de seguros, no técnico
3. Control y libertad del usuario — siempre poder cancelar/volver
4. Consistencia y estándares — mismo header, sidebar y footer en TODAS las vistas
5. Prevención de errores — confirmaciones antes de acciones críticas
6. Reconocer en vez de recordar — acciones visibles, no ocultas
7. Flexibilidad y eficiencia — atajos para usuarios avanzados (Enter para enviar)
8. Diseño estético y minimalista — NO duplicar controles, NO ruido visual
9. Ayudar a reconocer y recuperarse de errores — mensajes claros y accionables
10. Ayuda y documentación — tooltips, panel de ayuda accesible

### Reglas de layout
- Todo contenido principal centrado con max-width coherente
- La barra de input del chat debe alinearse al ancho del área de mensajes
- Nunca duplicar un control (ej: botones de exportar arriba Y abajo)
- Header sticky en todas las vistas con scroll
- Espaciado consistente: usar la escala de Tailwind (gap-4, p-6, etc.)

### Reglas de color (paleta FraudIA)
- Primario: #002662 (azul marino)
- Rojo riesgo: #ba1a1a
- Amarillo riesgo: #f97316 (naranja-ámbar)
- Verde riesgo: #16a34a
- Nunca texto blanco sobre fondo claro ni texto oscuro sobre fondo oscuro

### Reglas de motion
- Transiciones de 150-200ms en hover/focus
- Loaders con spin suave, nunca parpadeos bruscos
- Animaciones de entrada sutiles (fade/slide de máx 300ms)
- Respetar prefers-reduced-motion

## Qué NO hacer
- No inventar endpoints ni cambiar la API
- No romper la lógica de roles del Sidebar
- No usar localStorage en exceso (solo el historial del chat ya existente)
