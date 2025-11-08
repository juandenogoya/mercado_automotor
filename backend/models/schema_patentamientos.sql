-- Esquema de Base de Datos para Patentamientos DNRPA
-- Diseñado para manejar datos históricos y variabilidad de provincias/seccionales

-- ==============================================================================
-- TABLAS DE REFERENCIA (Dimensiones)
-- ==============================================================================

-- Tabla de provincias
CREATE TABLE IF NOT EXISTS provincias (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(2) NOT NULL UNIQUE,  -- Código DNRPA (ej: '01', '02')
    nombre VARCHAR(100) NOT NULL,        -- Nombre de la provincia
    activa BOOLEAN DEFAULT TRUE,         -- Si sigue apareciendo en datos actuales
    fecha_alta DATE DEFAULT CURRENT_DATE,-- Cuándo se detectó por primera vez
    fecha_baja DATE NULL,                -- Cuándo dejó de aparecer (si aplica)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para provincias
CREATE INDEX IF NOT EXISTS idx_provincias_codigo ON provincias(codigo);
CREATE INDEX IF NOT EXISTS idx_provincias_activa ON provincias(activa);

-- Tabla de seccionales (registros seccionales dentro de cada provincia)
CREATE TABLE IF NOT EXISTS seccionales (
    id SERIAL PRIMARY KEY,
    provincia_id INTEGER NOT NULL REFERENCES provincias(id) ON DELETE CASCADE,
    codigo VARCHAR(10) NOT NULL,         -- Código del seccional
    nombre VARCHAR(100) NOT NULL,        -- Nombre del seccional
    activa BOOLEAN DEFAULT TRUE,         -- Si sigue activa
    fecha_alta DATE DEFAULT CURRENT_DATE,-- Cuándo apareció
    fecha_baja DATE NULL,                -- Cuándo cerró (si aplica)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provincia_id, codigo, nombre) -- No duplicados
);

-- Índices para seccionales
CREATE INDEX IF NOT EXISTS idx_seccionales_provincia ON seccionales(provincia_id);
CREATE INDEX IF NOT EXISTS idx_seccionales_activa ON seccionales(activa);


-- ==============================================================================
-- TABLAS DE DATOS (Hechos)
-- ==============================================================================

-- Datos de patentamientos a nivel PROVINCIAL (agregado)
CREATE TABLE IF NOT EXISTS patentamientos_provincial (
    id SERIAL PRIMARY KEY,
    provincia_id INTEGER NOT NULL REFERENCES provincias(id) ON DELETE CASCADE,
    anio INTEGER NOT NULL,               -- Año (ej: 2024)
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12), -- Mes (1-12)
    cantidad INTEGER NOT NULL DEFAULT 0, -- Cantidad de patentamientos
    tipo_vehiculo VARCHAR(20) NOT NULL,  -- 'Autos', 'Motos', 'Camiones', 'Otros'
    tipo_tramite VARCHAR(20) DEFAULT 'inscripcion', -- 'inscripcion', 'transferencia', etc.
    fecha_scraping TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Cuándo se scrapeó
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provincia_id, anio, mes, tipo_vehiculo, tipo_tramite) -- No duplicados
);

-- Índices para patentamientos_provincial
CREATE INDEX IF NOT EXISTS idx_paten_prov_provincia ON patentamientos_provincial(provincia_id);
CREATE INDEX IF NOT EXISTS idx_paten_prov_anio ON patentamientos_provincial(anio);
CREATE INDEX IF NOT EXISTS idx_paten_prov_mes ON patentamientos_provincial(mes);
CREATE INDEX IF NOT EXISTS idx_paten_prov_tipo_veh ON patentamientos_provincial(tipo_vehiculo);
CREATE INDEX IF NOT EXISTS idx_paten_prov_anio_mes ON patentamientos_provincial(anio, mes);


-- Datos de patentamientos a nivel SECCIONAL (detallado)
CREATE TABLE IF NOT EXISTS patentamientos_seccional (
    id SERIAL PRIMARY KEY,
    seccional_id INTEGER NOT NULL REFERENCES seccionales(id) ON DELETE CASCADE,
    anio INTEGER NOT NULL,               -- Año
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12), -- Mes (1-12)
    cantidad INTEGER NOT NULL DEFAULT 0, -- Cantidad de patentamientos
    tipo_vehiculo VARCHAR(20) NOT NULL,  -- 'Autos', 'Motos', etc.
    tipo_tramite VARCHAR(20) DEFAULT 'inscripcion',
    fecha_scraping TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(seccional_id, anio, mes, tipo_vehiculo, tipo_tramite) -- No duplicados
);

-- Índices para patentamientos_seccional
CREATE INDEX IF NOT EXISTS idx_paten_secc_seccional ON patentamientos_seccional(seccional_id);
CREATE INDEX IF NOT EXISTS idx_paten_secc_anio ON patentamientos_seccional(anio);
CREATE INDEX IF NOT EXISTS idx_paten_secc_mes ON patentamientos_seccional(mes);
CREATE INDEX IF NOT EXISTS idx_paten_secc_tipo_veh ON patentamientos_seccional(tipo_vehiculo);
CREATE INDEX IF NOT EXISTS idx_paten_secc_anio_mes ON patentamientos_seccional(anio, mes);


-- ==============================================================================
-- VISTAS ÚTILES
-- ==============================================================================

-- Vista: Resumen de patentamientos por provincia y año
CREATE OR REPLACE VIEW v_patentamientos_provincia_anual AS
SELECT
    p.codigo AS provincia_codigo,
    p.nombre AS provincia_nombre,
    pp.anio,
    pp.tipo_vehiculo,
    SUM(pp.cantidad) AS total_anio,
    COUNT(DISTINCT pp.mes) AS meses_con_datos
FROM patentamientos_provincial pp
JOIN provincias p ON p.id = pp.provincia_id
GROUP BY p.codigo, p.nombre, pp.anio, pp.tipo_vehiculo
ORDER BY pp.anio DESC, total_anio DESC;


-- Vista: Top provincias por patentamientos
CREATE OR REPLACE VIEW v_top_provincias AS
SELECT
    p.nombre AS provincia,
    pp.anio,
    pp.tipo_vehiculo,
    SUM(pp.cantidad) AS total_patentamientos,
    RANK() OVER (PARTITION BY pp.anio, pp.tipo_vehiculo ORDER BY SUM(pp.cantidad) DESC) AS ranking
FROM patentamientos_provincial pp
JOIN provincias p ON p.id = pp.provincia_id
GROUP BY p.nombre, pp.anio, pp.tipo_vehiculo
ORDER BY pp.anio DESC, total_patentamientos DESC;


-- Vista: Datos mensuales por provincia (útil para gráficos)
CREATE OR REPLACE VIEW v_patentamientos_mensuales AS
SELECT
    p.codigo AS provincia_codigo,
    p.nombre AS provincia_nombre,
    pp.anio,
    pp.mes,
    TO_DATE(pp.anio || '-' || LPAD(pp.mes::TEXT, 2, '0') || '-01', 'YYYY-MM-DD') AS fecha,
    pp.tipo_vehiculo,
    pp.cantidad,
    pp.fecha_scraping
FROM patentamientos_provincial pp
JOIN provincias p ON p.id = pp.provincia_id
ORDER BY pp.anio, pp.mes, p.nombre;


-- Vista: Comparación año a año
CREATE OR REPLACE VIEW v_comparacion_anual AS
SELECT
    p.nombre AS provincia,
    pp.mes,
    pp.tipo_vehiculo,
    MAX(CASE WHEN pp.anio = EXTRACT(YEAR FROM CURRENT_DATE) THEN pp.cantidad END) AS anio_actual,
    MAX(CASE WHEN pp.anio = EXTRACT(YEAR FROM CURRENT_DATE) - 1 THEN pp.cantidad END) AS anio_anterior,
    (MAX(CASE WHEN pp.anio = EXTRACT(YEAR FROM CURRENT_DATE) THEN pp.cantidad END) -
     MAX(CASE WHEN pp.anio = EXTRACT(YEAR FROM CURRENT_DATE) - 1 THEN pp.cantidad END))::FLOAT /
     NULLIF(MAX(CASE WHEN pp.anio = EXTRACT(YEAR FROM CURRENT_DATE) - 1 THEN pp.cantidad END), 0) * 100 AS variacion_porcentual
FROM patentamientos_provincial pp
JOIN provincias p ON p.id = pp.provincia_id
WHERE pp.anio IN (EXTRACT(YEAR FROM CURRENT_DATE), EXTRACT(YEAR FROM CURRENT_DATE) - 1)
GROUP BY p.nombre, pp.mes, pp.tipo_vehiculo
ORDER BY p.nombre, pp.mes;


-- ==============================================================================
-- FUNCIONES ÚTILES
-- ==============================================================================

-- Función: Actualizar timestamp de updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para actualizar updated_at
DROP TRIGGER IF EXISTS update_provincias_updated_at ON provincias;
CREATE TRIGGER update_provincias_updated_at
    BEFORE UPDATE ON provincias
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_seccionales_updated_at ON seccionales;
CREATE TRIGGER update_seccionales_updated_at
    BEFORE UPDATE ON seccionales
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_paten_prov_updated_at ON patentamientos_provincial;
CREATE TRIGGER update_paten_prov_updated_at
    BEFORE UPDATE ON patentamientos_provincial
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_paten_secc_updated_at ON patentamientos_seccional;
CREATE TRIGGER update_paten_secc_updated_at
    BEFORE UPDATE ON patentamientos_seccional
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ==============================================================================
-- COMENTARIOS EN TABLAS
-- ==============================================================================

COMMENT ON TABLE provincias IS 'Catálogo de provincias argentinas con sus códigos DNRPA';
COMMENT ON TABLE seccionales IS 'Registros seccionales por provincia (pueden variar en el tiempo)';
COMMENT ON TABLE patentamientos_provincial IS 'Datos de patentamientos agregados por provincia, mes y año';
COMMENT ON TABLE patentamientos_seccional IS 'Datos de patentamientos detallados por seccional, mes y año';

COMMENT ON COLUMN provincias.codigo IS 'Código de 2 dígitos usado por DNRPA (01-24)';
COMMENT ON COLUMN provincias.activa IS 'FALSE si la provincia dejó de aparecer en los datos';
COMMENT ON COLUMN seccionales.activa IS 'FALSE si el seccional cerró o dejó de operar';
COMMENT ON COLUMN patentamientos_provincial.tipo_tramite IS 'Tipo de trámite: inscripcion, transferencia, etc.';
COMMENT ON COLUMN patentamientos_seccional.fecha_scraping IS 'Timestamp de cuándo se scrapearon los datos (para auditoría)';


-- ==============================================================================
-- DATOS INICIALES (SEED)
-- ==============================================================================

-- Insertar provincias conocidas (se actualizarán con scraping real)
INSERT INTO provincias (codigo, nombre) VALUES
    ('01', 'BUENOS AIRES'),
    ('02', 'C.AUTONOMA DE BS.AS'),
    ('03', 'CATAMARCA'),
    ('04', 'CORDOBA'),
    ('05', 'CORRIENTES'),
    ('06', 'CHACO'),
    ('07', 'CHUBUT'),
    ('08', 'ENTRE RIOS'),
    ('09', 'FORMOSA'),
    ('10', 'JUJUY'),
    ('11', 'LA PAMPA'),
    ('12', 'LA RIOJA'),
    ('13', 'MENDOZA'),
    ('14', 'MISIONES'),
    ('15', 'NEUQUEN'),
    ('16', 'RIO NEGRO'),
    ('17', 'SALTA'),
    ('18', 'SAN JUAN'),
    ('19', 'SAN LUIS'),
    ('20', 'SANTA CRUZ'),
    ('21', 'SANTA FE'),
    ('22', 'SANTIAGO DEL ESTERO'),
    ('23', 'TIERRA DEL FUEGO'),
    ('24', 'TUCUMAN')
ON CONFLICT (codigo) DO NOTHING;


-- ==============================================================================
-- VERIFICACIÓN
-- ==============================================================================

-- Query para verificar que todo se creó correctamente
SELECT
    'Tablas creadas' AS verificacion,
    COUNT(*) AS cantidad
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('provincias', 'seccionales', 'patentamientos_provincial', 'patentamientos_seccional')

UNION ALL

SELECT
    'Vistas creadas' AS verificacion,
    COUNT(*) AS cantidad
FROM information_schema.views
WHERE table_schema = 'public'
AND table_name LIKE 'v_%'

UNION ALL

SELECT
    'Provincias cargadas' AS verificacion,
    COUNT(*) AS cantidad
FROM provincias;
