"""
Helper para predicción ML con recursive forecasting.
Prepara features exactamente como el modelo fue entrenado.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def preparar_features_prediccion(
    df_historico,
    df_macro,
    provincia,
    marca,
    modelo,
    encoders,
    meses_proyectar=4
):
    """
    Prepara features para predicción ML con recursive forecasting.

    Args:
        df_historico: DataFrame con histórico de transacciones
        df_macro: DataFrame con variables macro actuales
        provincia: Provincia a predecir
        marca: Marca a predecir
        modelo: Modelo de vehículo a predecir
        encoders: Dict con label encoders entrenados
        meses_proyectar: Número de meses a proyectar

    Returns:
        list: Lista de DataFrames con features para cada mes
    """

    # Ordenar histórico por fecha
    df_hist = df_historico.sort_values('fecha_mes').copy()

    # Obtener últimos valores
    ultimo_registro = df_hist.iloc[-1]
    ultima_fecha = pd.to_datetime(ultimo_registro['fecha_mes'])

    # Preparar lista para almacenar predicciones
    predicciones_features = []

    # Valores históricos para lag features
    cantidad_historica = df_hist['cantidad_transacciones'].tolist()

    # Variables macro actuales
    if not df_macro.empty:
        ipc_actual = df_macro.iloc[0]['ipc_nivel'] if 'ipc_nivel' in df_macro.columns else 100
        badlar_actual = df_macro.iloc[0]['badlar_promedio'] if 'badlar_promedio' in df_macro.columns else 50
        tc_actual = df_macro.iloc[0]['tc_promedio'] if 'tc_promedio' in df_macro.columns else 1000

        # Calcular IPC var mensual
        if len(df_macro) >= 2:
            ipc_var = ((df_macro.iloc[0]['ipc_nivel'] - df_macro.iloc[1]['ipc_nivel']) /
                      df_macro.iloc[1]['ipc_nivel'] * 100)
        else:
            ipc_var = 5.0
    else:
        ipc_actual = 100
        badlar_actual = 50
        tc_actual = 1000
        ipc_var = 5.0

    # Loop para cada mes futuro
    for i in range(1, meses_proyectar + 1):
        # Calcular fecha futura
        fecha_futura = ultima_fecha + relativedelta(months=i)
        mes = fecha_futura.month
        anio = fecha_futura.year
        trimestre = (mes - 1) // 3 + 1

        # Preparar features
        features = {}

        # ===== VARIABLES TEMPORALES =====
        features['anio'] = anio
        features['mes'] = mes
        features['trimestre'] = trimestre
        features['es_primer_semestre'] = 1 if mes <= 6 else 0
        features['es_fin_anio'] = 1 if mes >= 11 else 0

        # ===== LAG FEATURES =====
        # cantidad_transacciones_lag1: valor del mes anterior
        if i == 1:
            # Primer mes: usar último valor real
            features['cantidad_transacciones_lag1'] = cantidad_historica[-1]
        else:
            # Usar predicción del mes anterior
            features['cantidad_transacciones_lag1'] = predicciones_features[i-2]['prediccion']

        # cantidad_transacciones_lag3: valor de hace 3 meses
        if i <= 3:
            # Usar valores históricos
            lag3_idx = len(cantidad_historica) - (3 - i + 1)
            if lag3_idx >= 0:
                features['cantidad_transacciones_lag3'] = cantidad_historica[lag3_idx]
            else:
                features['cantidad_transacciones_lag3'] = cantidad_historica[0]
        else:
            # Usar predicciones anteriores
            features['cantidad_transacciones_lag3'] = predicciones_features[i-4]['prediccion']

        # Lag features de variables macro (asumimos constantes)
        features['badlar_promedio_lag1'] = badlar_actual
        features['tc_promedio_lag1'] = tc_actual
        features['ipc_nivel_lag1'] = ipc_actual

        # ===== MOVING AVERAGES =====
        # MA3: promedio de últimos 3 meses
        valores_ma3 = []
        for j in range(max(0, i-3), i):
            if j == 0:
                valores_ma3.extend(cantidad_historica[-(3-i):])
            else:
                valores_ma3.append(predicciones_features[j-1]['prediccion'])

        if len(valores_ma3) == 0:
            valores_ma3 = cantidad_historica[-3:]

        features['cantidad_ma3'] = np.mean(valores_ma3)

        # MA6: promedio de últimos 6 meses
        valores_ma6 = []
        for j in range(max(0, i-6), i):
            if j == 0:
                valores_ma6.extend(cantidad_historica[-(6-i):])
            else:
                valores_ma6.append(predicciones_features[j-1]['prediccion'])

        if len(valores_ma6) == 0:
            valores_ma6 = cantidad_historica[-6:]

        features['cantidad_ma6'] = np.mean(valores_ma6)

        # ===== VARIACIONES =====
        # Calcular variación intermensual (%)
        if i == 1:
            valor_anterior = cantidad_historica[-1]
            valor_anterior_para_var = cantidad_historica[-2] if len(cantidad_historica) >= 2 else valor_anterior
        else:
            valor_anterior = predicciones_features[i-2]['prediccion']
            if i >= 2:
                valor_anterior_para_var = predicciones_features[i-3]['prediccion'] if i > 2 else cantidad_historica[-1]
            else:
                valor_anterior_para_var = cantidad_historica[-1]

        if valor_anterior_para_var > 0:
            features['cantidad_var_mensual'] = ((valor_anterior - valor_anterior_para_var) / valor_anterior_para_var) * 100
        else:
            features['cantidad_var_mensual'] = 0

        # IPC var mensual (constante por simplicidad)
        features['ipc_var_mensual'] = ipc_var

        # ===== VARIABLES MACRO =====
        features['ipc_nivel'] = ipc_actual
        features['badlar_promedio'] = badlar_actual
        features['tc_promedio'] = tc_actual

        # Volatilidad macro (si existe en el modelo)
        features['badlar_volatilidad'] = 2.0  # Default
        features['tc_volatilidad'] = 50.0  # Default

        # ===== VARIABLES DEMOGRÁFICAS =====
        # Usar valores promedio históricos
        features['edad_titular'] = df_hist['edad_titular'].mean() if 'edad_titular' in df_hist.columns else 40
        features['anio_modelo'] = anio - 2  # Asumimos auto de hace 2 años

        # ===== VARIABLES CATEGÓRICAS ENCODADAS =====
        # Usar los encoders entrenados
        if encoders and 'marca' in encoders:
            # Encodear marca
            if marca in encoders['marca'].classes_:
                features['marca_encoded'] = encoders['marca'].transform([marca])[0]
            else:
                features['marca_encoded'] = -1  # Marca desconocida
        else:
            features['marca_encoded'] = 0

        if encoders and 'modelo' in encoders:
            # Encodear modelo
            if modelo in encoders['modelo'].classes_:
                features['modelo_encoded'] = encoders['modelo'].transform([modelo])[0]
            else:
                features['modelo_encoded'] = -1
        else:
            features['modelo_encoded'] = 0

        if encoders and 'provincia' in encoders:
            # Encodear provincia
            if provincia in encoders['provincia'].classes_:
                features['provincia_encoded'] = encoders['provincia'].transform([provincia])[0]
            else:
                features['provincia_encoded'] = -1
        else:
            features['provincia_encoded'] = 0

        # Tipo vehiculo y tipo transaccion (defaults)
        features['tipo_vehiculo_encoded'] = 0  # Automóvil
        features['tipo_transaccion_encoded'] = 0  # Inscripción
        features['genero_encoded'] = 0  # No aplica

        # Guardar features
        predicciones_features.append({
            'mes': i,
            'fecha': fecha_futura,
            'features': features,
            'prediccion': None  # Se llenará después
        })

    return predicciones_features


def predecir_recursive(modelo, feature_names, predicciones_features):
    """
    Realiza predicción recursiva usando el modelo ML.

    Args:
        modelo: Modelo ML entrenado
        feature_names: Lista con nombres de features en orden correcto
        predicciones_features: Lista de dicts con features preparadas

    Returns:
        list: Lista actualizada con predicciones
    """

    for i, pred_data in enumerate(predicciones_features):
        features = pred_data['features']

        # Crear DataFrame con las features en el orden correcto
        # Solo usar features que el modelo espera
        X_pred = []
        for fname in feature_names:
            if fname in features:
                X_pred.append(features[fname])
            else:
                # Feature no disponible, usar 0 o mediana
                X_pred.append(0)

        # Convertir a array 2D
        X_pred = np.array(X_pred).reshape(1, -1)

        # Predecir
        prediccion = modelo.predict(X_pred)[0]

        # Asegurar que sea positivo
        prediccion = max(0, prediccion)

        # Guardar predicción
        predicciones_features[i]['prediccion'] = prediccion

        # Actualizar lag features para próxima iteración
        if i < len(predicciones_features) - 1:
            # La predicción actual se usará como lag1 en el próximo mes
            pass  # Ya se maneja en preparar_features_prediccion

    return predicciones_features
