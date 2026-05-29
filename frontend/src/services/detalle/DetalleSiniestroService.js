// URL base del backend (Docker expone el API en puerto 8000)
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Obtiene el detalle completo de un siniestro:
 * score, alertas, proveedor, póliza, documentos.
 * Endpoint: GET /api/v1/siniestros/{id}
 */
export async function getSiniestroDetalle(id) {
  const res = await fetch(`${API_BASE}/api/v1/siniestros/${id}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${res.status}: no se encontró el siniestro`);
  }
  return res.json();
}

/**
 * Obtiene la red de siniestros relacionados con un proveedor.
 * Endpoint: GET /api/v1/red/proveedor/{idProveedor}
 */
export async function getRedProveedor(idProveedor) {
  const res = await fetch(`${API_BASE}/api/v1/red/proveedor/${encodeURIComponent(idProveedor)}`);
  if (!res.ok) throw new Error(`Error ${res.status} al obtener red del proveedor`);
  return res.json();
}

/**
 * Pide al agente Gemini una explicación del caso en lenguaje natural.
 * Endpoint: POST /api/v1/chat
 * Respuesta: { pregunta, respuesta, modelo }
 */
export async function getExplicacionIA(idSiniestro) {
  const res = await fetch(`${API_BASE}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pregunta: `En 2-3 oraciones, explica por qué el siniestro ${idSiniestro} presenta señales que requieren revisión. Usa lenguaje como "presenta indicios de" o "requiere verificación". No acuses directamente.`,
      contexto_siniestro: idSiniestro,
    }),
  });
  if (!res.ok) throw new Error(`Error ${res.status} al consultar al agente IA`);
  return res.json(); // { pregunta, respuesta, modelo }
}
