export interface Stats {
  resumen: {
    total_siniestros: number
    score_promedio: number
    monto_total_riesgo: number
  }
  semaforo: {
    verde:    { total: number; monto: number }
    amarillo: { total: number; monto: number }
    rojo:     { total: number; monto: number }
  }
  por_ramo: { ramo: string; total: number }[]
  top_proveedores: { proveedor: string; total_alertas: number; alertas_rojas: number }[]
  top_asegurados: { id_asegurado: string; total_siniestros: number; score_max: number; monto_total: number }[]
  por_sucursal: { sucursal: string; total: number; rojos: number }[]
}
