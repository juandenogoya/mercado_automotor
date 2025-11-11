-- ==============================================================================
-- TABLAS PARA ESTADÍSTICAS AGREGADAS MENSUALES DE DNRPA
-- ==============================================================================
-- Estas tablas almacenan datos agregados (totales mensuales por provincia)
-- a diferencia de las tablas datos_gob_* que tienen datos detallados por trámite.
--
-- Ventajas:
-- - Consultas muy rápidas (pocos registros)
-- - Datos históricos desde 2007
-- - Incluye Maquinarias (no disponible en datos detallados)
-- ==============================================================================

-- Tabla: Estadísticas agregadas de Inscripciones Iniciales
CREATE TABLE IF NOT EXISTS estadisticas_inscripciones (
    id SERIAL PRIMARY KEY,
    tipo_vehiculo VARCHAR(50) NOT NULL,  -- 'Motovehículos' o 'Maquinarias'
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes >= 1 AND mes <= 12),
    provincia VARCHAR(100) NOT NULL,
    letra_provincia VARCHAR(1),
    provincia_id VARCHAR(2),
    cantidad INTEGER NOT NULL DEFAULT 0,

    -- Metadatos
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archivo_origen VARCHAR(255),

    -- Constraints
    CONSTRAINT uk_estadisticas_inscripciones UNIQUE (tipo_vehiculo, anio, mes, provincia),
    CONSTRAINT check_anio_inscripciones CHECK (anio >= 2007 AND anio <= 2100)
);

-- Tabla: Estadísticas agregadas de Transferencias
CREATE TABLE IF NOT EXISTS estadisticas_transferencias (
    id SERIAL PRIMARY KEY,
    tipo_vehiculo VARCHAR(50) NOT NULL,  -- 'Motovehículos' o 'Maquinarias'
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes >= 1 AND mes <= 12),
    provincia VARCHAR(100) NOT NULL,
    letra_provincia VARCHAR(1),
    provincia_id VARCHAR(2),
    cantidad INTEGER NOT NULL DEFAULT 0,

    -- Metadatos
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archivo_origen VARCHAR(255),

    -- Constraints
    CONSTRAINT uk_estadisticas_transferencias UNIQUE (tipo_vehiculo, anio, mes, provincia),
    CONSTRAINT check_anio_transferencias CHECK (anio >= 2007 AND anio <= 2100)
);

-- ==============================================================================
-- ÍNDICES PARA OPTIMIZAR CONSULTAS
-- ==============================================================================

-- Índices para inscripciones
CREATE INDEX IF NOT EXISTS idx_est_inscripciones_anio_mes
    ON estadisticas_inscripciones(anio, mes);

CREATE INDEX IF NOT EXISTS idx_est_inscripciones_provincia
    ON estadisticas_inscripciones(provincia);

CREATE INDEX IF NOT EXISTS idx_est_inscripciones_tipo
    ON estadisticas_inscripciones(tipo_vehiculo);

CREATE INDEX IF NOT EXISTS idx_est_inscripciones_anio_tipo
    ON estadisticas_inscripciones(anio, tipo_vehiculo);

-- Índices para transferencias
CREATE INDEX IF NOT EXISTS idx_est_transferencias_anio_mes
    ON estadisticas_transferencias(anio, mes);

CREATE INDEX IF NOT EXISTS idx_est_transferencias_provincia
    ON estadisticas_transferencias(provincia);

CREATE INDEX IF NOT EXISTS idx_est_transferencias_tipo
    ON estadisticas_transferencias(tipo_vehiculo);

CREATE INDEX IF NOT EXISTS idx_est_transferencias_anio_tipo
    ON estadisticas_transferencias(anio, tipo_vehiculo);

-- ==============================================================================
-- COMENTARIOS EN LAS TABLAS
-- ==============================================================================

COMMENT ON TABLE estadisticas_inscripciones IS
'Estadísticas agregadas mensuales de inscripciones iniciales por provincia.
Datos desde 2007 para motovehículos y desde 2013 para maquinarias.';

COMMENT ON TABLE estadisticas_transferencias IS
'Estadísticas agregadas mensuales de transferencias por provincia.
Datos desde 2007 para motovehículos y desde 2013 para maquinarias.';

COMMENT ON COLUMN estadisticas_inscripciones.tipo_vehiculo IS
'Tipo de vehículo: Motovehículos (autos/motos) o Maquinarias (agrícolas/industriales)';

COMMENT ON COLUMN estadisticas_inscripciones.cantidad IS
'Total de inscripciones iniciales en ese mes/año/provincia';

COMMENT ON COLUMN estadisticas_transferencias.cantidad IS
'Total de transferencias en ese mes/año/provincia';

-- ==============================================================================
-- VISTA: Totales nacionales mensuales
-- ==============================================================================

CREATE OR REPLACE VIEW vista_totales_mensuales_inscripciones AS
SELECT
    tipo_vehiculo,
    anio,
    mes,
    SUM(cantidad) as total_nacional,
    COUNT(DISTINCT provincia) as provincias_con_datos
FROM estadisticas_inscripciones
GROUP BY tipo_vehiculo, anio, mes
ORDER BY anio DESC, mes DESC;

CREATE OR REPLACE VIEW vista_totales_mensuales_transferencias AS
SELECT
    tipo_vehiculo,
    anio,
    mes,
    SUM(cantidad) as total_nacional,
    COUNT(DISTINCT provincia) as provincias_con_datos
FROM estadisticas_transferencias
GROUP BY tipo_vehiculo, anio, mes
ORDER BY anio DESC, mes DESC;

-- ==============================================================================
-- VISTA: Ranking provincial histórico
-- ==============================================================================

CREATE OR REPLACE VIEW vista_ranking_provincial_inscripciones AS
SELECT
    provincia,
    tipo_vehiculo,
    SUM(cantidad) as total_historico,
    MIN(anio) as primer_anio,
    MAX(anio) as ultimo_anio,
    COUNT(*) as meses_con_datos
FROM estadisticas_inscripciones
GROUP BY provincia, tipo_vehiculo
ORDER BY total_historico DESC;

CREATE OR REPLACE VIEW vista_ranking_provincial_transferencias AS
SELECT
    provincia,
    tipo_vehiculo,
    SUM(cantidad) as total_historico,
    MIN(anio) as primer_anio,
    MAX(anio) as ultimo_anio,
    COUNT(*) as meses_con_datos
FROM estadisticas_transferencias
GROUP BY provincia, tipo_vehiculo
ORDER BY total_historico DESC;

-- ==============================================================================
-- FIN DEL SCRIPT
-- ==============================================================================
