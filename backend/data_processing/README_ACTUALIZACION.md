# 🔄 Sistema de Actualización Automática de Datos Externos

Sistema para mantener actualizados los datos de **BCRA** e **INDEC** de forma eficiente y automática.

---

## 📋 Descripción General

Este sistema implementa **actualización incremental** de datos, descargando solo información nueva en lugar de recargar todo desde 2019 cada vez.

### ✨ Características

- ✅ **Actualización incremental** por defecto (solo datos nuevos)
- ✅ **Detección automática** de última fecha descargada
- ✅ **Ejecución automática** al iniciar el dashboard (.bat)
- ✅ **Opción de recarga completa** cuando sea necesario
- ✅ **Manejo de errores** por fuente (si una falla, continúa con la otra)
- ✅ **Reportes detallados** de actualización

---

## 📁 Archivos del Sistema

### Scripts Incrementales

1. **`04_obtener_datos_bcra_incremental.py`**
   - Actualiza datos del BCRA
   - Variables: IPC, USD, BADLAR, LELIQ, Reservas, etc.
   - Detecta última fecha en `bcra_datos_diarios.parquet`
   - Descarga solo desde esa fecha en adelante

2. **`05_obtener_datos_indec_incremental.py`**
   - Actualiza datos de INDEC
   - Series: EMAE, Desocupación, Actividad, Empleo, RIPTE
   - Detecta última fecha en `indec_datos_originales.parquet`
   - Descarga últimos 3 meses para asegurar datos trimestrales completos

### Script Maestro

3. **`actualizar_datos_externos.py`**
   - Orquesta la actualización de ambas fuentes
   - Ejecuta scripts incrementales en secuencia
   - Reporta resumen de actualización

### Scripts Originales (mantienen funcionalidad completa)

4. **`04_obtener_datos_bcra_v2.py`** - Descarga completa BCRA (desde 2019)
5. **`05_obtener_datos_indec.py`** - Descarga completa INDEC (desde 2019)

---

## 🚀 Uso del Sistema

### Opción A: Automático al iniciar Dashboard (Recomendado)

Simplemente ejecuta el archivo `.bat` como siempre:

```cmd
Iniciar_Dashboard_Mercado_Automotor.bat
```

El sistema automáticamente:
1. Verifica si hay datos nuevos en BCRA e INDEC
2. Descarga solo lo nuevo
3. Actualiza los archivos Parquet
4. Inicia Streamlit y ngrok

**Tiempo estimado:** 10-30 segundos (vs. 2-3 minutos con descarga completa)

---

### Opción B: Ejecutar Manualmente

#### 1️⃣ Actualización incremental normal (recomendado)

```powershell
# Desde: mercado_automotor/
python backend/data_processing/actualizar_datos_externos.py
```

Descarga solo datos nuevos desde la última actualización.

#### 2️⃣ Recarga completa desde 2019

```powershell
# Desde: mercado_automotor/
python backend/data_processing/actualizar_datos_externos.py --full-refresh
```

Útil si:
- Es la primera vez que ejecutas el script
- Los archivos Parquet se corrompieron
- Quieres verificar consistencia de datos

#### 3️⃣ Actualizar solo BCRA

```powershell
python backend/data_processing/actualizar_datos_externos.py --solo-bcra
```

#### 4️⃣ Actualizar solo INDEC

```powershell
python backend/data_processing/actualizar_datos_externos.py --solo-indec
```

---

## 🔍 Cómo Funciona el Sistema Incremental

### BCRA (Datos Diarios)

1. **Lee** `bcra_datos_diarios.parquet`
2. **Detecta** última fecha disponible (ej: `2025-11-10`)
3. **Descarga** solo desde `2025-11-11` hasta hoy
4. **Combina** datos existentes + nuevos
5. **Elimina** duplicados (si los hay)
6. **Recalcula** agregación mensual sobre todos los datos

```
Antes: Descargar 2019-01-01 → 2025-11-12 (7 años de datos)
Ahora: Descargar 2025-11-11 → 2025-11-12 (2 días de datos)
```

### INDEC (Datos Mensuales/Trimestrales)

1. **Lee** `indec_datos_originales.parquet`
2. **Detecta** última fecha disponible (ej: `2025-10-01`)
3. **Retrocede 3 meses** para asegurar datos trimestrales completos
4. **Descarga** desde `2025-07-01` hasta hoy
5. **Combina** datos existentes + nuevos
6. **Recalcula** interpolación mensual sobre todos los datos

```
Antes: Descargar 2019-01-01 → 2025-11-12 (7 años de datos)
Ahora: Descargar 2025-07-01 → 2025-11-12 (4 meses de datos)
```

---

## 📊 Archivos Generados

Todos los archivos se guardan en: `data/processed/`

| Archivo | Descripción | Actualización |
|---------|-------------|---------------|
| `bcra_datos_diarios.parquet` | Datos BCRA diarios (11 variables) | Incremental |
| `bcra_datos_mensuales.parquet` | Datos BCRA agregados mensualmente | Recalculado |
| `indec_datos_originales.parquet` | Datos INDEC sin interpolar | Incremental |
| `indec_datos_mensuales.parquet` | Datos INDEC interpolados mensualmente | Recalculado |

---

## ⏰ Frecuencia de Actualización Recomendada

### Datos BCRA
- **Frecuencia:** Mensual
- **Mejor momento:** Primeros 5 días hábiles del mes
- **Motivo:** IPC se publica entre el 13 y 15 de cada mes para el mes anterior

### Datos INDEC
- **Frecuencia:** Mensual
- **Mejor momento:** Primera semana del mes
- **Motivo:**
  - EMAE: Publicado ~40 días después del mes de referencia
  - EPH (laboral): Publicado trimestralmente (~3 meses de retraso)

### Ejecución Automática
Si usas el `.bat`, los datos se actualizan **cada vez que abres el dashboard**.

---

## 🛠️ Mantenimiento

### Primera ejecución
Si es tu primera vez ejecutando los scripts incrementales:

```powershell
# Esto descargará todo desde 2019
python backend/data_processing/actualizar_datos_externos.py
```

### Problemas comunes

#### ❌ Error: "No se encontraron archivos Parquet"
**Solución:** Es normal la primera vez. El script descargará todo automáticamente.

#### ❌ Error: "Error de conexión"
**Solución:**
1. Verificar conexión a internet
2. Las APIs pueden estar temporalmente caídas
3. Reintentar en unos minutos

#### ❌ Datos desactualizados o corruptos
**Solución:** Ejecutar con `--full-refresh`:

```powershell
python backend/data_processing/actualizar_datos_externos.py --full-refresh
```

---

## 📝 Logs y Reportes

El script muestra información detallada durante la ejecución:

```
================================================================================
  ACTUALIZACIÓN DE DATOS EXTERNOS - BCRA E INDEC
================================================================================
  Fecha: 2025-11-12 09:30:00
  Modo: INCREMENTAL
================================================================================

================================================================================
  ACTUALIZANDO: BCRA
================================================================================

📅 Modo INCREMENTAL:
   - Última fecha en archivo: 2025-11-10
   - Descargando desde: 2025-11-11
   - Hasta: 2025-11-12

📋 Variables a descargar: 11
🔄 Iniciando descarga...

✓ Descarga completada
   - Registros nuevos: 2

💾 Guardando datos diarios...
   - Registros existentes: 2,450
   - Registros nuevos: 2
   - Total final: 2,452
   ✓ Archivo guardado: data/processed/bcra_datos_diarios.parquet
   ✓ Tamaño: 0.18 MB

================================================================================
  RESUMEN DE ACTUALIZACIÓN
================================================================================

  📊 Fuentes procesadas: 2
  ✅ Exitosas: 2
  ❌ Fallidas: 0

  🎉 TODAS LAS ACTUALIZACIONES COMPLETADAS EXITOSAMENTE
```

---

## 🔄 Integración con .bat

El archivo `Iniciar_Dashboard_Mercado_Automotor.bat` fue modificado para incluir:

1. **Paso 1/4:** Actualización de datos (NUEVO)
2. **Paso 2/4:** Inicio de Streamlit
3. **Paso 3/4:** Inicio de ngrok
4. **Paso 4/4:** Confirmación

Si la actualización falla, el dashboard **continúa** con los datos existentes.

---

## 💡 Próximos Pasos

Para el futuro, podrías implementar:

1. **Actualización programada** (cron job / Task Scheduler)
2. **Notificaciones** cuando hay datos nuevos
3. **Dashboard de monitoreo** de actualización
4. **Validación automática** de calidad de datos

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs de ejecución
2. Verifica que los archivos Parquet existan en `data/processed/`
3. Prueba con `--full-refresh` si hay inconsistencias
4. Verifica conectividad a internet y acceso a APIs

---

**Última actualización:** 2025-11-12
**Versión:** 1.0
