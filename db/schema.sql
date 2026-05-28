-- ============================================================
--  FraudIA — Schema MySQL
--  hackIAthon 2026 · Reto Aseguradora del Sur
--  Base de datos: reasonscore_db (creada por Docker)
-- ============================================================

USE reasonscore_db;

CREATE TABLE IF NOT EXISTS usuarios (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre         VARCHAR(100)  NOT NULL,
    email          VARCHAR(150)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255)  NOT NULL,
    rol            ENUM('analista','antifraude','jefatura','admin') NOT NULL DEFAULT 'analista',
    activo         TINYINT(1)    NOT NULL DEFAULT 1,
    creado_en      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asegurados (
    id_asegurado       VARCHAR(20)  PRIMARY KEY,
    segmento           ENUM('Personal','Empresarial','Preferencial') NOT NULL DEFAULT 'Personal',
    antiguedad_meses   SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    ciudad             VARCHAR(80)  NOT NULL DEFAULT 'Quito',
    num_polizas        TINYINT UNSIGNED NOT NULL DEFAULT 1,
    reclamos_12m       TINYINT UNSIGNED NOT NULL DEFAULT 0,
    mora_actual        TINYINT(1)   NOT NULL DEFAULT 0,
    score_cliente      TINYINT UNSIGNED NOT NULL DEFAULT 80,
    creado_en          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS polizas (
    id_poliza      VARCHAR(20)  PRIMARY KEY,
    id_asegurado   VARCHAR(20)  NOT NULL,
    ramo           ENUM('Vehículos','Salud','Hogar','Vida','Generales') NOT NULL,
    fecha_inicio   DATE         NOT NULL DEFAULT '2022-01-01',
    fecha_fin      DATE         NOT NULL DEFAULT '2026-12-31',
    prima          DECIMAL(10,2) NOT NULL DEFAULT 500.00,
    suma_asegurada DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    deducible      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    canal_venta    ENUM('Agente','Broker','Digital','Bancaseguros') NOT NULL DEFAULT 'Agente',
    ciudad         VARCHAR(80)  NOT NULL DEFAULT 'Quito',
    estado_poliza  ENUM('Vigente','Vencida','Cancelada') NOT NULL DEFAULT 'Vigente',
    creado_en      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_poliza_asegurado FOREIGN KEY (id_asegurado)
        REFERENCES asegurados(id_asegurado) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS vehiculos (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_poliza  VARCHAR(20)  NOT NULL UNIQUE,
    placa      VARCHAR(10)  NOT NULL,
    chasis     VARCHAR(20)  NOT NULL,
    motor      VARCHAR(20)  NOT NULL,
    marca      VARCHAR(50)  NOT NULL,
    modelo     VARCHAR(50)  NOT NULL,
    anio       YEAR         NOT NULL,
    creado_en  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_vehiculo_poliza FOREIGN KEY (id_poliza)
        REFERENCES polizas(id_poliza) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS proveedores (
    id_proveedor                VARCHAR(20)  PRIMARY KEY,
    tipo                        ENUM('Taller','Clínica','Perito','Hospital','Centro Médico','Taller Multimarca') NOT NULL DEFAULT 'Taller',
    ciudad                      VARCHAR(80)  NOT NULL DEFAULT 'Quito',
    reclamos_asociados          SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    monto_promedio_reclamado    DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    pct_casos_observados        DECIMAL(5,3)  NOT NULL DEFAULT 0.000,
    antiguedad_anios            TINYINT UNSIGNED NOT NULL DEFAULT 1,
    en_lista_restrictiva        TINYINT(1)   NOT NULL DEFAULT 0,
    creado_en                   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS siniestros (
    id_siniestro                    VARCHAR(20)  PRIMARY KEY,
    id_poliza                       VARCHAR(20)  NOT NULL,
    id_asegurado                    VARCHAR(20)  NOT NULL,
    id_proveedor_beneficiario       VARCHAR(20),
    ramo                            ENUM('Vehículos','Salud','Hogar','Vida','Generales') NOT NULL,
    cobertura                       VARCHAR(60)  NOT NULL,
    fecha_ocurrencia                DATE         NOT NULL,
    fecha_reporte                   DATE         NOT NULL,
    monto_reclamado                 DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    monto_estimado                  DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    monto_pagado                    DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    estado                          ENUM('Reserva','Pago Total','Pago Parcial','Anticipo',
                                        'Negativa','Cierre Sin Consecuencia','Liquidado') NOT NULL,
    sucursal                        VARCHAR(60)  NOT NULL,
    descripcion                     TEXT,
    documentos_completos            TINYINT(1)   NOT NULL DEFAULT 1,
    dias_desde_inicio_poliza        SMALLINT     NOT NULL DEFAULT 0,
    dias_desde_fin_poliza           SMALLINT     NOT NULL DEFAULT 0,
    dias_entre_ocurrencia_reporte   SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    historial_siniestros_asegurado  TINYINT UNSIGNED NOT NULL DEFAULT 0,
    etiqueta_fraude_simulada        TINYINT(1)   NOT NULL DEFAULT 0,
    tiene_doc_inconsistente         TINYINT(1)   NOT NULL DEFAULT 0,
    creado_en                       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en                  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_sin_poliza    FOREIGN KEY (id_poliza)    REFERENCES polizas(id_poliza)       ON DELETE RESTRICT,
    CONSTRAINT fk_sin_asegurado FOREIGN KEY (id_asegurado) REFERENCES asegurados(id_asegurado) ON DELETE RESTRICT,
    CONSTRAINT fk_sin_proveedor FOREIGN KEY (id_proveedor_beneficiario) REFERENCES proveedores(id_proveedor) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS documentos (
    id_documento             VARCHAR(20)  PRIMARY KEY,
    id_siniestro             VARCHAR(20)  NOT NULL,
    tipo_documento           ENUM('Denuncia Policial','Factura Reparación','Informe Perito',
                                  'Fotos Daño','Cédula Asegurado','Parte Policial') NOT NULL,
    entregado                TINYINT(1)   NOT NULL DEFAULT 1,
    legible                  TINYINT(1)   NOT NULL DEFAULT 1,
    fecha_emision            DATE,
    inconsistencia_detectada TINYINT(1)   NOT NULL DEFAULT 0,
    observacion              VARCHAR(255),
    creado_en                DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_doc_siniestro FOREIGN KEY (id_siniestro)
        REFERENCES siniestros(id_siniestro) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scores_riesgo (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_siniestro            VARCHAR(20)  NOT NULL UNIQUE,
    score_raw               SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    score_normalizado       TINYINT UNSIGNED  NOT NULL DEFAULT 0,
    nivel_riesgo            ENUM('VERDE','AMARILLO','ROJO') NOT NULL DEFAULT 'VERDE',
    alertas_activadas       TEXT,
    reglas_criticas         JSON,
    tiene_doc_inconsistente TINYINT(1)   NOT NULL DEFAULT 0,
    similitud_max_narrativa DECIMAL(5,3) NOT NULL DEFAULT 0.000,
    id_siniestro_similar    VARCHAR(20),
    calculado_en            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version_modelo          VARCHAR(20)  NOT NULL DEFAULT 'v1.0',
    CONSTRAINT fk_score_siniestro FOREIGN KEY (id_siniestro)
        REFERENCES siniestros(id_siniestro) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alertas (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_siniestro  VARCHAR(20)  NOT NULL,
    codigo_regla  VARCHAR(10),
    tipo_alerta   VARCHAR(80)  NOT NULL,
    puntos        TINYINT UNSIGNED NOT NULL DEFAULT 0,
    descripcion   VARCHAR(512) NOT NULL,
    clasificacion ENUM('VERDE','AMARILLO','ROJO') NOT NULL DEFAULT 'AMARILLO',
    creado_en     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alerta_siniestro FOREIGN KEY (id_siniestro)
        REFERENCES siniestros(id_siniestro) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS log_consultas_agente (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_usuario    INT UNSIGNED,
    pregunta      TEXT         NOT NULL,
    respuesta     TEXT         NOT NULL,
    tokens_usados SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    latencia_ms   SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    creado_en     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_log_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE INDEX idx_score_nivel   ON scores_riesgo(nivel_riesgo);
CREATE INDEX idx_score_valor   ON scores_riesgo(score_normalizado DESC);
CREATE INDEX idx_sin_poliza    ON siniestros(id_poliza);
CREATE INDEX idx_sin_asegurado ON siniestros(id_asegurado);
CREATE INDEX idx_sin_proveedor ON siniestros(id_proveedor_beneficiario);
CREATE INDEX idx_sin_fecha     ON siniestros(fecha_ocurrencia);
CREATE INDEX idx_sin_fraude    ON siniestros(etiqueta_fraude_simulada);
CREATE INDEX idx_prov_lista    ON proveedores(en_lista_restrictiva);
CREATE INDEX idx_alerta_sin    ON alertas(id_siniestro);
CREATE INDEX idx_alerta_clasif ON alertas(clasificacion);

CREATE OR REPLACE VIEW v_bandeja_casos AS
SELECT
    s.id_siniestro,
    s.ramo,
    s.cobertura,
    s.fecha_ocurrencia,
    s.fecha_reporte,
    s.monto_reclamado,
    s.estado,
    s.sucursal,
    s.id_asegurado,
    p.ciudad            AS ciudad_poliza,
    pr.tipo             AS tipo_proveedor,
    pr.en_lista_restrictiva,
    sc.score_normalizado,
    sc.nivel_riesgo,
    sc.alertas_activadas,
    sc.calculado_en     AS score_calculado_en
FROM siniestros s
JOIN  polizas p          ON s.id_poliza    = p.id_poliza
LEFT JOIN proveedores pr ON s.id_proveedor_beneficiario = pr.id_proveedor
LEFT JOIN scores_riesgo sc ON s.id_siniestro = sc.id_siniestro
ORDER BY sc.score_normalizado DESC;

INSERT IGNORE INTO usuarios (nombre, email, password_hash, rol)
VALUES ('Admin FraudIA', 'admin@fraudia.com',
        '$2b$12$placeholder_cambiar_en_produccion', 'admin');
