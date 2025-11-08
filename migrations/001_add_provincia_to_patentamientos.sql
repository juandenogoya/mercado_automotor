-- Migration: Agregar campo 'provincia' a tabla patentamientos
-- Date: 2025-11-08
-- Purpose: Soportar datos de DNRPA con granularidad provincial

-- 1. Agregar columna provincia (nullable para compatibilidad con datos existentes)
ALTER TABLE patentamientos
ADD COLUMN IF NOT EXISTS provincia VARCHAR(100);

-- 2. Comentar la columna para documentación
COMMENT ON COLUMN patentamientos.provincia IS 'Provincia o registro seccional (usado por DNRPA)';

-- 3. Opcional: Crear índice si se van a hacer queries frecuentes por provincia
CREATE INDEX IF NOT EXISTS idx_patentamientos_provincia ON patentamientos(provincia);

-- 4. Verificar cambios
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'patentamientos'
-- ORDER BY ordinal_position;
