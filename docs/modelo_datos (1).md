# Modelo de Datos — FraudIA

## Diagrama de Relaciones

```
asegurados ──────< polizas >────── (ramo: Vehiculos) ──< vehiculos
                      │
                      └──────< siniestros >──────── proveedores
                                    │
                              ┌─────┴──────┐
                              ▼            ▼
                          documentos   scores_riesgo
                                            │
                                            ▼
                                         alertas
```

## Tablas

### asegurados
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_asegurado | VARCHAR(20) PK | Identificador anónimo (ASE-XXXX) |
| segmento | ENUM | Personal / Empresarial / Preferencial |
| antiguedad_meses | SMALLINT | Meses como cliente |
| ciudad | VARCHAR(80) | Ciudad de residencia |
| num_polizas | TINYINT | Número de pólizas activas |
| reclamos_12m | TINYINT | Reclamos últimos 12 meses |
| mora_actual | TINYINT(1) | 0=No / 1=Sí |
| score_cliente | TINYINT | Score interno 0-100 |

### polizas
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_poliza | VARCHAR(20) PK | Identificador (POL-XXXXX) |
| id_asegurado | VARCHAR(20) FK | Referencia a asegurados |
| ramo | VARCHAR(20) | Vehiculos / Salud / Hogar / Vida / Generales |
| fecha_inicio | DATE | Inicio de vigencia |
| fecha_fin | DATE | Fin de vigencia |
| prima | DECIMAL(10,2) | Prima pagada |
| suma_asegurada | DECIMAL(12,2) | Valor máximo de cobertura |
| deducible | DECIMAL(10,2) | Deducible aplicable |
| canal_venta | ENUM | Agente / Broker / Digital / Bancaseguros |
| estado_poliza | ENUM | Vigente / Vencida / Cancelada |

### siniestros (tabla central)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_siniestro | VARCHAR(20) PK | Identificador (SIN-XXXXX) |
| id_poliza | VARCHAR(20) FK | Referencia a polizas |
| id_asegurado | VARCHAR(20) FK | Referencia a asegurados |
| id_proveedor_beneficiario | VARCHAR(20) FK | Referencia a proveedores |
| ramo | VARCHAR(20) | Ramo del siniestro |
| cobertura | VARCHAR(60) | Tipo de cobertura activada |
| fecha_ocurrencia | DATE | Fecha del evento |
| fecha_reporte | DATE | Fecha de notificación |
| monto_reclamado | DECIMAL(12,2) | Valor solicitado |
| monto_estimado | DECIMAL(12,2) | Valor estimado aseguradora |
| monto_pagado | DECIMAL(12,2) | Valor pagado |
| estado | ENUM | Reserva / Pago Total / etc. |
| descripcion | TEXT | Narrativa libre del reclamo |
| etiqueta_fraude_simulada | TINYINT(1) | 0=Normal / 1=Fraude (para ML) |

### scores_riesgo
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_siniestro | VARCHAR(20) FK UNIQUE | Un score por siniestro |
| score_normalizado | TINYINT | Score 0-100 |
| nivel_riesgo | ENUM | VERDE / AMARILLO / ROJO |
| alertas_activadas | TEXT | Descripción de alertas (pipe-separated) |
| reglas_criticas | JSON | Lista de reglas RF activadas |
| version_modelo | VARCHAR(20) | Versión del motor |

### proveedores
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_proveedor | VARCHAR(20) PK | Identificador (PROV-XXX) |
| tipo | VARCHAR(30) | Taller / Clínica / Perito / etc. |
| reclamos_asociados | SMALLINT | Total de reclamos |
| pct_casos_observados | DECIMAL(5,3) | Porcentaje de casos sospechosos |
| en_lista_restrictiva | TINYINT(1) | Flag lista negra |

## Vista Principal

### v_bandeja_casos
Vista que une siniestros + pólizas + proveedores + scores, ordenada por score descendente. Es la fuente principal del dashboard.

```sql
SELECT s.*, sc.score_normalizado, sc.nivel_riesgo, sc.alertas_activadas
FROM siniestros s
JOIN polizas p ON s.id_poliza = p.id_poliza
LEFT JOIN proveedores pr ON s.id_proveedor_beneficiario = pr.id_proveedor
LEFT JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
ORDER BY sc.score_normalizado DESC;
```
