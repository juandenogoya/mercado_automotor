"""
ETL para cargar datos históricos de SIOGRANOS a PostgreSQL
============================================================================
Objetivo: Cargar operaciones desde 2020-01-01 hasta hoy
Estrategia: Carga incremental por chunks de 7 días para evitar timeouts
============================================================================
"""

import os
import sys
import time
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

from siogranos_codigos import PRODUCTOS, PROVINCIAS, MONEDAS

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

load_dotenv()

# URLs de API
SIOGRANOS_API_URL = os.getenv(
    'SIOGRANOS_API_URL',
    'https://test.bc.org.ar/SiogranosAPI/api/ConsultaPublica/consultarOperaciones'
)

# Configuración de chunking
CHUNK_DAYS = 7  # Procesar 7 días a la vez (1 semana)
MAX_RETRIES = 4  # Reintentos máximos por chunk
RETRY_DELAY_BASE = 2  # Segundos base para backoff exponencial
REQUEST_TIMEOUT = 60  # Timeout por request en segundos

# Período objetivo
FECHA_INICIO = datetime(2020, 1, 1)
FECHA_FIN = datetime.now()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_siogranos.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# MODELOS
# ============================================================================

@dataclass
class ChunkResult:
    """Resultado del procesamiento de un chunk"""
    fecha_desde: datetime
    fecha_hasta: datetime
    registros_procesados: int
    registros_insertados: int
    registros_duplicados: int
    registros_error: int
    success: bool
    error_message: Optional[str] = None
    duracion_segundos: float = 0


# ============================================================================
# FUNCIONES DE API
# ============================================================================

def fetch_operaciones_con_reintentos(
    fecha_desde: str,
    fecha_hasta: str,
    max_retries: int = MAX_RETRIES
) -> Optional[List[Dict]]:
    """
    Consulta la API de SIOGRANOS con reintentos exponenciales

    Args:
        fecha_desde: Fecha inicio formato 'YYYY-MM-DD'
        fecha_hasta: Fecha fin formato 'YYYY-MM-DD'
        max_retries: Número máximo de reintentos

    Returns:
        Lista de operaciones o None si falló
    """
    params = {
        'FechaOperacionDesde': fecha_desde,
        'FechaOperacionHasta': fecha_hasta
    }

    for intento in range(max_retries):
        try:
            logger.info(f"📡 Consultando API: {fecha_desde} a {fecha_hasta} (intento {intento + 1}/{max_retries})")

            response = requests.get(
                SIOGRANOS_API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                json_response = response.json()

                # Extraer operaciones según estructura de respuesta
                if isinstance(json_response, dict):
                    if 'result' in json_response and 'operaciones' in json_response['result']:
                        operaciones = json_response['result']['operaciones']
                    elif 'operaciones' in json_response:
                        operaciones = json_response['operaciones']
                    else:
                        operaciones = []
                elif isinstance(json_response, list):
                    operaciones = json_response
                else:
                    logger.warning(f"⚠️ Estructura de respuesta inesperada: {type(json_response)}")
                    operaciones = []

                logger.info(f"✅ Respuesta exitosa: {len(operaciones)} operaciones")
                return operaciones

            elif response.status_code == 404:
                logger.error(f"❌ Error 404: Endpoint no encontrado")
                return None

            elif response.status_code == 400:
                logger.error(f"❌ Error 400: Parámetros incorrectos - {response.text}")
                return None

            else:
                logger.warning(f"⚠️ Status {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout en intento {intento + 1}/{max_retries}")

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"🔌 Error de conexión en intento {intento + 1}/{max_retries}: {e}")

        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")

        # Backoff exponencial antes de reintentar
        if intento < max_retries - 1:
            delay = RETRY_DELAY_BASE ** (intento + 1)
            logger.info(f"⏳ Esperando {delay}s antes de reintentar...")
            time.sleep(delay)

    logger.error(f"❌ Falló después de {max_retries} intentos")
    return None


# ============================================================================
# FUNCIONES DE TRANSFORMACIÓN
# ============================================================================

def calcular_hash_registro(operacion: Dict) -> str:
    """Genera hash MD5 del registro para detectar duplicados"""
    # Crear string con campos clave
    key_string = json.dumps(operacion, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def transformar_operacion(operacion: Dict) -> Dict:
    """
    Transforma una operación de la API al formato de la tabla PostgreSQL

    Args:
        operacion: Dict con datos de la API

    Returns:
        Dict con datos transformados para insertar
    """
    # Mapear campos de API a campos de tabla
    # NOTA: Los nombres exactos de campos pueden variar según la API real
    # Ajustar según estructura real de respuesta

    transformado = {
        'id_operacion': operacion.get('idOperacion') or operacion.get('id'),
        'numero_operacion': operacion.get('numeroOperacion') or operacion.get('numero'),

        # Fechas
        'fecha_operacion': parse_fecha(operacion.get('fechaOperacion')),

        # Grano/Producto
        'id_grano': operacion.get('idGrano'),
        'nombre_grano': operacion.get('grano') or operacion.get('nombreGrano'),
        'codigo_grano': operacion.get('codigoGrano'),

        # Volumen y precio
        'volumen_tn': parse_decimal(operacion.get('volumenTN')),
        'precio_tn': parse_decimal(operacion.get('precioTN')),

        # Moneda
        'id_moneda': operacion.get('idMoneda'),
        'simbolo_moneda': operacion.get('simboloPrecioPorTN') or operacion.get('moneda'),
        'nombre_moneda': operacion.get('nombreMoneda'),

        # Procedencia
        'id_provincia_procedencia': operacion.get('idProvinciaProcedencia') or operacion.get('procedenciaProvincia'),
        'nombre_provincia_procedencia': operacion.get('nombreProvinciaProcedencia') or operacion.get('provinciaProcedencia'),
        'id_localidad_procedencia': operacion.get('idLocalidadProcedencia'),
        'nombre_localidad_procedencia': operacion.get('nombreLocalidadProcedencia') or operacion.get('localidadProcedencia'),

        # Destino
        'id_provincia_destino': operacion.get('idProvinciaDestino'),
        'nombre_provincia_destino': operacion.get('nombreProvinciaDestino') or operacion.get('provinciaDestino'),
        'id_localidad_destino': operacion.get('idLocalidadDestino'),
        'nombre_localidad_destino': operacion.get('nombreLocalidadDestino') or operacion.get('localidadDestino'),

        # Tipo de operación
        'id_tipo_operacion': operacion.get('idTipoOperacion'),
        'nombre_tipo_operacion': operacion.get('nombreTipoOperacion') or operacion.get('tipoOperacion'),

        # Contrato
        'id_tipo_contrato': operacion.get('idTipoContrato'),
        'nombre_tipo_contrato': operacion.get('nombreTipoContrato') or operacion.get('tipoContrato'),

        # Modalidad
        'id_modalidad': operacion.get('idModalidad'),
        'nombre_modalidad': operacion.get('nombreModalidad') or operacion.get('modalidad'),

        # Estado
        'id_estado': operacion.get('idEstado'),
        'nombre_estado': operacion.get('nombreEstado') or operacion.get('estado'),

        # Condiciones
        'id_condicion_pago': operacion.get('idCondicionPago'),
        'nombre_condicion_pago': operacion.get('nombreCondicionPago') or operacion.get('condicionPago'),
        'id_condicion_calidad': operacion.get('idCondicionCalidad'),
        'nombre_condicion_calidad': operacion.get('nombreCondicionCalidad') or operacion.get('condicionCalidad'),

        # Zona
        'id_zona': operacion.get('idZona'),
        'nombre_zona': operacion.get('nombreZona') or operacion.get('zona'),

        # Puerto
        'id_puerto': operacion.get('idPuerto'),
        'nombre_puerto': operacion.get('nombrePuerto') or operacion.get('puerto'),

        # Guardar datos originales en JSON para debugging
        'datos_adicionales': json.dumps(operacion),

        # Hash para deduplicación
        'hash_registro': calcular_hash_registro(operacion),

        # Metadatos
        'fuente_api': 'SIOGRANOS',
        'version_api': operacion.get('version', '1.0')
    }

    # Calcular monto total si tenemos precio y volumen
    if transformado['precio_tn'] and transformado['volumen_tn']:
        transformado['monto_total'] = transformado['precio_tn'] * transformado['volumen_tn']
    else:
        transformado['monto_total'] = None

    return transformado


def parse_fecha(fecha_str) -> Optional[str]:
    """Parsea fecha de varios formatos a YYYY-MM-DD"""
    if not fecha_str:
        return None

    # Si ya es un objeto datetime
    if isinstance(fecha_str, datetime):
        return fecha_str.strftime('%Y-%m-%d')

    # Intentar varios formatos comunes
    formatos = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%d/%m/%Y',
        '%d-%m-%Y'
    ]

    for formato in formatos:
        try:
            dt = datetime.strptime(str(fecha_str).split('T')[0] if 'T' in str(fecha_str) else str(fecha_str), formato.split('T')[0])
            return dt.strftime('%Y-%m-%d')
        except:
            continue

    logger.warning(f"⚠️ No se pudo parsear fecha: {fecha_str}")
    return None


def parse_decimal(valor) -> Optional[float]:
    """Parsea valor decimal de forma segura"""
    if valor is None:
        return None
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


# ============================================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================================

def get_db_connection():
    """Obtiene conexión a PostgreSQL desde variables de entorno"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'mercado_automotor'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )


def insertar_operaciones_bulk(
    conn,
    operaciones: List[Dict]
) -> Tuple[int, int, int]:
    """
    Inserta operaciones en bulk usando ON CONFLICT para manejar duplicados

    Returns:
        (insertados, duplicados, errores)
    """
    if not operaciones:
        return 0, 0, 0

    cursor = conn.cursor()

    # Preparar columnas
    columnas = [
        'id_operacion', 'numero_operacion', 'fecha_operacion',
        'id_grano', 'nombre_grano', 'codigo_grano',
        'volumen_tn', 'precio_tn', 'monto_total',
        'id_moneda', 'simbolo_moneda', 'nombre_moneda',
        'id_provincia_procedencia', 'nombre_provincia_procedencia',
        'id_localidad_procedencia', 'nombre_localidad_procedencia',
        'id_provincia_destino', 'nombre_provincia_destino',
        'id_localidad_destino', 'nombre_localidad_destino',
        'id_tipo_operacion', 'nombre_tipo_operacion',
        'id_tipo_contrato', 'nombre_tipo_contrato',
        'id_modalidad', 'nombre_modalidad',
        'id_estado', 'nombre_estado',
        'id_condicion_pago', 'nombre_condicion_pago',
        'id_condicion_calidad', 'nombre_condicion_calidad',
        'id_zona', 'nombre_zona',
        'id_puerto', 'nombre_puerto',
        'datos_adicionales', 'hash_registro',
        'fuente_api', 'version_api'
    ]

    # Preparar valores
    valores = []
    for op in operaciones:
        fila = tuple(op.get(col) for col in columnas)
        valores.append(fila)

    # SQL con ON CONFLICT
    sql = f"""
        INSERT INTO siogranos_operaciones ({', '.join(columnas)})
        VALUES %s
        ON CONFLICT (id_operacion, fecha_operacion)
        DO UPDATE SET
            fecha_actualizacion = CURRENT_TIMESTAMP,
            hash_registro = EXCLUDED.hash_registro
        RETURNING (xmax = 0) AS inserted
    """

    try:
        # Ejecutar insert bulk
        results = execute_values(
            cursor,
            sql,
            valores,
            template=None,
            page_size=1000,
            fetch=True
        )

        # Contar inserciones vs actualizaciones
        insertados = sum(1 for r in results if r[0])
        duplicados = len(results) - insertados

        conn.commit()
        return insertados, duplicados, 0

    except Exception as e:
        logger.error(f"❌ Error en inserción bulk: {e}")
        conn.rollback()
        return 0, 0, len(operaciones)
    finally:
        cursor.close()


def registrar_chunk_control(
    conn,
    resultado: ChunkResult
):
    """Registra resultado del chunk en tabla de control ETL"""
    cursor = conn.cursor()

    sql = """
        INSERT INTO siogranos_etl_control (
            fecha_desde, fecha_hasta,
            registros_procesados, registros_insertados,
            registros_duplicados, registros_error,
            estado, inicio_ejecucion, fin_ejecucion,
            duracion_segundos, mensaje_error
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (fecha_desde, fecha_hasta)
        DO UPDATE SET
            registros_procesados = EXCLUDED.registros_procesados,
            registros_insertados = EXCLUDED.registros_insertados,
            registros_duplicados = EXCLUDED.registros_duplicados,
            registros_error = EXCLUDED.registros_error,
            estado = EXCLUDED.estado,
            fin_ejecucion = EXCLUDED.fin_ejecucion,
            duracion_segundos = EXCLUDED.duracion_segundos,
            mensaje_error = EXCLUDED.mensaje_error
    """

    try:
        cursor.execute(sql, (
            resultado.fecha_desde.date(),
            resultado.fecha_hasta.date(),
            resultado.registros_procesados,
            resultado.registros_insertados,
            resultado.registros_duplicados,
            resultado.registros_error,
            'completed' if resultado.success else 'failed',
            resultado.fecha_desde,
            resultado.fecha_hasta,
            resultado.duracion_segundos,
            resultado.error_message
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Error al registrar control: {e}")
        conn.rollback()
    finally:
        cursor.close()


def obtener_chunks_pendientes(conn, fecha_inicio: datetime, fecha_fin: datetime) -> List[Tuple[datetime, datetime]]:
    """
    Obtiene lista de chunks pendientes a procesar
    Excluye chunks ya completados exitosamente
    """
    cursor = conn.cursor()

    # Obtener chunks completados
    sql = """
        SELECT fecha_desde, fecha_hasta
        FROM siogranos_etl_control
        WHERE estado = 'completed'
          AND registros_error = 0
    """

    cursor.execute(sql)
    completados = set((row[0], row[1]) for row in cursor.fetchall())
    cursor.close()

    # Generar todos los chunks posibles
    todos_chunks = []
    current = fecha_inicio

    while current < fecha_fin:
        chunk_fin = min(current + timedelta(days=CHUNK_DAYS), fecha_fin)

        # Verificar si ya está completado
        if (current.date(), chunk_fin.date()) not in completados:
            todos_chunks.append((current, chunk_fin))

        current = chunk_fin

    return todos_chunks


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def procesar_chunk(
    conn,
    fecha_desde: datetime,
    fecha_hasta: datetime
) -> ChunkResult:
    """
    Procesa un chunk de fechas: consulta API, transforma e inserta en DB
    """
    inicio = time.time()

    logger.info(f"\n{'='*80}")
    logger.info(f"📦 PROCESANDO CHUNK: {fecha_desde.date()} → {fecha_hasta.date()}")
    logger.info(f"{'='*80}")

    # Consultar API
    operaciones_raw = fetch_operaciones_con_reintentos(
        fecha_desde.strftime('%Y-%m-%d'),
        fecha_hasta.strftime('%Y-%m-%d')
    )

    if operaciones_raw is None:
        duracion = time.time() - inicio
        return ChunkResult(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            registros_procesados=0,
            registros_insertados=0,
            registros_duplicados=0,
            registros_error=0,
            success=False,
            error_message="Error al consultar API",
            duracion_segundos=duracion
        )

    # Transformar operaciones
    logger.info(f"🔄 Transformando {len(operaciones_raw)} operaciones...")
    operaciones_transformadas = []

    for op in operaciones_raw:
        try:
            transformada = transformar_operacion(op)
            operaciones_transformadas.append(transformada)
        except Exception as e:
            logger.warning(f"⚠️ Error al transformar operación: {e}")
            continue

    logger.info(f"✅ Transformadas: {len(operaciones_transformadas)} operaciones")

    # Insertar en base de datos
    if operaciones_transformadas:
        logger.info(f"💾 Insertando en PostgreSQL...")
        insertados, duplicados, errores = insertar_operaciones_bulk(conn, operaciones_transformadas)
        logger.info(f"✅ Insertados: {insertados} | Duplicados: {duplicados} | Errores: {errores}")
    else:
        insertados, duplicados, errores = 0, 0, 0

    duracion = time.time() - inicio

    resultado = ChunkResult(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        registros_procesados=len(operaciones_raw),
        registros_insertados=insertados,
        registros_duplicados=duplicados,
        registros_error=errores,
        success=True,
        duracion_segundos=duracion
    )

    # Registrar en control
    registrar_chunk_control(conn, resultado)

    logger.info(f"⏱️ Duración: {duracion:.2f}s")

    return resultado


def main():
    """Función principal del ETL"""
    logger.info("\n" + "="*80)
    logger.info("🌾 ETL SIOGRANOS - Carga Histórica")
    logger.info("="*80)
    logger.info(f"📅 Período: {FECHA_INICIO.date()} → {FECHA_FIN.date()}")
    logger.info(f"📦 Tamaño chunk: {CHUNK_DAYS} días")
    logger.info(f"🔄 Reintentos máximos: {MAX_RETRIES}")
    logger.info(f"🔗 API: {SIOGRANOS_API_URL}")
    logger.info("="*80 + "\n")

    # Conectar a base de datos
    try:
        conn = get_db_connection()
        logger.info("✅ Conexión a PostgreSQL establecida")
    except Exception as e:
        logger.error(f"❌ Error al conectar a PostgreSQL: {e}")
        logger.error("💡 Verifica las variables de entorno: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        return

    try:
        # Obtener chunks pendientes
        chunks = obtener_chunks_pendientes(conn, FECHA_INICIO, FECHA_FIN)
        total_chunks = len(chunks)

        logger.info(f"📋 Total de chunks a procesar: {total_chunks}")

        if total_chunks == 0:
            logger.info("✅ ¡No hay chunks pendientes! Todo está actualizado.")
            return

        # Procesar cada chunk
        resultados = []

        for i, (fecha_desde, fecha_hasta) in enumerate(chunks, 1):
            logger.info(f"\n🔄 Progreso: {i}/{total_chunks} ({i*100//total_chunks}%)")

            resultado = procesar_chunk(conn, fecha_desde, fecha_hasta)
            resultados.append(resultado)

            # Pequeña pausa entre chunks para no saturar la API
            if i < total_chunks:
                time.sleep(1)

        # Resumen final
        logger.info("\n" + "="*80)
        logger.info("📊 RESUMEN FINAL")
        logger.info("="*80)

        total_procesados = sum(r.registros_procesados for r in resultados)
        total_insertados = sum(r.registros_insertados for r in resultados)
        total_duplicados = sum(r.registros_duplicados for r in resultados)
        total_errores = sum(r.registros_error for r in resultados)
        chunks_exitosos = sum(1 for r in resultados if r.success)

        logger.info(f"✅ Chunks procesados: {chunks_exitosos}/{total_chunks}")
        logger.info(f"📊 Registros procesados: {total_procesados:,}")
        logger.info(f"💾 Registros insertados: {total_insertados:,}")
        logger.info(f"🔄 Registros duplicados: {total_duplicados:,}")
        logger.info(f"❌ Registros con error: {total_errores:,}")
        logger.info("="*80)

        logger.info("\n✅ ETL completado exitosamente")

    except KeyboardInterrupt:
        logger.info("\n⚠️ ETL interrumpido por usuario")
        logger.info("💡 Puedes reanudar ejecutando el script nuevamente")

    except Exception as e:
        logger.error(f"\n❌ Error fatal en ETL: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()
        logger.info("🔌 Conexión a PostgreSQL cerrada")


if __name__ == "__main__":
    main()
