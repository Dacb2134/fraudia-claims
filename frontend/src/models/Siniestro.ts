export interface Siniestro {
  id_siniestro: string
  id_asegurado: string
  ramo: string
  cobertura: string
  fecha_ocurrencia: string
  fecha_reporte: string
  monto_reclamado: number
  estado: string
  sucursal: string
  documentos_completos: boolean
  tiene_doc_inconsistente: boolean
  dias_reporte: number
  historial_siniestros: number
  proveedor: string | null
  score_riesgo: number
  nivel_riesgo: 'VERDE' | 'AMARILLO' | 'ROJO'
  alertas_activadas: string
}

export interface SiniestroDetalle {
  id_siniestro: string
  id_asegurado: string
  id_poliza: string
  ramo: string
  cobertura: string
  fecha_ocurrencia: string
  fecha_reporte: string
  monto_reclamado: number
  monto_estimado: number
  monto_pagado: number
  estado: string
  sucursal: string
  descripcion: string | null
  documentos_completos: boolean
  tiene_doc_inconsistente: boolean
  dias_reporte: number
  historial_siniestros: number
  poliza: {
    suma_asegurada: number
    prima: number
    fecha_inicio: string
    fecha_fin: string
  }
  proveedor: {
    id: string | null
    tipo: string | null
    en_lista_restrictiva: boolean
    pct_casos_observados: number
  }
  score: {
    valor: number
    nivel: 'VERDE' | 'AMARILLO' | 'ROJO'
    alertas: string
    reglas_criticas: string[]
    calculado_en: string | null
  }
}

export interface SiniestrosResponse {
  total: number
  page: number
  page_size: number
  pages: number
  data: Siniestro[]
}
