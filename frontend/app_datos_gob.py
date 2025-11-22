"""
Dashboard de Datos datos.gob.ar - Streamlit App
Sistema de Análisis de Trámites Automotores (DNRPA)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime
from sqlalchemy import create_engine, text
import sys
from pathlib import Path
import calendar

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.settings import settings

# Page config
st.set_page_config(
    page_title="Datos.gob.ar - Análisis Automotor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 500;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_database_engine():
    """Create database engine."""
    return create_engine(settings.get_database_url_sync())

engine = get_database_engine()

# Utilidades
MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

MESES_ORDEN = list(MESES_ES.values())

def format_number(num):
    """Formatear número con separadores de miles."""
    return f"{int(num):,}".replace(",", ".")

def calcular_variacion(actual, anterior):
    """Calcular variación porcentual."""
    if anterior == 0:
        return 0
    return ((actual - anterior) / anterior) * 100

# Header principal
st.markdown('<p class="main-header">📊 Análisis de Trámites Automotores - DNRPA</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Fuente: datos.gob.ar - Ministerio de Justicia</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar - Filtros globales
st.sidebar.markdown("## 🔍 Filtros de Análisis")
st.sidebar.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🚗 Inscripciones",
    "🔄 Transferencias",
    "💰 Prendas",
    "📍 Registro por Localidad",
    "🔬 Análisis Detallado",
    "📊 Tendencias Históricas",
    "🔮 Predicciones ML",
    "📈 KPIs de Mercado"
])

# ==================== FUNCIÓN GENÉRICA PARA ANÁLISIS ====================
def analizar_tramites(tabla_nombre, titulo, icono):
    """
    Función genérica para analizar inscripciones, transferencias o prendas.
    """
    st.header(f"{icono} {titulo}")

    # 1. Obtener años disponibles
    query_anios = text(f"""
        SELECT DISTINCT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio
        FROM {tabla_nombre}
        WHERE tramite_fecha IS NOT NULL
        ORDER BY anio DESC
    """)

    try:
        df_anios = pd.read_sql(query_anios, engine)
        anios_disponibles = df_anios['anio'].tolist() if not df_anios.empty else []
    except:
        anios_disponibles = []

    if not anios_disponibles:
        st.warning(f"⚠️ No hay datos disponibles en la tabla `{tabla_nombre}`")
        st.info("💡 **Para cargar datos:**\n\n"
                "1. Descarga datos CSV desde datos.gob.ar\n"
                "2. Coloca los archivos en `INPUT/INSCRIPCIONES/`, `INPUT/TRANSFERENCIAS/` o `INPUT/PRENDAS/`\n"
                "3. Ejecuta: `python cargar_datos_gob_ar_postgresql.py`")
        return

    # 2. Filtros en columnas
    st.markdown("### 🎯 Filtros de Búsqueda")

    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)

    with col_filtro1:
        anios_seleccionados = st.multiselect(
            "📅 Años",
            options=anios_disponibles,
            default=anios_disponibles[:2] if len(anios_disponibles) >= 2 else anios_disponibles,
            key=f"{tabla_nombre}_anios"
        )

    with col_filtro2:
        meses_seleccionados = st.multiselect(
            "📆 Meses",
            options=MESES_ORDEN,
            default=MESES_ORDEN,
            key=f"{tabla_nombre}_meses"
        )

    # Obtener provincias disponibles
    query_provincias = text(f"""
        SELECT DISTINCT titular_domicilio_provincia as provincia
        FROM {tabla_nombre}
        WHERE titular_domicilio_provincia IS NOT NULL
        AND titular_domicilio_provincia != ''
        ORDER BY provincia
    """)

    try:
        df_provincias = pd.read_sql(query_provincias, engine)
        provincias_disponibles = df_provincias['provincia'].tolist()
    except:
        provincias_disponibles = []

    with col_filtro3:
        provincias_seleccionadas = st.multiselect(
            "📍 Provincias",
            options=provincias_disponibles,
            default=provincias_disponibles[:3] if len(provincias_disponibles) >= 3 else provincias_disponibles,
            key=f"{tabla_nombre}_provincias"
        )

    # Filtro de localidades (cascading)
    if provincias_seleccionadas and anios_seleccionados:
        query_localidades = text(f"""
            SELECT DISTINCT titular_domicilio_localidad as localidad
            FROM {tabla_nombre}
            WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
            AND titular_domicilio_provincia = ANY(:provincias)
            AND titular_domicilio_localidad IS NOT NULL
            AND titular_domicilio_localidad != ''
            ORDER BY localidad
        """)

        try:
            df_localidades = pd.read_sql(
                query_localidades,
                engine,
                params={'anios': anios_seleccionados, 'provincias': provincias_seleccionadas}
            )
            localidades_disponibles = df_localidades['localidad'].tolist()
        except:
            localidades_disponibles = []
    else:
        localidades_disponibles = []

    col_loc1, col_loc2 = st.columns([1, 1])
    with col_loc1:
        localidades_seleccionadas = st.multiselect(
            "🏘️ Localidades (opcional)",
            options=localidades_disponibles,
            default=[],
            key=f"{tabla_nombre}_localidades",
            help="Filtra por localidades específicas. Dejar vacío para incluir todas."
        )

    # Filtro de género
    col_filtro4, col_filtro5 = st.columns([1, 2])
    with col_filtro4:
        generos_opciones = ['Todos', 'Masculino', 'Femenino', 'No aplica', 'No identificado']
        genero_seleccionado = st.selectbox(
            "👤 Género del Titular",
            options=generos_opciones,
            index=0,
            key=f"{tabla_nombre}_genero"
        )

    if not anios_seleccionados or not meses_seleccionados or not provincias_seleccionadas:
        st.warning("⚠️ Selecciona al menos un año, un mes y una provincia")
        return

    # Convertir meses a números
    meses_numeros = [list(MESES_ES.keys())[list(MESES_ES.values()).index(mes)] for mes in meses_seleccionados]

    st.markdown("---")

    # 3. Consulta principal con filtros
    # Construir condición de género
    if genero_seleccionado == 'Todos':
        filtro_genero = ""  # Todos los géneros
    else:
        filtro_genero = f"AND titular_genero = '{genero_seleccionado}'"

    # Construir condición de localidad
    filtro_localidad = ""
    if localidades_seleccionadas:
        filtro_localidad = "AND titular_domicilio_localidad = ANY(:localidades)"

    query = text(f"""
        SELECT
            EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
            EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
            titular_domicilio_provincia as provincia,
            titular_domicilio_localidad as localidad,
            automotor_marca_descripcion as marca,
            automotor_tipo_descripcion as tipo_vehiculo,
            titular_genero as genero,
            COUNT(*) as cantidad,
            AVG(EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento) as edad_promedio_titular
        FROM {tabla_nombre}
        WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
        AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
        AND titular_domicilio_provincia = ANY(:provincias)
        {filtro_localidad}
        AND tramite_fecha IS NOT NULL
        AND titular_anio_nacimiento IS NOT NULL
        {filtro_genero}
        GROUP BY anio, mes, provincia, localidad, marca, tipo_vehiculo, genero
        ORDER BY anio, mes, provincia, localidad
    """)

    try:
        params_query = {
            'anios': anios_seleccionados,
            'meses': meses_numeros,
            'provincias': provincias_seleccionadas
        }
        if localidades_seleccionadas:
            params_query['localidades'] = localidades_seleccionadas

        df = pd.read_sql(query, engine, params=params_query)

        if df.empty:
            st.warning("⚠️ No se encontraron datos con los filtros seleccionados")
            return

        # Agregar nombre de mes
        df['mes_nombre'] = df['mes'].map(MESES_ES)

        # 4. KPIs principales
        st.markdown("### 📊 Métricas Principales")

        col1, col2, col3, col4 = st.columns(4)

        total_tramites = df['cantidad'].sum()

        with col1:
            st.metric("Total Trámites", format_number(total_tramites))

        with col2:
            st.metric("Provincias", len(provincias_seleccionadas))

        with col3:
            st.metric("Marcas Únicas", df['marca'].nunique())

        with col4:
            promedio_mensual = total_tramites / (len(anios_seleccionados) * len(meses_seleccionados))
            st.metric("Promedio Mensual", format_number(promedio_mensual))

        st.markdown("---")

        # 5. Análisis por Año - Comparación YoY
        st.markdown("### 📈 Análisis Comparativo por Año (YoY)")

        df_por_anio = df.groupby('anio')['cantidad'].sum().reset_index()
        df_por_anio = df_por_anio.sort_values('anio')

        col_yoy1, col_yoy2 = st.columns([2, 1])

        with col_yoy1:
            fig_anios = px.bar(
                df_por_anio,
                x='anio',
                y='cantidad',
                title=f'{titulo} - Comparación por Año',
                labels={'anio': 'Año', 'cantidad': 'Cantidad de Trámites'},
                text='cantidad',
                color='anio',
                color_continuous_scale='Blues'
            )
            fig_anios.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_anios.update_layout(showlegend=False, xaxis_type='category')
            st.plotly_chart(fig_anios, use_container_width=True)

        with col_yoy2:
            st.markdown("#### Variaciones YoY")

            for i in range(len(df_por_anio) - 1):
                anio_anterior = df_por_anio.iloc[i]
                anio_actual = df_por_anio.iloc[i + 1]

                variacion = calcular_variacion(anio_actual['cantidad'], anio_anterior['cantidad'])

                st.metric(
                    f"{int(anio_actual['anio'])} vs {int(anio_anterior['anio'])}",
                    f"{format_number(anio_actual['cantidad'])}",
                    f"{variacion:+.1f}%"
                )

        st.markdown("---")

        # 6. Evolución Mensual - Gráfico de líneas por año
        st.markdown("### 📅 Evolución Mensual Comparativa")

        # Agrupar por año y mes
        df_mensual = df.groupby(['anio', 'mes', 'mes_nombre'])['cantidad'].sum().reset_index()
        df_mensual = df_mensual.sort_values(['anio', 'mes'])

        # Crear gráfico de líneas con un color por año
        fig_mensual = px.line(
            df_mensual,
            x='mes_nombre',
            y='cantidad',
            color='anio',
            title=f'{titulo} - Evolución Mensual por Año',
            labels={'mes_nombre': 'Mes', 'cantidad': 'Cantidad', 'anio': 'Año'},
            markers=True,
            category_orders={'mes_nombre': MESES_ORDEN}
        )

        fig_mensual.update_layout(
            hovermode='x unified',
            xaxis_title='Mes',
            yaxis_title='Cantidad de Trámites',
            legend_title='Año'
        )

        st.plotly_chart(fig_mensual, use_container_width=True)

        st.markdown("---")

        # 7. Análisis por Provincia
        st.markdown("### 🗺️ Análisis por Provincia")

        df_provincia = df.groupby('provincia')['cantidad'].sum().reset_index()
        df_provincia = df_provincia.sort_values('cantidad', ascending=False)

        col_prov1, col_prov2 = st.columns([2, 1])

        with col_prov1:
            fig_provincia = px.bar(
                df_provincia,
                x='cantidad',
                y='provincia',
                orientation='h',
                title='Trámites por Provincia',
                labels={'provincia': 'Provincia', 'cantidad': 'Cantidad'},
                text='cantidad',
                color='cantidad',
                color_continuous_scale='Viridis'
            )
            fig_provincia.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_provincia.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
            st.plotly_chart(fig_provincia, use_container_width=True)

        with col_prov2:
            fig_pie = px.pie(
                df_provincia,
                values='cantidad',
                names='provincia',
                title='Distribución Provincial'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")

        # 8. Top Marcas
        st.markdown("### 🏆 Top 10 Marcas")

        # Agrupar por marca: cantidad y edad promedio del titular
        df_marcas_agg = df.groupby('marca').agg({
            'cantidad': 'sum',
            'edad_promedio_titular': 'mean'
        }).reset_index()
        df_marcas_agg = df_marcas_agg.sort_values('cantidad', ascending=False).head(10)

        # Crear gráfico combinado con barras y línea
        fig_marcas = make_subplots(specs=[[{"secondary_y": True}]])

        # Barras de cantidad
        fig_marcas.add_trace(
            go.Bar(
                x=df_marcas_agg['marca'],
                y=df_marcas_agg['cantidad'],
                name='Cantidad',
                text=df_marcas_agg['cantidad'],
                texttemplate='%{text:,.0f}',
                textposition='outside',
                marker_color='lightsalmon'
            ),
            secondary_y=False
        )

        # Línea de edad promedio del titular
        fig_marcas.add_trace(
            go.Scatter(
                x=df_marcas_agg['marca'],
                y=df_marcas_agg['edad_promedio_titular'],
                name='Edad Promedio Titular (años)',
                mode='lines+markers+text',
                text=df_marcas_agg['edad_promedio_titular'].round(1),
                texttemplate='%{text:.1f} años',
                textposition='top center',
                line=dict(color='darkblue', width=3),
                marker=dict(size=10, color='darkblue')
            ),
            secondary_y=True
        )

        # Configurar ejes
        fig_marcas.update_xaxes(title_text="Marca")
        fig_marcas.update_yaxes(title_text="Cantidad de Trámites", secondary_y=False)
        fig_marcas.update_yaxes(title_text="Edad Promedio Titular (años)", secondary_y=True)

        fig_marcas.update_layout(
            title_text='Top 10 Marcas - Cantidad y Edad Promedio de Titulares',
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        st.plotly_chart(fig_marcas, use_container_width=True)

        # 8.1 Análisis Comparativo por Género
        if genero_seleccionado == 'Todos':
            st.markdown("#### 👥 Comparación por Género")

            # Agrupar por género
            df_genero = df.groupby('genero').agg({
                'cantidad': 'sum',
                'edad_promedio_titular': 'mean'
            }).reset_index()

            # Filtrar solo Masculino y Femenino (excluir "No aplica", "No identificado", etc.)
            df_genero = df_genero[df_genero['genero'].isin(['Masculino', 'Femenino'])]

            if not df_genero.empty:
                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    # Gráfico de cantidad por género
                    fig_genero_cant = px.bar(
                        df_genero,
                        x='genero',
                        y='cantidad',
                        title='Cantidad de Trámites por Género',
                        labels={'genero': 'Género', 'cantidad': 'Cantidad'},
                        text='cantidad',
                        color='genero',
                        color_discrete_map={'Masculino': 'lightblue', 'Femenino': 'pink'}
                    )
                    fig_genero_cant.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    fig_genero_cant.update_layout(showlegend=False)
                    st.plotly_chart(fig_genero_cant, use_container_width=True)

                with col_g2:
                    # Gráfico de edad promedio por género
                    fig_genero_edad = px.bar(
                        df_genero,
                        x='genero',
                        y='edad_promedio_titular',
                        title='Edad Promedio de Titulares por Género',
                        labels={'genero': 'Género', 'edad_promedio_titular': 'Edad Promedio (años)'},
                        text='edad_promedio_titular',
                        color='genero',
                        color_discrete_map={'Masculino': 'darkblue', 'Femenino': 'deeppink'}
                    )
                    fig_genero_edad.update_traces(texttemplate='%{text:.1f} años', textposition='outside')
                    fig_genero_edad.update_layout(showlegend=False)
                    st.plotly_chart(fig_genero_edad, use_container_width=True)

                # Métricas comparativas - verificar que existen ambos géneros
                col_gm1, col_gm2, col_gm3 = st.columns(3)

                masculino_data = df_genero[df_genero['genero'] == 'Masculino']
                femenino_data = df_genero[df_genero['genero'] == 'Femenino']

                if len(masculino_data) > 0 and len(femenino_data) > 0:
                    masculino = masculino_data.iloc[0]
                    femenino = femenino_data.iloc[0]

                    with col_gm1:
                        total_m = masculino['cantidad']
                        total_f = femenino['cantidad']
                        porc_m = (total_m / (total_m + total_f)) * 100
                        st.metric("Proporción Masculino", f"{porc_m:.1f}%", f"{total_m:,} trámites")

                    with col_gm2:
                        porc_f = 100 - porc_m
                        st.metric("Proporción Femenino", f"{porc_f:.1f}%", f"{total_f:,} trámites")

                    with col_gm3:
                        diff_edad = masculino['edad_promedio_titular'] - femenino['edad_promedio_titular']
                        genero_mayor = 'Masculino' if diff_edad > 0 else 'Femenino'
                        st.metric(
                            "Diferencia de Edad Promedio",
                            f"{abs(diff_edad):.1f} años",
                            f"{genero_mayor} mayor"
                        )
                elif len(masculino_data) > 0:
                    with col_gm1:
                        st.metric("Total Masculino", f"{masculino_data.iloc[0]['cantidad']:,} trámites")
                    with col_gm2:
                        st.info("ℹ️ No hay datos de género Femenino para comparar")
                elif len(femenino_data) > 0:
                    with col_gm1:
                        st.metric("Total Femenino", f"{femenino_data.iloc[0]['cantidad']:,} trámites")
                    with col_gm2:
                        st.info("ℹ️ No hay datos de género Masculino para comparar")

            st.markdown("---")

        # 8.2 Top Modelos por Marca (Interactivo)
        st.markdown("#### 🔍 Análisis de Modelos por Marca")

        # Obtener todas las marcas disponibles (no solo top 10) para el selectbox
        todas_marcas = df.groupby('marca')['cantidad'].sum().reset_index()
        todas_marcas = todas_marcas.sort_values('cantidad', ascending=False)
        lista_marcas = todas_marcas['marca'].tolist()

        # Selectbox para elegir marca
        marca_seleccionada = st.selectbox(
            "Selecciona una marca para ver sus modelos más vendidos:",
            options=['-- Ninguna --'] + lista_marcas,
            key=f"{tabla_nombre}_marca_modelos"
        )

        if marca_seleccionada != '-- Ninguna --':
            # Query para obtener modelos de la marca seleccionada
            query_modelos = text(f"""
                SELECT
                    automotor_modelo_descripcion as modelo,
                    COUNT(*) as cantidad,
                    AVG(EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento) as edad_promedio_titular
                FROM {tabla_nombre}
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND titular_domicilio_provincia = ANY(:provincias)
                {filtro_localidad}
                AND automotor_marca_descripcion = :marca
                AND automotor_modelo_descripcion IS NOT NULL
                AND automotor_modelo_descripcion != ''
                AND tramite_fecha IS NOT NULL
                AND titular_anio_nacimiento IS NOT NULL
                GROUP BY modelo
                ORDER BY cantidad DESC
                LIMIT 10
            """)

            try:
                df_modelos = pd.read_sql(query_modelos, engine, params={
                    'anios': anios_seleccionados,
                    'meses': meses_numeros,
                    'provincias': provincias_seleccionadas,
                    'marca': marca_seleccionada
                })

                if not df_modelos.empty:
                    # Gráfico combinado de Top 10 Modelos con edad promedio del titular
                    fig_modelos = make_subplots(specs=[[{"secondary_y": True}]])

                    # Barras de cantidad
                    fig_modelos.add_trace(
                        go.Bar(
                            x=df_modelos['modelo'],
                            y=df_modelos['cantidad'],
                            name='Cantidad',
                            text=df_modelos['cantidad'],
                            texttemplate='%{text:,.0f}',
                            textposition='outside',
                            marker_color='lightblue'
                        ),
                        secondary_y=False
                    )

                    # Línea de edad promedio del titular
                    fig_modelos.add_trace(
                        go.Scatter(
                            x=df_modelos['modelo'],
                            y=df_modelos['edad_promedio_titular'],
                            name='Edad Promedio Titular (años)',
                            mode='lines+markers+text',
                            text=df_modelos['edad_promedio_titular'].round(1),
                            texttemplate='%{text:.1f} años',
                            textposition='top center',
                            line=dict(color='darkgreen', width=3),
                            marker=dict(size=10, color='darkgreen')
                        ),
                        secondary_y=True
                    )

                    # Configurar ejes
                    fig_modelos.update_xaxes(title_text="Modelo", tickangle=-45)
                    fig_modelos.update_yaxes(title_text="Cantidad de Trámites", secondary_y=False)
                    fig_modelos.update_yaxes(title_text="Edad Promedio Titular (años)", secondary_y=True)

                    fig_modelos.update_layout(
                        title_text=f'Top 10 Modelos de {marca_seleccionada} - Cantidad y Edad Promedio de Titulares',
                        hovermode='x unified',
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )

                    st.plotly_chart(fig_modelos, use_container_width=True)

                    # Métricas de la marca seleccionada
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    with col_m1:
                        total_marca = df_modelos['cantidad'].sum()
                        st.metric("Total de la Marca", f"{total_marca:,}")
                    with col_m2:
                        modelos_unicos = len(df_modelos)
                        st.metric("Modelos en Top 10", modelos_unicos)
                    with col_m3:
                        if len(df_modelos) > 0:
                            modelo_top = df_modelos.iloc[0]['modelo']
                            cant_top = df_modelos.iloc[0]['cantidad']
                            st.metric("Modelo Más Vendido", f"{modelo_top[:20]}...", f"{cant_top:,}")
                    with col_m4:
                        edad_prom_titular = df_modelos['edad_promedio_titular'].mean()
                        st.metric("Edad Promedio Titular", f"{edad_prom_titular:.1f} años")
                else:
                    st.info(f"ℹ️ No se encontraron modelos para la marca {marca_seleccionada} con los filtros seleccionados")

            except Exception as e:
                st.error(f"❌ Error al consultar modelos: {e}")

        st.markdown("---")

        # 9. Tabla de datos detallada
        st.markdown("### 📋 Datos Detallados")

        # Preparar datos para tabla
        df_tabla = df.copy()
        df_tabla = df_tabla.sort_values(['anio', 'mes', 'provincia'], ascending=[False, True, True])

        # Reorganizar columnas
        df_tabla = df_tabla[['anio', 'mes_nombre', 'provincia', 'marca', 'tipo_vehiculo', 'cantidad']]
        df_tabla.columns = ['Año', 'Mes', 'Provincia', 'Marca', 'Tipo Vehículo', 'Cantidad']

        st.dataframe(df_tabla, use_container_width=True, hide_index=True, height=400)

        # Botón de descarga
        csv = df_tabla.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos (CSV)",
            data=csv,
            file_name=f"{tabla_nombre}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        # 10. Estadísticas adicionales
        with st.expander("📊 Ver Estadísticas Adicionales"):
            col_stat1, col_stat2, col_stat3 = st.columns(3)

            with col_stat1:
                st.markdown("**Por Tipo de Vehículo**")
                df_tipo = df.groupby('tipo_vehiculo')['cantidad'].sum().reset_index()
                df_tipo = df_tipo.sort_values('cantidad', ascending=False)
                for _, row in df_tipo.head(5).iterrows():
                    st.write(f"• {row['tipo_vehiculo']}: {format_number(row['cantidad'])}")

            with col_stat2:
                st.markdown("**Distribución Mensual**")
                df_mes_total = df.groupby('mes_nombre')['cantidad'].sum().reset_index()
                # Ordenar por orden de meses
                df_mes_total['mes_num'] = df_mes_total['mes_nombre'].map({v: k for k, v in MESES_ES.items()})
                df_mes_total = df_mes_total.sort_values('mes_num')
                for _, row in df_mes_total.iterrows():
                    st.write(f"• {row['mes_nombre']}: {format_number(row['cantidad'])}")

            with col_stat3:
                st.markdown("**Métricas Generales**")
                st.write(f"• Registros analizados: {format_number(len(df))}")
                st.write(f"• Cantidad promedio: {format_number(df['cantidad'].mean())}")
                st.write(f"• Máximo en un registro: {format_number(df['cantidad'].max())}")
                st.write(f"• Mínimo en un registro: {format_number(df['cantidad'].min())}")

    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        st.exception(e)


# ==================== TAB 1: INSCRIPCIONES ====================
with tab1:
    analizar_tramites('datos_gob_inscripciones', 'Inscripciones Iniciales (0km)', '🚗')

# ==================== TAB 2: TRANSFERENCIAS ====================
with tab2:
    analizar_tramites('datos_gob_transferencias', 'Transferencias de Vehículos Usados', '🔄')

# ==================== TAB 3: PRENDAS ====================
with tab3:
    st.header("💰 Prendas sobre Vehículos - Análisis Detallado")
    st.markdown("""
    **Clasificación de Prendas:**
    - **Prenda 0km**: Cuando `tramite_fecha = fecha_inscripcion_inicial` (financiamiento de vehículo nuevo)
    - **Prenda Usados**: Cuando `tramite_fecha ≠ fecha_inscripcion_inicial` (financiamiento de vehículo usado)
    """)

    # 1. Obtener años disponibles
    query_anios_prendas = text("""
        SELECT DISTINCT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio
        FROM datos_gob_prendas
        WHERE tramite_fecha IS NOT NULL
        ORDER BY anio DESC
    """)

    try:
        df_anios_prendas = pd.read_sql(query_anios_prendas, engine)
        anios_disponibles_prendas = df_anios_prendas['anio'].tolist() if not df_anios_prendas.empty else []
    except:
        anios_disponibles_prendas = []

    if not anios_disponibles_prendas:
        st.warning("⚠️ No hay datos disponibles en la tabla `datos_gob_prendas`")
    else:
        # 2. Filtros
        st.markdown("### 🎯 Filtros de Búsqueda")

        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)

        with col_filtro1:
            anios_sel_prendas = st.multiselect(
                "📅 Años",
                options=anios_disponibles_prendas,
                default=anios_disponibles_prendas[:2] if len(anios_disponibles_prendas) >= 2 else anios_disponibles_prendas,
                key="prendas_anios_v2"
            )

        with col_filtro2:
            meses_sel_prendas = st.multiselect(
                "📆 Meses",
                options=MESES_ORDEN,
                default=MESES_ORDEN,
                key="prendas_meses_v2"
            )

        # Obtener provincias disponibles
        query_prov_prendas = text("""
            SELECT DISTINCT titular_domicilio_provincia as provincia
            FROM datos_gob_prendas
            WHERE titular_domicilio_provincia IS NOT NULL
            AND titular_domicilio_provincia != ''
            ORDER BY provincia
        """)

        try:
            df_prov_prendas = pd.read_sql(query_prov_prendas, engine)
            provincias_disp_prendas = df_prov_prendas['provincia'].tolist()
        except:
            provincias_disp_prendas = []

        with col_filtro3:
            provincias_sel_prendas = st.multiselect(
                "📍 Provincias",
                options=provincias_disp_prendas,
                default=provincias_disp_prendas[:3] if len(provincias_disp_prendas) >= 3 else provincias_disp_prendas,
                key="prendas_provincias_v2"
            )

        if not anios_sel_prendas or not meses_sel_prendas or not provincias_sel_prendas:
            st.warning("⚠️ Selecciona al menos un año, un mes y una provincia")
        else:
            # Convertir meses a números
            meses_numeros_prendas = [list(MESES_ES.keys())[list(MESES_ES.values()).index(mes)] for mes in meses_sel_prendas]

            st.markdown("---")

            # 3. Consulta principal CON CLASIFICACIÓN 0km vs Usados
            query_prendas_clasificado = text("""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    titular_domicilio_provincia as provincia,
                    automotor_marca_descripcion as marca,
                    automotor_tipo_descripcion as tipo_vehiculo,
                    titular_genero as genero,
                    CASE
                        WHEN DATE(tramite_fecha) = DATE(fecha_inscripcion_inicial) THEN 'Prenda 0km'
                        ELSE 'Prenda Usados'
                    END as tipo_prenda,
                    COUNT(*) as cantidad,
                    AVG(EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento) as edad_promedio_titular,
                    AVG(EXTRACT(YEAR FROM tramite_fecha) - EXTRACT(YEAR FROM fecha_inscripcion_inicial)) as antiguedad_promedio_vehiculo
                FROM datos_gob_prendas
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND titular_domicilio_provincia = ANY(:provincias)
                AND tramite_fecha IS NOT NULL
                AND fecha_inscripcion_inicial IS NOT NULL
                GROUP BY anio, mes, provincia, marca, tipo_vehiculo, genero, tipo_prenda
                ORDER BY anio, mes, provincia
            """)

            try:
                df_prendas = pd.read_sql(query_prendas_clasificado, engine, params={
                    'anios': anios_sel_prendas,
                    'meses': meses_numeros_prendas,
                    'provincias': provincias_sel_prendas
                })

                if df_prendas.empty:
                    st.warning("⚠️ No se encontraron datos con los filtros seleccionados")
                else:
                    df_prendas['mes_nombre'] = df_prendas['mes'].map(MESES_ES)

                    # 4. KPIs PRINCIPALES CON DISTINCIÓN 0km vs Usados
                    st.markdown("### 📊 Métricas Principales - Clasificación 0km vs Usados")

                    total_prendas = df_prendas['cantidad'].sum()
                    total_0km = df_prendas[df_prendas['tipo_prenda'] == 'Prenda 0km']['cantidad'].sum()
                    total_usados = df_prendas[df_prendas['tipo_prenda'] == 'Prenda Usados']['cantidad'].sum()
                    pct_0km = (total_0km / total_prendas * 100) if total_prendas > 0 else 0
                    pct_usados = (total_usados / total_prendas * 100) if total_prendas > 0 else 0

                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        st.metric("Total Prendas", format_number(total_prendas))

                    with col2:
                        st.metric("🆕 Prendas 0km", format_number(total_0km), f"{pct_0km:.1f}%")

                    with col3:
                        st.metric("🔄 Prendas Usados", format_number(total_usados), f"{pct_usados:.1f}%")

                    with col4:
                        edad_prom_0km = df_prendas[df_prendas['tipo_prenda'] == 'Prenda 0km']['edad_promedio_titular'].mean()
                        st.metric("Edad Prom. Titular (0km)", f"{edad_prom_0km:.1f} años" if pd.notna(edad_prom_0km) else "N/A")

                    with col5:
                        edad_prom_usados = df_prendas[df_prendas['tipo_prenda'] == 'Prenda Usados']['edad_promedio_titular'].mean()
                        st.metric("Edad Prom. Titular (Usados)", f"{edad_prom_usados:.1f} años" if pd.notna(edad_prom_usados) else "N/A")

                    # Métricas adicionales de antigüedad de vehículos
                    col_ant1, col_ant2, col_ant3 = st.columns(3)

                    with col_ant1:
                        st.metric("Marcas Únicas", df_prendas['marca'].nunique())

                    with col_ant2:
                        antig_0km = df_prendas[df_prendas['tipo_prenda'] == 'Prenda 0km']['antiguedad_promedio_vehiculo'].mean()
                        st.metric("Antigüedad Vehículo (0km)", f"{antig_0km:.1f} años" if pd.notna(antig_0km) else "0 años")

                    with col_ant3:
                        antig_usados = df_prendas[df_prendas['tipo_prenda'] == 'Prenda Usados']['antiguedad_promedio_vehiculo'].mean()
                        st.metric("Antigüedad Vehículo (Usados)", f"{antig_usados:.1f} años" if pd.notna(antig_usados) else "N/A")

                    st.markdown("---")

                    # 5. GRÁFICO DE DISTRIBUCIÓN 0km vs Usados
                    st.markdown("### 📊 Distribución de Prendas: 0km vs Usados")

                    col_graf1, col_graf2 = st.columns(2)

                    with col_graf1:
                        df_tipo_prenda = df_prendas.groupby('tipo_prenda')['cantidad'].sum().reset_index()

                        fig_pie = px.pie(
                            df_tipo_prenda,
                            values='cantidad',
                            names='tipo_prenda',
                            title='Distribución Total de Prendas',
                            color='tipo_prenda',
                            color_discrete_map={'Prenda 0km': '#2ecc71', 'Prenda Usados': '#3498db'},
                            hole=0.4
                        )
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_pie, use_container_width=True)

                    with col_graf2:
                        # Evolución mensual por tipo de prenda
                        df_mensual_tipo = df_prendas.groupby(['anio', 'mes', 'mes_nombre', 'tipo_prenda'])['cantidad'].sum().reset_index()

                        fig_evol = px.line(
                            df_mensual_tipo,
                            x='mes_nombre',
                            y='cantidad',
                            color='tipo_prenda',
                            line_dash='anio' if len(anios_sel_prendas) > 1 else None,
                            title='Evolución Mensual por Tipo de Prenda',
                            labels={'mes_nombre': 'Mes', 'cantidad': 'Cantidad', 'tipo_prenda': 'Tipo'},
                            markers=True,
                            category_orders={'mes_nombre': MESES_ORDEN},
                            color_discrete_map={'Prenda 0km': '#2ecc71', 'Prenda Usados': '#3498db'}
                        )
                        fig_evol.update_layout(hovermode='x unified')
                        st.plotly_chart(fig_evol, use_container_width=True)

                    st.markdown("---")

                    # 6. Comparación YoY por Tipo de Prenda
                    st.markdown("### 📈 Comparación Anual por Tipo de Prenda")

                    df_anual_tipo = df_prendas.groupby(['anio', 'tipo_prenda'])['cantidad'].sum().reset_index()

                    fig_bar_tipo = px.bar(
                        df_anual_tipo,
                        x='anio',
                        y='cantidad',
                        color='tipo_prenda',
                        barmode='group',
                        title='Prendas por Año: 0km vs Usados',
                        labels={'anio': 'Año', 'cantidad': 'Cantidad', 'tipo_prenda': 'Tipo'},
                        text='cantidad',
                        color_discrete_map={'Prenda 0km': '#2ecc71', 'Prenda Usados': '#3498db'}
                    )
                    fig_bar_tipo.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    fig_bar_tipo.update_layout(xaxis_type='category')
                    st.plotly_chart(fig_bar_tipo, use_container_width=True)

                    st.markdown("---")

                    # 7. Top Marcas por Tipo de Prenda
                    st.markdown("### 🏆 Top 10 Marcas por Tipo de Prenda")

                    col_marcas1, col_marcas2 = st.columns(2)

                    with col_marcas1:
                        df_marcas_0km = df_prendas[df_prendas['tipo_prenda'] == 'Prenda 0km'].groupby('marca')['cantidad'].sum().nlargest(10).reset_index()

                        if not df_marcas_0km.empty:
                            fig_marcas_0km = px.bar(
                                df_marcas_0km,
                                x='cantidad',
                                y='marca',
                                orientation='h',
                                title='Top 10 Marcas - Prendas 0km',
                                labels={'marca': 'Marca', 'cantidad': 'Cantidad'},
                                text='cantidad',
                                color='cantidad',
                                color_continuous_scale='Greens'
                            )
                            fig_marcas_0km.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                            fig_marcas_0km.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
                            st.plotly_chart(fig_marcas_0km, use_container_width=True)
                        else:
                            st.info("No hay datos de marcas para prendas 0km")

                    with col_marcas2:
                        df_marcas_usados = df_prendas[df_prendas['tipo_prenda'] == 'Prenda Usados'].groupby('marca')['cantidad'].sum().nlargest(10).reset_index()

                        if not df_marcas_usados.empty:
                            fig_marcas_usados = px.bar(
                                df_marcas_usados,
                                x='cantidad',
                                y='marca',
                                orientation='h',
                                title='Top 10 Marcas - Prendas Usados',
                                labels={'marca': 'Marca', 'cantidad': 'Cantidad'},
                                text='cantidad',
                                color='cantidad',
                                color_continuous_scale='Blues'
                            )
                            fig_marcas_usados.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                            fig_marcas_usados.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
                            st.plotly_chart(fig_marcas_usados, use_container_width=True)
                        else:
                            st.info("No hay datos de marcas para prendas usados")

                    st.markdown("---")

                    # 8. Análisis por Provincia
                    st.markdown("### 🗺️ Distribución Provincial por Tipo de Prenda")

                    df_prov_tipo = df_prendas.groupby(['provincia', 'tipo_prenda'])['cantidad'].sum().reset_index()
                    df_prov_total = df_prov_tipo.groupby('provincia')['cantidad'].sum().nlargest(10).index.tolist()
                    df_prov_tipo_top = df_prov_tipo[df_prov_tipo['provincia'].isin(df_prov_total)]

                    fig_prov_tipo = px.bar(
                        df_prov_tipo_top,
                        x='provincia',
                        y='cantidad',
                        color='tipo_prenda',
                        title='Top 10 Provincias - Distribución 0km vs Usados',
                        labels={'provincia': 'Provincia', 'cantidad': 'Cantidad', 'tipo_prenda': 'Tipo'},
                        barmode='stack',
                        color_discrete_map={'Prenda 0km': '#2ecc71', 'Prenda Usados': '#3498db'}
                    )
                    st.plotly_chart(fig_prov_tipo, use_container_width=True)

                    st.markdown("---")

                    # 9. Tabla resumen
                    st.markdown("### 📋 Resumen por Tipo de Prenda")

                    df_resumen = df_prendas.groupby('tipo_prenda').agg({
                        'cantidad': 'sum',
                        'edad_promedio_titular': 'mean',
                        'antiguedad_promedio_vehiculo': 'mean',
                        'marca': 'nunique'
                    }).reset_index()

                    df_resumen.columns = ['Tipo de Prenda', 'Total', 'Edad Prom. Titular', 'Antigüedad Prom. Vehículo', 'Marcas Únicas']
                    df_resumen['% del Total'] = (df_resumen['Total'] / df_resumen['Total'].sum() * 100).round(1)
                    df_resumen['Total'] = df_resumen['Total'].apply(lambda x: f"{int(x):,}")
                    df_resumen['Edad Prom. Titular'] = df_resumen['Edad Prom. Titular'].apply(lambda x: f"{x:.1f} años" if pd.notna(x) else "N/A")
                    df_resumen['Antigüedad Prom. Vehículo'] = df_resumen['Antigüedad Prom. Vehículo'].apply(lambda x: f"{x:.1f} años" if pd.notna(x) else "N/A")
                    df_resumen['% del Total'] = df_resumen['% del Total'].apply(lambda x: f"{x}%")

                    st.dataframe(df_resumen, use_container_width=True, hide_index=True)

                    # Botón de descarga
                    csv_prendas = df_prendas.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar datos de prendas (CSV)",
                        data=csv_prendas,
                        file_name=f"prendas_clasificadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

            except Exception as e:
                st.error(f"❌ Error al cargar datos: {str(e)}")
                st.exception(e)

# ==================== TAB 4: REGISTRO POR LOCALIDAD ====================
with tab4:
    st.header("📍 Registro por Localidad - Inscripciones de Vehículos")
    st.markdown("Análisis de inscripciones agrupadas por provincia y localidad del titular")

    query_localidades = text("""
        SELECT
            titular_domicilio_provincia as provincia,
            titular_domicilio_localidad as localidad,
            COUNT(*) as total_inscripciones,
            COUNT(DISTINCT automotor_origen) as origenes,
            COUNT(DISTINCT EXTRACT(YEAR FROM tramite_fecha)) as anios_activos
        FROM datos_gob_inscripciones
        WHERE titular_domicilio_provincia IS NOT NULL
        AND titular_domicilio_provincia != ''
        AND titular_domicilio_localidad IS NOT NULL
        AND titular_domicilio_localidad != ''
        GROUP BY titular_domicilio_provincia, titular_domicilio_localidad
        ORDER BY total_inscripciones DESC
    """)

    try:
        df_localidades = pd.read_sql(query_localidades, engine)

        if not df_localidades.empty:
            st.success(f"✅ {len(df_localidades):,} localidades con inscripciones registradas")

            # Filtros
            col_f1, col_f2 = st.columns(2)

            with col_f1:
                provincias_disponibles = sorted(df_localidades['provincia'].unique())
                provincia_filtro = st.multiselect(
                    "🏙️ Filtrar por provincia:",
                    options=provincias_disponibles,
                    default=provincias_disponibles[:5] if len(provincias_disponibles) >= 5 else provincias_disponibles,
                    key="localidad_provincia"
                )

            with col_f2:
                buscar_localidad = st.text_input("🔍 Buscar localidad:", "")

            # Aplicar filtros
            df_filtrado = df_localidades.copy()

            if provincia_filtro:
                df_filtrado = df_filtrado[df_filtrado['provincia'].isin(provincia_filtro)]

            if buscar_localidad:
                df_filtrado = df_filtrado[
                    df_filtrado['localidad'].str.contains(buscar_localidad, case=False, na=False)
                ]

            st.markdown("---")

            # Métricas
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Localidades", f"{len(df_filtrado):,}")

            with col2:
                st.metric("Total Provincias", df_filtrado['provincia'].nunique())

            with col3:
                total_insc = df_filtrado['total_inscripciones'].sum()
                st.metric("Total Inscripciones", f"{int(total_insc):,}")

            with col4:
                prom_insc = df_filtrado['total_inscripciones'].mean()
                st.metric("Promedio por Localidad", f"{int(prom_insc):,}")

            st.markdown("---")

            # Top 20 Localidades
            st.markdown("### 🏆 Top 20 Localidades por Inscripciones")

            df_top20 = df_filtrado.nlargest(20, 'total_inscripciones').copy()

            col_top1, col_top2 = st.columns([3, 2])

            with col_top1:
                fig_top = px.bar(
                    df_top20,
                    y='localidad',
                    x='total_inscripciones',
                    color='provincia',
                    orientation='h',
                    title='Top 20 Localidades con más Inscripciones',
                    labels={'localidad': 'Localidad', 'total_inscripciones': 'Inscripciones', 'provincia': 'Provincia'},
                    text='total_inscripciones',
                    hover_data=['provincia', 'localidad', 'total_inscripciones']
                )
                fig_top.update_traces(textposition='outside')
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=True, height=600)
                st.plotly_chart(fig_top, use_container_width=True)

            with col_top2:
                # Mostrar tabla de top 10
                st.markdown("#### 📊 Top 10 Detalle")
                df_top10_display = df_top20.head(10)[['localidad', 'provincia', 'total_inscripciones']].copy()
                df_top10_display.columns = ['Localidad', 'Provincia', 'Inscripciones']
                df_top10_display.index = range(1, len(df_top10_display) + 1)
                st.dataframe(df_top10_display, use_container_width=True)

            st.markdown("---")

            # Distribución por provincia
            st.markdown("### 🗺️ Distribución por Provincia")

            df_prov_stats = df_filtrado.groupby('provincia').agg({
                'localidad': 'count',
                'total_inscripciones': 'sum'
            }).reset_index()
            df_prov_stats.columns = ['provincia', 'cantidad_localidades', 'total_inscripciones']
            df_prov_stats = df_prov_stats.sort_values('total_inscripciones', ascending=False)

            col_prov1, col_prov2 = st.columns(2)

            with col_prov1:
                fig_prov_insc = px.bar(
                    df_prov_stats.head(15),
                    x='total_inscripciones',
                    y='provincia',
                    orientation='h',
                    title='Top 15 Provincias - Total Inscripciones',
                    labels={'provincia': 'Provincia', 'total_inscripciones': 'Inscripciones'},
                    text='total_inscripciones',
                    color='total_inscripciones',
                    color_continuous_scale='Viridis'
                )
                fig_prov_insc.update_traces(textposition='outside')
                fig_prov_insc.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                st.plotly_chart(fig_prov_insc, use_container_width=True)

            with col_prov2:
                fig_prov_loc = px.bar(
                    df_prov_stats.head(15),
                    x='cantidad_localidades',
                    y='provincia',
                    orientation='h',
                    title='Top 15 Provincias - Cantidad de Localidades',
                    labels={'provincia': 'Provincia', 'cantidad_localidades': 'Localidades'},
                    text='cantidad_localidades',
                    color='cantidad_localidades',
                    color_continuous_scale='Teal'
                )
                fig_prov_loc.update_traces(textposition='outside')
                fig_prov_loc.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                st.plotly_chart(fig_prov_loc, use_container_width=True)

            st.markdown("---")

            # Tabla completa de localidades
            st.markdown("### 📋 Tabla Completa de Localidades")

            # Formatear para visualización
            df_display = df_filtrado.copy()
            df_display['total_inscripciones'] = df_display['total_inscripciones'].apply(lambda x: f"{int(x):,}")
            df_display.columns = ['Provincia', 'Localidad', 'Total Inscripciones', 'Orígenes', 'Años Activos']

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    "Total Inscripciones": st.column_config.TextColumn("Total Inscripciones", width="medium"),
                    "Localidad": st.column_config.TextColumn("Localidad", width="large"),
                }
            )

            # Botón de descarga
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar datos por localidad (CSV)",
                data=csv,
                file_name=f"inscripciones_por_localidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ No hay datos de inscripciones por localidad")
            st.info("💡 Para cargar datos:\n\n"
                    "1. Descarga datos CSV desde datos.gob.ar\n"
                    "2. Coloca los archivos en `INPUT/INSCRIPCIONES/`\n"
                    "3. Ejecuta el script de carga")

    except Exception as e:
        st.error(f"❌ Error al cargar datos de localidades: {str(e)}")
        st.exception(e)

# ==================== TAB 5: ANÁLISIS DETALLADO ====================
with tab5:
    st.header("🔬 Análisis Detallado - Perfil de Compradores y Prendas")
    st.markdown("Análisis personalizado cruzando datos de inscripciones, edad de compradores y prendas")

    # 1. Obtener años disponibles desde inscripciones
    query_anios_detalle = text("""
        SELECT DISTINCT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio
        FROM datos_gob_inscripciones
        WHERE tramite_fecha IS NOT NULL
        ORDER BY anio DESC
    """)

    try:
        df_anios_detalle = pd.read_sql(query_anios_detalle, engine)
        anios_disponibles_detalle = df_anios_detalle['anio'].tolist() if not df_anios_detalle.empty else []
    except:
        anios_disponibles_detalle = []

    if not anios_disponibles_detalle:
        st.warning("⚠️ No hay datos disponibles para el análisis detallado")
        st.info("💡 **Para cargar datos:**\n\n"
                "1. Descarga datos CSV desde datos.gob.ar\n"
                "2. Coloca los archivos en `INPUT/INSCRIPCIONES/` y `INPUT/PRENDAS/`\n"
                "3. Ejecuta: `python cargar_datos_gob_ar_postgresql.py`")
    else:
        # 2. FILTROS PERSONALIZABLES
        st.markdown("### 🎯 Filtros de Análisis")

        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)

        with col_f1:
            anio_seleccionado = st.selectbox(
                "📅 Año",
                options=anios_disponibles_detalle,
                index=0,
                key="detalle_anio"
            )

        with col_f2:
            meses_seleccionados_detalle = st.multiselect(
                "📆 Meses",
                options=MESES_ORDEN,
                default=MESES_ORDEN,
                key="detalle_meses"
            )

        with col_f3:
            origen_seleccionado = st.selectbox(
                "🌍 Origen",
                options=["Ambos", "Nacional", "Importado"],
                index=0,
                key="detalle_origen"
            )

        with col_f4:
            tipo_persona_seleccionado = st.selectbox(
                "👤 Tipo Persona",
                options=["Ambos", "Física", "Jurídica"],
                index=0,
                key="detalle_tipo_persona"
            )

        with col_f5:
            genero_seleccionado = st.selectbox(
                "⚧ Género",
                options=["Todos", "Masculino", "Femenino", "No Aplica", "No Identificado"],
                index=0,
                key="detalle_genero"
            )

        # Obtener provincias disponibles para el filtro global
        query_provincias_global = text(f"""
            SELECT DISTINCT titular_domicilio_provincia as provincia
            FROM datos_gob_inscripciones
            WHERE EXTRACT(YEAR FROM tramite_fecha) = :anio
            AND titular_domicilio_provincia IS NOT NULL
            AND titular_domicilio_provincia != ''
            ORDER BY provincia
        """)

        try:
            df_provincias_global = pd.read_sql(query_provincias_global, engine, params={'anio': anio_seleccionado})
            provincias_disponibles_global = df_provincias_global['provincia'].tolist()
        except:
            provincias_disponibles_global = []

        # Filtro de provincias (transversal a todos los gráficos)
        st.markdown("#### 🏙️ Provincias")
        provincias_seleccionadas = st.multiselect(
            "Selecciona una o más provincias para filtrar todos los gráficos:",
            options=provincias_disponibles_global,
            default=provincias_disponibles_global[:3] if len(provincias_disponibles_global) >= 3 else provincias_disponibles_global,
            key="provincias_global"
        )

        # Filtro de localidades (basado en provincias seleccionadas)
        st.markdown("#### 📍 Localidades")

        if provincias_seleccionadas:
            query_localidades_global = text("""
                SELECT DISTINCT titular_domicilio_localidad as localidad
                FROM datos_gob_inscripciones
                WHERE EXTRACT(YEAR FROM tramite_fecha) = :anio
                AND titular_domicilio_provincia = ANY(:provincias)
                AND titular_domicilio_localidad IS NOT NULL
                AND titular_domicilio_localidad != ''
                ORDER BY localidad
            """)

            try:
                df_localidades_global = pd.read_sql(
                    query_localidades_global,
                    engine,
                    params={'anio': anio_seleccionado, 'provincias': provincias_seleccionadas}
                )
                localidades_disponibles_global = df_localidades_global['localidad'].tolist()
            except:
                localidades_disponibles_global = []

            localidades_seleccionadas = st.multiselect(
                "Selecciona localidades (opcional - si no seleccionas ninguna, se mostrarán todas):",
                options=localidades_disponibles_global,
                default=[],  # Por defecto ninguna seleccionada = todas
                key="localidades_global"
            )
        else:
            localidades_seleccionadas = []

        if not meses_seleccionados_detalle:
            st.warning("⚠️ Selecciona al menos un mes")
        elif not provincias_seleccionadas:
            st.warning("⚠️ Selecciona al menos una provincia")
        else:
            # Convertir meses a números
            meses_numeros_detalle = [list(MESES_ES.keys())[list(MESES_ES.values()).index(mes)] for mes in meses_seleccionados_detalle]

            st.markdown("---")

            # Advertencia sobre Personas Jurídicas
            if tipo_persona_seleccionado == "Jurídica":
                st.info("ℹ️ **Nota:** Las Personas Jurídicas (empresas) no tienen edad registrada, por lo que el análisis demográfico estará vacío o muy limitado. Se recomienda seleccionar 'Física' o 'Ambos' para ver análisis de edades.")

            # 3. CONSULTA PRINCIPAL - INSCRIPCIONES CON EDAD
            # Construir filtros WHERE dinámicos
            filtro_origen = ""
            if origen_seleccionado != "Ambos":
                filtro_origen = f"AND UPPER(automotor_origen) = '{origen_seleccionado.upper()}'"

            filtro_tipo_persona = ""
            if tipo_persona_seleccionado == "Física":
                filtro_tipo_persona = "AND titular_tipo_persona = 'Física'"
            elif tipo_persona_seleccionado == "Jurídica":
                filtro_tipo_persona = "AND titular_tipo_persona = 'Jurídica'"

            filtro_genero = ""
            if genero_seleccionado != "Todos":
                filtro_genero = f"AND titular_genero = '{genero_seleccionado}'"

            filtro_localidad = ""
            if localidades_seleccionadas:
                filtro_localidad = "AND titular_domicilio_localidad = ANY(:localidades)"

            query_inscripciones_edad = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento as edad,
                    automotor_marca_descripcion as marca,
                    automotor_tipo_descripcion as tipo_vehiculo,
                    automotor_origen as origen,
                    titular_tipo_persona as tipo_persona,
                    titular_genero as genero,
                    titular_domicilio_provincia as provincia,
                    COUNT(*) as cantidad
                FROM datos_gob_inscripciones
                WHERE EXTRACT(YEAR FROM tramite_fecha) = :anio
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND titular_domicilio_provincia = ANY(:provincias)
                {filtro_localidad}
                AND tramite_fecha IS NOT NULL
                AND titular_anio_nacimiento IS NOT NULL
                AND titular_anio_nacimiento > 0
                {filtro_origen}
                {filtro_tipo_persona}
                {filtro_genero}
                GROUP BY edad, marca, tipo_vehiculo, origen, tipo_persona, genero, provincia
                HAVING EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento BETWEEN 18 AND 100
                ORDER BY edad
            """)

            try:
                params_inscripciones = {
                    'anio': anio_seleccionado,
                    'meses': meses_numeros_detalle,
                    'provincias': provincias_seleccionadas
                }
                if localidades_seleccionadas:
                    params_inscripciones['localidades'] = localidades_seleccionadas

                df_inscripciones = pd.read_sql(query_inscripciones_edad, engine, params=params_inscripciones)

                if df_inscripciones.empty:
                    st.warning("⚠️ No se encontraron inscripciones con los filtros seleccionados")
                else:
                    # 4. CONSULTA DE PRENDAS CON EDAD
                    query_prendas_edad = text(f"""
                        SELECT
                            EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento as edad,
                            automotor_marca_descripcion as marca,
                            automotor_tipo_descripcion as tipo_vehiculo,
                            automotor_origen as origen,
                            titular_tipo_persona as tipo_persona,
                            titular_genero as genero,
                            titular_domicilio_provincia as provincia,
                            COUNT(*) as cantidad_prendas
                        FROM datos_gob_prendas
                        WHERE EXTRACT(YEAR FROM tramite_fecha) = :anio
                        AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                        AND titular_domicilio_provincia = ANY(:provincias)
                        {filtro_localidad}
                        AND tramite_fecha IS NOT NULL
                        AND titular_anio_nacimiento IS NOT NULL
                        AND titular_anio_nacimiento > 0
                        {filtro_origen}
                        {filtro_tipo_persona}
                        {filtro_genero}
                        GROUP BY edad, marca, tipo_vehiculo, origen, tipo_persona, genero, provincia
                        HAVING EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento BETWEEN 18 AND 100
                        ORDER BY edad
                    """)

                    params_prendas = {
                        'anio': anio_seleccionado,
                        'meses': meses_numeros_detalle,
                        'provincias': provincias_seleccionadas
                    }
                    if localidades_seleccionadas:
                        params_prendas['localidades'] = localidades_seleccionadas

                    df_prendas = pd.read_sql(query_prendas_edad, engine, params=params_prendas)

                    # 5. KPIs PRINCIPALES
                    st.markdown("### 📊 Métricas Principales")

                    col1, col2, col3, col4 = st.columns(4)

                    total_inscripciones = df_inscripciones['cantidad'].sum()
                    total_prendas = df_prendas['cantidad_prendas'].sum() if not df_prendas.empty else 0
                    porcentaje_prendas = (total_prendas / total_inscripciones * 100) if total_inscripciones > 0 else 0
                    edad_promedio = (df_inscripciones['edad'] * df_inscripciones['cantidad']).sum() / total_inscripciones if total_inscripciones > 0 else 0

                    with col1:
                        st.metric("Total Inscripciones", format_number(total_inscripciones))

                    with col2:
                        st.metric("Total Prendas", format_number(total_prendas))

                    with col3:
                        st.metric("% Prendas", f"{porcentaje_prendas:.1f}%")

                    with col4:
                        st.metric("Edad Promedio", f"{edad_promedio:.0f} años")

                    st.markdown("---")

                    # 6. GRÁFICO 1: DISTRIBUCIÓN DE EDADES DE COMPRADORES
                    st.markdown("### 👥 Gráfico 1: Distribución de Edades de Compradores")

                    df_edades_compradores = df_inscripciones.groupby('edad')['cantidad'].sum().reset_index()
                    df_edades_compradores = df_edades_compradores.sort_values('edad')

                    fig_edades = px.bar(
                        df_edades_compradores,
                        x='edad',
                        y='cantidad',
                        title=f'Distribución de Edades de Compradores - Año {anio_seleccionado}',
                        labels={'edad': 'Edad (años)', 'cantidad': 'Cantidad de Compradores'},
                        color='cantidad',
                        color_continuous_scale='Blues'
                    )
                    fig_edades.update_layout(
                        xaxis_title='Edad (años)',
                        yaxis_title='Cantidad de Compradores',
                        showlegend=False,
                        hovermode='x'
                    )
                    st.plotly_chart(fig_edades, use_container_width=True)

                    # Estadísticas de edad
                    if not df_edades_compradores.empty and len(df_edades_compradores) > 0:
                        col_edad1, col_edad2, col_edad3 = st.columns(3)
                        with col_edad1:
                            edad_mas_comun = df_edades_compradores.loc[df_edades_compradores['cantidad'].idxmax(), 'edad']
                            st.info(f"🎯 **Edad más frecuente:** {int(edad_mas_comun)} años")
                        with col_edad2:
                            st.info(f"📊 **Edad mínima:** {int(df_edades_compradores['edad'].min())} años")
                        with col_edad3:
                            st.info(f"📊 **Edad máxima:** {int(df_edades_compradores['edad'].max())} años")

                    st.markdown("---")

                    # 7. GRÁFICO 2: PRENDAS POR EDAD
                    st.markdown("### 💰 Gráfico 2: Prendas por Edad del Comprador")

                    if not df_prendas.empty:
                        df_prendas_edad = df_prendas.groupby('edad')['cantidad_prendas'].sum().reset_index()
                        df_prendas_edad = df_prendas_edad.sort_values('edad')

                        # Calcular porcentaje de financiación por edad
                        df_edad_completo = df_edades_compradores.merge(
                            df_prendas_edad,
                            on='edad',
                            how='left'
                        )
                        df_edad_completo['cantidad_prendas'] = df_edad_completo['cantidad_prendas'].fillna(0)
                        df_edad_completo['porcentaje_prenda'] = (df_edad_completo['cantidad_prendas'] / df_edad_completo['cantidad'] * 100)

                        # Gráfico de barras de prendas por edad
                        fig_prendas_edad = px.bar(
                            df_prendas_edad,
                            x='edad',
                            y='cantidad_prendas',
                            title=f'Cantidad de Prendas por Edad - Año {anio_seleccionado}',
                            labels={'edad': 'Edad (años)', 'cantidad_prendas': 'Cantidad de Prendas'},
                            color='cantidad_prendas',
                            color_continuous_scale='Oranges'
                        )
                        fig_prendas_edad.update_layout(
                            xaxis_title='Edad (años)',
                            yaxis_title='Cantidad de Prendas',
                            showlegend=False,
                            hovermode='x'
                        )
                        st.plotly_chart(fig_prendas_edad, use_container_width=True)

                        # Gráfico de línea: porcentaje de financiación por edad
                        fig_porc_prenda = px.line(
                            df_edad_completo,
                            x='edad',
                            y='porcentaje_prenda',
                            title=f'Porcentaje de Financiación por Edad - Año {anio_seleccionado}',
                            labels={'edad': 'Edad (años)', 'porcentaje_prenda': '% Financiación'},
                            markers=True
                        )
                        fig_porc_prenda.update_traces(line_color='#FF6B35')
                        fig_porc_prenda.update_layout(
                            xaxis_title='Edad (años)',
                            yaxis_title='% Financiación',
                            hovermode='x'
                        )
                        st.plotly_chart(fig_porc_prenda, use_container_width=True)

                        # Estadísticas de prendas por edad
                        if not df_prendas_edad.empty and len(df_prendas_edad) > 0:
                            edad_max_prendas = df_prendas_edad.loc[df_prendas_edad['cantidad_prendas'].idxmax(), 'edad']
                            edad_max_porc = df_edad_completo.loc[df_edad_completo['porcentaje_prenda'].idxmax(), 'edad']

                            col_prenda1, col_prenda2 = st.columns(2)
                            with col_prenda1:
                                st.info(f"🎯 **Edad con más prendas:** {int(edad_max_prendas)} años ({int(df_prendas_edad.loc[df_prendas_edad['edad']==edad_max_prendas, 'cantidad_prendas'].values[0])} prendas)")
                            with col_prenda2:
                                st.info(f"💰 **Edad con mayor % financiación:** {int(edad_max_porc)} años ({df_edad_completo.loc[df_edad_completo['edad']==edad_max_porc, 'porcentaje_prenda'].values[0]:.1f}%)")

                    else:
                        st.warning("⚠️ No se encontraron prendas con los filtros seleccionados")

                    st.markdown("---")

                    # 8. GRÁFICO 3: PRENDAS POR MARCA
                    st.markdown("### 🏆 Gráfico 3: Prendas por Marca")

                    if not df_prendas.empty:
                        df_prendas_marca = df_prendas.groupby('marca')['cantidad_prendas'].sum().reset_index()
                        df_prendas_marca = df_prendas_marca.sort_values('cantidad_prendas', ascending=False).head(15)

                        # Calcular porcentaje de financiación por marca
                        df_inscripciones_marca = df_inscripciones.groupby('marca')['cantidad'].sum().reset_index()
                        df_marca_completo = df_prendas_marca.merge(
                            df_inscripciones_marca,
                            on='marca',
                            how='left'
                        )
                        df_marca_completo['porcentaje_prenda'] = (df_marca_completo['cantidad_prendas'] / df_marca_completo['cantidad'] * 100)
                        df_marca_completo = df_marca_completo.sort_values('cantidad_prendas', ascending=False)

                        col_marca1, col_marca2 = st.columns(2)

                        with col_marca1:
                            fig_prendas_marca = px.bar(
                                df_marca_completo,
                                x='cantidad_prendas',
                                y='marca',
                                orientation='h',
                                title='Top 15 Marcas - Cantidad de Prendas',
                                labels={'marca': 'Marca', 'cantidad_prendas': 'Cantidad de Prendas'},
                                text='cantidad_prendas',
                                color='cantidad_prendas',
                                color_continuous_scale='Reds'
                            )
                            fig_prendas_marca.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                            fig_prendas_marca.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                            st.plotly_chart(fig_prendas_marca, use_container_width=True)

                        with col_marca2:
                            fig_porc_marca = px.bar(
                                df_marca_completo,
                                x='porcentaje_prenda',
                                y='marca',
                                orientation='h',
                                title='Top 15 Marcas - % Financiación',
                                labels={'marca': 'Marca', 'porcentaje_prenda': '% Financiación'},
                                text='porcentaje_prenda',
                                color='porcentaje_prenda',
                                color_continuous_scale='Greens'
                            )
                            fig_porc_marca.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                            fig_porc_marca.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                            st.plotly_chart(fig_porc_marca, use_container_width=True)

                        # Marcas más financiadas
                        if not df_marca_completo.empty and len(df_marca_completo) > 0:
                            marca_max_prendas = df_marca_completo.iloc[0]['marca']
                            marca_max_porc = df_marca_completo.loc[df_marca_completo['porcentaje_prenda'].idxmax(), 'marca']

                            col_m1, col_m2 = st.columns(2)
                            with col_m1:
                                st.success(f"🥇 **Marca con más prendas:** {marca_max_prendas} ({int(df_marca_completo.iloc[0]['cantidad_prendas'])} prendas)")
                            with col_m2:
                                st.success(f"💰 **Marca con mayor % financiación:** {marca_max_porc} ({df_marca_completo.loc[df_marca_completo['marca']==marca_max_porc, 'porcentaje_prenda'].values[0]:.1f}%)")

                    st.markdown("---")

                    # 9. GRÁFICO 4: PRENDAS POR MARCA Y TIPO DE VEHÍCULO
                    st.markdown("### 🚗 Gráfico 4: Prendas por Marca y Tipo de Vehículo")

                    if not df_prendas.empty:
                        # Obtener top marcas
                        top_marcas = df_prendas.groupby('marca')['cantidad_prendas'].sum().nlargest(10).index.tolist()

                        df_prendas_tipo = df_prendas[df_prendas['marca'].isin(top_marcas)]
                        df_prendas_tipo = df_prendas_tipo.groupby(['marca', 'tipo_vehiculo'])['cantidad_prendas'].sum().reset_index()
                        df_prendas_tipo = df_prendas_tipo.sort_values('cantidad_prendas', ascending=False)

                        # Gráfico de barras agrupadas
                        fig_marca_tipo = px.bar(
                            df_prendas_tipo,
                            x='marca',
                            y='cantidad_prendas',
                            color='tipo_vehiculo',
                            title='Top 10 Marcas - Prendas por Tipo de Vehículo',
                            labels={'marca': 'Marca', 'cantidad_prendas': 'Cantidad de Prendas', 'tipo_vehiculo': 'Tipo de Vehículo'},
                            barmode='group'
                        )
                        fig_marca_tipo.update_layout(
                            xaxis_title='Marca',
                            yaxis_title='Cantidad de Prendas',
                            xaxis_tickangle=-45,
                            legend_title='Tipo de Vehículo'
                        )
                        st.plotly_chart(fig_marca_tipo, use_container_width=True)

                        # Tabla detallada
                        st.markdown("#### 📋 Detalle por Marca y Tipo")

                        df_marca_tipo_pivot = df_prendas_tipo.pivot_table(
                            index='marca',
                            columns='tipo_vehiculo',
                            values='cantidad_prendas',
                            aggfunc='sum',
                            fill_value=0
                        ).reset_index()

                        df_marca_tipo_pivot['Total'] = df_marca_tipo_pivot.select_dtypes(include='number').sum(axis=1)
                        df_marca_tipo_pivot = df_marca_tipo_pivot.sort_values('Total', ascending=False)

                        st.dataframe(df_marca_tipo_pivot, use_container_width=True, hide_index=True)

                    st.markdown("---")

                    # 10. COMPARACIÓN ENTRE PROVINCIAS
                    st.markdown("### 🗺️ Gráfico 5: Comparación entre Provincias")

                    # Usar las provincias ya seleccionadas en el filtro global
                    if len(provincias_seleccionadas) > 1:
                        # Agrupar por provincia y edad desde los datos ya cargados
                        df_prov_edad = df_inscripciones.groupby(['provincia', 'edad'])['cantidad'].sum().reset_index()
                        df_prov_edad = df_prov_edad.sort_values(['provincia', 'edad'])

                        if not df_prov_edad.empty:
                            # Gráfico 1: Distribución de edades por provincia
                            st.markdown("#### 📊 Distribución de Edades por Provincia")

                            fig_prov_edad = px.line(
                                df_prov_edad,
                                x='edad',
                                y='cantidad',
                                color='provincia',
                                title=f'Comparación de Edades entre Provincias - Año {anio_seleccionado}',
                                labels={'edad': 'Edad (años)', 'cantidad': 'Cantidad de Compradores', 'provincia': 'Provincia'},
                                markers=True
                            )
                            fig_prov_edad.update_layout(
                                xaxis_title='Edad (años)',
                                yaxis_title='Cantidad de Compradores',
                                legend_title='Provincia',
                                hovermode='x unified'
                            )
                            st.plotly_chart(fig_prov_edad, use_container_width=True)

                            # Agrupar prendas por provincia y edad desde los datos ya cargados
                            if not df_prendas.empty:
                                df_prendas_prov_edad = df_prendas.groupby(['provincia', 'edad'])['cantidad_prendas'].sum().reset_index()
                                df_prendas_prov_edad = df_prendas_prov_edad.sort_values(['provincia', 'edad'])

                                if not df_prendas_prov_edad.empty:
                                    # Gráfico 2: Prendas por edad y provincia
                                    st.markdown("#### 💰 Prendas por Edad y Provincia")

                                    fig_prendas_prov = px.line(
                                        df_prendas_prov_edad,
                                        x='edad',
                                        y='cantidad_prendas',
                                        color='provincia',
                                        title=f'Comparación de Prendas por Edad entre Provincias - Año {anio_seleccionado}',
                                        labels={'edad': 'Edad (años)', 'cantidad_prendas': 'Cantidad de Prendas', 'provincia': 'Provincia'},
                                        markers=True
                                    )
                                    fig_prendas_prov.update_layout(
                                        xaxis_title='Edad (años)',
                                        yaxis_title='Cantidad de Prendas',
                                        legend_title='Provincia',
                                        hovermode='x unified'
                                    )
                                    st.plotly_chart(fig_prendas_prov, use_container_width=True)

                                    # Calcular % de financiación por provincia
                                    st.markdown("#### 📈 Porcentaje de Financiación por Provincia")

                                    # Agrupar totales por provincia
                                    total_inscripciones_prov = df_prov_edad.groupby('provincia')['cantidad'].sum().reset_index()
                                    total_prendas_prov = df_prendas_prov_edad.groupby('provincia')['cantidad_prendas'].sum().reset_index()

                                    df_financiacion_prov = total_inscripciones_prov.merge(
                                        total_prendas_prov,
                                        on='provincia',
                                        how='left'
                                    )
                                    df_financiacion_prov['cantidad_prendas'] = df_financiacion_prov['cantidad_prendas'].fillna(0)
                                    df_financiacion_prov['porcentaje_financiacion'] = (
                                        df_financiacion_prov['cantidad_prendas'] / df_financiacion_prov['cantidad'] * 100
                                    )
                                    df_financiacion_prov = df_financiacion_prov.sort_values('porcentaje_financiacion', ascending=False)

                                    # Gráfico de barras
                                    fig_financ_prov = px.bar(
                                        df_financiacion_prov,
                                        x='provincia',
                                        y='porcentaje_financiacion',
                                        title='Porcentaje de Financiación por Provincia',
                                        labels={'provincia': 'Provincia', 'porcentaje_financiacion': '% Financiación'},
                                        text='porcentaje_financiacion',
                                        color='porcentaje_financiacion',
                                        color_continuous_scale='RdYlGn_r'
                                    )
                                    fig_financ_prov.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                                    fig_financ_prov.update_layout(showlegend=False)
                                    st.plotly_chart(fig_financ_prov, use_container_width=True)

                                    # Tabla comparativa
                                    st.markdown("#### 📋 Tabla Comparativa de Provincias")
                                    df_tabla_comp = df_financiacion_prov.copy()
                                    df_tabla_comp.columns = ['Provincia', 'Total Inscripciones', 'Total Prendas', '% Financiación']
                                    df_tabla_comp['Total Inscripciones'] = df_tabla_comp['Total Inscripciones'].apply(lambda x: format_number(x))
                                    df_tabla_comp['Total Prendas'] = df_tabla_comp['Total Prendas'].apply(lambda x: format_number(x))
                                    df_tabla_comp['% Financiación'] = df_tabla_comp['% Financiación'].apply(lambda x: f"{x:.1f}%")

                                    st.dataframe(df_tabla_comp, use_container_width=True, hide_index=True)
                        else:
                            st.info("No hay datos suficientes para comparar las provincias seleccionadas")
                    else:
                        st.info("💡 Selecciona **2 o más provincias** en el filtro de arriba para ver la comparación entre provincias")

                    st.markdown("---")

                    # 11. INSIGHTS Y CONCLUSIONES
                    with st.expander("💡 Ver Insights y Análisis Adicionales"):
                        col_ins1, col_ins2 = st.columns(2)

                        with col_ins1:
                            st.markdown("**📊 Análisis Demográfico**")

                            # Rango de edad más activo
                            df_edad_rangos = df_inscripciones.copy()
                            df_edad_rangos['rango_edad'] = pd.cut(
                                df_edad_rangos['edad'],
                                bins=[18, 25, 35, 45, 55, 65, 100],
                                labels=['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
                            )
                            df_rangos = df_edad_rangos.groupby('rango_edad', observed=True)['cantidad'].sum().reset_index()
                            df_rangos = df_rangos.sort_values('cantidad', ascending=False)

                            if not df_rangos.empty and len(df_rangos) > 0:
                                st.write(f"• **Rango etario más activo:** {df_rangos.iloc[0]['rango_edad']} años")
                                st.write(f"• **Total inscripciones en ese rango:** {format_number(df_rangos.iloc[0]['cantidad'])}")

                            if origen_seleccionado == "Ambos" and not df_inscripciones.empty:
                                df_origen_agg = df_inscripciones.groupby('origen')['cantidad'].sum()
                                if not df_origen_agg.empty:
                                    origen_preferido = df_origen_agg.idxmax()
                                    st.write(f"• **Origen preferido:** {origen_preferido}")

                        with col_ins2:
                            st.markdown("**💰 Análisis de Financiación**")

                            if not df_prendas.empty:
                                # Tipo de vehículo más financiado
                                tipo_mas_financiado = df_prendas.groupby('tipo_vehiculo')['cantidad_prendas'].sum().idxmax()
                                cantidad_tipo = df_prendas.groupby('tipo_vehiculo')['cantidad_prendas'].sum().max()

                                st.write(f"• **Tipo más financiado:** {tipo_mas_financiado}")
                                st.write(f"• **Cantidad de prendas:** {format_number(cantidad_tipo)}")
                                st.write(f"• **Tasa de financiación global:** {porcentaje_prendas:.1f}%")

            except Exception as e:
                st.error(f"❌ Error al cargar datos: {str(e)}")
                st.exception(e)

# ==================== TAB 6: TENDENCIAS HISTÓRICAS ====================
with tab6:
    st.header("📊 Tendencias Históricas (2007-2025)")
    st.markdown("Análisis de estadísticas agregadas mensuales por provincia")
    st.markdown("---")

    # Verificar que las tablas existan
    try:
        test_query = text("SELECT COUNT(*) FROM estadisticas_inscripciones")
        with engine.connect() as conn:
            result = conn.execute(test_query)
            count_insc = result.fetchone()[0]

        if count_insc == 0:
            st.warning("⚠️ No hay datos de estadísticas agregadas cargados")
            st.info("💡 **Para cargar datos:**\n\n"
                    "1. Asegúrate de tener los archivos CSV en `data/estadisticas_dnrpa/`\n"
                    "2. Ejecuta: `python cargar_estadisticas_agregadas.py`")
        else:
            # ========== FILTROS ==========
            st.markdown("### 🎯 Filtros de Análisis")

            col_f1, col_f2, col_f3, col_f4 = st.columns(4)

            with col_f1:
                tipo_vehiculo_hist = st.selectbox(
                    "🚗 Tipo de Vehículo",
                    options=["Automóviles", "Motovehículos", "Maquinarias"],
                    index=0,
                    key="hist_tipo_vehiculo"
                )

            with col_f2:
                tipo_tramite_hist = st.selectbox(
                    "📋 Tipo de Trámite",
                    options=["Inscripciones", "Transferencias", "Inscripciones + Transferencias"],
                    index=0,
                    key="hist_tipo_tramite"
                )

            # Obtener años disponibles
            if tipo_vehiculo_hist == "Automóviles":
                # Para automóviles usamos tablas detalladas
                if tipo_tramite_hist == "Inscripciones":
                    query_anios_hist = text("""
                        SELECT DISTINCT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio
                        FROM datos_gob_inscripciones
                        WHERE tramite_fecha IS NOT NULL
                        ORDER BY anio DESC
                    """)
                elif tipo_tramite_hist == "Transferencias":
                    query_anios_hist = text("""
                        SELECT DISTINCT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio
                        FROM datos_gob_transferencias
                        WHERE tramite_fecha IS NOT NULL
                        ORDER BY anio DESC
                    """)
                else:  # Inscripciones + Transferencias
                    query_anios_hist = text("""
                        SELECT DISTINCT anio FROM (
                            SELECT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio
                            FROM datos_gob_inscripciones
                            WHERE tramite_fecha IS NOT NULL
                            UNION
                            SELECT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio
                            FROM datos_gob_transferencias
                            WHERE tramite_fecha IS NOT NULL
                        ) AS combined
                        ORDER BY anio DESC
                    """)

                with engine.connect() as conn:
                    df_anios_hist = pd.read_sql(query_anios_hist, conn)
            else:
                # Para motovehículos y maquinarias usamos tablas agregadas
                if tipo_tramite_hist == "Inscripciones":
                    tabla_hist = "estadisticas_inscripciones"
                elif tipo_tramite_hist == "Transferencias":
                    tabla_hist = "estadisticas_transferencias"
                else:  # Inscripciones + Transferencias
                    tabla_hist = "estadisticas_inscripciones"  # Usamos una para obtener años

                query_anios_hist = text(f"""
                    SELECT DISTINCT anio
                    FROM {tabla_hist}
                    WHERE tipo_vehiculo = :tipo_vehiculo
                    ORDER BY anio DESC
                """)

                with engine.connect() as conn:
                    df_anios_hist = pd.read_sql(query_anios_hist, conn, params={"tipo_vehiculo": tipo_vehiculo_hist})

            anios_disponibles_hist = df_anios_hist['anio'].tolist() if not df_anios_hist.empty else []

            with col_f3:
                anio_desde_hist = st.selectbox(
                    "📅 Año Desde",
                    options=anios_disponibles_hist[::-1],  # Orden ascendente
                    index=0 if len(anios_disponibles_hist) > 10 else 0,
                    key="hist_anio_desde"
                )

            with col_f4:
                anio_hasta_hist = st.selectbox(
                    "📅 Año Hasta",
                    options=anios_disponibles_hist,
                    index=0,
                    key="hist_anio_hasta"
                )

            # Filtro de provincias
            if tipo_vehiculo_hist == "Automóviles":
                # Para automóviles usamos tablas detalladas
                if tipo_tramite_hist == "Inscripciones":
                    query_provincias_hist = text("""
                        SELECT DISTINCT titular_domicilio_provincia as provincia
                        FROM datos_gob_inscripciones
                        WHERE titular_domicilio_provincia IS NOT NULL
                        ORDER BY provincia
                    """)
                elif tipo_tramite_hist == "Transferencias":
                    query_provincias_hist = text("""
                        SELECT DISTINCT titular_domicilio_provincia as provincia
                        FROM datos_gob_transferencias
                        WHERE titular_domicilio_provincia IS NOT NULL
                        ORDER BY provincia
                    """)
                else:  # Inscripciones + Transferencias
                    query_provincias_hist = text("""
                        SELECT DISTINCT provincia FROM (
                            SELECT titular_domicilio_provincia as provincia
                            FROM datos_gob_inscripciones
                            WHERE titular_domicilio_provincia IS NOT NULL
                            UNION
                            SELECT titular_domicilio_provincia as provincia
                            FROM datos_gob_transferencias
                            WHERE titular_domicilio_provincia IS NOT NULL
                        ) AS combined
                        ORDER BY provincia
                    """)

                with engine.connect() as conn:
                    df_provincias_hist = pd.read_sql(query_provincias_hist, conn)
            else:
                # Para motovehículos y maquinarias usamos tablas agregadas
                query_provincias_hist = text(f"""
                    SELECT DISTINCT provincia
                    FROM {tabla_hist}
                    WHERE tipo_vehiculo = :tipo_vehiculo
                    ORDER BY provincia
                """)

                with engine.connect() as conn:
                    df_provincias_hist = pd.read_sql(query_provincias_hist, conn, params={"tipo_vehiculo": tipo_vehiculo_hist})

            provincias_disponibles_hist = df_provincias_hist['provincia'].tolist() if not df_provincias_hist.empty else []

            provincias_seleccionadas_hist = st.multiselect(
                "🗺️ Provincias (dejar vacío para todas)",
                options=provincias_disponibles_hist,
                default=[],
                key="hist_provincias"
            )

            st.markdown("---")

            # ========== CONSULTA PRINCIPAL ==========
            filtro_provincias_hist = ""
            filtro_provincias_detallado = ""

            if provincias_seleccionadas_hist:
                provincias_str = "', '".join(provincias_seleccionadas_hist)
                filtro_provincias_hist = f"AND provincia IN ('{provincias_str}')"
                filtro_provincias_detallado = f"AND titular_domicilio_provincia IN ('{provincias_str}')"

            # Construir consulta según tipo de vehículo
            if tipo_vehiculo_hist == "Automóviles":
                # Para automóviles usamos tablas detalladas
                if tipo_tramite_hist == "Inscripciones + Transferencias":
                    # UNION de inscripciones y transferencias
                    query_datos_hist = text(f"""
                        SELECT
                            anio,
                            mes,
                            provincia,
                            SUM(total) as total
                        FROM (
                            SELECT
                                EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                                EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                                titular_domicilio_provincia as provincia,
                                COUNT(*) as total
                            FROM datos_gob_inscripciones
                            WHERE tramite_fecha IS NOT NULL
                            AND titular_domicilio_provincia IS NOT NULL
                            AND EXTRACT(YEAR FROM tramite_fecha) BETWEEN :anio_desde AND :anio_hasta
                            {filtro_provincias_detallado}
                            GROUP BY anio, mes, provincia

                            UNION ALL

                            SELECT
                                EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                                EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                                titular_domicilio_provincia as provincia,
                                COUNT(*) as total
                            FROM datos_gob_transferencias
                            WHERE tramite_fecha IS NOT NULL
                            AND titular_domicilio_provincia IS NOT NULL
                            AND EXTRACT(YEAR FROM tramite_fecha) BETWEEN :anio_desde AND :anio_hasta
                            {filtro_provincias_detallado}
                            GROUP BY anio, mes, provincia
                        ) AS combined
                        GROUP BY anio, mes, provincia
                        ORDER BY anio, mes
                    """)
                elif tipo_tramite_hist == "Inscripciones":
                    query_datos_hist = text(f"""
                        SELECT
                            EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                            EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                            titular_domicilio_provincia as provincia,
                            COUNT(*) as total
                        FROM datos_gob_inscripciones
                        WHERE tramite_fecha IS NOT NULL
                        AND titular_domicilio_provincia IS NOT NULL
                        AND EXTRACT(YEAR FROM tramite_fecha) BETWEEN :anio_desde AND :anio_hasta
                        {filtro_provincias_detallado}
                        GROUP BY anio, mes, provincia
                        ORDER BY anio, mes
                    """)
                else:  # Transferencias
                    query_datos_hist = text(f"""
                        SELECT
                            EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                            EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                            titular_domicilio_provincia as provincia,
                            COUNT(*) as total
                        FROM datos_gob_transferencias
                        WHERE tramite_fecha IS NOT NULL
                        AND titular_domicilio_provincia IS NOT NULL
                        AND EXTRACT(YEAR FROM tramite_fecha) BETWEEN :anio_desde AND :anio_hasta
                        {filtro_provincias_detallado}
                        GROUP BY anio, mes, provincia
                        ORDER BY anio, mes
                    """)

                with engine.connect() as conn:
                    df_hist = pd.read_sql(query_datos_hist, conn, params={
                        "anio_desde": anio_desde_hist,
                        "anio_hasta": anio_hasta_hist
                    })
            else:
                # Para motovehículos y maquinarias usamos tablas agregadas
                if tipo_tramite_hist == "Inscripciones + Transferencias":
                    # UNION de ambas tablas
                    query_datos_hist = text(f"""
                        SELECT
                            anio,
                            mes,
                            provincia,
                            SUM(cantidad) as total
                        FROM (
                            SELECT anio, mes, provincia, cantidad
                            FROM estadisticas_inscripciones
                            WHERE tipo_vehiculo = :tipo_vehiculo
                            AND anio BETWEEN :anio_desde AND :anio_hasta
                            {filtro_provincias_hist}

                            UNION ALL

                            SELECT anio, mes, provincia, cantidad
                            FROM estadisticas_transferencias
                            WHERE tipo_vehiculo = :tipo_vehiculo
                            AND anio BETWEEN :anio_desde AND :anio_hasta
                            {filtro_provincias_hist}
                        ) AS combined
                        GROUP BY anio, mes, provincia
                        ORDER BY anio, mes
                    """)
                else:
                    # Consulta simple para una sola tabla
                    query_datos_hist = text(f"""
                        SELECT
                            anio,
                            mes,
                            provincia,
                            SUM(cantidad) as total
                        FROM {tabla_hist}
                        WHERE tipo_vehiculo = :tipo_vehiculo
                        AND anio BETWEEN :anio_desde AND :anio_hasta
                        {filtro_provincias_hist}
                        GROUP BY anio, mes, provincia
                        ORDER BY anio, mes
                    """)

                with engine.connect() as conn:
                    df_hist = pd.read_sql(query_datos_hist, conn, params={
                        "tipo_vehiculo": tipo_vehiculo_hist,
                        "anio_desde": anio_desde_hist,
                        "anio_hasta": anio_hasta_hist
                    })

            if df_hist.empty:
                st.warning("⚠️ No hay datos para los filtros seleccionados")
            else:
                # Crear columna de fecha para gráficos
                df_hist['fecha'] = pd.to_datetime(df_hist['anio'].astype(str) + '-' + df_hist['mes'].astype(str) + '-01')
                df_hist['mes_nombre'] = df_hist['mes'].map(MESES_ES)

                # ========== MÉTRICAS GENERALES ==========
                st.markdown("### 📈 Métricas Generales")

                total_tramites = df_hist['total'].sum()
                provincias_activas = df_hist['provincia'].nunique()
                periodo_meses = df_hist['fecha'].nunique()
                promedio_mensual = total_tramites / periodo_meses if periodo_meses > 0 else 0

                col_m1, col_m2, col_m3, col_m4 = st.columns(4)

                with col_m1:
                    st.metric("Total de Trámites", format_number(total_tramites))

                with col_m2:
                    st.metric("Provincias Activas", provincias_activas)

                with col_m3:
                    st.metric("Período", f"{periodo_meses} meses")

                with col_m4:
                    st.metric("Promedio Mensual", format_number(promedio_mensual))

                st.markdown("---")

                # ========== GRÁFICO 1: SERIE TEMPORAL NACIONAL ==========
                st.markdown("### 📊 Evolución Temporal Nacional")

                df_temporal = df_hist.groupby('fecha')['total'].sum().reset_index()

                fig_temporal = px.line(
                    df_temporal,
                    x='fecha',
                    y='total',
                    title=f'Evolución de {tipo_tramite_hist} - {tipo_vehiculo_hist} ({anio_desde_hist}-{anio_hasta_hist})',
                    labels={'fecha': 'Fecha', 'total': 'Cantidad'}
                )

                fig_temporal.update_layout(
                    hovermode='x unified',
                    height=400
                )

                fig_temporal.update_traces(
                    line=dict(width=2),
                    hovertemplate='<b>%{x|%Y-%m}</b><br>Cantidad: %{y:,.0f}<extra></extra>'
                )

                st.plotly_chart(fig_temporal, use_container_width=True)

                # ========== GRÁFICO 2: TOP 10 PROVINCIAS ==========
                st.markdown("### 🏆 Top 10 Provincias")

                df_provincias_total = df_hist.groupby('provincia')['total'].sum().reset_index()
                df_provincias_total = df_provincias_total.sort_values('total', ascending=False).head(10)

                fig_provincias = px.bar(
                    df_provincias_total,
                    x='total',
                    y='provincia',
                    orientation='h',
                    title=f'Top 10 Provincias - {tipo_tramite_hist} de {tipo_vehiculo_hist}',
                    labels={'total': 'Total de Trámites', 'provincia': 'Provincia'}
                )

                fig_provincias.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    height=500
                )

                fig_provincias.update_traces(
                    hovertemplate='<b>%{y}</b><br>Total: %{x:,.0f}<extra></extra>'
                )

                st.plotly_chart(fig_provincias, use_container_width=True)

                # ========== GRÁFICOS EN COLUMNAS ==========
                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    # GRÁFICO 3: ESTACIONALIDAD (MES)
                    st.markdown("### 📅 Estacionalidad por Mes")

                    df_estacional = df_hist.groupby('mes_nombre')['total'].sum().reset_index()
                    df_estacional['mes_numero'] = df_estacional['mes_nombre'].map({v: k for k, v in MESES_ES.items()})
                    df_estacional = df_estacional.sort_values('mes_numero')

                    fig_estacional = px.bar(
                        df_estacional,
                        x='mes_nombre',
                        y='total',
                        title='Distribución por Mes del Año',
                        labels={'mes_nombre': 'Mes', 'total': 'Total'}
                    )

                    fig_estacional.update_traces(
                        hovertemplate='<b>%{x}</b><br>Total: %{y:,.0f}<extra></extra>'
                    )

                    fig_estacional.update_layout(height=400)

                    st.plotly_chart(fig_estacional, use_container_width=True)

                with col_g2:
                    # GRÁFICO 4: EVOLUCIÓN ANUAL
                    st.markdown("### 📊 Evolución por Año")

                    df_anual = df_hist.groupby('anio')['total'].sum().reset_index()

                    fig_anual = px.bar(
                        df_anual,
                        x='anio',
                        y='total',
                        title='Total por Año',
                        labels={'anio': 'Año', 'total': 'Total'}
                    )

                    fig_anual.update_traces(
                        hovertemplate='<b>%{x}</b><br>Total: %{y:,.0f}<extra></extra>'
                    )

                    fig_anual.update_layout(height=400)

                    st.plotly_chart(fig_anual, use_container_width=True)

                # ========== GRÁFICO 5: HEATMAP ESTACIONAL ==========
                if len(anios_disponibles_hist) > 1 and anio_hasta_hist - anio_desde_hist >= 2:
                    st.markdown("### 🌡️ Mapa de Calor Estacional (Año vs Mes)")

                    df_heatmap = df_hist.groupby(['anio', 'mes'])['total'].sum().reset_index()
                    df_pivot = df_heatmap.pivot(index='anio', columns='mes', values='total').fillna(0)

                    # Renombrar columnas con nombres de meses
                    df_pivot.columns = [MESES_ES[int(col)] for col in df_pivot.columns]

                    fig_heatmap = px.imshow(
                        df_pivot,
                        labels=dict(x="Mes", y="Año", color="Cantidad"),
                        x=df_pivot.columns,
                        y=df_pivot.index,
                        title=f'Mapa de Calor - {tipo_tramite_hist} de {tipo_vehiculo_hist}',
                        color_continuous_scale='Blues',
                        aspect='auto'
                    )

                    fig_heatmap.update_layout(height=400)

                    st.plotly_chart(fig_heatmap, use_container_width=True)

                # ========== TABLA DE DATOS ==========
                with st.expander("📋 Ver Datos Detallados"):
                    df_tabla = df_hist.groupby(['anio', 'mes', 'mes_nombre', 'provincia'])['total'].sum().reset_index()
                    df_tabla = df_tabla.sort_values(['anio', 'mes', 'total'], ascending=[False, False, False])
                    df_tabla_display = df_tabla[['anio', 'mes_nombre', 'provincia', 'total']].copy()
                    df_tabla_display.columns = ['Año', 'Mes', 'Provincia', 'Total']
                    st.dataframe(df_tabla_display, use_container_width=True, height=400)

    except Exception as e:
        st.error(f"❌ Error al cargar estadísticas históricas: {str(e)}")
        st.info("💡 Asegúrate de haber ejecutado:\n\n"
                "1. `python -c \"...\"` para crear las tablas\n"
                "2. `python cargar_estadisticas_agregadas.py` para cargar los datos")

# ==================== TAB 7: PREDICCIONES ML ====================
with tab7:
    st.header("🔮 Predicciones de Demanda con Machine Learning")
    st.markdown("Predice la demanda futura de vehículos utilizando modelos de Machine Learning entrenados")
    st.markdown("---")

    import pickle
    import numpy as np
    from pathlib import Path as PathlibPath

    # Rutas a los modelos (intentar múltiples ubicaciones y modelos)
    BASE_PATH = PathlibPath(__file__).parent.parent

    # Intentar cargar modelos en orden de preferencia
    MODEL_PATHS = [
        (BASE_PATH / "data" / "models" / "mejor_modelo_LightGBM.pkl", "LightGBM"),
        (BASE_PATH / "data" / "models" / "mejor_modelo_XGBoost.pkl", "XGBoost"),
        (BASE_PATH / "models" / "xgboost_optimized_model.pkl", "XGBoost"),
        (BASE_PATH / "data" / "models" / "todos_modelos_*.pkl", "Ensemble"),
    ]

    ENCODERS_PATH = BASE_PATH / "data" / "models" / "encoders.pkl"
    FEATURE_NAMES_PATH = BASE_PATH / "data" / "models" / "feature_names.pkl"

    # Buscar el primer modelo disponible
    MODEL_PATH = None
    MODEL_NAME = None
    for path, name in MODEL_PATHS:
        if path.exists():
            MODEL_PATH = path
            MODEL_NAME = name
            break

    # Verificar si se encontró algún modelo
    if MODEL_PATH is None:
        st.warning("⚠️ Modelo de Machine Learning no encontrado")
        st.info("💡 **Para entrenar el modelo:**\n\n"
                "1. Ejecuta: `python notebooks/01_preparacion_datos_ml.py`\n"
                "2. Ejecuta: `python notebooks/02_modelado_predictivo.py`\n"
                "3. Los modelos se guardarán en `data/models/`")

        st.markdown("### 📚 Información del Modelo")
        st.markdown("""
        El modelo de predicción utiliza **LightGBM** (Gradient Boosting) con las siguientes características:

        **Features principales:**
        - Variables históricas: cantidad_transacciones_lag1, cantidad_transacciones_lag3
        - Promedios móviles: cantidad_ma3, cantidad_ma6
        - Variación intermensual: cantidad_var_mensual
        - Variables categóricas: marca, modelo, provincia, tipo_vehiculo, tipo_transaccion
        - Variables macro: IPC, BADLAR, Tipo de Cambio
        - Variables temporales: año, mes, trimestre

        **Métricas de desempeño:**
        - R² Score: ~0.974
        - MAE: ~0.22
        - Tiempo de entrenamiento: ~13 segundos
        """)
    else:
        try:
            # Cargar modelo y encoders
            with open(MODEL_PATH, 'rb') as f:
                modelo = pickle.load(f)

            with open(ENCODERS_PATH, 'rb') as f:
                encoders = pickle.load(f)

            with open(FEATURE_NAMES_PATH, 'rb') as f:
                feature_names = pickle.load(f)

            st.success(f"✅ Modelo {MODEL_NAME} cargado correctamente desde: `{MODEL_PATH.name}`")

            # ========== FILTROS EN CASCADA ==========
            st.markdown("### 🎯 Configuración de Predicción")
            st.markdown("Selecciona los parámetros para realizar la predicción:")

            col_pred1, col_pred2 = st.columns(2)

            # PASO 1: Seleccionar Provincia
            with col_pred1:
                st.markdown("#### 📍 Paso 1: Provincia")
                query_provincias_pred = text("""
                    SELECT DISTINCT titular_domicilio_provincia as provincia
                    FROM datos_gob_inscripciones
                    WHERE titular_domicilio_provincia IS NOT NULL
                    AND titular_domicilio_provincia != ''
                    ORDER BY provincia
                """)

                try:
                    df_prov_pred = pd.read_sql(query_provincias_pred, engine)
                    provincias_pred = df_prov_pred['provincia'].tolist()
                except:
                    provincias_pred = []

                if provincias_pred:
                    provincia_pred = st.selectbox(
                        "Selecciona la provincia:",
                        options=provincias_pred,
                        key="pred_provincia"
                    )
                else:
                    st.error("No se encontraron provincias disponibles")
                    provincia_pred = None

            # PASO 2: Seleccionar Horizonte de Predicción
            with col_pred2:
                st.markdown("#### ⏱️ Paso 2: Horizonte de Predicción")
                horizonte_pred = st.selectbox(
                    "Selecciona el horizonte temporal:",
                    options=[30, 60, 90, 120],
                    format_func=lambda x: f"{x} días ({x//30} {'mes' if x==30 else 'meses'})",
                    key="pred_horizonte"
                )

            # PASO 3: Seleccionar Marca (filtrada por provincia)
            if provincia_pred:
                col_pred3, col_pred4 = st.columns(2)

                with col_pred3:
                    st.markdown("#### 🏭 Paso 3: Marca")

                    # Query para obtener marcas disponibles en la provincia seleccionada
                    query_marcas_pred = text("""
                        SELECT DISTINCT automotor_marca_descripcion as marca,
                               COUNT(*) as cantidad
                        FROM datos_gob_inscripciones
                        WHERE titular_domicilio_provincia = :provincia
                        AND automotor_marca_descripcion IS NOT NULL
                        AND automotor_marca_descripcion != ''
                        AND tramite_fecha >= NOW() - INTERVAL '2 years'
                        GROUP BY marca
                        ORDER BY cantidad DESC
                        LIMIT 50
                    """)

                    try:
                        df_marcas_pred = pd.read_sql(query_marcas_pred, engine, params={'provincia': provincia_pred})
                        marcas_pred = df_marcas_pred['marca'].tolist()
                    except:
                        marcas_pred = []

                    if marcas_pred:
                        marca_pred = st.selectbox(
                            "Selecciona la marca:",
                            options=marcas_pred,
                            key="pred_marca"
                        )
                    else:
                        st.warning(f"No hay marcas disponibles para {provincia_pred}")
                        marca_pred = None

                # PASO 4: Seleccionar Modelo (filtrado por marca y provincia)
                with col_pred4:
                    st.markdown("#### 🚗 Paso 4: Modelo de Vehículo")

                    if marca_pred:
                        query_modelos_pred = text("""
                            SELECT DISTINCT automotor_modelo_descripcion as modelo,
                                   COUNT(*) as cantidad
                            FROM datos_gob_inscripciones
                            WHERE titular_domicilio_provincia = :provincia
                            AND automotor_marca_descripcion = :marca
                            AND automotor_modelo_descripcion IS NOT NULL
                            AND automotor_modelo_descripcion != ''
                            AND tramite_fecha >= NOW() - INTERVAL '2 years'
                            GROUP BY modelo
                            ORDER BY cantidad DESC
                            LIMIT 30
                        """)

                        try:
                            df_modelos_pred = pd.read_sql(query_modelos_pred, engine, params={
                                'provincia': provincia_pred,
                                'marca': marca_pred
                            })
                            modelos_pred = df_modelos_pred['modelo'].tolist()
                        except:
                            modelos_pred = []

                        if modelos_pred:
                            modelo_pred = st.selectbox(
                                "Selecciona el modelo:",
                                options=modelos_pred,
                                key="pred_modelo"
                            )
                        else:
                            st.warning(f"No hay modelos disponibles para {marca_pred} en {provincia_pred}")
                            modelo_pred = None
                    else:
                        modelo_pred = None
                        st.info("Selecciona una marca primero")

                st.markdown("---")

                # ========== REALIZAR PREDICCIÓN ==========
                if provincia_pred and marca_pred and modelo_pred:
                    st.markdown("### 📊 Resultado de la Predicción")

                    # Botón para ejecutar predicción
                    if st.button("🔮 Realizar Predicción", type="primary", use_container_width=True):
                        with st.spinner("Procesando predicción..."):
                            try:
                                # 1. Obtener datos históricos
                                query_historico = text("""
                                    SELECT
                                        DATE_TRUNC('month', tramite_fecha) as fecha_mes,
                                        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                                        EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                                        EXTRACT(QUARTER FROM tramite_fecha)::INTEGER as trimestre,
                                        COUNT(*) as cantidad_transacciones,
                                        AVG(EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento) as edad_titular,
                                        AVG(automotor_anio_modelo) as anio_modelo
                                    FROM datos_gob_inscripciones
                                    WHERE titular_domicilio_provincia = :provincia
                                    AND automotor_marca_descripcion = :marca
                                    AND automotor_modelo_descripcion = :modelo
                                    AND tramite_fecha >= NOW() - INTERVAL '12 months'
                                    AND tramite_fecha IS NOT NULL
                                    AND titular_anio_nacimiento IS NOT NULL
                                    GROUP BY fecha_mes, anio, mes, trimestre
                                    ORDER BY fecha_mes DESC
                                    LIMIT 12
                                """)

                                df_hist_pred = pd.read_sql(query_historico, engine, params={
                                    'provincia': provincia_pred,
                                    'marca': marca_pred,
                                    'modelo': modelo_pred
                                })

                                if df_hist_pred.empty:
                                    st.warning("⚠️ No hay suficientes datos históricos para realizar la predicción")
                                    st.info("💡 Se requiere al menos 3 meses de historial para este modelo/marca/provincia")
                                else:
                                    # ========== CARGAR VARIABLES MACRO ACTUALES ==========
                                    query_macro = text("""
                                        SELECT
                                            DATE_TRUNC('month', fecha) as fecha_mes,
                                            AVG(ipc_mensual) as ipc_nivel
                                        FROM ipc_diario
                                        WHERE fecha >= NOW() - INTERVAL '6 months'
                                        GROUP BY DATE_TRUNC('month', fecha)
                                        ORDER BY fecha_mes DESC
                                        LIMIT 6
                                    """)

                                    query_badlar = text("""
                                        SELECT
                                            DATE_TRUNC('month', fecha) as fecha_mes,
                                            AVG(tasa) as badlar_promedio,
                                            STDDEV(tasa) as badlar_volatilidad
                                        FROM badlar
                                        WHERE fecha >= NOW() - INTERVAL '6 months'
                                        GROUP BY DATE_TRUNC('month', fecha)
                                        ORDER BY fecha_mes DESC
                                        LIMIT 6
                                    """)

                                    query_tc = text("""
                                        SELECT
                                            DATE_TRUNC('month', fecha) as fecha_mes,
                                            AVG(promedio) as tc_promedio,
                                            STDDEV(promedio) as tc_volatilidad
                                        FROM tipo_cambio
                                        WHERE fecha >= NOW() - INTERVAL '6 months'
                                        GROUP BY DATE_TRUNC('month', fecha)
                                        ORDER BY fecha_mes DESC
                                        LIMIT 6
                                    """)

                                    try:
                                        df_ipc = pd.read_sql(query_macro, engine)
                                        df_badlar = pd.read_sql(query_badlar, engine)
                                        df_tc = pd.read_sql(query_tc, engine)

                                        # Calcular valores macro para usar en ambos métodos (ML y estadístico)
                                        ipc_actual = df_ipc.iloc[0]['ipc_nivel'] if not df_ipc.empty else 100
                                        badlar_actual = df_badlar.iloc[0]['badlar_promedio'] if not df_badlar.empty else 50
                                        tc_actual = df_tc.iloc[0]['tc_promedio'] if not df_tc.empty else 1000

                                        # Calcular IPC var mensual
                                        if len(df_ipc) >= 2:
                                            ipc_var_mensual = ((df_ipc.iloc[0]['ipc_nivel'] - df_ipc.iloc[1]['ipc_nivel']) /
                                                              df_ipc.iloc[1]['ipc_nivel'] * 100)
                                        else:
                                            ipc_var_mensual = 5.0  # Default

                                        # Verificar que tenemos variables macro
                                        tiene_macro = not (df_ipc.empty or df_badlar.empty or df_tc.empty)
                                    except Exception as e:
                                        st.warning(f"⚠️ No se pudieron cargar variables macro: {e}")
                                        tiene_macro = False
                                        # Valores por defecto si fallan las macros
                                        ipc_actual = 100
                                        badlar_actual = 50
                                        tc_actual = 1000
                                        ipc_var_mensual = 5.0

                                if not df_hist_pred.empty and tiene_macro:
                                    # Mostrar información histórica
                                    st.markdown("#### 📈 Datos Históricos (Últimos 12 meses)")

                                    col_h1, col_h2, col_h3, col_h4 = st.columns(4)

                                    with col_h1:
                                        total_hist = df_hist_pred['cantidad_transacciones'].sum()
                                        st.metric("Total Histórico", format_number(total_hist))

                                    with col_h2:
                                        promedio_mensual_hist = df_hist_pred['cantidad_transacciones'].mean()
                                        st.metric("Promedio Mensual", format_number(promedio_mensual_hist))

                                    with col_h3:
                                        ultimo_mes = df_hist_pred.iloc[0]['cantidad_transacciones']
                                        st.metric("Último Mes", format_number(ultimo_mes))

                                    with col_h4:
                                        meses_data = len(df_hist_pred)
                                        st.metric("Meses de Datos", meses_data)

                                    # Gráfico de tendencia histórica
                                    st.markdown("#### 📊 Tendencia Histórica")

                                    df_hist_plot = df_hist_pred.sort_values('fecha_mes')
                                    df_hist_plot['fecha_str'] = df_hist_plot['fecha_mes'].dt.strftime('%Y-%m')

                                    fig_hist = px.line(
                                        df_hist_plot,
                                        x='fecha_str',
                                        y='cantidad_transacciones',
                                        title=f'Evolución Mensual - {marca_pred} {modelo_pred} en {provincia_pred}',
                                        labels={'fecha_str': 'Mes', 'cantidad_transacciones': 'Cantidad'},
                                        markers=True
                                    )

                                    fig_hist.update_layout(
                                        hovermode='x unified',
                                        height=400,
                                        xaxis_title='Mes',
                                        yaxis_title='Cantidad de Transacciones'
                                    )

                                    st.plotly_chart(fig_hist, use_container_width=True)

                                    # ========== PREDICCIÓN ML COMPLETA CON RECURSIVE FORECASTING ==========
                                    st.markdown("#### 🤖 Predicción Machine Learning (Modelo Completo)")

                                    usar_ml_completo = False
                                    predicciones_ml = []

                                    try:
                                        # Importar helper de predicción ML
                                        import sys
                                        sys.path.insert(0, str(PathlibPath(__file__).parent))
                                        from prediccion_ml_helper import predecir_recursive

                                        # Preparar datos históricos
                                        df_hist_sorted = df_hist_pred.sort_values('fecha_mes')

                                        # Usar valores macro ya calculados arriba
                                        meses_proyeccion = horizonte_pred // 30

                                        st.success(f"""
                                        ✅ **Predicción ML con {MODEL_NAME}** - Modelo completo activado

                                        - **Horizonte:** {meses_proyeccion} {'mes' if meses_proyeccion == 1 else 'meses'} ({horizonte_pred} días)
                                        - **Variables macro:** IPC={ipc_actual:.1f}, BADLAR={badlar_actual:.1f}%, TC=${tc_actual:.0f}
                                        - **Método:** Recursive forecasting iterativo (mes a mes)
                                        - **Features:** lag1, lag3, MA3, MA6, variaciones, encodings, temporales
                                        """)

                                        # Preparar DataFrame macro combinado
                                        df_macro_combined = df_ipc.merge(df_badlar, on='fecha_mes', how='outer').merge(df_tc, on='fecha_mes', how='outer')

                                        # Realizar predicción recursiva mes a mes
                                        predicciones_ml = predecir_recursive(
                                            modelo=modelo,
                                            feature_names=feature_names,
                                            df_historico=df_hist_sorted,
                                            df_macro=df_macro_combined,
                                            provincia=provincia_pred,
                                            marca=marca_pred,
                                            modelo_vehiculo=modelo_pred,
                                            encoders=encoders,
                                            meses_proyectar=meses_proyeccion
                                        )

                                        st.info("""
                                        ✨ **Predicción completada exitosamente**

                                        El modelo usó:
                                        - 📊 Lag features (valores de meses anteriores)
                                        - 📈 Moving averages (promedios móviles 3 y 6 meses)
                                        - 🔄 Recursive forecasting (cada predicción alimenta la siguiente)
                                        - 🏷️ Encodings categóricos para marca/modelo/provincia
                                        - 📅 Variables temporales (mes, trimestre, estacionalidad)
                                        - 💰 Variables macroeconómicas (IPC, BADLAR, TC)
                                        """)

                                        usar_ml_completo = True

                                    except Exception as e_ml:
                                        st.warning(f"⚠️ No se pudo usar modelo ML completo: {e_ml}")
                                        st.info("Usando proyección estadística con tendencia + estacionalidad como fallback")
                                        usar_ml_completo = False

                                    # ========== MOSTRAR RESULTADOS ==========
                                    if usar_ml_completo and len(predicciones_ml) > 0:
                                        # ===== MOSTRAR PREDICCIONES ML =====
                                        st.markdown("---")
                                        st.markdown("### 📊 Resultados de Predicción ML")

                                        # Calcular total
                                        proyeccion_total_ml = sum([p['prediccion'] for p in predicciones_ml])

                                        # Métricas principales
                                        col_ml1, col_ml2, col_ml3, col_ml4 = st.columns(4)

                                        with col_ml1:
                                            st.metric(
                                                f"Proyección ML {meses_proyeccion} {'mes' if meses_proyeccion==1 else 'meses'}",
                                                format_number(proyeccion_total_ml)
                                            )

                                        with col_ml2:
                                            promedio_ml = proyeccion_total_ml / meses_proyeccion
                                            st.metric(
                                                "Promedio Mensual ML",
                                                format_number(promedio_ml)
                                            )

                                        with col_ml3:
                                            ultimo_mes_real = df_hist_pred.iloc[0]['cantidad_transacciones']
                                            cambio_vs_ultimo = ((promedio_ml - ultimo_mes_real) / ultimo_mes_real * 100) if ultimo_mes_real > 0 else 0
                                            st.metric(
                                                "Cambio vs Último Mes",
                                                f"{cambio_vs_ultimo:+.1f}%"
                                            )

                                        with col_ml4:
                                            primer_mes_ml = predicciones_ml[0]['prediccion']
                                            ultimo_mes_ml = predicciones_ml[-1]['prediccion']
                                            tendencia_ml = ((ultimo_mes_ml - primer_mes_ml) / primer_mes_ml * 100) if primer_mes_ml > 0 else 0
                                            st.metric(
                                                "Tendencia Proyectada",
                                                f"{tendencia_ml:+.1f}%"
                                            )

                                        # Tabla detallada de predicciones ML
                                        st.markdown("#### 📅 Proyección Mensual Detallada (Modelo ML)")

                                        MESES_NOMBRES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

                                        df_pred_ml = pd.DataFrame({
                                            'Mes': [f"{MESES_NOMBRES[p['fecha'].month]} {p['fecha'].year}" for p in predicciones_ml],
                                            'Predicción ML': [f"{p['prediccion']:.0f}" for p in predicciones_ml],
                                            'Acumulado': [f"{sum([pr['prediccion'] for pr in predicciones_ml[:i+1]]):.0f}" for i in range(len(predicciones_ml))]
                                        })
                                        st.dataframe(df_pred_ml, use_container_width=True, hide_index=True)

                                        # Gráfico de predicción ML vs histórico
                                        st.markdown("#### 📈 Histórico + Proyección ML")

                                        # Preparar datos para gráfico
                                        df_hist_grafico = df_hist_plot[['fecha_str', 'cantidad_transacciones']].copy()
                                        df_hist_grafico.columns = ['Mes', 'Cantidad']

                                        df_pred_grafico = pd.DataFrame({
                                            'Mes': [p['fecha'].strftime('%Y-%m') for p in predicciones_ml],
                                            'Cantidad': [p['prediccion'] for p in predicciones_ml]
                                        })

                                        fig_ml = go.Figure()

                                        # Histórico
                                        fig_ml.add_trace(go.Scatter(
                                            x=df_hist_grafico['Mes'],
                                            y=df_hist_grafico['Cantidad'],
                                            name='Histórico Real',
                                            mode='lines+markers',
                                            line=dict(color='#1f77b4', width=2),
                                            marker=dict(size=6)
                                        ))

                                        # Predicción ML
                                        fig_ml.add_trace(go.Scatter(
                                            x=df_pred_grafico['Mes'],
                                            y=df_pred_grafico['Cantidad'],
                                            name=f'Predicción {MODEL_NAME}',
                                            mode='lines+markers',
                                            line=dict(color='#ff7f0e', width=3, dash='dash'),
                                            marker=dict(size=10, symbol='star')
                                        ))

                                        fig_ml.update_layout(
                                            title=f'Histórico + Proyección ML - {marca_pred} {modelo_pred} en {provincia_pred}',
                                            xaxis_title='Mes',
                                            yaxis_title='Cantidad de Transacciones',
                                            hovermode='x unified',
                                            height=500
                                        )

                                        st.plotly_chart(fig_ml, use_container_width=True)

                                    # ===== SOLO EJECUTAR PROYECCIÓN ESTADÍSTICA SI ML FALLÓ =====
                                    if not usar_ml_completo:
                                        # ===== FALLBACK: PROYECCIÓN ESTADÍSTICA =====
                                        st.markdown("---")
                                        st.markdown("#### 📊 Proyección Estadística (Tendencia + Estacionalidad)")

                                        # Calcular base de proyección usando últimos 3 meses (más reciente)
                                        ultimos_3_meses = df_hist_pred.head(3)['cantidad_transacciones'].mean()
                                        ultimo_mes = df_hist_pred.iloc[0]['cantidad_transacciones']

                                        # Calcular tendencia lineal (últimos 6 meses)
                                        if len(df_hist_pred) >= 6:
                                            df_tendencia = df_hist_pred.head(6).copy()
                                            df_tendencia['indice'] = range(len(df_tendencia))
                                            # Regresión lineal simple
                                            from numpy import polyfit
                                            pendiente, intercepto = polyfit(df_tendencia['indice'],
                                                                            df_tendencia['cantidad_transacciones'], 1)
                                            tendencia_mensual = pendiente
                                        else:
                                            tendencia_mensual = 0

                                        # ========== CALCULAR ESTACIONALIDAD DESDE HISTÓRICOS ==========
                                        # Agrupar por mes del año para detectar patrones estacionales
                                        estacionalidad_dict = {}
                                        if len(df_hist_pred) >= 6:
                                            df_estacional = df_hist_pred.copy()
                                            # Calcular índice estacional por mes
                                            promedio_general = df_estacional['cantidad_transacciones'].mean()
                                            if promedio_general > 0:
                                                for _, row in df_estacional.iterrows():
                                                    mes_num = int(row['mes'])
                                                    indice = row['cantidad_transacciones'] / promedio_general
                                                    if mes_num not in estacionalidad_dict:
                                                        estacionalidad_dict[mes_num] = []
                                                    estacionalidad_dict[mes_num].append(indice)

                                                # Promediar índices por mes
                                                estacionalidad = {mes: np.mean(indices) for mes, indices in estacionalidad_dict.items()}
                                            else:
                                                estacionalidad = {i: 1.0 for i in range(1, 13)}
                                        else:
                                            # Estacionalidad genérica del mercado automotor argentino
                                            estacionalidad = {
                                                1: 0.85,   # Enero: bajo (post vacaciones)
                                                2: 0.90,   # Febrero: bajo
                                                3: 0.95,   # Marzo: medio (inicio escolar)
                                                4: 1.00,   # Abril: medio
                                                5: 1.05,   # Mayo: medio-alto
                                                6: 1.10,   # Junio: alto (medio año)
                                                7: 0.95,   # Julio: medio (vacaciones)
                                                8: 1.00,   # Agosto: medio
                                                9: 1.05,   # Septiembre: medio-alto
                                                10: 1.10,  # Octubre: alto
                                                11: 1.15,  # Noviembre: alto (pre-verano)
                                                12: 1.20   # Diciembre: muy alto (fin de año)
                                            }

                                        # Detectar volatilidad alta
                                        desv_std = df_hist_pred['cantidad_transacciones'].std()
                                        coef_variacion = (desv_std / promedio_mensual_hist * 100) if promedio_mensual_hist > 0 else 0

                                        # Decidir método de proyección
                                        if coef_variacion > 50:  # Alta volatilidad
                                            # Usar último mes como base conservadora
                                            base_proyeccion = ultimo_mes
                                            metodo = "Último mes (alta volatilidad detectada)"
                                            st.warning(f"⚠️ **Alta volatilidad detectada** (CV: {coef_variacion:.1f}%). Usando último mes como base conservadora.")
                                        elif abs(tendencia_mensual) > promedio_mensual_hist * 0.1:  # Tendencia fuerte
                                            # Usar últimos 3 meses + tendencia
                                            base_proyeccion = ultimos_3_meses
                                            metodo = "Promedio últimos 3 meses con ajuste de tendencia"
                                            if tendencia_mensual < 0:
                                                st.info(f"📉 **Tendencia bajista** detectada ({tendencia_mensual:.1f} unidades/mes)")
                                            else:
                                                st.info(f"📈 **Tendencia alcista** detectada (+{tendencia_mensual:.1f} unidades/mes)")
                                        else:
                                            # Usar promedio de últimos 3 meses
                                            base_proyeccion = ultimos_3_meses
                                            metodo = "Promedio de últimos 3 meses"

                                        # Calcular proyecciones CON ESTACIONALIDAD
                                        meses_proyeccion = horizonte_pred // 30
                                        proyecciones = []
                                        proyecciones_sin_estacional = []

                                        # Obtener mes actual y año para proyección
                                        from datetime import datetime
                                        fecha_base = df_hist_pred.iloc[0]['fecha_mes']
                                        mes_base = int(df_hist_pred.iloc[0]['mes'])
                                        anio_base = int(df_hist_pred.iloc[0]['anio'])

                                        for i in range(1, meses_proyeccion + 1):
                                            # Calcular proyección base con tendencia
                                            proyeccion_base_mes = base_proyeccion + (tendencia_mensual * i)
                                            proyeccion_base_mes = max(0, proyeccion_base_mes)
                                            proyecciones_sin_estacional.append(proyeccion_base_mes)

                                            # Calcular mes futuro
                                            mes_futuro = ((mes_base + i - 1) % 12) + 1

                                            # Aplicar factor estacional
                                            factor_estacional = estacionalidad.get(mes_futuro, 1.0)
                                            proyeccion_ajustada = proyeccion_base_mes * factor_estacional
                                            proyeccion_ajustada = max(0, proyeccion_ajustada)

                                            proyecciones.append({
                                                'mes_num': i,
                                                'mes_calendario': mes_futuro,
                                                'base': proyeccion_base_mes,
                                                'factor_estacional': factor_estacional,
                                                'proyeccion': proyeccion_ajustada
                                            })

                                        proyeccion_total = sum([p['proyeccion'] for p in proyecciones])
                                        proyeccion_total_sin_estacional = sum(proyecciones_sin_estacional)

                                        # Mostrar métricas
                                        col_p1, col_p2, col_p3, col_p4 = st.columns(4)

                                        with col_p1:
                                            impacto_estacional = ((proyeccion_total - proyeccion_total_sin_estacional) /
                                                                 proyeccion_total_sin_estacional * 100) if proyeccion_total_sin_estacional > 0 else 0
                                            st.metric(
                                                f"Proyección {meses_proyeccion} {'mes' if meses_proyeccion==1 else 'meses'}",
                                                format_number(proyeccion_total),
                                                f"Estacional: {impacto_estacional:+.1f}%"
                                            )

                                        with col_p2:
                                            st.metric(
                                                "Base Mensual",
                                                format_number(base_proyeccion),
                                                f"Último: {ultimo_mes:.0f}"
                                            )

                                        with col_p3:
                                            # Calcular tendencia reciente (último vs hace 3 meses)
                                            if len(df_hist_pred) >= 4:
                                                tendencia = ((df_hist_pred.iloc[0]['cantidad_transacciones'] -
                                                            df_hist_pred.iloc[-1]['cantidad_transacciones']) /
                                                           df_hist_pred.iloc[-1]['cantidad_transacciones'] * 100)
                                                st.metric(
                                                    "Tendencia 12 meses",
                                                    f"{tendencia:+.1f}%",
                                                    "Último vs más antiguo"
                                                )

                                        with col_p4:
                                            st.metric(
                                                "Volatilidad",
                                                f"±{desv_std:.0f}",
                                                f"CV: {coef_variacion:.1f}%"
                                            )

                                        # Mostrar desglose mensual de la proyección CON ESTACIONALIDAD
                                        if meses_proyeccion > 1:
                                            with st.expander("📅 Ver Proyección Mensual Detallada (con Estacionalidad)"):
                                                # Nombres de meses
                                                MESES_NOMBRES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                                               'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

                                                df_proyeccion = pd.DataFrame({
                                                    'Mes Futuro': [f"{MESES_NOMBRES[p['mes_calendario']]} ({p['mes_num']})" for p in proyecciones],
                                                    'Base + Tendencia': [f"{p['base']:.0f}" for p in proyecciones],
                                                    'Factor Estacional': [f"{p['factor_estacional']:.2f}x" for p in proyecciones],
                                                    'Proyección Final': [f"{p['proyeccion']:.0f}" for p in proyecciones],
                                                    'Acumulado': [f"{sum([pr['proyeccion'] for pr in proyecciones[:i+1]]):.0f}" for i in range(len(proyecciones))]
                                                })
                                                st.dataframe(df_proyeccion, use_container_width=True, hide_index=True)

                                                # Gráfico de comparación
                                                st.markdown("**Comparación: Con vs Sin Estacionalidad**")
                                                df_comp = pd.DataFrame({
                                                    'Mes': [f"Mes {i+1}" for i in range(len(proyecciones))],
                                                    'Con Estacionalidad': [p['proyeccion'] for p in proyecciones],
                                                    'Sin Estacionalidad': proyecciones_sin_estacional
                                                })

                                                fig_comp = go.Figure()
                                                fig_comp.add_trace(go.Scatter(
                                                    x=df_comp['Mes'],
                                                    y=df_comp['Con Estacionalidad'],
                                                    name='Con Estacionalidad',
                                                    mode='lines+markers',
                                                    line=dict(color='#1f77b4', width=3),
                                                    marker=dict(size=10)
                                                ))
                                                fig_comp.add_trace(go.Scatter(
                                                    x=df_comp['Mes'],
                                                    y=df_comp['Sin Estacionalidad'],
                                                    name='Sin Estacionalidad (tendencia lineal)',
                                                    mode='lines+markers',
                                                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                                                    marker=dict(size=8)
                                                ))
                                                fig_comp.update_layout(
                                                    title='Impacto de la Estacionalidad en la Proyección',
                                                    xaxis_title='Mes Proyectado',
                                                    yaxis_title='Cantidad Proyectada',
                                                    hovermode='x unified',
                                                    height=400
                                                )
                                                st.plotly_chart(fig_comp, use_container_width=True)

                                        # Explicación del método
                                        st.markdown("---")
                                        st.markdown("##### 📖 Metodología de Proyección")
                                        st.markdown(f"""
                                        **Método aplicado:** {metodo} + Ajuste Estacional

                                        **Componentes:**
                                        1. **Base de cálculo:** {"Último mes" if coef_variacion > 50 else "Promedio últimos 3 meses"} = {base_proyeccion:.0f} unidades/mes
                                        2. **Tendencia lineal:** {tendencia_mensual:+.2f} unidades/mes (regresión últimos 6 meses)
                                        3. **Estacionalidad:** Calculada desde históricos (índices por mes del año)
                                        4. **Volatilidad:** CV = {coef_variacion:.1f}% {"(⚠️ Alta)" if coef_variacion > 50 else "(✓ Moderada)"}

                                        **Fórmula:**
                                        ```
                                        Proyección(mes_i) = [Base + (Tendencia × i)] × Factor_Estacional(mes)
                                        ```

                                        **Interpretación:**
                                        {"- ⚠️ Debido a la alta volatilidad, se usa el **último mes** como base conservadora" if coef_variacion > 50 else ""}
                                        {"- 📉 Tendencia bajista detectada: **disminución sostenida** en la demanda" if tendencia_mensual < -promedio_mensual_hist * 0.1 else ""}
                                        {"- 📈 Tendencia alcista detectada: **crecimiento sostenido** en la demanda" if tendencia_mensual > promedio_mensual_hist * 0.1 else ""}
                                        {"- ✓ Sin tendencia fuerte, se usa promedio reciente + estacionalidad" if abs(tendencia_mensual) <= promedio_mensual_hist * 0.1 and coef_variacion <= 50 else ""}
                                        - 📊 **Impacto estacional total:** {impacto_estacional:+.1f}% sobre proyección lineal

                                        **Variables macro consideradas:**
                                        - IPC actual: {ipc_actual:.1f} (var: {ipc_var_mensual:+.1f}%)
                                        - BADLAR actual: {badlar_actual:.1f}%
                                        - TC actual: ${tc_actual:.0f}
                                        """)

                                    # Tabla de datos históricos
                                    with st.expander("📋 Ver Datos Históricos Detallados"):
                                        df_tabla_hist = df_hist_plot[['fecha_str', 'cantidad_transacciones', 'edad_titular', 'anio_modelo']].copy()
                                        df_tabla_hist.columns = ['Mes', 'Cantidad', 'Edad Promedio Titular', 'Año Modelo Promedio']
                                        df_tabla_hist['Edad Promedio Titular'] = df_tabla_hist['Edad Promedio Titular'].round(1)
                                        df_tabla_hist['Año Modelo Promedio'] = df_tabla_hist['Año Modelo Promedio'].round(0)
                                        st.dataframe(df_tabla_hist, use_container_width=True, hide_index=True)

                            except Exception as e:
                                st.error(f"❌ Error al realizar predicción: {str(e)}")
                                st.exception(e)

                    # Información adicional
                    with st.expander("ℹ️ Acerca del Modelo de Predicción"):
                        modelo_info = {
                            "LightGBM": {
                                "nombre": "LightGBM (Light Gradient Boosting Machine)",
                                "r2": "~0.974",
                                "mae": "~0.22"
                            },
                            "XGBoost": {
                                "nombre": "XGBoost (Extreme Gradient Boosting)",
                                "r2": "~0.957",
                                "mae": "~0.12"
                            }
                        }

                        info = modelo_info.get(MODEL_NAME, modelo_info["XGBoost"])

                        st.markdown(f"""
                        ### 🤖 Modelo de Machine Learning

                        **Algoritmo:** {info["nombre"]}

                        **Características del modelo:**
                        - **R² Score:** {info["r2"]} (varianza explicada)
                        - **MAE:** {info["mae"]} (Error Absoluto Medio)
                        - **Tiempo de predicción:** < 1 segundo

                        **Variables utilizadas:**
                        1. **Históricas:** Cantidad de transacciones en meses anteriores (lag 1, lag 3)
                        2. **Promedios móviles:** MA3, MA6
                        3. **Variación intermensual:** Tasa de cambio mes a mes
                        4. **Categóricas:** Marca, modelo, provincia, tipo de vehículo
                        5. **Macro-económicas:** IPC, BADLAR, Tipo de Cambio
                        6. **Temporales:** Año, mes, trimestre, estacionalidad

                        **Limitaciones:**
                        - Requiere al menos 3-6 meses de historial para predicciones confiables
                        - Funciona mejor con marcas/modelos con volúmenes consistentes
                        - Las predicciones de largo plazo (>120 días) tienen mayor incertidumbre

                        **Casos de uso:**
                        - Planificación de inventario de concesionarias
                        - Estimación de demanda por región
                        - Análisis de tendencias de mercado
                        - Evaluación de impacto de variables macro-económicas
                        """)

        except Exception as e:
            st.error(f"❌ Error al cargar el modelo: {str(e)}")
            st.exception(e)

# ==================== TAB 8: KPIs DE MERCADO ====================
with tab8:
    st.header("📈 KPIs de Mercado Automotor")
    st.markdown("Indicadores clave de rendimiento del mercado automotor con filtros avanzados y análisis comparativo")
    st.markdown("---")

    # ========== FILTROS GLOBALES ==========
    st.markdown("## 🔍 Filtros de Análisis")

    # Fila 1: Años y Meses
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        st.markdown("#### 📅 Período Temporal")

        # Obtener años disponibles
        query_anios_kpi = text("""
            SELECT DISTINCT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio
            FROM datos_gob_inscripciones
            WHERE tramite_fecha IS NOT NULL
            ORDER BY anio DESC
        """)

        try:
            df_anios_kpi = pd.read_sql(query_anios_kpi, engine)
            anios_disponibles_kpi = df_anios_kpi['anio'].tolist()
        except:
            anios_disponibles_kpi = []

        anios_seleccionados_kpi = st.multiselect(
            "Selecciona uno o más años (para comparación YoY):",
            options=anios_disponibles_kpi,
            default=[anios_disponibles_kpi[0]] if anios_disponibles_kpi else [],
            key="kpi_anios"
        )

        meses_seleccionados_kpi = st.multiselect(
            "Selecciona uno o más meses (para comparación MoM):",
            options=list(MESES_ES.values()),
            default=list(MESES_ES.values()),
            key="kpi_meses"
        )

    with col_f2:
        st.markdown("#### 🎯 Segmentación")

        # Obtener marcas disponibles
        query_marcas_kpi = text("""
            SELECT DISTINCT automotor_marca_descripcion as marca
            FROM datos_gob_inscripciones
            WHERE automotor_marca_descripcion IS NOT NULL
            AND automotor_marca_descripcion != ''
            ORDER BY marca
        """)

        try:
            df_marcas_kpi = pd.read_sql(query_marcas_kpi, engine)
            marcas_disponibles_kpi = df_marcas_kpi['marca'].tolist()
        except:
            marcas_disponibles_kpi = []

        marcas_seleccionadas_kpi = st.multiselect(
            "Marcas (opcional - dejar vacío para todas):",
            options=marcas_disponibles_kpi,
            default=[],
            key="kpi_marcas"
        )

        tipo_persona_kpi = st.selectbox(
            "Tipo de Persona:",
            options=["Ambos", "Física", "Jurídica"],
            index=0,
            key="kpi_tipo_persona"
        )

    # Fila 2: Geografía
    st.markdown("#### 🗺️ Filtros Geográficos")
    col_geo1, col_geo2 = st.columns(2)

    with col_geo1:
        # Obtener provincias disponibles
        if anios_seleccionados_kpi:
            query_prov_kpi = text("""
                SELECT DISTINCT titular_domicilio_provincia as provincia
                FROM datos_gob_inscripciones
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND titular_domicilio_provincia IS NOT NULL
                AND titular_domicilio_provincia != ''
                ORDER BY provincia
            """)

            try:
                df_prov_kpi = pd.read_sql(query_prov_kpi, engine, params={'anios': anios_seleccionados_kpi})
                provincias_disponibles_kpi = df_prov_kpi['provincia'].tolist()
            except:
                provincias_disponibles_kpi = []
        else:
            provincias_disponibles_kpi = []

        provincias_seleccionadas_kpi = st.multiselect(
            "Provincias (opcional - dejar vacío para todas):",
            options=provincias_disponibles_kpi,
            default=[],
            key="kpi_provincias"
        )

    with col_geo2:
        # Filtro de localidades (cascading)
        if provincias_seleccionadas_kpi and anios_seleccionados_kpi:
            query_loc_kpi = text("""
                SELECT DISTINCT titular_domicilio_localidad as localidad
                FROM datos_gob_inscripciones
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND titular_domicilio_provincia = ANY(:provincias)
                AND titular_domicilio_localidad IS NOT NULL
                AND titular_domicilio_localidad != ''
                ORDER BY localidad
            """)

            try:
                df_loc_kpi = pd.read_sql(
                    query_loc_kpi,
                    engine,
                    params={'anios': anios_seleccionados_kpi, 'provincias': provincias_seleccionadas_kpi}
                )
                localidades_disponibles_kpi = df_loc_kpi['localidad'].tolist()
            except:
                localidades_disponibles_kpi = []
        else:
            localidades_disponibles_kpi = []

        localidades_seleccionadas_kpi = st.multiselect(
            "Localidades (opcional - dejar vacío para todas):",
            options=localidades_disponibles_kpi,
            default=[],
            key="kpi_localidades"
        )

    # Fila 3: Otros filtros
    col_otros1, col_otros2, col_otros3 = st.columns(3)

    with col_otros1:
        genero_kpi = st.selectbox(
            "Género:",
            options=["Todos", "Masculino", "Femenino"],
            index=0,
            key="kpi_genero"
        )

    with col_otros2:
        origen_kpi = st.selectbox(
            "Origen del Vehículo:",
            options=["Ambos", "Nacional", "Importado"],
            index=0,
            key="kpi_origen"
        )

    with col_otros3:
        # Obtener tipos de vehículo
        query_tipos_kpi = text("""
            SELECT DISTINCT automotor_tipo_descripcion as tipo
            FROM datos_gob_inscripciones
            WHERE automotor_tipo_descripcion IS NOT NULL
            AND automotor_tipo_descripcion != ''
            ORDER BY tipo
        """)

        try:
            df_tipos_kpi = pd.read_sql(query_tipos_kpi, engine)
            tipos_disponibles_kpi = ['Todos'] + df_tipos_kpi['tipo'].tolist()
        except:
            tipos_disponibles_kpi = ['Todos']

        tipo_vehiculo_kpi = st.selectbox(
            "Tipo de Vehículo:",
            options=tipos_disponibles_kpi,
            index=0,
            key="kpi_tipo_vehiculo"
        )

    st.markdown("---")

    # Validar filtros
    if not anios_seleccionados_kpi:
        st.warning("⚠️ Selecciona al menos un año para comenzar el análisis")
    elif not meses_seleccionados_kpi:
        st.warning("⚠️ Selecciona al menos un mes")
    else:
        # Convertir meses a números
        meses_numeros_kpi = [list(MESES_ES.keys())[list(MESES_ES.values()).index(mes)] for mes in meses_seleccionados_kpi]

        # Construir filtros WHERE dinámicos
        filtro_marca_kpi = ""
        if marcas_seleccionadas_kpi:
            filtro_marca_kpi = "AND automotor_marca_descripcion = ANY(:marcas)"

        filtro_tipo_persona_kpi = ""
        if tipo_persona_kpi == "Física":
            filtro_tipo_persona_kpi = "AND titular_tipo_persona = 'Física'"
        elif tipo_persona_kpi == "Jurídica":
            filtro_tipo_persona_kpi = "AND titular_tipo_persona = 'Jurídica'"

        filtro_provincia_kpi = ""
        if provincias_seleccionadas_kpi:
            filtro_provincia_kpi = "AND titular_domicilio_provincia = ANY(:provincias)"

        filtro_localidad_kpi = ""
        if localidades_seleccionadas_kpi:
            filtro_localidad_kpi = "AND titular_domicilio_localidad = ANY(:localidades)"

        filtro_genero_kpi = ""
        if genero_kpi != "Todos":
            filtro_genero_kpi = f"AND titular_genero = '{genero_kpi}'"

        filtro_origen_kpi = ""
        if origen_kpi != "Ambos":
            filtro_origen_kpi = f"AND UPPER(automotor_origen) = '{origen_kpi.upper()}'"

        filtro_tipo_vehiculo_kpi = ""
        if tipo_vehiculo_kpi != "Todos":
            filtro_tipo_vehiculo_kpi = f"AND automotor_tipo_descripcion = '{tipo_vehiculo_kpi}'"

        # Construir params dict
        params_kpi = {
            'anios': anios_seleccionados_kpi,
            'meses': meses_numeros_kpi
        }
        if marcas_seleccionadas_kpi:
            params_kpi['marcas'] = marcas_seleccionadas_kpi
        if provincias_seleccionadas_kpi:
            params_kpi['provincias'] = provincias_seleccionadas_kpi
        if localidades_seleccionadas_kpi:
            params_kpi['localidades'] = localidades_seleccionadas_kpi

        # ========== SECCIÓN 1: MERCADO DE USADOS ==========
        st.markdown("## 🚙 Mercado de Usados")

        try:
            # KPI: EVT - Edad del Vehículo al Transferirse
            st.markdown("### 📅 EVT: Edad del Vehículo al Transferirse")
            st.markdown("_Antigüedad promedio de los vehículos que cambian de manos_")

            query_evt = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo as edad_vehiculo,
                    COUNT(*) as cantidad
                FROM datos_gob_transferencias
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND automotor_anio_modelo IS NOT NULL
                AND automotor_anio_modelo > 1900
                AND tramite_fecha IS NOT NULL
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, mes, edad_vehiculo
                HAVING EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo >= 0
                AND EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo <= 50
                ORDER BY anio, mes, edad_vehiculo
            """)

            df_evt = pd.read_sql(query_evt, engine, params=params_kpi)

            if not df_evt.empty:
                # Calcular EVT promedio por año y mes
                df_evt['mes_nombre'] = df_evt['mes'].map(MESES_ES)
                df_evt_agg = df_evt.groupby(['anio', 'mes', 'mes_nombre']).apply(
                    lambda x: (x['edad_vehiculo'] * x['cantidad']).sum() / x['cantidad'].sum()
                ).reset_index(name='evt_promedio')

                # Métricas generales
                col_evt1, col_evt2, col_evt3, col_evt4 = st.columns(4)

                total_transferencias = df_evt['cantidad'].sum()
                evt_general = (df_evt['edad_vehiculo'] * df_evt['cantidad']).sum() / total_transferencias
                edad_min = df_evt['edad_vehiculo'].min()
                edad_max = df_evt['edad_vehiculo'].max()

                with col_evt1:
                    st.metric("EVT Promedio", f"{evt_general:.1f} años")
                with col_evt2:
                    st.metric("Total Transferencias", format_number(total_transferencias))
                with col_evt3:
                    st.metric("Edad Mínima", f"{edad_min} años")
                with col_evt4:
                    st.metric("Edad Máxima", f"{edad_max} años")

                # Gráfico de tendencia temporal
                if len(anios_seleccionados_kpi) > 1:
                    # Comparación YoY
                    fig_evt = px.line(
                        df_evt_agg,
                        x='mes',
                        y='evt_promedio',
                        color='anio',
                        title='Evolución de la Edad Promedio de Vehículos Transferidos (Comparación YoY)',
                        labels={'evt_promedio': 'Edad Promedio (años)', 'mes': 'Mes', 'anio': 'Año'},
                        markers=True
                    )
                    fig_evt.update_xaxis(tickmode='array', tickvals=list(range(1, 13)), ticktext=list(MESES_ES.values()))
                else:
                    # Tendencia mensual
                    fig_evt = px.bar(
                        df_evt_agg,
                        x='mes_nombre',
                        y='evt_promedio',
                        title=f'Edad Promedio de Vehículos Transferidos - Año {anios_seleccionados_kpi[0]}',
                        labels={'evt_promedio': 'Edad Promedio (años)', 'mes_nombre': 'Mes'},
                        text='evt_promedio',
                        color='evt_promedio',
                        color_continuous_scale='Blues'
                    )
                    fig_evt.update_traces(texttemplate='%{text:.1f}', textposition='outside')

                st.plotly_chart(fig_evt, use_container_width=True)

                # Distribución de edades
                st.markdown("#### 📊 Distribución de Edades")
                df_dist_edad = df_evt.groupby('edad_vehiculo')['cantidad'].sum().reset_index()

                fig_dist = px.bar(
                    df_dist_edad,
                    x='edad_vehiculo',
                    y='cantidad',
                    title='Distribución de Transferencias por Edad del Vehículo',
                    labels={'edad_vehiculo': 'Edad del Vehículo (años)', 'cantidad': 'Cantidad de Transferencias'},
                    color='cantidad',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig_dist, use_container_width=True)

            else:
                st.warning("⚠️ No se encontraron datos de transferencias con los filtros seleccionados")

            st.markdown("---")

            # KPI: IAM - Índice de Antigüedad del Mercado
            st.markdown("### 📊 IAM: Índice de Antigüedad del Mercado")
            st.markdown("_Antigüedad promedio de todos los vehículos en transacción_")

            query_iam = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    'Inscripciones' as tipo_transaccion,
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo as edad_vehiculo,
                    COUNT(*) as cantidad
                FROM datos_gob_inscripciones
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND automotor_anio_modelo IS NOT NULL
                AND automotor_anio_modelo > 1900
                AND tramite_fecha IS NOT NULL
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, mes, edad_vehiculo
                HAVING EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo >= 0

                UNION ALL

                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    'Transferencias' as tipo_transaccion,
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo as edad_vehiculo,
                    COUNT(*) as cantidad
                FROM datos_gob_transferencias
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND automotor_anio_modelo IS NOT NULL
                AND automotor_anio_modelo > 1900
                AND tramite_fecha IS NOT NULL
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, mes, edad_vehiculo
                HAVING EXTRACT(YEAR FROM tramite_fecha)::INTEGER - automotor_anio_modelo >= 0

                ORDER BY anio, mes, tipo_transaccion, edad_vehiculo
            """)

            df_iam = pd.read_sql(query_iam, engine, params=params_kpi)

            if not df_iam.empty:
                # Calcular IAM por tipo de transacción
                df_iam['mes_nombre'] = df_iam['mes'].map(MESES_ES)
                df_iam_agg = df_iam.groupby(['anio', 'mes', 'mes_nombre', 'tipo_transaccion']).apply(
                    lambda x: (x['edad_vehiculo'] * x['cantidad']).sum() / x['cantidad'].sum()
                ).reset_index(name='iam_promedio')

                # Métricas comparativas
                col_iam1, col_iam2, col_iam3 = st.columns(3)

                df_insc = df_iam[df_iam['tipo_transaccion'] == 'Inscripciones']
                df_trans = df_iam[df_iam['tipo_transaccion'] == 'Transferencias']

                iam_insc = (df_insc['edad_vehiculo'] * df_insc['cantidad']).sum() / df_insc['cantidad'].sum() if not df_insc.empty else 0
                iam_trans = (df_trans['edad_vehiculo'] * df_trans['cantidad']).sum() / df_trans['cantidad'].sum() if not df_trans.empty else 0
                iam_general = (df_iam['edad_vehiculo'] * df_iam['cantidad']).sum() / df_iam['cantidad'].sum()

                with col_iam1:
                    st.metric("IAM Inscripciones", f"{iam_insc:.1f} años", help="0km + usados nuevos")
                with col_iam2:
                    st.metric("IAM Transferencias", f"{iam_trans:.1f} años", help="Mercado de usados")
                with col_iam3:
                    delta_iam = iam_trans - iam_insc
                    st.metric("Diferencia", f"{delta_iam:.1f} años", delta=f"{delta_iam:+.1f}")

                # Gráfico comparativo
                fig_iam = px.line(
                    df_iam_agg,
                    x='mes',
                    y='iam_promedio',
                    color='tipo_transaccion',
                    facet_col='anio' if len(anios_seleccionados_kpi) > 1 else None,
                    title='Índice de Antigüedad del Mercado por Tipo de Transacción',
                    labels={'iam_promedio': 'Edad Promedio (años)', 'mes': 'Mes', 'tipo_transaccion': 'Tipo'},
                    markers=True
                )
                fig_iam.update_xaxes(tickmode='array', tickvals=list(range(1, 13)), ticktext=list(MESES_ES.values()))
                st.plotly_chart(fig_iam, use_container_width=True)

            else:
                st.warning("⚠️ No se encontraron datos con los filtros seleccionados")

            st.markdown("---")

            # KPI: IDA - Índice de Demanda Activa
            st.markdown("### 🔄 IDA: Índice de Demanda Activa")
            st.markdown("_Ratio de transferencias sobre inscripciones - indica dinamismo del mercado de usados_")

            query_ida = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    COUNT(*) as inscripciones
                FROM datos_gob_inscripciones
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND tramite_fecha IS NOT NULL
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, mes
                ORDER BY anio, mes
            """)

            query_ida_trans = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    COUNT(*) as transferencias
                FROM datos_gob_transferencias
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND tramite_fecha IS NOT NULL
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, mes
                ORDER BY anio, mes
            """)

            df_ida_insc = pd.read_sql(query_ida, engine, params=params_kpi)
            df_ida_trans = pd.read_sql(query_ida_trans, engine, params=params_kpi)

            if not df_ida_insc.empty and not df_ida_trans.empty:
                # Merge
                df_ida = df_ida_insc.merge(df_ida_trans, on=['anio', 'mes'], how='outer').fillna(0)
                df_ida['ida'] = (df_ida['transferencias'] / df_ida['inscripciones'] * 100).fillna(0)
                df_ida['mes_nombre'] = df_ida['mes'].map(MESES_ES)

                # Métricas
                col_ida1, col_ida2, col_ida3, col_ida4 = st.columns(4)

                total_insc = df_ida['inscripciones'].sum()
                total_trans = df_ida['transferencias'].sum()
                ida_general = (total_trans / total_insc * 100) if total_insc > 0 else 0

                with col_ida1:
                    st.metric("IDA Promedio", f"{ida_general:.1f}%")
                with col_ida2:
                    st.metric("Total Inscripciones", format_number(int(total_insc)))
                with col_ida3:
                    st.metric("Total Transferencias", format_number(int(total_trans)))
                with col_ida4:
                    ratio_text = "Usados > 0km" if ida_general > 100 else "0km > Usados"
                    st.metric("Mercado Dominante", ratio_text)

                # Gráfico
                if len(anios_seleccionados_kpi) > 1:
                    fig_ida = px.line(
                        df_ida,
                        x='mes',
                        y='ida',
                        color='anio',
                        title='Índice de Demanda Activa - Comparación YoY',
                        labels={'ida': 'IDA (%)', 'mes': 'Mes', 'anio': 'Año'},
                        markers=True
                    )
                    fig_ida.update_xaxis(tickmode='array', tickvals=list(range(1, 13)), ticktext=list(MESES_ES.values()))
                    fig_ida.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Equilibrio (100%)")
                else:
                    fig_ida = px.bar(
                        df_ida,
                        x='mes_nombre',
                        y='ida',
                        title=f'Índice de Demanda Activa - Año {anios_seleccionados_kpi[0]}',
                        labels={'ida': 'IDA (%)', 'mes_nombre': 'Mes'},
                        text='ida',
                        color='ida',
                        color_continuous_scale='RdYlGn'
                    )
                    fig_ida.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig_ida.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Equilibrio")

                st.plotly_chart(fig_ida, use_container_width=True)

                st.info("""
                **💡 Interpretación del IDA:**
                - **IDA > 100%**: El mercado de usados es más activo que el de 0km
                - **IDA = 100%**: Equilibrio entre ambos mercados
                - **IDA < 100%**: El mercado de 0km es más activo
                """)

            else:
                st.warning("⚠️ No se encontraron datos suficientes para calcular el IDA")

        except Exception as e:
            st.error(f"❌ Error al calcular KPIs de Mercado de Usados: {str(e)}")
            st.exception(e)

        st.markdown("---")

        # ========== SECCIÓN 2: FINANCIAMIENTO ==========
        st.markdown("## 💳 Financiamiento")
        st.markdown("""
        **Metodología corregida:**
        - **IF 0km** = Prendas 0km / Inscripciones (donde `tramite_fecha = fecha_inscripcion_inicial`)
        - **IF Usados** = Prendas Usados / Transferencias (donde `tramite_fecha ≠ fecha_inscripcion_inicial`)
        """)

        try:
            # KPI: IF - Índice de Financiamiento (CORREGIDO)
            st.markdown("### 💰 IF: Índice de Financiamiento")

            # Query para Inscripciones (0km)
            query_if_insc = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    COUNT(*) as inscripciones
                FROM datos_gob_inscripciones
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND tramite_fecha IS NOT NULL
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, mes
                ORDER BY anio, mes
            """)

            # Query para Transferencias (Usados)
            query_if_transf = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    COUNT(*) as transferencias
                FROM datos_gob_transferencias
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND tramite_fecha IS NOT NULL
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, mes
                ORDER BY anio, mes
            """)

            # Query para Prendas 0km (tramite_fecha = fecha_inscripcion_inicial)
            query_if_prendas_0km = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    COUNT(*) as prendas_0km
                FROM datos_gob_prendas
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND tramite_fecha IS NOT NULL
                AND fecha_inscripcion_inicial IS NOT NULL
                AND DATE(tramite_fecha) = DATE(fecha_inscripcion_inicial)
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, mes
                ORDER BY anio, mes
            """)

            # Query para Prendas Usados (tramite_fecha <> fecha_inscripcion_inicial)
            query_if_prendas_usados = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
                    COUNT(*) as prendas_usados
                FROM datos_gob_prendas
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND tramite_fecha IS NOT NULL
                AND fecha_inscripcion_inicial IS NOT NULL
                AND DATE(tramite_fecha) <> DATE(fecha_inscripcion_inicial)
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, mes
                ORDER BY anio, mes
            """)

            df_if_insc = pd.read_sql(query_if_insc, engine, params=params_kpi)
            df_if_transf = pd.read_sql(query_if_transf, engine, params=params_kpi)
            df_if_prendas_0km = pd.read_sql(query_if_prendas_0km, engine, params=params_kpi)
            df_if_prendas_usados = pd.read_sql(query_if_prendas_usados, engine, params=params_kpi)

            if not df_if_insc.empty:
                # Merge todos los dataframes
                df_if = df_if_insc.merge(df_if_prendas_0km, on=['anio', 'mes'], how='left').fillna(0)
                df_if = df_if.merge(df_if_transf, on=['anio', 'mes'], how='left').fillna(0)
                df_if = df_if.merge(df_if_prendas_usados, on=['anio', 'mes'], how='left').fillna(0)

                # Calcular IF para 0km y Usados
                df_if['if_0km'] = (df_if['prendas_0km'] / df_if['inscripciones'] * 100).fillna(0)
                df_if['if_usados'] = (df_if['prendas_usados'] / df_if['transferencias'] * 100).fillna(0)
                df_if['mes_nombre'] = df_if['mes'].map(MESES_ES)

                # Métricas principales
                st.markdown("#### 🆕 Financiamiento de Vehículos 0km")
                col_if1, col_if2, col_if3 = st.columns(3)

                total_prendas_0km = df_if['prendas_0km'].sum()
                total_insc_if = df_if['inscripciones'].sum()
                if_0km_general = (total_prendas_0km / total_insc_if * 100) if total_insc_if > 0 else 0

                with col_if1:
                    st.metric("IF 0km", f"{if_0km_general:.1f}%", help="Prendas 0km / Inscripciones")
                with col_if2:
                    st.metric("Prendas 0km", format_number(int(total_prendas_0km)))
                with col_if3:
                    st.metric("Inscripciones", format_number(int(total_insc_if)))

                st.markdown("#### 🔄 Financiamiento de Vehículos Usados")
                col_if4, col_if5, col_if6 = st.columns(3)

                total_prendas_usados = df_if['prendas_usados'].sum()
                total_transf_if = df_if['transferencias'].sum()
                if_usados_general = (total_prendas_usados / total_transf_if * 100) if total_transf_if > 0 else 0

                with col_if4:
                    st.metric("IF Usados", f"{if_usados_general:.1f}%", help="Prendas Usados / Transferencias")
                with col_if5:
                    st.metric("Prendas Usados", format_number(int(total_prendas_usados)))
                with col_if6:
                    st.metric("Transferencias", format_number(int(total_transf_if)))

                # Gráfico comparativo IF 0km vs IF Usados
                st.markdown("#### 📈 Evolución Mensual del Financiamiento")

                col_graf_if1, col_graf_if2 = st.columns(2)

                with col_graf_if1:
                    # Gráfico IF 0km
                    if len(anios_seleccionados_kpi) > 1:
                        fig_if_0km = px.line(
                            df_if,
                            x='mes',
                            y='if_0km',
                            color='anio',
                            title='IF 0km - Comparación YoY',
                            labels={'if_0km': 'IF 0km (%)', 'mes': 'Mes', 'anio': 'Año'},
                            markers=True
                        )
                        fig_if_0km.update_xaxis(tickmode='array', tickvals=list(range(1, 13)), ticktext=list(MESES_ES.values()))
                    else:
                        fig_if_0km = px.bar(
                            df_if,
                            x='mes_nombre',
                            y='if_0km',
                            title=f'IF 0km - Año {anios_seleccionados_kpi[0]}',
                            labels={'if_0km': 'IF 0km (%)', 'mes_nombre': 'Mes'},
                            text='if_0km',
                            color='if_0km',
                            color_continuous_scale='Greens'
                        )
                        fig_if_0km.update_traces(texttemplate='%{text:.1f}%', textposition='outside')

                    st.plotly_chart(fig_if_0km, use_container_width=True)

                with col_graf_if2:
                    # Gráfico IF Usados
                    if len(anios_seleccionados_kpi) > 1:
                        fig_if_usados = px.line(
                            df_if,
                            x='mes',
                            y='if_usados',
                            color='anio',
                            title='IF Usados - Comparación YoY',
                            labels={'if_usados': 'IF Usados (%)', 'mes': 'Mes', 'anio': 'Año'},
                            markers=True
                        )
                        fig_if_usados.update_xaxis(tickmode='array', tickvals=list(range(1, 13)), ticktext=list(MESES_ES.values()))
                    else:
                        fig_if_usados = px.bar(
                            df_if,
                            x='mes_nombre',
                            y='if_usados',
                            title=f'IF Usados - Año {anios_seleccionados_kpi[0]}',
                            labels={'if_usados': 'IF Usados (%)', 'mes_nombre': 'Mes'},
                            text='if_usados',
                            color='if_usados',
                            color_continuous_scale='Blues'
                        )
                        fig_if_usados.update_traces(texttemplate='%{text:.1f}%', textposition='outside')

                    st.plotly_chart(fig_if_usados, use_container_width=True)

                # Análisis por segmento
                st.markdown("#### 📊 Financiamiento 0km por Segmento")

                col_seg1, col_seg2 = st.columns(2)

                with col_seg1:
                    # Por género (solo prendas 0km)
                    if genero_kpi == "Todos":
                        query_if_genero = text(f"""
                            SELECT
                                titular_genero as genero,
                                COUNT(*) as prendas
                            FROM datos_gob_prendas
                            WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                            AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                            AND titular_genero IS NOT NULL
                            AND titular_genero != ''
                            AND fecha_inscripcion_inicial IS NOT NULL
                            AND DATE(tramite_fecha) = DATE(fecha_inscripcion_inicial)
                            {filtro_marca_kpi}
                            {filtro_tipo_persona_kpi}
                            {filtro_provincia_kpi}
                            {filtro_localidad_kpi}
                            {filtro_origen_kpi}
                            {filtro_tipo_vehiculo_kpi}
                            GROUP BY genero
                        """)

                        query_if_genero_insc = text(f"""
                            SELECT
                                titular_genero as genero,
                                COUNT(*) as inscripciones
                            FROM datos_gob_inscripciones
                            WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                            AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                            AND titular_genero IS NOT NULL
                            AND titular_genero != ''
                            {filtro_marca_kpi}
                            {filtro_tipo_persona_kpi}
                            {filtro_provincia_kpi}
                            {filtro_localidad_kpi}
                            {filtro_origen_kpi}
                            {filtro_tipo_vehiculo_kpi}
                            GROUP BY genero
                        """)

                        df_if_gen_p = pd.read_sql(query_if_genero, engine, params=params_kpi)
                        df_if_gen_i = pd.read_sql(query_if_genero_insc, engine, params=params_kpi)

                        if not df_if_gen_p.empty and not df_if_gen_i.empty:
                            df_if_gen = df_if_gen_i.merge(df_if_gen_p, on='genero', how='left').fillna(0)
                            df_if_gen['if_pct'] = (df_if_gen['prendas'] / df_if_gen['inscripciones'] * 100).fillna(0)

                            fig_gen = px.bar(
                                df_if_gen,
                                x='genero',
                                y='if_pct',
                                title='IF por Género',
                                labels={'if_pct': 'IF (%)', 'genero': 'Género'},
                                text='if_pct',
                                color='genero'
                            )
                            fig_gen.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                            st.plotly_chart(fig_gen, use_container_width=True)

                with col_seg2:
                    # Por origen (solo prendas 0km)
                    if origen_kpi == "Ambos":
                        query_if_origen = text(f"""
                            SELECT
                                automotor_origen as origen,
                                COUNT(*) as prendas
                            FROM datos_gob_prendas
                            WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                            AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                            AND automotor_origen IS NOT NULL
                            AND automotor_origen != ''
                            AND fecha_inscripcion_inicial IS NOT NULL
                            AND DATE(tramite_fecha) = DATE(fecha_inscripcion_inicial)
                            {filtro_marca_kpi}
                            {filtro_tipo_persona_kpi}
                            {filtro_provincia_kpi}
                            {filtro_localidad_kpi}
                            {filtro_genero_kpi}
                            {filtro_tipo_vehiculo_kpi}
                            GROUP BY origen
                        """)

                        query_if_origen_insc = text(f"""
                            SELECT
                                automotor_origen as origen,
                                COUNT(*) as inscripciones
                            FROM datos_gob_inscripciones
                            WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                            AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                            AND automotor_origen IS NOT NULL
                            AND automotor_origen != ''
                            {filtro_marca_kpi}
                            {filtro_tipo_persona_kpi}
                            {filtro_provincia_kpi}
                            {filtro_localidad_kpi}
                            {filtro_genero_kpi}
                            {filtro_tipo_vehiculo_kpi}
                            GROUP BY origen
                        """)

                        df_if_ori_p = pd.read_sql(query_if_origen, engine, params=params_kpi)
                        df_if_ori_i = pd.read_sql(query_if_origen_insc, engine, params=params_kpi)

                        if not df_if_ori_p.empty and not df_if_ori_i.empty:
                            df_if_ori = df_if_ori_i.merge(df_if_ori_p, on='origen', how='left').fillna(0)
                            df_if_ori['if_pct'] = (df_if_ori['prendas'] / df_if_ori['inscripciones'] * 100).fillna(0)

                            fig_ori = px.bar(
                                df_if_ori,
                                x='origen',
                                y='if_pct',
                                title='IF por Origen',
                                labels={'if_pct': 'IF (%)', 'origen': 'Origen'},
                                text='if_pct',
                                color='origen'
                            )
                            fig_ori.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                            st.plotly_chart(fig_ori, use_container_width=True)

            else:
                st.warning("⚠️ No se encontraron datos suficientes para calcular el IF")

        except Exception as e:
            st.error(f"❌ Error al calcular KPIs de Financiamiento: {str(e)}")
            st.exception(e)

        st.markdown("---")

        # ========== SECCIÓN 3: PERFIL DEMOGRÁFICO ==========
        st.markdown("## 👥 Distribución Demográfica de Compradores")

        try:
            # KPI: DDC - Distribución Demográfica formalizada
            st.markdown("### 📈 DDC: Perfil del Comprador")
            st.markdown("_Análisis demográfico detallado de compradores de vehículos_")

            query_ddc = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento as edad,
                    titular_genero as genero,
                    titular_tipo_persona as tipo_persona,
                    COUNT(*) as cantidad
                FROM datos_gob_inscripciones
                WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND titular_anio_nacimiento IS NOT NULL
                AND titular_anio_nacimiento > 0
                AND tramite_fecha IS NOT NULL
                {filtro_marca_kpi}
                {filtro_tipo_persona_kpi}
                {filtro_provincia_kpi}
                {filtro_localidad_kpi}
                {filtro_genero_kpi}
                {filtro_origen_kpi}
                {filtro_tipo_vehiculo_kpi}
                GROUP BY anio, edad, genero, tipo_persona
                HAVING EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento BETWEEN 18 AND 100
                ORDER BY anio, edad
            """)

            df_ddc = pd.read_sql(query_ddc, engine, params=params_kpi)

            if not df_ddc.empty:
                # Métricas generales
                total_compradores = df_ddc['cantidad'].sum()
                edad_promedio = (df_ddc['edad'] * df_ddc['cantidad']).sum() / total_compradores
                edad_moda = df_ddc.groupby('edad')['cantidad'].sum().idxmax()
                edad_mediana = df_ddc.loc[df_ddc.index.repeat(df_ddc['cantidad'])]['edad'].median()

                col_ddc1, col_ddc2, col_ddc3, col_ddc4 = st.columns(4)

                with col_ddc1:
                    st.metric("Edad Promedio", f"{edad_promedio:.0f} años")
                with col_ddc2:
                    st.metric("Edad Moda", f"{edad_moda:.0f} años", help="Edad más frecuente")
                with col_ddc3:
                    st.metric("Edad Mediana", f"{edad_mediana:.0f} años")
                with col_ddc4:
                    st.metric("Total Compradores", format_number(total_compradores))

                # Distribución de edades
                df_edad_dist = df_ddc.groupby('edad')['cantidad'].sum().reset_index()

                fig_edad = px.area(
                    df_edad_dist,
                    x='edad',
                    y='cantidad',
                    title='Distribución de Edades de Compradores',
                    labels={'edad': 'Edad (años)', 'cantidad': 'Cantidad de Compradores'},
                    color_discrete_sequence=['#636EFA']
                )
                st.plotly_chart(fig_edad, use_container_width=True)

                # Análisis por género
                col_gen1, col_gen2 = st.columns(2)

                with col_gen1:
                    df_genero = df_ddc.groupby('genero')['cantidad'].sum().reset_index()
                    df_genero = df_genero[df_genero['genero'].isin(['Masculino', 'Femenino'])]

                    if not df_genero.empty:
                        fig_gen_pie = px.pie(
                            df_genero,
                            values='cantidad',
                            names='genero',
                            title='Distribución por Género',
                            color='genero',
                            color_discrete_map={'Masculino': '#636EFA', 'Femenino': '#EF553B'}
                        )
                        st.plotly_chart(fig_gen_pie, use_container_width=True)

                with col_gen2:
                    # Edad promedio por género
                    df_edad_gen = df_ddc[df_ddc['genero'].isin(['Masculino', 'Femenino'])].groupby('genero').apply(
                        lambda x: (x['edad'] * x['cantidad']).sum() / x['cantidad'].sum()
                    ).reset_index(name='edad_promedio')

                    if not df_edad_gen.empty:
                        fig_edad_gen = px.bar(
                            df_edad_gen,
                            x='genero',
                            y='edad_promedio',
                            title='Edad Promedio por Género',
                            labels={'edad_promedio': 'Edad Promedio (años)', 'genero': 'Género'},
                            text='edad_promedio',
                            color='genero',
                            color_discrete_map={'Masculino': '#636EFA', 'Femenino': '#EF553B'}
                        )
                        fig_edad_gen.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                        st.plotly_chart(fig_edad_gen, use_container_width=True)

                # Segmentación por rangos de edad
                st.markdown("#### 📊 Segmentación por Rangos de Edad")

                def categorizar_edad(edad):
                    if edad < 25:
                        return '18-24'
                    elif edad < 35:
                        return '25-34'
                    elif edad < 45:
                        return '35-44'
                    elif edad < 55:
                        return '45-54'
                    elif edad < 65:
                        return '55-64'
                    else:
                        return '65+'

                df_ddc['rango_edad'] = df_ddc['edad'].apply(categorizar_edad)
                df_rangos = df_ddc.groupby('rango_edad')['cantidad'].sum().reset_index()
                df_rangos['porcentaje'] = (df_rangos['cantidad'] / df_rangos['cantidad'].sum() * 100).round(1)

                # Ordenar rangos
                orden_rangos = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
                df_rangos['rango_edad'] = pd.Categorical(df_rangos['rango_edad'], categories=orden_rangos, ordered=True)
                df_rangos = df_rangos.sort_values('rango_edad')

                fig_rangos = px.bar(
                    df_rangos,
                    x='rango_edad',
                    y='cantidad',
                    title='Compradores por Rango de Edad',
                    labels={'rango_edad': 'Rango de Edad', 'cantidad': 'Cantidad'},
                    text='porcentaje',
                    color='cantidad',
                    color_continuous_scale='Viridis'
                )
                fig_rangos.update_traces(texttemplate='%{text}%', textposition='outside')
                st.plotly_chart(fig_rangos, use_container_width=True)

            else:
                st.warning("⚠️ No se encontraron datos demográficos con los filtros seleccionados")

        except Exception as e:
            st.error(f"❌ Error al calcular Distribución Demográfica: {str(e)}")
            st.exception(e)

        st.markdown("---")

        # ========== SECCIÓN 4: PREDICCIÓN ML - PROPENSIÓN DE COMPRA ==========
        st.markdown("## 🔮 Predicción de Propensión de Compra (ML)")
        st.markdown("_Modelo de Machine Learning con Cross-Validation para predecir marcas con mayor probabilidad de compra_")
        st.markdown("_🎯 Accuracy: 71.6% | Top-3: 92.4% | Top-5: 96.7%_")

        try:
            # Verificar si existe el modelo entrenado con CV
            modelo_path = Path("data/models/propension_compra_cv/modelo_propension_compra_cv.pkl")

            if modelo_path.exists():
                # Obtener provincias disponibles para el formulario ML
                try:
                    query_prov_ml = text("""
                        SELECT DISTINCT titular_domicilio_provincia as provincia
                        FROM datos_gob_inscripciones
                        WHERE titular_domicilio_provincia IS NOT NULL
                        AND titular_domicilio_provincia != ''
                        ORDER BY provincia
                    """)
                    df_prov_ml = pd.read_sql(query_prov_ml, engine)
                    provincias_ml_options = df_prov_ml['provincia'].tolist()
                except:
                    provincias_ml_options = []

                col_form, col_result = st.columns([1, 1])

                with col_form:
                    st.markdown("### 📋 Perfil del Comprador")

                    # PROVINCIA Y LOCALIDAD FUERA DEL FORM para que sean reactivos
                    st.markdown("#### 📍 Ubicación")

                    # Provincia (FUERA del form para reactividad)
                    prov_ml = st.selectbox(
                        "Provincia",
                        options=provincias_ml_options,
                        index=0 if provincias_ml_options else None,
                        key="prov_ml_select",
                        help="Selecciona una provincia para ver sus localidades"
                    )

                    # Localidad (filtrada por provincia seleccionada - REACTIVO)
                    localidades_ml = []
                    if prov_ml:
                        try:
                            query_loc_ml = text("""
                                SELECT DISTINCT titular_domicilio_localidad as localidad
                                FROM datos_gob_inscripciones
                                WHERE titular_domicilio_provincia = :provincia
                                AND titular_domicilio_localidad IS NOT NULL
                                AND titular_domicilio_localidad != ''
                                ORDER BY localidad
                            """)
                            df_loc_ml = pd.read_sql(query_loc_ml, engine, params={'provincia': prov_ml})
                            localidades_ml = df_loc_ml['localidad'].tolist()
                        except:
                            localidades_ml = []

                    locs_ml = st.multiselect(
                        "Localidad(es)",
                        options=localidades_ml if localidades_ml else [],
                        default=[],
                        key="loc_ml_select",
                        help="Selecciona localidades específicas o deja vacío para proyección provincial completa."
                    )

                    st.markdown("---")

                    # Resto del formulario para otros campos
                    with st.form("form_prediccion_ml"):
                        st.markdown("#### 👤 Datos del Comprador")

                        # Edad
                        edad_ml = st.number_input(
                            "Edad",
                            min_value=18,
                            max_value=100,
                            value=35,
                            step=1,
                            key="edad_ml"
                        )

                        col_gen, col_tipo = st.columns(2)

                        with col_gen:
                            # Género
                            genero_ml = st.selectbox(
                                "Género",
                                options=["M", "F", "OTRO"],
                                format_func=lambda x: {"M": "Masculino", "F": "Femenino", "OTRO": "Otro"}[x],
                                key="genero_ml"
                            )

                        with col_tipo:
                            # Tipo de Persona
                            tipo_pers_ml = st.selectbox(
                                "Tipo de Persona",
                                options=["FISICA", "JURIDICA"],
                                format_func=lambda x: {"FISICA": "Física", "JURIDICA": "Jurídica"}[x],
                                key="tipo_pers_ml"
                            )

                        st.markdown("#### 🚗 Tipo de Vehículo")

                        col_veh, col_ori = st.columns(2)

                        with col_veh:
                            # Tipo de Vehículo
                            tipo_veh_ml = st.selectbox(
                                "Tipo de Vehículo",
                                options=["AUTOMOVIL", "MOTOVEHICULO", "CAMION", "UTILITARIO"],
                                key="tipo_veh_ml"
                            )

                        with col_ori:
                            # Origen
                            origen_ml = st.selectbox(
                                "Origen",
                                options=["NACIONAL", "IMPORTADO"],
                                key="origen_ml"
                            )

                        # Top N
                        top_n_ml = st.slider(
                            "Top N marcas a mostrar",
                            min_value=3,
                            max_value=10,
                            value=5,
                            step=1,
                            key="top_n_ml"
                        )

                        # Botón de predicción
                        submitted = st.form_submit_button("🔮 Predecir Propensión", use_container_width=True)

                with col_result:
                    st.markdown("### 📊 Resultados de Predicción")

                    # Validar que provincia esté seleccionada
                    if not prov_ml or not localidades_ml:
                        st.info("👈 Selecciona una **provincia** para ver las localidades disponibles")
                    elif submitted:
                        with st.spinner("Calculando propensión de compra..."):
                            try:
                                # Importar función de predicción
                                from backend.ml.predecir_propension import predecir_propension_compra
                                from collections import defaultdict

                                # Determinar localidades a usar
                                es_provincial = len(locs_ml) == 0
                                localidades_prediccion = []

                                if es_provincial:
                                    # Predicción provincial: obtener top 10 localidades por volumen
                                    query_top_locs = text("""
                                        SELECT titular_domicilio_localidad as localidad, COUNT(*) as total
                                        FROM datos_gob_inscripciones
                                        WHERE titular_domicilio_provincia = :provincia
                                        AND titular_domicilio_localidad IS NOT NULL
                                        AND titular_domicilio_localidad != ''
                                        GROUP BY titular_domicilio_localidad
                                        ORDER BY total DESC
                                        LIMIT 10
                                    """)
                                    df_top_locs = pd.read_sql(query_top_locs, engine, params={'provincia': prov_ml})
                                    localidades_prediccion = df_top_locs['localidad'].tolist()
                                    loc_display = f"🌐 Proyección Provincial ({prov_ml})"
                                else:
                                    localidades_prediccion = locs_ml
                                    if len(locs_ml) == 1:
                                        loc_display = locs_ml[0]
                                    else:
                                        loc_display = f"{len(locs_ml)} localidades"

                                # Si hay solo una localidad (y no es provincial)
                                if len(localidades_prediccion) == 1 and not es_provincial:
                                    # Una sola localidad
                                    resultados = predecir_propension_compra(
                                        provincia=prov_ml,
                                        localidad=localidades_prediccion[0],
                                        edad=edad_ml,
                                        genero=genero_ml,
                                        tipo_persona=tipo_pers_ml,
                                        tipo_vehiculo=tipo_veh_ml,
                                        origen=origen_ml,
                                        top_n=top_n_ml * 2,  # Pedir más para tener suficientes
                                        modelo_dir="data/models/propension_compra_cv"
                                    )
                                else:
                                    # Múltiples localidades o provincial: promediar probabilidades
                                    prob_acumuladas = defaultdict(float)
                                    n_localidades = len(localidades_prediccion)

                                    for loc in localidades_prediccion:
                                        try:
                                            res_loc = predecir_propension_compra(
                                                provincia=prov_ml,
                                                localidad=loc,
                                                edad=edad_ml,
                                                genero=genero_ml,
                                                tipo_persona=tipo_pers_ml,
                                                tipo_vehiculo=tipo_veh_ml,
                                                origen=origen_ml,
                                                top_n=100,  # Todas las marcas para promediar
                                                modelo_dir="data/models/propension_compra_cv"
                                            )
                                            for marca, prob in res_loc:
                                                prob_acumuladas[marca] += prob
                                        except:
                                            n_localidades -= 1

                                    # Promediar
                                    if n_localidades > 0:
                                        resultados = [(marca, prob / n_localidades) for marca, prob in prob_acumuladas.items()]
                                        resultados = sorted(resultados, key=lambda x: x[1], reverse=True)[:top_n_ml]
                                    else:
                                        resultados = []

                                # Mostrar resultados
                                if resultados:
                                    # Tomar solo top_n resultados
                                    resultados = resultados[:top_n_ml]

                                    st.success(f"✅ Predicción completada para {prov_ml} - {loc_display}")

                                    # Mostrar localidades usadas en la predicción
                                    if es_provincial:
                                        with st.expander(f"📍 Top {len(localidades_prediccion)} localidades de {prov_ml} (por volumen de inscripciones)"):
                                            st.write(", ".join(localidades_prediccion))
                                    elif len(locs_ml) > 1:
                                        with st.expander(f"📍 Localidades incluidas ({len(locs_ml)})"):
                                            st.write(", ".join(locs_ml))

                                    # Crear DataFrame para visualización
                                    df_pred = pd.DataFrame(
                                        [(marca, prob * 100) for marca, prob in resultados],
                                        columns=['Marca', 'Probabilidad']
                                    )

                                    # Gráfico de barras horizontales
                                    fig_pred = px.bar(
                                        df_pred,
                                        x='Probabilidad',
                                        y='Marca',
                                        orientation='h',
                                        title=f'Top {top_n_ml} Marcas con Mayor Propensión',
                                        labels={'Probabilidad': 'Probabilidad (%)', 'Marca': 'Marca'},
                                        text='Probabilidad',
                                        color='Probabilidad',
                                        color_continuous_scale='Viridis'
                                    )
                                    fig_pred.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                                    fig_pred.update_layout(
                                        yaxis={'categoryorder': 'total ascending'},
                                        showlegend=False,
                                        height=400
                                    )
                                    st.plotly_chart(fig_pred, use_container_width=True)

                                    # Tabla con detalles
                                    st.markdown("#### 📋 Detalle de Probabilidades")
                                    df_pred['Ranking'] = range(1, len(df_pred) + 1)
                                    df_pred = df_pred[['Ranking', 'Marca', 'Probabilidad']]
                                    df_pred['Probabilidad'] = df_pred['Probabilidad'].apply(lambda x: f"{x:.2f}%")
                                    st.dataframe(df_pred, use_container_width=True, hide_index=True)

                                    # Métricas
                                    st.markdown("#### 📈 Métricas del Perfil")
                                    met1, met2, met3 = st.columns(3)

                                    with met1:
                                        st.metric(
                                            "1ª Marca",
                                            resultados[0][0],
                                            f"{resultados[0][1]*100:.1f}%"
                                        )

                                    with met2:
                                        if len(resultados) > 1:
                                            st.metric(
                                                "2ª Marca",
                                                resultados[1][0],
                                                f"{resultados[1][1]*100:.1f}%"
                                            )

                                    with met3:
                                        if len(resultados) > 2:
                                            st.metric(
                                                "3ª Marca",
                                                resultados[2][0],
                                                f"{resultados[2][1]*100:.1f}%"
                                            )

                                else:
                                    st.warning("⚠️ No se pudieron obtener predicciones")

                            except ImportError:
                                st.error("❌ Módulo de predicción no disponible. Verifica la instalación.")
                            except FileNotFoundError as e:
                                st.error(f"❌ Modelo no encontrado: {str(e)}")
                            except Exception as e:
                                st.error(f"❌ Error al realizar predicción: {str(e)}")
                                st.exception(e)

                    elif submitted:
                        st.warning("⚠️ Por favor selecciona una Provincia y Localidad específicas")
                    else:
                        st.info("👆 Completa el formulario y presiona 'Predecir Propensión' para ver resultados")

            else:
                st.info("ℹ️ El modelo de ML aún no ha sido entrenado. Ejecuta los scripts de preparación y entrenamiento:")
                st.code("""
# 1. Preparar datos (versión LITE - rápida)
python backend/ml/preparar_datos_propension_lite.py --output data/ml/

# 2. Entrenar modelo con Cross-Validation
python backend/ml/entrenar_modelo_propension_cv.py --input data/ml/

# Modelo guardado en: data/models/propension_compra_cv/
                """, language="bash")

                st.markdown("**Resultados esperados:**")
                st.markdown("- ✅ Accuracy: ~71.6%")
                st.markdown("- ✅ Top-3 Accuracy: ~92.4% (la marca correcta en las 3 recomendaciones)")
                st.markdown("- ✅ Top-5 Accuracy: ~96.7% (la marca correcta en las 5 recomendaciones)")

        except Exception as e:
            st.error(f"❌ Error al cargar módulo de predicción ML: {str(e)}")
            st.exception(e)

# Footer
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.markdown("**🔗 Fuente de Datos**")
    st.markdown("[datos.gob.ar](https://datos.gob.ar)")

with col_footer2:
    st.markdown("**📊 Dataset**")
    st.markdown("Estadística de Trámites de Automotores")

with col_footer3:
    st.markdown("**🏛️ Organismo**")
    st.markdown("DNRPA - Ministerio de Justicia")

st.markdown("---")
st.markdown("**Mercado Automotor Dashboard** | Análisis de datos.gob.ar | Desarrollado con Streamlit")
