# 📚 Guía: Cómo Buscar IDs Correctos de Series en datos.gob.ar

Esta guía te ayudará a encontrar los IDs correctos para las series de datos económicos de Argentina.

## 🎯 ¿Por qué necesito hacer esto?

Algunos IDs de series de la API de datos.gob.ar cambian con el tiempo o se actualizan. Cuando ves errores como:

```
400 Client Error: Bad Request for url: https://apis.datos.gob.ar/series/api/series/?ids=133.2_OFABAUT_DICI_M_42
```

Significa que el ID `133.2_OFABAUT_DICI_M_42` ya no es válido o cambió.

---

## 🔍 Método 1: Portal de Datos Argentina (Recomendado)

### Paso 1: Ir al catálogo de datos
```
https://datos.gob.ar/dataset
```

### Paso 2: Buscar el indicador
En la barra de búsqueda, escribir palabras clave relacionadas con lo que buscás:

**Para IPI Automotriz:**
- `IPI automotriz`
- `producción industrial automotriz`
- `industria automotriz`
- `fabricación vehículos`

**Para Empleo:**
- `empleo registrado`
- `trabajadores registrados privado`
- `ITCRP`

**Para Construcción:**
- `ISAC`
- `índice sintético actividad construcción`

**Para Ventas:**
- `ventas supermercados`
- `comercio minorista`

### Paso 3: Abrir el dataset correcto
Buscar datasets que digan:
- **Fuente:** INDEC
- **Publicador:** Subsecretaría de Programación Macroeconómica
- Que tengan el logo de "Series de Tiempo"

### Paso 4: Encontrar el ID
Una vez en la página del dataset:

1. Buscar la sección **"Recursos"** o **"Distribuciones"**
2. Buscar el link que dice **"API"** o **"Series de Tiempo"**
3. Click en **"Ver más"** o **"Detalles"**
4. Copiar el **ID de la serie** (formato: `XXX.X_XXXXXX_XXXX_X_XX`)

**Ejemplo de ID válido:**
```
148.3_INIVELNAL_DICI_M_26  ← IPC Nacional (este funciona)
```

---

## 🔍 Método 2: API de Búsqueda (Más técnico)

### Buscar directamente con la API

Abrir en el navegador o usar `curl`:

**Buscar IPI Automotriz:**
```
https://apis.datos.gob.ar/series/api/search/?q=automotriz&format=json
```

**Buscar Empleo:**
```
https://apis.datos.gob.ar/series/api/search/?q=empleo+registrado&format=json
```

**Buscar Construcción:**
```
https://apis.datos.gob.ar/series/api/search/?q=ISAC&format=json
```

**Buscar Ventas:**
```
https://apis.datos.gob.ar/series/api/search/?q=ventas+supermercados&format=json
```

### Interpretar el resultado

El JSON retornará algo como:

```json
{
  "data": [
    {
      "id": "133.2_OFABAUT_DICI_M_42",
      "description": "Índice de Producción Industrial - Automotriz",
      "source": "INDEC",
      ...
    }
  ]
}
```

Copiar el campo `"id"` que sea más relevante.

---

## 🔍 Método 3: Explorador de Series (Herramienta visual)

### Usar el explorador web

```
https://datos.gob.ar/series/
```

1. Escribir palabras clave en el buscador
2. Seleccionar las series que te interesen
3. Click en **"API"** para ver el ID

---

## 📝 ¿Cómo usar el ID encontrado?

### Paso 1: Abrir el archivo de configuración

```bash
backend/api_clients/indec_client.py
```

### Paso 2: Buscar la sección SERIES_IDS (línea ~57)

```python
SERIES_IDS = {
    # IPC - funciona ✅
    'ipc_nacional': '148.3_INIVELNAL_DICI_M_26',

    # IPI Automotriz - comentado ⚠️
    # 'ipi_automotriz': '133.2_OFABAUT_DICI_M_42',  # ERROR 400
}
```

### Paso 3: Actualizar con el ID correcto

Reemplazar el ID viejo por el nuevo que encontraste:

```python
SERIES_IDS = {
    # IPI Automotriz - ACTUALIZADO ✅
    'ipi_automotriz': 'NUEVO_ID_AQUI',  # Reemplazar NUEVO_ID_AQUI
}
```

### Paso 4: Descomentar la línea

Quitar el `#` al principio:

```python
SERIES_IDS = {
    # IPI Automotriz - ACTUALIZADO ✅
    'ipi_automotriz': '133.2_NUEVO_ID_REAL_12',  # ← Ahora activo
}
```

### Paso 5: Verificar que funciona

Ejecutar el script de carga:

```bash
python cargar_datos_inteligente.py
```

O el script específico de automotrices:

```bash
python cargar_datos_automotrices.py
```

---

## 🎯 Lista de IDs que necesitan verificación

Estas son las series que actualmente están deshabilitadas y necesitan IDs actualizados:

| Indicador | Nombre Completo | ID Viejo (no funciona) | ID Nuevo (a buscar) |
|-----------|----------------|----------------------|-------------------|
| **IPI Automotriz** | Índice Producción Industrial - Automotriz | `133.2_OFABAUT_DICI_M_42` | ❓ Buscar |
| **Empleo Privado** | Índice Trabajadores Registrados Privado | `11.5_ITCRP_0_M_21` | ❓ Buscar |
| **Ventas Supermercados** | Ventas en Supermercados | `134.3_IVSMSTO_DICI_M_13` | ❓ Buscar |
| **ISAC** | Índice Sintético Actividad Construcción | `137.2_ISBISTOD_DICI_M_16` | ❓ Buscar |
| **Salarios** | Índice de Salarios | `11.3_ISAC_0_M_18` | ❓ Buscar |

---

## 🧪 Probar un ID antes de agregarlo

Antes de actualizar el código, podés probar el ID directamente en el navegador:

```
https://apis.datos.gob.ar/series/api/series/?ids=TU_ID_AQUI&format=json
```

**Si funciona:** Verás datos JSON
**Si no funciona:** Verás error 400 o 404

---

## 💡 Recursos Adicionales

- **Documentación oficial:** https://datosgobar.github.io/series-tiempo-ar-api/
- **GitHub del proyecto:** https://github.com/datosgobar/series-tiempo-ar-api
- **Catálogo de datos:** https://datos.gob.ar/dataset
- **Buscador de series:** https://datos.gob.ar/series/

---

## ❓ Problemas Comunes

### "No encuentro el dataset"
- Probar con diferentes palabras clave
- Buscar directamente en Google: `site:datos.gob.ar IPI automotriz`
- Verificar en la página del INDEC: https://www.indec.gob.ar/

### "El ID no funciona"
- Asegurarse de copiar el ID completo
- No incluir espacios ni comillas
- Verificar que sea para la API de Series de Tiempo

### "Error 403 Forbidden"
- Puede ser geoblocking (estás fuera de Argentina)
- Probar con VPN argentina
- Intentar desde una red diferente

---

## ✅ Checklist Final

- [ ] Busqué el indicador en datos.gob.ar
- [ ] Encontré el ID correcto
- [ ] Lo probé en el navegador (retorna JSON sin error)
- [ ] Actualicé `backend/api_clients/indec_client.py`
- [ ] Descomente la línea del ID
- [ ] Ejecuté el script de carga
- [ ] Verifiqué que los datos se guardaron en la base de datos
- [ ] Revisé el dashboard de Streamlit

---

**¿Necesitás ayuda adicional?**

Si después de seguir esta guía aún tenés problemas:
1. Verificar logs de error detallados
2. Revisar documentación oficial de la API
3. Contactar soporte de datos.gob.ar
