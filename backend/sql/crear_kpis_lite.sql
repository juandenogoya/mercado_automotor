-- =====================================================
-- VERSIÓN LITE DE KPIs - MÁS RÁPIDA, MENOS DIMENSIONES
-- =====================================================
-- Esta versión reduce dimensiones para procesar más rápido
-- Ideal para testing o PCs con recursos limitados

-- Limpiar si existen
DROP MATERIALIZED VIEW IF EXISTS kpi_segmentacion_demografica_lite CASCADE;
DROP MATERIALIZED VIEW IF EXISTS kpi_financiamiento_lite CASCADE;
DROP MATERIALIZED VIEW IF EXISTS kpi_antiguedad_vehiculos_lite CASCADE;
DROP MATERIALIZED VIEW IF EXISTS kpi_demanda_activa_lite CASCADE;

-- =====================================================
-- 1. KPI SEGMENTACIÓN DEMOGRÁFICA (LITE)
-- Solo dimensiones principales: provincia, marca, año, mes
-- =====================================================

CREATE MATERIALIZED VIEW kpi_segmentacion_demografica_lite AS
SELECT
    titular_domicilio_provincia as provincia,
    automotor_marca_descripcion as marca,
    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
    COUNT(*) as total_inscripciones,
    AVG(EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento) as edad_promedio,
    COUNT(DISTINCT automotor_modelo_descripcion) as modelos_distintos
FROM datos_gob_inscripciones
WHERE titular_domicilio_provincia IS NOT NULL
AND titular_domicilio_provincia != ''
AND automotor_marca_descripcion IS NOT NULL
AND automotor_marca_descripcion != ''
AND titular_anio_nacimiento IS NOT NULL
GROUP BY provincia, marca, anio, mes;

-- Crear índices
CREATE UNIQUE INDEX idx_seg_lite_pk
    ON kpi_segmentacion_demografica_lite(provincia, marca, anio, mes);
CREATE INDEX idx_seg_lite_anio_mes
    ON kpi_segmentacion_demografica_lite(anio, mes);
CREATE INDEX idx_seg_lite_provincia
    ON kpi_segmentacion_demografica_lite(provincia);

-- =====================================================
-- 2. KPI FINANCIAMIENTO (LITE)
-- Índice de financiamiento por provincia y marca
-- =====================================================

CREATE MATERIALIZED VIEW kpi_financiamiento_lite AS
WITH inscripciones_base AS (
    SELECT
        titular_domicilio_provincia as provincia,
        automotor_marca_descripcion as marca,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        COUNT(*) as total_inscripciones
    FROM datos_gob_inscripciones
    WHERE titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_provincia != ''
    AND automotor_marca_descripcion IS NOT NULL
    AND automotor_marca_descripcion != ''
    GROUP BY provincia, marca, anio, mes
),
prendas_base AS (
    SELECT
        titular_domicilio_provincia as provincia,
        automotor_marca_descripcion as marca,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        COUNT(*) as total_prendas
    FROM datos_gob_prendas
    WHERE titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_provincia != ''
    AND automotor_marca_descripcion IS NOT NULL
    AND automotor_marca_descripcion != ''
    GROUP BY provincia, marca, anio, mes
)
SELECT
    i.provincia,
    i.marca,
    i.anio,
    i.mes,
    i.total_inscripciones,
    COALESCE(p.total_prendas, 0) as total_prendas,
    CASE
        WHEN i.total_inscripciones > 0 THEN
            (COALESCE(p.total_prendas, 0)::FLOAT / i.total_inscripciones * 100)
        ELSE 0
    END as indice_financiamiento
FROM inscripciones_base i
LEFT JOIN prendas_base p
    ON i.provincia = p.provincia
    AND i.marca = p.marca
    AND i.anio = p.anio
    AND i.mes = p.mes;

-- Crear índices
CREATE UNIQUE INDEX idx_fin_lite_pk
    ON kpi_financiamiento_lite(provincia, marca, anio, mes);
CREATE INDEX idx_fin_lite_anio_mes
    ON kpi_financiamiento_lite(anio, mes);

-- =====================================================
-- 3. KPI ANTIGÜEDAD VEHÍCULOS (LITE)
-- EVT e IAM por provincia y marca
-- =====================================================

CREATE MATERIALIZED VIEW kpi_antiguedad_vehiculos_lite AS
WITH evt_data AS (
    SELECT
        titular_domicilio_provincia as provincia,
        automotor_marca_descripcion as marca,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        'transferencia' as tipo_transaccion,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo as edad_vehiculo,
        COUNT(*) as cantidad
    FROM datos_gob_transferencias
    WHERE titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_provincia != ''
    AND automotor_marca_descripcion IS NOT NULL
    AND automotor_marca_descripcion != ''
    AND automotor_anio_modelo IS NOT NULL
    AND EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo >= 0
    AND EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo <= 50
    GROUP BY provincia, marca, anio, mes, edad_vehiculo

    UNION ALL

    SELECT
        titular_domicilio_provincia as provincia,
        automotor_marca_descripcion as marca,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        'inscripcion' as tipo_transaccion,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo as edad_vehiculo,
        COUNT(*) as cantidad
    FROM datos_gob_inscripciones
    WHERE titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_provincia != ''
    AND automotor_marca_descripcion IS NOT NULL
    AND automotor_marca_descripcion != ''
    AND automotor_anio_modelo IS NOT NULL
    AND EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo >= 0
    AND EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo <= 50
    GROUP BY provincia, marca, anio, mes, edad_vehiculo
)
SELECT
    provincia,
    marca,
    anio,
    mes,
    tipo_transaccion,
    SUM(cantidad) as total_transacciones,
    SUM(edad_vehiculo * cantidad)::FLOAT / NULLIF(SUM(cantidad), 0) as edad_promedio,
    MIN(edad_vehiculo) as edad_minima,
    MAX(edad_vehiculo) as edad_maxima
FROM evt_data
GROUP BY provincia, marca, anio, mes, tipo_transaccion;

-- Crear índices
CREATE INDEX idx_ant_lite_pk
    ON kpi_antiguedad_vehiculos_lite(provincia, marca, anio, mes, tipo_transaccion);
CREATE INDEX idx_ant_lite_anio_mes
    ON kpi_antiguedad_vehiculos_lite(anio, mes);

-- =====================================================
-- 4. KPI DEMANDA ACTIVA (LITE)
-- IDA por provincia y marca
-- =====================================================

CREATE MATERIALIZED VIEW kpi_demanda_activa_lite AS
WITH inscripciones_mes AS (
    SELECT
        titular_domicilio_provincia as provincia,
        automotor_marca_descripcion as marca,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        COUNT(*) as total_inscripciones
    FROM datos_gob_inscripciones
    WHERE titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_provincia != ''
    AND automotor_marca_descripcion IS NOT NULL
    AND automotor_marca_descripcion != ''
    GROUP BY provincia, marca, anio, mes
),
transferencias_mes AS (
    SELECT
        titular_domicilio_provincia as provincia,
        automotor_marca_descripcion as marca,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        COUNT(*) as total_transferencias
    FROM datos_gob_transferencias
    WHERE titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_provincia != ''
    AND automotor_marca_descripcion IS NOT NULL
    AND automotor_marca_descripcion != ''
    GROUP BY provincia, marca, anio, mes
)
SELECT
    COALESCE(i.provincia, t.provincia) as provincia,
    COALESCE(i.marca, t.marca) as marca,
    COALESCE(i.anio, t.anio) as anio,
    COALESCE(i.mes, t.mes) as mes,
    COALESCE(i.total_inscripciones, 0) as total_inscripciones,
    COALESCE(t.total_transferencias, 0) as total_transferencias,
    CASE
        WHEN COALESCE(i.total_inscripciones, 0) > 0 THEN
            (COALESCE(t.total_transferencias, 0)::FLOAT / i.total_inscripciones * 100)
        ELSE 0
    END as indice_demanda_activa
FROM inscripciones_mes i
FULL OUTER JOIN transferencias_mes t
    ON i.provincia = t.provincia
    AND i.marca = t.marca
    AND i.anio = t.anio
    AND i.mes = t.mes;

-- Crear índices
CREATE INDEX idx_ida_lite_pk
    ON kpi_demanda_activa_lite(provincia, marca, anio, mes);
CREATE INDEX idx_ida_lite_anio_mes
    ON kpi_demanda_activa_lite(anio, mes);

-- =====================================================
-- FUNCIÓN PARA REFRESCAR KPIs LITE
-- =====================================================

CREATE OR REPLACE FUNCTION refresh_kpis_lite(
    modo TEXT DEFAULT 'CONCURRENT'
) RETURNS TEXT AS $$
DECLARE
    inicio TIMESTAMP;
    fin TIMESTAMP;
    duracion INTERVAL;
    resultado TEXT;
BEGIN
    inicio := clock_timestamp();
    resultado := '🔄 Refresh KPIs LITE iniciado: ' || inicio || E'\n';

    -- Refresh vistas materializadas
    IF modo = 'CONCURRENT' THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_segmentacion_demografica_lite;
        resultado := resultado || '✓ kpi_segmentacion_demografica_lite (CONCURRENT)' || E'\n';

        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_financiamiento_lite;
        resultado := resultado || '✓ kpi_financiamiento_lite (CONCURRENT)' || E'\n';

        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_antiguedad_vehiculos_lite;
        resultado := resultado || '✓ kpi_antiguedad_vehiculos_lite (CONCURRENT)' || E'\n';

        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_demanda_activa_lite;
        resultado := resultado || '✓ kpi_demanda_activa_lite (CONCURRENT)' || E'\n';
    ELSE
        REFRESH MATERIALIZED VIEW kpi_segmentacion_demografica_lite;
        resultado := resultado || '✓ kpi_segmentacion_demografica_lite' || E'\n';

        REFRESH MATERIALIZED VIEW kpi_financiamiento_lite;
        resultado := resultado || '✓ kpi_financiamiento_lite' || E'\n';

        REFRESH MATERIALIZED VIEW kpi_antiguedad_vehiculos_lite;
        resultado := resultado || '✓ kpi_antiguedad_vehiculos_lite' || E'\n';

        REFRESH MATERIALIZED VIEW kpi_demanda_activa_lite;
        resultado := resultado || '✓ kpi_demanda_activa_lite' || E'\n';
    END IF;

    fin := clock_timestamp();
    duracion := fin - inicio;
    resultado := resultado || E'\n✅ Refresh completado en: ' || duracion;

    RETURN resultado;
END;
$$ LANGUAGE plpgsql;
