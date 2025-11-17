-- Script SOLO para crear la función refresh_kpis_materializados
-- Usa este script después de cancelar la creación de la tabla ML
-- Las vistas materializadas YA están creadas, solo falta la función

-- Limpiar función anterior si existe
DROP FUNCTION IF EXISTS refresh_kpis_materializados(TEXT);

-- Crear función de refresh (sin incluir tabla ML)
CREATE OR REPLACE FUNCTION refresh_kpis_materializados(
    modo TEXT DEFAULT 'CONCURRENT'
) RETURNS TEXT AS $$
DECLARE
    inicio TIMESTAMP;
    fin TIMESTAMP;
    duracion INTERVAL;
    resultado TEXT;
BEGIN
    inicio := clock_timestamp();
    resultado := '🔄 Refresh KPIs iniciado: ' || inicio || E'\n';

    RAISE NOTICE 'Iniciando refresh de KPIs materializados...';

    -- Refresh vistas materializadas según modo
    IF modo = 'CONCURRENT' THEN
        RAISE NOTICE 'Modo CONCURRENT (no bloquea lecturas)';

        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_segmentacion_demografica;
        resultado := resultado || '✓ kpi_segmentacion_demografica (CONCURRENT)' || E'\n';

        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_financiamiento_segmento;
        resultado := resultado || '✓ kpi_financiamiento_segmento (CONCURRENT)' || E'\n';

        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_antiguedad_vehiculos;
        resultado := resultado || '✓ kpi_antiguedad_vehiculos (CONCURRENT)' || E'\n';

        REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_demanda_activa;
        resultado := resultado || '✓ kpi_demanda_activa (CONCURRENT)' || E'\n';

    ELSE
        RAISE NOTICE 'Modo FULL (bloquea lecturas pero es más rápido)';

        REFRESH MATERIALIZED VIEW kpi_segmentacion_demografica;
        resultado := resultado || '✓ kpi_segmentacion_demografica' || E'\n';

        REFRESH MATERIALIZED VIEW kpi_financiamiento_segmento;
        resultado := resultado || '✓ kpi_financiamiento_segmento' || E'\n';

        REFRESH MATERIALIZED VIEW kpi_antiguedad_vehiculos;
        resultado := resultado || '✓ kpi_antiguedad_vehiculos' || E'\n';

        REFRESH MATERIALIZED VIEW kpi_demanda_activa;
        resultado := resultado || '✓ kpi_demanda_activa' || E'\n';
    END IF;

    fin := clock_timestamp();
    duracion := fin - inicio;
    resultado := resultado || E'\n✅ Refresh completado en: ' || duracion;

    RETURN resultado;
END;
$$ LANGUAGE plpgsql;

-- Comentario explicativo
COMMENT ON FUNCTION refresh_kpis_materializados(TEXT) IS
'Actualiza las vistas materializadas de KPIs.
Modo CONCURRENT: No bloquea lecturas pero es más lento.
Modo FULL: Bloquea lecturas pero es más rápido.
Nota: La tabla ml_features_propension_compra se debe crear/actualizar por separado.';
