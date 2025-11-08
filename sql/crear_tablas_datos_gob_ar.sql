-- ============================================================================
-- TABLAS PARA DATOS DE datos.gob.ar
-- Dataset: Estadística de trámites de automotores (Ministerio de Justicia)
-- Fuente: DNRPA vía datos.gob.ar
-- ============================================================================

-- Eliminar tablas si existen
DROP TABLE IF EXISTS datos_gob_inscripciones CASCADE;
DROP TABLE IF EXISTS datos_gob_transferencias CASCADE;
DROP TABLE IF EXISTS datos_gob_prendas CASCADE;
DROP TABLE IF EXISTS datos_gob_registros_seccionales CASCADE;

-- ============================================================================
-- TABLA: INSCRIPCIONES INICIALES
-- Registra patentamientos de vehículos 0km
-- ============================================================================
CREATE TABLE datos_gob_inscripciones (
    id SERIAL PRIMARY KEY,

    -- Datos del trámite
    tramite_tipo VARCHAR(100),
    tramite_fecha DATE,
    fecha_inscripcion_inicial DATE,

    -- Registro seccional
    registro_seccional_codigo INTEGER,
    registro_seccional_descripcion VARCHAR(200),
    registro_seccional_provincia VARCHAR(100),

    -- Datos del automotor
    automotor_origen VARCHAR(50),
    automotor_anio_modelo INTEGER,
    automotor_tipo_codigo VARCHAR(10),
    automotor_tipo_descripcion VARCHAR(100),
    automotor_marca_codigo VARCHAR(10),
    automotor_marca_descripcion VARCHAR(100),
    automotor_modelo_codigo VARCHAR(20),
    automotor_modelo_descripcion VARCHAR(200),
    automotor_uso_codigo VARCHAR(10),
    automotor_uso_descripcion VARCHAR(50),

    -- Datos del titular
    titular_tipo_persona VARCHAR(50),
    titular_domicilio_localidad VARCHAR(200),
    titular_domicilio_provincia VARCHAR(100),
    titular_genero VARCHAR(50),
    titular_anio_nacimiento INTEGER,
    titular_pais_nacimiento VARCHAR(100),
    titular_porcentaje_titularidad NUMERIC(5,2),
    titular_domicilio_provincia_id VARCHAR(10),
    titular_pais_nacimiento_id VARCHAR(10),

    -- Metadata
    archivo_origen VARCHAR(200),
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: TRANSFERENCIAS
-- Registra transferencias de vehículos usados
-- ============================================================================
CREATE TABLE datos_gob_transferencias (
    id SERIAL PRIMARY KEY,

    -- Datos del trámite
    tramite_tipo VARCHAR(100),
    tramite_fecha DATE,
    fecha_inscripcion_inicial DATE,

    -- Registro seccional
    registro_seccional_codigo INTEGER,
    registro_seccional_descripcion VARCHAR(200),
    registro_seccional_provincia VARCHAR(100),

    -- Datos del automotor
    automotor_origen VARCHAR(50),
    automotor_anio_modelo INTEGER,
    automotor_tipo_codigo VARCHAR(10),
    automotor_tipo_descripcion VARCHAR(100),
    automotor_marca_codigo VARCHAR(10),
    automotor_marca_descripcion VARCHAR(100),
    automotor_modelo_codigo VARCHAR(20),
    automotor_modelo_descripcion VARCHAR(200),
    automotor_uso_codigo VARCHAR(10),
    automotor_uso_descripcion VARCHAR(50),

    -- Datos del titular
    titular_tipo_persona VARCHAR(50),
    titular_domicilio_localidad VARCHAR(200),
    titular_domicilio_provincia VARCHAR(100),
    titular_genero VARCHAR(50),
    titular_anio_nacimiento INTEGER,
    titular_pais_nacimiento VARCHAR(100),
    titular_porcentaje_titularidad NUMERIC(5,2),
    titular_domicilio_provincia_id VARCHAR(10),
    titular_pais_nacimiento_id VARCHAR(10),

    -- Metadata
    archivo_origen VARCHAR(200),
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: PRENDAS
-- Registra prendas sobre vehículos
-- ============================================================================
CREATE TABLE datos_gob_prendas (
    id SERIAL PRIMARY KEY,

    -- Datos del trámite
    tramite_tipo VARCHAR(100),
    tramite_fecha DATE,
    fecha_inscripcion_inicial DATE,

    -- Registro seccional
    registro_seccional_codigo INTEGER,
    registro_seccional_descripcion VARCHAR(200),
    registro_seccional_provincia VARCHAR(100),

    -- Datos del automotor
    automotor_origen VARCHAR(50),
    automotor_anio_modelo INTEGER,
    automotor_tipo_codigo VARCHAR(10),
    automotor_tipo_descripcion VARCHAR(100),
    automotor_marca_codigo VARCHAR(10),
    automotor_marca_descripcion VARCHAR(100),
    automotor_modelo_codigo VARCHAR(20),
    automotor_modelo_descripcion VARCHAR(200),
    automotor_uso_codigo VARCHAR(10),
    automotor_uso_descripcion VARCHAR(50),

    -- Datos del titular
    titular_tipo_persona VARCHAR(50),
    titular_domicilio_localidad VARCHAR(200),
    titular_domicilio_provincia VARCHAR(100),
    titular_genero VARCHAR(50),
    titular_anio_nacimiento INTEGER,
    titular_pais_nacimiento VARCHAR(100),
    titular_porcentaje_titularidad NUMERIC(5,2),
    titular_domicilio_provincia_id VARCHAR(10),
    titular_pais_nacimiento_id VARCHAR(10),

    -- Metadata
    archivo_origen VARCHAR(200),
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: REGISTROS SECCIONALES (CATÁLOGO/MAESTRO)
-- Catálogo de oficinas de registro automotor
-- ============================================================================
CREATE TABLE datos_gob_registros_seccionales (
    id SERIAL PRIMARY KEY,

    -- Datos del registro
    competencia VARCHAR(50),
    codigo INTEGER UNIQUE,
    denominacion VARCHAR(200),

    -- Encargado
    encargado VARCHAR(200),
    encargado_cuit VARCHAR(20),

    -- Ubicación
    domicilio VARCHAR(300),
    localidad VARCHAR(200),
    provincia_nombre VARCHAR(100),
    provincia_letra VARCHAR(5),
    codigo_postal VARCHAR(20),
    provincia_id VARCHAR(10),

    -- Contacto
    telefono VARCHAR(100),
    horario_atencion VARCHAR(100),

    -- Metadata
    archivo_origen VARCHAR(200),
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP
);

-- ============================================================================
-- ÍNDICES PARA MEJORAR PERFORMANCE
-- ============================================================================

-- Inscripciones
CREATE INDEX idx_inscripciones_fecha ON datos_gob_inscripciones(tramite_fecha);
CREATE INDEX idx_inscripciones_provincia ON datos_gob_inscripciones(registro_seccional_provincia);
CREATE INDEX idx_inscripciones_marca ON datos_gob_inscripciones(automotor_marca_descripcion);
CREATE INDEX idx_inscripciones_anio ON datos_gob_inscripciones(automotor_anio_modelo);
CREATE INDEX idx_inscripciones_fecha_provincia ON datos_gob_inscripciones(tramite_fecha, registro_seccional_provincia);

-- Transferencias
CREATE INDEX idx_transferencias_fecha ON datos_gob_transferencias(tramite_fecha);
CREATE INDEX idx_transferencias_provincia ON datos_gob_transferencias(registro_seccional_provincia);
CREATE INDEX idx_transferencias_marca ON datos_gob_transferencias(automotor_marca_descripcion);
CREATE INDEX idx_transferencias_anio ON datos_gob_transferencias(automotor_anio_modelo);
CREATE INDEX idx_transferencias_fecha_provincia ON datos_gob_transferencias(tramite_fecha, registro_seccional_provincia);

-- Prendas
CREATE INDEX idx_prendas_fecha ON datos_gob_prendas(tramite_fecha);
CREATE INDEX idx_prendas_provincia ON datos_gob_prendas(registro_seccional_provincia);
CREATE INDEX idx_prendas_marca ON datos_gob_prendas(automotor_marca_descripcion);
CREATE INDEX idx_prendas_anio ON datos_gob_prendas(automotor_anio_modelo);
CREATE INDEX idx_prendas_fecha_provincia ON datos_gob_prendas(tramite_fecha, registro_seccional_provincia);

-- Registros Seccionales
CREATE INDEX idx_seccionales_codigo ON datos_gob_registros_seccionales(codigo);
CREATE INDEX idx_seccionales_provincia ON datos_gob_registros_seccionales(provincia_nombre);
CREATE INDEX idx_seccionales_localidad ON datos_gob_registros_seccionales(localidad);

-- ============================================================================
-- COMENTARIOS EN TABLAS
-- ============================================================================

COMMENT ON TABLE datos_gob_inscripciones IS 'Inscripciones iniciales de automotores (0km) - Fuente: datos.gob.ar/DNRPA';
COMMENT ON TABLE datos_gob_transferencias IS 'Transferencias de automotores usados - Fuente: datos.gob.ar/DNRPA';
COMMENT ON TABLE datos_gob_prendas IS 'Prendas sobre automotores - Fuente: datos.gob.ar/DNRPA';
COMMENT ON TABLE datos_gob_registros_seccionales IS 'Catálogo de registros seccionales automotor - Fuente: datos.gob.ar/DNRPA';

-- ============================================================================
-- LISTO!
-- ============================================================================
