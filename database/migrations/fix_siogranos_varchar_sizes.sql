-- ============================================================================
-- Migración: Cambiar campos ID a TEXT en siogranos_operaciones
-- ============================================================================
-- Soluciona: "el valor es demasiado largo para el tipo character varying"
-- Cambio: VARCHAR con límites -> TEXT (sin límites) para flexibilidad con API
-- ============================================================================

-- Cambiar campos de provincia a TEXT
ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_provincia_procedencia TYPE TEXT;

ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_provincia_destino TYPE TEXT;

-- Cambiar campos de localidad a TEXT
ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_localidad_procedencia TYPE TEXT;

ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_localidad_destino TYPE TEXT;

-- Cambiar campo puerto a TEXT
ALTER TABLE siogranos_operaciones
    ALTER COLUMN id_puerto TYPE TEXT;

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
