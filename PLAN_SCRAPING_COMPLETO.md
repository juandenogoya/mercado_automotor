# 📋 Plan Completo - Scraping DNRPA

## 🎯 Objetivo
Obtener datos históricos de patentamientos de DNRPA en dos niveles:
1. **Provincial** (resumen por provincia)
2. **Seccional** (detalle por registro seccional)

---

## 📊 Estructura de Datos

### Nivel 1: Provincial (Agregado)
```
Año → Provincia → [Ene, Feb, Mar, ..., Dic, Total]
```

**Ejemplo:**
- 2024 → Buenos Aires → [10237, 7366, 7204, ..., 102680]
- 2023 → Buenos Aires → [9845, 7123, 6987, ..., 98234]

### Nivel 2: Seccional (Detalle)
```
Año → Provincia → Seccional → [Ene, Feb, Mar, ..., Dic, Total]
```

**Ejemplo:**
- 2024 → Buenos Aires → La Plata → [1234, 1123, 1089, ..., 13567]
- 2024 → Buenos Aires → San Isidro → [987, 876, 845, ..., 10234]

---

## 🗄️ Diseño Base de Datos

### Tabla: `provincias`
```sql
id               SERIAL PRIMARY KEY
codigo           VARCHAR(2)      -- Código DNRPA (ej: "01")
nombre           VARCHAR(100)    -- Nombre provincia
activa           BOOLEAN         -- Si sigue activa
fecha_alta       DATE            -- Cuándo apareció
fecha_baja       DATE NULL       -- Cuándo dejó de existir (si aplica)
```

### Tabla: `seccionales`
```sql
id               SERIAL PRIMARY KEY
provincia_id     INTEGER         -- FK a provincias
codigo           VARCHAR(10)     -- Código seccional
nombre           VARCHAR(100)    -- Nombre seccional
activa           BOOLEAN         -- Si sigue activa
fecha_alta       DATE            -- Cuándo apareció
fecha_baja       DATE NULL       -- Cuándo dejó de existir
```

### Tabla: `patentamientos_provincial`
```sql
id               SERIAL PRIMARY KEY
provincia_id     INTEGER         -- FK a provincias
anio             INTEGER         -- Año (2015-2024)
mes              INTEGER         -- Mes (1-12)
cantidad         INTEGER         -- Cantidad de patentamientos
tipo_vehiculo    VARCHAR(20)     -- 'autos', 'motos', etc.
tipo_tramite     VARCHAR(20)     -- 'inscripcion', 'transferencia', etc.
fecha_scraping   TIMESTAMP       -- Cuándo se scrapeó
```

### Tabla: `patentamientos_seccional`
```sql
id               SERIAL PRIMARY KEY
seccional_id     INTEGER         -- FK a seccionales
anio             INTEGER         -- Año
mes              INTEGER         -- Mes (1-12)
cantidad         INTEGER         -- Cantidad de patentamientos
tipo_vehiculo    VARCHAR(20)     -- 'autos', 'motos', etc.
tipo_tramite     VARCHAR(20)     -- 'inscripcion', 'transferencia', etc.
fecha_scraping   TIMESTAMP       -- Cuándo se scrapeó
```

---

## 🚀 Scripts a Crear

### 1. `scraping_provincial_historico.py` ✅ PARCIALMENTE HECHO
- Scrapea datos provinciales para múltiples años
- Parámetros: año_inicio, año_fin, tipo_vehiculo
- Salida: `patentamientos_provincial_2015_2024.xlsx`

### 2. `scraping_seccional.py` ⏳ PENDIENTE
- Scrapea datos por seccional de cada provincia
- Para cada provincia, obtiene sus seccionales
- Parámetros: año, provincia (o todas)
- Salida: `patentamientos_seccional_PROVINCIA_AÑO.xlsx`

### 3. `scraping_seccional_historico.py` ⏳ PENDIENTE
- Combina scraping de todas las provincias y años
- Loop: años → provincias → seccionales
- Salida: `patentamientos_seccional_historico.xlsx`

### 4. `cargar_datos_postgresql.py` ⏳ PENDIENTE
- Lee archivos Excel generados
- Carga a PostgreSQL con manejo de duplicados
- Actualiza solo datos nuevos/modificados

---

## 📅 Orden de Ejecución

### Fase 1: Datos Provinciales (1-2 días)
```bash
# 1. Scrapear histórico provincial (2015-2024)
python scraping_provincial_historico.py --anio-inicio 2015 --anio-fin 2024

# 2. Verificar datos generados
# Revisar archivo: patentamientos_provincial_2015_2024.xlsx

# 3. Cargar a PostgreSQL
python cargar_datos_postgresql.py --tipo provincial
```

### Fase 2: Datos Seccionales (3-5 días)
```bash
# 1. Scrapear seccionales de un año primero (prueba)
python scraping_seccional.py --anio 2024

# 2. Verificar estructura y datos
# Revisar archivos generados por provincia

# 3. Si funciona, scrapear histórico completo
python scraping_seccional_historico.py --anio-inicio 2020 --anio-fin 2024

# 4. Cargar a PostgreSQL
python cargar_datos_postgresql.py --tipo seccional
```

### Fase 3: Dashboard (1 día)
```bash
# 1. Actualizar dashboard Streamlit
# Agregar visualizaciones de datos provinciales y seccionales

# 2. Agregar filtros por:
#    - Año
#    - Provincia
#    - Seccional
#    - Tipo de vehículo
```

---

## ⚠️ Consideraciones Importantes

### Rate Limiting
- **Esperar entre requests**: 2-3 segundos
- **Evitar bloqueos**: No más de 100 requests/hora
- **Ejecutar de noche**: Menos carga en servidor DNRPA

### Manejo de Errores
- **Reintentos**: 3 intentos con backoff exponencial
- **Checkpoint**: Guardar progreso cada 10 provincias/años
- **Logs detallados**: Registrar qué se scrapeó y cuándo

### Datos Históricos
- **Años disponibles**: Verificar desde qué año hay datos en DNRPA
- **Cambios de estructura**: La tabla HTML puede cambiar entre años
- **Seccionales desaparecidos**: Algunos pueden no existir en años viejos

### Validación de Datos
- **Verificar totales**: Suma de seccionales = total provincial
- **Detectar anomalías**: Cambios drásticos año a año
- **Comparar con fuentes**: Contrastar con INDEC, ACARA

---

## 📝 Próximos Pasos Inmediatos

1. ✅ **Verificar datos 2024**: Confirmar que Excel tiene datos correctos
2. ⏳ **Crear script histórico provincial**: Scrapear 2015-2024
3. ⏳ **Probar scraping seccional**: Un año, una provincia primero
4. ⏳ **Diseñar esquema BD**: Crear tablas en PostgreSQL
5. ⏳ **Crear script de carga**: Migrar Excel → PostgreSQL

---

## 🎯 Decisiones Pendientes

- [ ] ¿Desde qué año scrapear datos históricos? (¿2015? ¿2010?)
- [ ] ¿Scrapear todos los tipos de vehículos? (autos, motos, camiones, etc.)
- [ ] ¿Scrapear todos los tipos de trámite? (inscripciones, transferencias, etc.)
- [ ] ¿Actualización automática? (mensual, semanal)
- [ ] ¿Deploy en cloud o ejecución local permanente?

---

**Última actualización:** 2025-11-08
