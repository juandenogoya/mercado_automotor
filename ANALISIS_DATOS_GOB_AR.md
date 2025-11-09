# 📊 ANÁLISIS DE DATOS - datos.gob.ar

## 🎯 Datos Disponibles en PostgreSQL

**Total: 13,599,300 registros**

| Tabla | Registros | Período | Provincias |
|-------|-----------|---------|------------|
| `datos_gob_inscripciones` | 2,970,063 | 2019-2025 | 26 |
| `datos_gob_transferencias` | 8,834,929 | 2020-2025 | 26 |
| `datos_gob_prendas` | 1,793,747 | 2019-2025 | 26 |
| `datos_gob_registros_seccionales` | 1,561 | Catálogo | 26 |

---

## 📋 Columnas Disponibles

### Por Trámite (Inscripciones, Transferencias, Prendas):
- **Trámite**: tipo, fecha, fecha_inscripcion_inicial
- **Registro Seccional**: codigo, descripcion, provincia
- **Automotor**: origen, anio_modelo, tipo, marca, modelo, uso
- **Titular**: tipo_persona, domicilio (localidad, provincia), genero, anio_nacimiento, pais_nacimiento

### Registros Seccionales (Catálogo):
- codigo, denominacion, encargado, domicilio, localidad, provincia, telefono, horario

---

## 🔍 Queries Útiles

### 1. Top 10 Marcas más Patentadas (0km)

```sql
SELECT
    automotor_marca_descripcion AS marca,
    COUNT(*) AS cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS porcentaje
FROM datos_gob_inscripciones
WHERE tramite_tipo LIKE '%0 KM%' OR tramite_tipo LIKE '%INICIAL%'
GROUP BY automotor_marca_descripcion
ORDER BY cantidad DESC
LIMIT 10;
```

### 2. Evolución Mensual de Patentamientos (Último Año)

```sql
SELECT
    DATE_TRUNC('month', tramite_fecha) AS mes,
    COUNT(*) AS patentamientos
FROM datos_gob_inscripciones
WHERE tramite_fecha >= '2024-01-01'
GROUP BY mes
ORDER BY mes;
```

### 3. Top Provincias por Patentamientos

```sql
SELECT
    registro_seccional_provincia AS provincia,
    COUNT(*) AS total_patentamientos,
    COUNT(CASE WHEN tramite_fecha >= '2024-01-01' THEN 1 END) AS patentamientos_2024
FROM datos_gob_inscripciones
GROUP BY provincia
ORDER BY total_patentamientos DESC
LIMIT 10;
```

### 4. Modelos Más Populares por Marca

```sql
SELECT
    automotor_marca_descripcion AS marca,
    automotor_modelo_descripcion AS modelo,
    COUNT(*) AS cantidad
FROM datos_gob_inscripciones
WHERE automotor_marca_descripcion IN ('TOYOTA', 'FORD', 'VOLKSWAGEN', 'CHEVROLET', 'FIAT')
  AND tramite_fecha >= '2024-01-01'
GROUP BY marca, modelo
ORDER BY marca, cantidad DESC;
```

### 5. Análisis de Género de Compradores (Personas Físicas)

```sql
SELECT
    titular_genero AS genero,
    COUNT(*) AS cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS porcentaje
FROM datos_gob_inscripciones
WHERE titular_tipo_persona = 'Física'
  AND titular_genero != 'No aplica'
  AND titular_genero != ''
GROUP BY genero
ORDER BY cantidad DESC;
```

### 6. Vehículos Importados vs Nacionales

```sql
SELECT
    automotor_origen,
    COUNT(*) AS cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS porcentaje
FROM datos_gob_inscripciones
WHERE tramite_fecha >= '2024-01-01'
GROUP BY automotor_origen
ORDER BY cantidad DESC;
```

### 7. Transferencias vs Patentamientos 0km (Comparación)

```sql
SELECT
    DATE_TRUNC('month', tramite_fecha) AS mes,
    'Inscripciones (0km)' AS tipo,
    COUNT(*) AS cantidad
FROM datos_gob_inscripciones
WHERE tramite_fecha >= '2024-01-01'
GROUP BY mes

UNION ALL

SELECT
    DATE_TRUNC('month', tramite_fecha) AS mes,
    'Transferencias (usados)' AS tipo,
    COUNT(*) AS cantidad
FROM datos_gob_transferencias
WHERE tramite_fecha >= '2024-01-01'
GROUP BY mes

ORDER BY mes, tipo;
```

### 8. Ranking de Registros Seccionales por Volumen

```sql
SELECT
    i.registro_seccional_descripcion,
    i.registro_seccional_provincia,
    COUNT(*) AS total_tramites
FROM datos_gob_inscripciones i
WHERE tramite_fecha >= '2024-01-01'
GROUP BY i.registro_seccional_descripcion, i.registro_seccional_provincia
ORDER BY total_tramites DESC
LIMIT 20;
```

### 9. Edad Promedio de Compradores por Marca

```sql
SELECT
    automotor_marca_descripcion AS marca,
    ROUND(AVG(2025 - titular_anio_nacimiento)) AS edad_promedio,
    COUNT(*) AS cantidad_compradores
FROM datos_gob_inscripciones
WHERE titular_tipo_persona = 'Física'
  AND titular_anio_nacimiento > 1940
  AND titular_anio_nacimiento < 2007
  AND tramite_fecha >= '2024-01-01'
GROUP BY marca
HAVING COUNT(*) > 100
ORDER BY edad_promedio DESC
LIMIT 15;
```

### 10. Prendas: Marcas con Mayor Financiamiento

```sql
SELECT
    automotor_marca_descripcion AS marca,
    COUNT(*) AS vehiculos_prendados,
    ROUND(COUNT(*) * 100.0 /
          (SELECT COUNT(*) FROM datos_gob_inscripciones i2
           WHERE i2.automotor_marca_descripcion = p.automotor_marca_descripcion), 2) AS porcentaje_financiado
FROM datos_gob_prendas p
WHERE tramite_fecha >= '2024-01-01'
GROUP BY marca
ORDER BY vehiculos_prendados DESC
LIMIT 10;
```

---

## 📈 Análisis Posibles

### 1. **Tendencias de Mercado**
- Evolución temporal de patentamientos
- Estacionalidad (mejores/peores meses)
- Crecimiento/caída por marca

### 2. **Análisis Geográfico**
- Distribución de ventas por provincia
- Preferencias de marca por región
- Densidad de registros seccionales

### 3. **Perfil de Compradores**
- Edad promedio por marca/modelo
- Género predominante
- Persona física vs jurídica

### 4. **Mercado de Usados**
- Volumen de transferencias vs 0km
- Marcas más transaccionadas
- Análisis temporal

### 5. **Financiamiento**
- Porcentaje de vehículos prendados
- Marcas con mayor financiamiento
- Evolución del crédito automotor

### 6. **Market Share**
- Participación de mercado por marca
- Evolución trimestral/anual
- Top modelos por segmento

---

## 🎯 Próximos Pasos

1. **Dashboard Interactivo**
   - Visualizaciones con Streamlit
   - Gráficos de evolución temporal
   - Mapas geográficos

2. **Reportes Automáticos**
   - Resumen mensual del mercado
   - Alertas de cambios significativos
   - KPIs clave

3. **Predicciones**
   - Forecast de ventas
   - Tendencias de marcas
   - Estacionalidad

4. **Integraciones**
   - Combinar con datos de MercadoLibre (precios)
   - Cruzar con datos económicos (INDEC)
   - Análisis de correlaciones

---

## ⚠️ Consideraciones

**Performance:**
- Usar índices para queries frecuentes
- Agregar filtros de fecha siempre que sea posible
- Materializar vistas para cálculos complejos

**Límites:**
- 13.6M de registros = queries pueden tardar
- Usar LIMIT en exploraciones
- Agregar WHERE para reducir dataset

