"""
PREDICCIONES CON MODELOS ENTRENADOS
===================================

Script para hacer predicciones de demanda usando los modelos entrenados.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
from datetime import datetime
from sqlalchemy import create_engine, text

# Configuración
sys.path.append(str(Path(__file__).parent.parent))
from backend.config.settings import settings

MODELS_DIR = Path("data/models")
RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def log(message):
    """Logger simple."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def cargar_modelo_y_artefactos(modelo_nombre=None):
    """
    Carga el modelo entrenado y artefactos necesarios.

    Args:
        modelo_nombre: Nombre del modelo (None para el mejor)

    Returns:
        tuple: (modelo, encoders, feature_names)
    """
    log("=" * 80)
    log("📥 CARGANDO MODELO Y ARTEFACTOS")
    log("=" * 80)

    # Cargar mejor modelo si no se especifica
    if modelo_nombre is None:
        modelo_files = list(MODELS_DIR.glob("mejor_modelo_*.pkl"))
        if not modelo_files:
            log("❌ No se encuentra ningún modelo entrenado")
            log("💡 Ejecuta primero: python notebooks/02_modelado_predictivo.py")
            sys.exit(1)

        file_modelo = modelo_files[0]
        modelo_nombre = file_modelo.stem.replace("mejor_modelo_", "")
    else:
        file_modelo = MODELS_DIR / f"mejor_modelo_{modelo_nombre}.pkl"

    log(f"\n📦 Cargando modelo: {modelo_nombre}")

    with open(file_modelo, 'rb') as f:
        modelo = pickle.load(f)
    log(f"  ✓ Modelo cargado: {file_modelo}")

    # Cargar encoders
    file_encoders = MODELS_DIR / "encoders.pkl"
    with open(file_encoders, 'rb') as f:
        encoders = pickle.load(f)
    log(f"  ✓ Encoders cargados: {len(encoders)} variables")

    # Cargar feature names
    file_features = MODELS_DIR / "feature_names.pkl"
    with open(file_features, 'rb') as f:
        feature_names = pickle.load(f)
    log(f"  ✓ Feature names cargados: {len(feature_names)} features")

    return modelo, encoders, feature_names


def preparar_datos_prediccion(marca, modelo_nombre, provincia, tipo_transaccion,
                               mes_prediccion, anio_prediccion):
    """
    Prepara datos para predicción de una combinación específica.

    Args:
        marca: Marca del vehículo
        modelo_nombre: Modelo del vehículo
        provincia: Provincia
        tipo_transaccion: Tipo de transacción
        mes_prediccion: Mes a predecir (1-12)
        anio_prediccion: Año a predecir

    Returns:
        pd.DataFrame: Datos preparados para predicción
    """
    log("\n" + "=" * 80)
    log("🔧 PREPARANDO DATOS PARA PREDICCIÓN")
    log("=" * 80)

    log(f"\nParámetros:")
    log(f"  Marca: {marca}")
    log(f"  Modelo: {modelo_nombre}")
    log(f"  Provincia: {provincia}")
    log(f"  Tipo: {tipo_transaccion}")
    log(f"  Periodo: {mes_prediccion}/{anio_prediccion}")

    # Conectar a BD para obtener datos históricos
    engine = create_engine(settings.get_database_url_sync())

    # Obtener último valor de variables macro
    log("\n📈 Obteniendo variables macro más recientes...")

    query_macro = """
    SELECT
        MAX(fecha) as fecha_max
    FROM indicadores_calculados
    """

    with engine.connect() as conn:
        result = conn.execute(text(query_macro))
        fecha_max_macro = result.fetchone()[0]

    log(f"  ✓ Última fecha disponible: {fecha_max_macro}")

    # Obtener valores macro para esa fecha
    query_valores = f"""
    SELECT
        fecha,
        tasa_real,
        tcr,
        accesibilidad,
        volatilidad
    FROM indicadores_calculados
    WHERE fecha = '{fecha_max_macro}'
    """

    df_macro = pd.read_sql(query_valores, engine)

    # IPC, BADLAR, TC
    query_ipc = f"""
    SELECT nivel_general as ipc_nivel,
           variacion_mensual as ipc_var_mensual,
           variacion_interanual as ipc_var_interanual
    FROM ipc
    WHERE indice_tiempo <= '{fecha_max_macro}'
    ORDER BY indice_tiempo DESC
    LIMIT 1
    """
    df_ipc = pd.read_sql(query_ipc, engine)

    query_badlar = f"""
    SELECT AVG(valor) as badlar_promedio,
           STDDEV(valor) as badlar_volatilidad
    FROM badlar
    WHERE fecha >= '{fecha_max_macro}'::date - interval '30 days'
      AND fecha <= '{fecha_max_macro}'
    """
    df_badlar = pd.read_sql(query_badlar, engine)

    query_tc = f"""
    SELECT AVG(valor) as tc_promedio,
           STDDEV(valor) as tc_volatilidad
    FROM tipo_cambio
    WHERE fecha >= '{fecha_max_macro}'::date - interval '30 days'
      AND fecha <= '{fecha_max_macro}'
    """
    df_tc = pd.read_sql(query_tc, engine)

    engine.dispose()

    # Crear DataFrame de predicción
    data_pred = {
        'anio': anio_prediccion,
        'mes': mes_prediccion,
        'trimestre': (mes_prediccion - 1) // 3 + 1,
        'marca': marca,
        'modelo': modelo_nombre,
        'provincia': provincia,
        'tipo_transaccion': tipo_transaccion,
        'genero': 'Masculino',  # Valor por defecto
        'edad_titular': 40.0,  # Promedio estimado
        'anio_modelo': anio_prediccion - 1,  # Asumimos vehículo casi nuevo
        'es_primer_semestre': 1 if mes_prediccion <= 6 else 0,
        'es_fin_anio': 1 if mes_prediccion >= 11 else 0,
    }

    # Agregar variables macro
    if not df_macro.empty:
        data_pred['tasa_real_promedio'] = df_macro['tasa_real'].iloc[0]
        data_pred['tcr_promedio'] = df_macro['tcr'].iloc[0]
        data_pred['accesibilidad_promedio'] = df_macro['accesibilidad'].iloc[0]
        data_pred['volatilidad_promedio'] = df_macro['volatilidad'].iloc[0]

    if not df_ipc.empty:
        data_pred['ipc_nivel'] = df_ipc['ipc_nivel'].iloc[0]
        data_pred['ipc_var_mensual'] = df_ipc['ipc_var_mensual'].iloc[0]
        data_pred['ipc_var_interanual'] = df_ipc['ipc_var_interanual'].iloc[0]

    if not df_badlar.empty:
        data_pred['badlar_promedio'] = df_badlar['badlar_promedio'].iloc[0]
        data_pred['badlar_volatilidad'] = df_badlar['badlar_volatilidad'].iloc[0]

    if not df_tc.empty:
        data_pred['tc_promedio'] = df_tc['tc_promedio'].iloc[0]
        data_pred['tc_volatilidad'] = df_tc['tc_volatilidad'].iloc[0]

    df_pred = pd.DataFrame([data_pred])

    log(f"\n✓ Datos preparados: {len(df_pred.columns)} variables")

    return df_pred


def predecir(modelo, encoders, feature_names, df_pred):
    """
    Realiza predicción.

    Args:
        modelo: Modelo entrenado
        encoders: Encoders de variables categóricas
        feature_names: Nombres de features
        df_pred: DataFrame con datos a predecir

    Returns:
        float: Predicción
    """
    log("\n" + "=" * 80)
    log("🔮 REALIZANDO PREDICCIÓN")
    log("=" * 80)

    df_work = df_pred.copy()

    # Aplicar encoders a variables categóricas
    log("\n🏷️ Aplicando encoders...")
    for col, encoder in encoders.items():
        if col in df_work.columns:
            # Manejar valores desconocidos
            valor = df_work[col].iloc[0]
            if valor not in encoder.classes_:
                log(f"  ⚠️ Valor desconocido en '{col}': {valor} → usando clase más frecuente")
                valor = encoder.classes_[0]

            df_work[f'{col}_encoded'] = encoder.transform([valor])[0]

    # Asegurarse de tener todas las features
    log("\n📋 Preparando features finales...")
    X_pred = []
    for feat in feature_names:
        if feat in df_work.columns:
            X_pred.append(df_work[feat].iloc[0])
        else:
            # Feature faltante (probablemente one-hot encoding)
            X_pred.append(0)

    X_pred = np.array(X_pred).reshape(1, -1)

    log(f"  ✓ Vector de predicción: shape {X_pred.shape}")

    # Predicción
    prediccion = modelo.predict(X_pred)[0]

    log(f"\n🎯 PREDICCIÓN: {prediccion:.0f} transacciones")

    return prediccion


def predecir_multiples_escenarios():
    """
    Predice para múltiples escenarios de variables macro.
    """
    log("\n" + "=" * 80)
    log("📊 PREDICCIÓN MÚLTIPLES ESCENARIOS")
    log("=" * 80)

    # Cargar modelo
    modelo, encoders, feature_names = cargar_modelo_y_artefactos()

    # Definir escenarios
    escenarios = {
        'Optimista': {'ipc_var_mensual': 3.0, 'badlar_promedio': 45.0, 'tc_promedio': 900},
        'Base': {'ipc_var_mensual': 5.0, 'badlar_promedio': 55.0, 'tc_promedio': 1000},
        'Pesimista': {'ipc_var_mensual': 8.0, 'badlar_promedio': 65.0, 'tc_promedio': 1200},
    }

    # Configuración base
    marca = "TOYOTA"
    modelo_nombre = "COROLLA"
    provincia = "CAPITAL FEDERAL"
    tipo_transaccion = "inscripcion"
    mes = 12
    anio = 2024

    resultados = []

    for escenario, valores in escenarios.items():
        log(f"\n{'='*60}")
        log(f"Escenario: {escenario}")
        log(f"{'='*60}")

        # Preparar datos base
        df_pred = preparar_datos_prediccion(
            marca, modelo_nombre, provincia, tipo_transaccion, mes, anio
        )

        # Ajustar variables macro según escenario
        for var, val in valores.items():
            if var in df_pred.columns:
                df_pred[var] = val

        # Predecir
        pred = predecir(modelo, encoders, feature_names, df_pred)

        resultados.append({
            'escenario': escenario,
            'marca': marca,
            'modelo': modelo_nombre,
            'provincia': provincia,
            'tipo': tipo_transaccion,
            'mes': mes,
            'anio': anio,
            'prediccion': pred,
            **valores
        })

    # Mostrar comparación
    df_resultados = pd.DataFrame(resultados)

    log("\n" + "=" * 80)
    log("📈 COMPARACIÓN DE ESCENARIOS")
    log("=" * 80)

    print("\n")
    print(df_resultados.to_string(index=False))

    # Guardar
    file_out = RESULTS_DIR / f"predicciones_escenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_resultados.to_csv(file_out, index=False)
    log(f"\n✓ Resultados guardados: {file_out}")


def main():
    """Función principal."""
    log("=" * 80)
    log("🔮 PREDICCIONES CON MODELO ENTRENADO")
    log("=" * 80)

    # Ejemplo de predicción simple
    log("\n📌 EJEMPLO: Predicción simple")
    log("=" * 80)

    modelo, encoders, feature_names = cargar_modelo_y_artefactos()

    df_pred = preparar_datos_prediccion(
        marca="TOYOTA",
        modelo_nombre="COROLLA",
        provincia="CAPITAL FEDERAL",
        tipo_transaccion="inscripcion",
        mes_prediccion=12,
        anio_prediccion=2024
    )

    prediccion = predecir(modelo, encoders, feature_names, df_pred)

    # Predicción múltiples escenarios
    log("\n\n")
    predecir_multiples_escenarios()

    log("\n" + "=" * 80)
    log("✅ PREDICCIONES COMPLETADAS")
    log("=" * 80)


if __name__ == "__main__":
    main()
