-- ===================================================================
-- SCRIPT DE CREACIÓN DE KPIs MATERIALIZADOS PARA MERCADO AUTOMOTOR
-- ===================================================================
-- Propósito: Precalcular KPIs para mejorar performance del dashboard
--            y proveer features para modelos de ML
-- Actualización: Incremental vía función refresh_kpis()
-- ===================================================================

-- ===================================================================
-- 1. VISTA MATERIALIZADA: SEGMENTACIÓN DEMOGRÁFICA
-- ===================================================================
-- Propósito: Análisis de compradores por edad, género, ubicación y marca
-- KPI: DDC (Distribución Demográfica de Compradores)

DROP MATERIALIZED VIEW IF EXISTS kpi_segmentacion_demografica CASCADE;

CREATE MATERIALIZED VIEW kpi_segmentacion_demografica AS
WITH inscripciones_con_edad AS (
    SELECT
        titular_domicilio_provincia as provincia,
        titular_domicilio_localidad as localidad,
        EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento as edad,
        titular_genero as genero,
        titular_tipo_persona as tipo_persona,
        automotor_marca_descripcion as marca,
        automotor_modelo_descripcion as modelo,
        automotor_tipo_descripcion as tipo_vehiculo,
        automotor_origen as origen,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes
    FROM datos_gob_inscripciones
    WHERE titular_anio_nacimiento IS NOT NULL
    AND titular_anio_nacimiento > 1900
    AND titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_localidad IS NOT NULL
    AND tramite_fecha IS NOT NULL
    AND EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento BETWEEN 18 AND 100
)
SELECT
    provincia,
    localidad,
    CASE
        WHEN edad < 25 THEN '18-24'
        WHEN edad < 35 THEN '25-34'
        WHEN edad < 45 THEN '35-44'
        WHEN edad < 55 THEN '45-54'
        WHEN edad < 65 THEN '55-64'
        ELSE '65+'
    END as rango_edad,
    genero,
    tipo_persona,
    marca,
    tipo_vehiculo,
    origen,
    anio,
    mes,
    COUNT(*) as total_inscripciones,
    AVG(edad) as edad_promedio,
    MIN(edad) as edad_minima,
    MAX(edad) as edad_maxima,
    COUNT(DISTINCT modelo) as modelos_distintos
FROM inscripciones_con_edad
GROUP BY provincia, localidad, rango_edad, genero, tipo_persona, marca, tipo_vehiculo, origen, anio, mes;

-- Índices para optimizar consultas
CREATE INDEX idx_seg_dem_provincia_localidad ON kpi_segmentacion_demografica(provincia, localidad);
CREATE INDEX idx_seg_dem_marca ON kpi_segmentacion_demografica(marca);
CREATE INDEX idx_seg_dem_anio_mes ON kpi_segmentacion_demografica(anio, mes);
CREATE INDEX idx_seg_dem_rango_edad ON kpi_segmentacion_demografica(rango_edad);
CREATE INDEX idx_seg_dem_genero ON kpi_segmentacion_demografica(genero);

COMMENT ON MATERIALIZED VIEW kpi_segmentacion_demografica IS 'KPI DDC: Distribución demográfica de compradores por provincia, localidad, edad, género y marca';

-- ===================================================================
-- 2. VISTA MATERIALIZADA: ÍNDICE DE FINANCIAMIENTO
-- ===================================================================
-- Propósito: Calcular propensión a financiar por segmento
-- KPI: IF (Índice de Financiamiento)

DROP MATERIALIZED VIEW IF EXISTS kpi_financiamiento_segmento CASCADE;

CREATE MATERIALIZED VIEW kpi_financiamiento_segmento AS
WITH inscripciones_base AS (
    SELECT
        titular_domicilio_provincia as provincia,
        titular_domicilio_localidad as localidad,
        automotor_marca_descripcion as marca,
        automotor_tipo_descripcion as tipo_vehiculo,
        automotor_origen as origen,
        titular_genero as genero,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        COUNT(*) as total_inscripciones
    FROM datos_gob_inscripciones
    WHERE titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_localidad IS NOT NULL
    AND tramite_fecha IS NOT NULL
    GROUP BY provincia, localidad, marca, tipo_vehiculo, origen, genero, anio, mes
),
prendas_base AS (
    SELECT
        titular_domicilio_provincia as provincia,
        titular_domicilio_localidad as localidad,
        automotor_marca_descripcion as marca,
        automotor_tipo_descripcion as tipo_vehiculo,
        automotor_origen as origen,
        titular_genero as genero,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        COUNT(*) as total_prendas
    FROM datos_gob_prendas
    WHERE titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_localidad IS NOT NULL
    AND tramite_fecha IS NOT NULL
    GROUP BY provincia, localidad, marca, tipo_vehiculo, origen, genero, anio, mes
)
SELECT
    i.provincia,
    i.localidad,
    i.marca,
    i.tipo_vehiculo,
    i.origen,
    i.genero,
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
LEFT JOIN prendas_base p ON
    i.provincia = p.provincia
    AND i.localidad = p.localidad
    AND i.marca = p.marca
    AND COALESCE(i.tipo_vehiculo, '') = COALESCE(p.tipo_vehiculo, '')
    AND COALESCE(i.origen, '') = COALESCE(p.origen, '')
    AND COALESCE(i.genero, '') = COALESCE(p.genero, '')
    AND i.anio = p.anio
    AND i.mes = p.mes;

-- Índices
CREATE INDEX idx_if_provincia_localidad ON kpi_financiamiento_segmento(provincia, localidad);
CREATE INDEX idx_if_marca ON kpi_financiamiento_segmento(marca);
CREATE INDEX idx_if_anio_mes ON kpi_financiamiento_segmento(anio, mes);
CREATE INDEX idx_if_genero ON kpi_financiamiento_segmento(genero);

COMMENT ON MATERIALIZED VIEW kpi_financiamiento_segmento IS 'KPI IF: Índice de financiamiento por provincia, localidad, marca, género y período';

-- ===================================================================
-- 3. VISTA MATERIALIZADA: EDAD DE VEHÍCULOS (EVT e IAM)
-- ===================================================================
-- Propósito: Calcular antigüedad promedio de vehículos en transacción
-- KPI: EVT (Edad del Vehículo al Transferirse), IAM (Índice de Antigüedad del Mercado)

DROP MATERIALIZED VIEW IF EXISTS kpi_antiguedad_vehiculos CASCADE;

CREATE MATERIALIZED VIEW kpi_antiguedad_vehiculos AS
WITH transferencias_edad AS (
    SELECT
        titular_domicilio_provincia as provincia,
        titular_domicilio_localidad as localidad,
        automotor_marca_descripcion as marca,
        automotor_tipo_descripcion as tipo_vehiculo,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        'Transferencias' as tipo_transaccion,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo as edad_vehiculo,
        COUNT(*) as cantidad
    FROM datos_gob_transferencias
    WHERE automotor_anio_modelo IS NOT NULL
    AND automotor_anio_modelo > 1900
    AND tramite_fecha IS NOT NULL
    AND titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_localidad IS NOT NULL
    AND EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo BETWEEN 0 AND 50
    GROUP BY provincia, localidad, marca, tipo_vehiculo, anio, mes, edad_vehiculo
),
inscripciones_edad AS (
    SELECT
        titular_domicilio_provincia as provincia,
        titular_domicilio_localidad as localidad,
        automotor_marca_descripcion as marca,
        automotor_tipo_descripcion as tipo_vehiculo,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        'Inscripciones' as tipo_transaccion,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo as edad_vehiculo,
        COUNT(*) as cantidad
    FROM datos_gob_inscripciones
    WHERE automotor_anio_modelo IS NOT NULL
    AND automotor_anio_modelo > 1900
    AND tramite_fecha IS NOT NULL
    AND titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_localidad IS NOT NULL
    AND EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo >= 0
    GROUP BY provincia, localidad, marca, tipo_vehiculo, anio, mes, edad_vehiculo
),
combinado AS (
    SELECT * FROM transferencias_edad
    UNION ALL
    SELECT * FROM inscripciones_edad
)
SELECT
    provincia,
    localidad,
    marca,
    tipo_vehiculo,
    anio,
    mes,
    tipo_transaccion,
    SUM(cantidad) as total_transacciones,
    SUM(edad_vehiculo * cantidad)::FLOAT / NULLIF(SUM(cantidad), 0) as edad_promedio,
    MIN(edad_vehiculo) as edad_minima,
    MAX(edad_vehiculo) as edad_maxima
FROM combinado
GROUP BY provincia, localidad, marca, tipo_vehiculo, anio, mes, tipo_transaccion;

-- Índices
CREATE INDEX idx_edad_provincia_localidad ON kpi_antiguedad_vehiculos(provincia, localidad);
CREATE INDEX idx_edad_marca ON kpi_antiguedad_vehiculos(marca);
CREATE INDEX idx_edad_anio_mes ON kpi_antiguedad_vehiculos(anio, mes);
CREATE INDEX idx_edad_tipo_transaccion ON kpi_antiguedad_vehiculos(tipo_transaccion);

COMMENT ON MATERIALIZED VIEW kpi_antiguedad_vehiculos IS 'KPI EVT/IAM: Edad promedio de vehículos en transacción por provincia, localidad, marca y tipo';

-- ===================================================================
-- 4. VISTA MATERIALIZADA: ÍNDICE DE DEMANDA ACTIVA
-- ===================================================================
-- Propósito: Medir dinamismo del mercado (usados vs 0km)
-- KPI: IDA (Índice de Demanda Activa)

DROP MATERIALIZED VIEW IF EXISTS kpi_demanda_activa CASCADE;

CREATE MATERIALIZED VIEW kpi_demanda_activa AS
WITH inscripciones_mes AS (
    SELECT
        titular_domicilio_provincia as provincia,
        titular_domicilio_localidad as localidad,
        automotor_marca_descripcion as marca,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        COUNT(*) as total_inscripciones
    FROM datos_gob_inscripciones
    WHERE tramite_fecha IS NOT NULL
    AND titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_localidad IS NOT NULL
    GROUP BY provincia, localidad, marca, anio, mes
),
transferencias_mes AS (
    SELECT
        titular_domicilio_provincia as provincia,
        titular_domicilio_localidad as localidad,
        automotor_marca_descripcion as marca,
        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
        COUNT(*) as total_transferencias
    FROM datos_gob_transferencias
    WHERE tramite_fecha IS NOT NULL
    AND titular_domicilio_provincia IS NOT NULL
    AND titular_domicilio_localidad IS NOT NULL
    GROUP BY provincia, localidad, marca, anio, mes
)
SELECT
    COALESCE(i.provincia, t.provincia) as provincia,
    COALESCE(i.localidad, t.localidad) as localidad,
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
FULL OUTER JOIN transferencias_mes t ON
    i.provincia = t.provincia
    AND i.localidad = t.localidad
    AND COALESCE(i.marca, '') = COALESCE(t.marca, '')
    AND i.anio = t.anio
    AND i.mes = t.mes;

-- Índices
CREATE INDEX idx_ida_provincia_localidad ON kpi_demanda_activa(provincia, localidad);
CREATE INDEX idx_ida_marca ON kpi_demanda_activa(marca);
CREATE INDEX idx_ida_anio_mes ON kpi_demanda_activa(anio, mes);

COMMENT ON MATERIALIZED VIEW kpi_demanda_activa IS 'KPI IDA: Índice de demanda activa (transferencias/inscripciones) por provincia, localidad, marca y período';

-- ===================================================================
-- 5. TABLA: FEATURES PARA MACHINE LEARNING
-- ===================================================================
-- Propósito: Tabla consolidada con features precalculadas para ML
-- Uso: Training de modelos de propensión a compra

DROP TABLE IF EXISTS ml_features_propension_compra CASCADE;

CREATE TABLE ml_features_propension_compra AS
SELECT
    s.provincia,
    s.localidad,
    s.rango_edad,
    s.genero,
    s.tipo_persona,
    s.marca,
    s.tipo_vehiculo,
    s.origen,
    s.anio,
    s.mes,

    -- Features de volumen
    s.total_inscripciones,
    s.edad_promedio as edad_promedio_comprador,
    s.modelos_distintos,

    -- Features de financiamiento
    f.indice_financiamiento,
    f.total_prendas,

    -- Features de antigüedad de mercado
    evt.edad_promedio as evt_promedio,
    iam.edad_promedio as iam_promedio,

    -- Features de dinamismo de mercado
    ida.indice_demanda_activa,
    ida.total_transferencias,

    -- Features derivadas: Concentración de marca
    s.total_inscripciones::FLOAT / NULLIF(SUM(s.total_inscripciones) OVER (
        PARTITION BY s.provincia, s.localidad, s.anio, s.mes
    ), 0) as concentracion_marca_localidad,

    -- Ranking de marca en la zona
    RANK() OVER (
        PARTITION BY s.provincia, s.localidad, s.anio, s.mes
        ORDER BY s.total_inscripciones DESC
    ) as ranking_marca_localidad,

    -- Features de tendencia
    LAG(s.total_inscripciones, 1) OVER (
        PARTITION BY s.provincia, s.localidad, s.marca
        ORDER BY s.anio, s.mes
    ) as inscripciones_mes_anterior,

    LAG(s.total_inscripciones, 12) OVER (
        PARTITION BY s.provincia, s.localidad, s.marca
        ORDER BY s.anio, s.mes
    ) as inscripciones_mismo_mes_anio_anterior,

    -- Timestamp de actualización
    NOW() as fecha_actualizacion

FROM kpi_segmentacion_demografica s
LEFT JOIN kpi_financiamiento_segmento f ON
    s.provincia = f.provincia
    AND s.localidad = f.localidad
    AND s.marca = f.marca
    AND s.anio = f.anio
    AND s.mes = f.mes
    AND COALESCE(s.genero, '') = COALESCE(f.genero, '')
LEFT JOIN kpi_antiguedad_vehiculos evt ON
    s.provincia = evt.provincia
    AND s.localidad = evt.localidad
    AND s.marca = evt.marca
    AND s.anio = evt.anio
    AND s.mes = evt.mes
    AND evt.tipo_transaccion = 'Transferencias'
LEFT JOIN kpi_antiguedad_vehiculos iam ON
    s.provincia = iam.provincia
    AND s.localidad = iam.localidad
    AND s.marca = iam.marca
    AND s.anio = iam.anio
    AND s.mes = iam.mes
    AND iam.tipo_transaccion = 'Inscripciones'
LEFT JOIN kpi_demanda_activa ida ON
    s.provincia = ida.provincia
    AND s.localidad = ida.localidad
    AND s.marca = ida.marca
    AND s.anio = ida.anio
    AND s.mes = ida.mes
WHERE s.total_inscripciones >= 5; -- Filtrar casos con muy poca data

-- Índices para tabla ML
CREATE INDEX idx_ml_provincia_localidad ON ml_features_propension_compra(provincia, localidad);
CREATE INDEX idx_ml_marca ON ml_features_propension_compra(marca);
CREATE INDEX idx_ml_anio_mes ON ml_features_propension_compra(anio, mes);
CREATE INDEX idx_ml_rango_edad ON ml_features_propension_compra(rango_edad);
CREATE INDEX idx_ml_genero ON ml_features_propension_compra(genero);

COMMENT ON TABLE ml_features_propension_compra IS 'Features consolidadas para modelo de ML de propensión a compra';

-- ===================================================================
-- 6. FUNCIÓN: REFRESH INCREMENTAL DE KPIs
-- ===================================================================
-- Propósito: Actualizar las vistas materializadas después de cargar nuevos datos

CREATE OR REPLACE FUNCTION refresh_kpis_materializados(
    modo TEXT DEFAULT 'CONCURRENT'  -- 'CONCURRENT' o 'FULL'
) RETURNS TEXT AS $$
DECLARE
    inicio TIMESTAMP;
    fin TIMESTAMP;
    duracion INTERVAL;
    resultado TEXT;
BEGIN
    inicio := clock_timestamp();
    resultado := '';

    RAISE NOTICE 'Iniciando refresh de KPIs materializados...';

    -- 1. Segmentación Demográfica
    RAISE NOTICE '  [1/4] Actualizando kpi_segmentacion_demografica...';
    IF modo = 'CONCURRENT' THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_segmentacion_demografica;
    ELSE
        REFRESH MATERIALIZED VIEW kpi_segmentacion_demografica;
    END IF;
    resultado := resultado || '✓ kpi_segmentacion_demografica actualizada' || E'\n';

    -- 2. Financiamiento
    RAISE NOTICE '  [2/4] Actualizando kpi_financiamiento_segmento...';
    IF modo = 'CONCURRENT' THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_financiamiento_segmento;
    ELSE
        REFRESH MATERIALIZED VIEW kpi_financiamiento_segmento;
    END IF;
    resultado := resultado || '✓ kpi_financiamiento_segmento actualizada' || E'\n';

    -- 3. Antigüedad de Vehículos
    RAISE NOTICE '  [3/4] Actualizando kpi_antiguedad_vehiculos...';
    IF modo = 'CONCURRENT' THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_antiguedad_vehiculos;
    ELSE
        REFRESH MATERIALIZED VIEW kpi_antiguedad_vehiculos;
    END IF;
    resultado := resultado || '✓ kpi_antiguedad_vehiculos actualizada' || E'\n';

    -- 4. Demanda Activa
    RAISE NOTICE '  [4/4] Actualizando kpi_demanda_activa...';
    IF modo = 'CONCURRENT' THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_demanda_activa;
    ELSE
        REFRESH MATERIALIZED VIEW kpi_demanda_activa;
    END IF;
    resultado := resultado || '✓ kpi_demanda_activa actualizada' || E'\n';

    -- 5. Recrear tabla de ML features
    RAISE NOTICE '  [5/5] Recreando ml_features_propension_compra...';
    DROP TABLE IF EXISTS ml_features_propension_compra_temp CASCADE;

    CREATE TABLE ml_features_propension_compra_temp AS
    SELECT
        s.provincia,
        s.localidad,
        s.rango_edad,
        s.genero,
        s.tipo_persona,
        s.marca,
        s.tipo_vehiculo,
        s.origen,
        s.anio,
        s.mes,
        s.total_inscripciones,
        s.edad_promedio as edad_promedio_comprador,
        s.modelos_distintos,
        f.indice_financiamiento,
        f.total_prendas,
        evt.edad_promedio as evt_promedio,
        iam.edad_promedio as iam_promedio,
        ida.indice_demanda_activa,
        ida.total_transferencias,
        s.total_inscripciones::FLOAT / NULLIF(SUM(s.total_inscripciones) OVER (
            PARTITION BY s.provincia, s.localidad, s.anio, s.mes
        ), 0) as concentracion_marca_localidad,
        RANK() OVER (
            PARTITION BY s.provincia, s.localidad, s.anio, s.mes
            ORDER BY s.total_inscripciones DESC
        ) as ranking_marca_localidad,
        LAG(s.total_inscripciones, 1) OVER (
            PARTITION BY s.provincia, s.localidad, s.marca
            ORDER BY s.anio, s.mes
        ) as inscripciones_mes_anterior,
        LAG(s.total_inscripciones, 12) OVER (
            PARTITION BY s.provincia, s.localidad, s.marca
            ORDER BY s.anio, s.mes
        ) as inscripciones_mismo_mes_anio_anterior,
        NOW() as fecha_actualizacion
    FROM kpi_segmentacion_demografica s
    LEFT JOIN kpi_financiamiento_segmento f ON
        s.provincia = f.provincia
        AND s.localidad = f.localidad
        AND s.marca = f.marca
        AND s.anio = f.anio
        AND s.mes = f.mes
        AND COALESCE(s.genero, '') = COALESCE(f.genero, '')
    LEFT JOIN kpi_antiguedad_vehiculos evt ON
        s.provincia = evt.provincia
        AND s.localidad = evt.localidad
        AND s.marca = evt.marca
        AND s.anio = evt.anio
        AND s.mes = evt.mes
        AND evt.tipo_transaccion = 'Transferencias'
    LEFT JOIN kpi_antiguedad_vehiculos iam ON
        s.provincia = iam.provincia
        AND s.localidad = iam.localidad
        AND s.marca = iam.marca
        AND s.anio = iam.anio
        AND s.mes = iam.mes
        AND iam.tipo_transaccion = 'Inscripciones'
    LEFT JOIN kpi_demanda_activa ida ON
        s.provincia = ida.provincia
        AND s.localidad = ida.localidad
        AND s.marca = ida.marca
        AND s.anio = ida.anio
        AND s.mes = ida.mes
    WHERE s.total_inscripciones >= 5;

    -- Reemplazar tabla antigua
    DROP TABLE IF EXISTS ml_features_propension_compra CASCADE;
    ALTER TABLE ml_features_propension_compra_temp RENAME TO ml_features_propension_compra;

    -- Recrear índices
    CREATE INDEX idx_ml_provincia_localidad ON ml_features_propension_compra(provincia, localidad);
    CREATE INDEX idx_ml_marca ON ml_features_propension_compra(marca);
    CREATE INDEX idx_ml_anio_mes ON ml_features_propension_compra(anio, mes);
    CREATE INDEX idx_ml_rango_edad ON ml_features_propension_compra(rango_edad);
    CREATE INDEX idx_ml_genero ON ml_features_propension_compra(genero);

    resultado := resultado || '✓ ml_features_propension_compra recreada' || E'\n';

    fin := clock_timestamp();
    duracion := fin - inicio;

    resultado := resultado || E'\n' || '⏱ Tiempo total: ' || duracion::TEXT;

    RAISE NOTICE 'Refresh completado en: %', duracion;

    RETURN resultado;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_kpis_materializados IS 'Actualiza todas las vistas materializadas de KPIs y la tabla de features para ML';

-- ===================================================================
-- 7. VISTA: RESUMEN DE KPIs POR LOCALIDAD (para dashboard)
-- ===================================================================
-- Propósito: Vista consolidada de KPIs más comunes para dashboard

CREATE OR REPLACE VIEW v_kpis_resumen_localidad AS
SELECT
    sd.provincia,
    sd.localidad,
    sd.anio,
    sd.mes,

    -- Demografía
    SUM(sd.total_inscripciones) as total_inscripciones,
    AVG(sd.edad_promedio) as edad_promedio_compradores,

    -- Financiamiento
    AVG(fs.indice_financiamiento) as if_promedio,

    -- Antigüedad
    AVG(CASE WHEN av.tipo_transaccion = 'Transferencias' THEN av.edad_promedio END) as evt_promedio,
    AVG(CASE WHEN av.tipo_transaccion = 'Inscripciones' THEN av.edad_promedio END) as iam_promedio,

    -- Demanda
    AVG(da.indice_demanda_activa) as ida_promedio,

    -- Top marcas
    STRING_AGG(DISTINCT sd.marca, ', ' ORDER BY sd.marca) FILTER (WHERE sd.total_inscripciones > 10) as marcas_principales

FROM kpi_segmentacion_demografica sd
LEFT JOIN kpi_financiamiento_segmento fs ON
    sd.provincia = fs.provincia
    AND sd.localidad = fs.localidad
    AND sd.anio = fs.anio
    AND sd.mes = fs.mes
LEFT JOIN kpi_antiguedad_vehiculos av ON
    sd.provincia = av.provincia
    AND sd.localidad = av.localidad
    AND sd.anio = av.anio
    AND sd.mes = av.mes
LEFT JOIN kpi_demanda_activa da ON
    sd.provincia = da.provincia
    AND sd.localidad = da.localidad
    AND sd.anio = da.anio
    AND sd.mes = da.mes
GROUP BY sd.provincia, sd.localidad, sd.anio, sd.mes;

COMMENT ON VIEW v_kpis_resumen_localidad IS 'Vista consolidada de KPIs por localidad para dashboard';

-- ===================================================================
-- FIN DEL SCRIPT
-- ===================================================================
-- Para ejecutar: psql -U usuario -d mercado_automotor -f crear_kpis_materializados.sql
-- Para actualizar: SELECT refresh_kpis_materializados();
-- ===================================================================
