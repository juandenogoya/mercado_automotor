#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Diagnóstico EFICIENTE de Variables Categóricas

Usa DuckDB para hacer queries SQL sobre el Parquet sin cargar todo en memoria.
Analiza solo las columnas CATEGÓRICAS con los nombres EXACTOS del dataset.

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/diagnosticar_categoricas_eficiente.py
"""

import duckdb
import pandas as pd
import os
from datetime import datetime

INPUT_FILE = 'data/processed/dataset_transaccional_unificado.parquet'

# NOMBRES EXACTOS de las columnas categóricas (del script 02_unir_datasets_v3.py)
CATEGORICAS = {
    'provincia': 'registro_seccional_provincia',
    'marca': 'automotor_marca_descripcion',
    'modelo': 'automotor_modelo_descripcion',
    'origen': 'automotor_origen',
    'tipo_operacion': 'tipo_operacion',
    'marca_categoria': 'marca_categoria',  # Ya procesada (Top 10 + Otros)
}

# Buscar también estas si existen (género, tipo_persona, etc.)
CATEGORICAS_OPCIONALES = {
    'genero': ['genero', 'sexo', 'titular_genero', 'persona_genero'],
    'tipo_persona': ['tipo_persona', 'persona_tipo', 'titular_tipo'],
    'uso': ['uso', 'tipo_uso', 'vehiculo_uso'],
}


def analizar_columna_con_duckdb(columna):
    """
    Analiza una columna categórica usando DuckDB (sin cargar todo en memoria).

    Returns:
        dict con estadísticas de la columna
    """
    print(f"\n{'='*100}")
    print(f"📊 ANALIZANDO: {columna}")
    print(f"{'='*100}")

    con = duckdb.connect()

    try:
        # 1. Total de registros
        query_total = f"SELECT COUNT(*) as total FROM read_parquet('{INPUT_FILE}')"
        total = con.execute(query_total).fetchone()[0]

        # 2. Contar valores únicos (incluyendo NULL)
        query_unicos = f"""
        SELECT
            COUNT(DISTINCT {columna}) as valores_unicos,
            COUNT(*) as total_registros,
            SUM(CASE WHEN {columna} IS NULL THEN 1 ELSE 0 END) as nulos
        FROM read_parquet('{INPUT_FILE}')
        """
        stats = con.execute(query_unicos).fetchone()
        n_unicos = stats[0]
        n_total = stats[1]
        n_nulos = stats[2]
        pct_nulos = (n_nulos / n_total) * 100

        print(f"\n📈 Estadísticas:")
        print(f"   - Total registros: {n_total:,}")
        print(f"   - Valores únicos: {n_unicos:,}")
        print(f"   - Valores nulos: {n_nulos:,} ({pct_nulos:.2f}%)")

        # 3. Top 30 valores más frecuentes
        query_top = f"""
        SELECT
            {columna} as valor,
            COUNT(*) as count,
            (COUNT(*) * 100.0 / {n_total}) as porcentaje
        FROM read_parquet('{INPUT_FILE}')
        WHERE {columna} IS NOT NULL
        GROUP BY {columna}
        ORDER BY count DESC
        LIMIT 30
        """
        top_valores = con.execute(query_top).fetchall()

        print(f"\n🔝 Top 30 valores más frecuentes:")
        for idx, (valor, count, pct) in enumerate(top_valores, 1):
            print(f"   {idx:2}. {str(valor)[:45]:45} | {count:>12,} ({pct:>6.2f}%)")

        # 4. Calcular % acumulado
        df_top = pd.DataFrame(top_valores, columns=['valor', 'count', 'pct'])

        if len(df_top) >= 10:
            top_10_pct = df_top.head(10)['pct'].sum()
            print(f"\n   💡 Top 10 valores representan: {top_10_pct:.2f}% del total")

        if len(df_top) >= 20:
            top_20_pct = df_top.head(20)['pct'].sum()
            print(f"   💡 Top 20 valores representan: {top_20_pct:.2f}% del total")

        if len(df_top) >= 30:
            top_30_pct = df_top.head(30)['pct'].sum()
            print(f"   💡 Top 30 valores representan: {top_30_pct:.2f}% del total")

        # 5. Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")

        if n_unicos == 2:
            print(f"   ✅ BINARY (2 valores) → Label Encoding (0/1)")
            print(f"      Valores: {[row[0] for row in top_valores[:2]]}")
        elif n_unicos <= 5:
            print(f"   ✅ POCOS VALORES → One-Hot Encoding")
            print(f"      Creará {n_unicos} columnas binarias")
        elif n_unicos <= 25:
            print(f"   ✅ MODERADOS VALORES ({n_unicos}) → One-Hot Encoding o Target Encoding")
            print(f"      - One-Hot: {n_unicos} columnas")
            print(f"      - Target Encoding: 1 columna numérica")
        elif n_unicos <= 50:
            print(f"   ⚠️  MUCHOS VALORES ({n_unicos}) → Agrupar Top 20-30 + 'otros'")
            print(f"      Top 20 representa: {df_top.head(20)['pct'].sum():.2f}%")
        else:
            print(f"   ❌ DEMASIADOS VALORES ({n_unicos:,})")
            print(f"      Opción 1: Agrupar Top 20-30 + 'otros' (cubre {df_top.head(30)['pct'].sum():.2f}%)")
            print(f"      Opción 2: Eliminar (demasiada cardinalidad)")

        # 6. Estrategia de agregación temporal
        print(f"\n🔧 ESTRATEGIA PARA AGREGACIÓN TEMPORAL (semanal/mensual):")

        if n_unicos <= 30:
            print(f"   ✅ Crear una columna numérica por valor:")
            print(f"      Ejemplo para semanal:")
            for idx, (valor, _, _) in enumerate(top_valores[:5], 1):
                valor_normalizado = str(valor).lower().replace(' ', '_').replace('.', '')
                print(f"         df.groupby(['fecha_semana', '{columna}']).size() → operaciones_{valor_normalizado}")
            print(f"      ...")
            print(f"   Resultado: {n_unicos} columnas numéricas (conteo por {columna})")
        else:
            top_n = min(30, n_unicos)
            print(f"   ⚠️  Primero agrupar (demasiados valores):")
            print(f"      1. Identificar Top {top_n} valores")
            print(f"      2. Agrupar resto en 'otros'")
            print(f"      3. Luego crear columnas para Top {top_n} + 'otros'")
            print(f"   Resultado: {top_n + 1} columnas numéricas")

        # Retornar resultados
        return {
            'columna': columna,
            'n_total': n_total,
            'n_unicos': n_unicos,
            'n_nulos': n_nulos,
            'pct_nulos': pct_nulos,
            'top_30': df_top.to_dict('records') if not df_top.empty else []
        }

    except Exception as e:
        print(f"\n❌ ERROR al analizar columna '{columna}': {e}")
        return None
    finally:
        con.close()


def verificar_columnas_opcionales():
    """Verifica qué columnas opcionales existen en el dataset."""
    print(f"\n{'='*100}")
    print(f"🔍 VERIFICANDO COLUMNAS OPCIONALES (género, tipo_persona, etc.)")
    print(f"{'='*100}")

    con = duckdb.connect()

    # Obtener todas las columnas del dataset
    query_cols = f"DESCRIBE SELECT * FROM read_parquet('{INPUT_FILE}')"
    columnas_df = con.execute(query_cols).fetchdf()
    columnas_disponibles = columnas_df['column_name'].tolist()

    print(f"\n✓ Total de columnas en el dataset: {len(columnas_disponibles)}")

    # Buscar columnas opcionales
    encontradas = {}

    for concepto, posibles_nombres in CATEGORICAS_OPCIONALES.items():
        for nombre in posibles_nombres:
            if nombre in columnas_disponibles:
                encontradas[concepto] = nombre
                print(f"   ✅ {concepto:15} → columna '{nombre}' ENCONTRADA")
                break
        else:
            print(f"   ❌ {concepto:15} → No encontrada (buscadas: {posibles_nombres})")

    con.close()
    return encontradas


def main():
    """Función principal."""
    print("\n" + "="*100)
    print("DIAGNÓSTICO EFICIENTE: VARIABLES CATEGÓRICAS DEL DATASET TRANSACCIONAL")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    # Verificar archivo
    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ ERROR: Archivo no encontrado: {INPUT_FILE}")
        print(f"\n📝 Ejecuta primero:")
        print(f"   python backend/data_processing/02_unir_datasets_v3.py")
        return

    print(f"\n📂 Archivo: {INPUT_FILE}")
    size_mb = os.path.getsize(INPUT_FILE) / 1024**2
    print(f"   Tamaño: {size_mb:,.2f} MB")

    # 1. Analizar columnas categóricas conocidas
    print(f"\n{'='*100}")
    print(f"ANÁLISIS DE VARIABLES CATEGÓRICAS PRINCIPALES")
    print(f"{'='*100}")

    resultados = {}

    for concepto, columna in CATEGORICAS.items():
        resultado = analizar_columna_con_duckdb(columna)
        if resultado:
            resultados[concepto] = resultado

    # 2. Verificar y analizar columnas opcionales
    columnas_opcionales = verificar_columnas_opcionales()

    if columnas_opcionales:
        print(f"\n{'='*100}")
        print(f"ANÁLISIS DE VARIABLES CATEGÓRICAS OPCIONALES")
        print(f"{'='*100}")

        for concepto, columna in columnas_opcionales.items():
            resultado = analizar_columna_con_duckdb(columna)
            if resultado:
                resultados[concepto] = resultado

    # 3. Resumen final
    print(f"\n{'='*100}")
    print(f"📋 RESUMEN EJECUTIVO")
    print(f"{'='*100}")

    print(f"\n✅ Variables categóricas analizadas: {len(resultados)}")
    for concepto, resultado in resultados.items():
        print(f"   - {concepto:20} ({resultado['columna']:40})")
        print(f"     └─ {resultado['n_unicos']:>6,} valores únicos | {resultado['pct_nulos']:>6.2f}% NaNs")

    print(f"\n💡 PLAN DE ACCIÓN RECOMENDADO:")
    print(f"\n1. Variables LISTAS para agregación (≤ 30 valores):")
    for concepto, resultado in resultados.items():
        if resultado['n_unicos'] <= 30:
            print(f"   ✅ {concepto:20} → {resultado['n_unicos']:>3} columnas numéricas")

    print(f"\n2. Variables que REQUIEREN agrupación (> 30 valores):")
    for concepto, resultado in resultados.items():
        if resultado['n_unicos'] > 30:
            top_30_pct = sum(r['pct'] for r in resultado['top_30'][:30]) if resultado['top_30'] else 0
            print(f"   ⚠️  {concepto:20} → Agrupar Top 30 + 'otros' (cubre {top_30_pct:.1f}%)")

    print(f"\n3. PRÓXIMO PASO:")
    print(f"   Crear script que:")
    print(f"   a) Agrupe valores raros en 'otros' para columnas con > 30 valores")
    print(f"   b) Haga pivot/groupby por semana + categoría")
    print(f"   c) Genere features numéricas del tipo: operaciones_provincia_buenos_aires")
    print(f"   d) Estas features SÍ tendrán valores (no NaN)")

    # 4. Guardar reporte
    output_file = INPUT_FILE.replace('.parquet', '_diagnostico_categoricas.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"DIAGNÓSTICO: VARIABLES CATEGÓRICAS\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*100}\n\n")

        for concepto, resultado in resultados.items():
            f.write(f"\n{concepto.upper()} ({resultado['columna']})\n")
            f.write(f"  Valores únicos: {resultado['n_unicos']:,}\n")
            f.write(f"  Nulos: {resultado['n_nulos']:,} ({resultado['pct_nulos']:.2f}%)\n")
            f.write(f"  Top 30:\n")
            for item in resultado['top_30'][:30]:
                f.write(f"    {item['valor']}: {item['count']:,} ({item['pct']:.2f}%)\n")

    print(f"\n💾 Reporte guardado: {output_file}")

    print(f"\n{'='*100}")
    print(f"✅ DIAGNÓSTICO COMPLETADO")
    print(f"{'='*100}")


if __name__ == "__main__":
    # Verificar que DuckDB esté instalado
    try:
        import duckdb
    except ImportError:
        print("\n❌ ERROR: DuckDB no está instalado")
        print("\n📝 Instalar con:")
        print("   pip install duckdb")
        exit(1)

    main()
