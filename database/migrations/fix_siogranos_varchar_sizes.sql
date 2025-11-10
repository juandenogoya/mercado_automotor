-- ============================================================================
-- Migración: Aumentar tamaño de campos VARCHAR en siogranos_operaciones
-- ============================================================================
-- Soluciona: "el valor es demasiado largo para el tipo character varying(5)"
-- ============================================================================

-- Aumentar tamaño de campos de provincia
ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_provincia_procedencia TYPE VARCHAR(20);

ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_provincia_destino TYPE VARCHAR(20);

-- Aumentar tamaño de campos de localidad
ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_localidad_procedencia TYPE VARCHAR(50);

ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_localidad_destino TYPE VARCHAR(50);

-- Aumentar tamaño de campo puerto
ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_puerto TYPE VARCHAR(50);

-- Verificar cambios
SELECT
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'siogranos_operaciones'
  AND column_name IN (
      'id_provincia_procedencia',
      'id_provincia_destino',
      'id_localidad_procedencia',
      'id_localidad_destino',
      'id_puerto'
  )
ORDER BY column_name;
