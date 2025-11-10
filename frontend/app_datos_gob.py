"""
Dashboard de Datos datos.gob.ar - Streamlit App
Sistema de Análisis de Trámites Automotores (DNRPA)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
tab1, tab2, tab3, tab4 = st.tabs([
    "🚗 Inscripciones",
    "🔄 Transferencias",
    "💰 Prendas",
    "📍 Registros Seccionales"
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
        SELECT DISTINCT registro_seccional_provincia as provincia
        FROM {tabla_nombre}
        WHERE registro_seccional_provincia IS NOT NULL
        AND registro_seccional_provincia != ''
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

    if not anios_seleccionados or not meses_seleccionados or not provincias_seleccionadas:
        st.warning("⚠️ Selecciona al menos un año, un mes y una provincia")
        return

    # Convertir meses a números
    meses_numeros = [list(MESES_ES.keys())[list(MESES_ES.values()).index(mes)] for mes in meses_seleccionados]

    st.markdown("---")

    # 3. Consulta principal
    query = text(f"""
        SELECT
            EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
            EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
            registro_seccional_provincia as provincia,
            automotor_marca_descripcion as marca,
            automotor_tipo_descripcion as tipo_vehiculo,
            COUNT(*) as cantidad
        FROM {tabla_nombre}
        WHERE EXTRACT(YEAR FROM tramite_fecha) = ANY(:anios)
        AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
        AND registro_seccional_provincia = ANY(:provincias)
        AND tramite_fecha IS NOT NULL
        GROUP BY anio, mes, provincia, marca, tipo_vehiculo
        ORDER BY anio, mes, provincia
    """)

    try:
        df = pd.read_sql(query, engine, params={
            'anios': anios_seleccionados,
            'meses': meses_numeros,
            'provincias': provincias_seleccionadas
        })

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

        df_marcas = df.groupby('marca')['cantidad'].sum().reset_index()
        df_marcas = df_marcas.sort_values('cantidad', ascending=False).head(10)

        fig_marcas = px.bar(
            df_marcas,
            x='marca',
            y='cantidad',
            title='Top 10 Marcas más Tramitadas',
            labels={'marca': 'Marca', 'cantidad': 'Cantidad'},
            text='cantidad',
            color='cantidad',
            color_continuous_scale='Oranges'
        )
        fig_marcas.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_marcas.update_layout(showlegend=False)
        st.plotly_chart(fig_marcas, use_container_width=True)

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
    analizar_tramites('datos_gob_prendas', 'Prendas sobre Vehículos', '💰')

# ==================== TAB 4: REGISTROS SECCIONALES ====================
with tab4:
    st.header("📍 Catálogo de Registros Seccionales")

    query_seccionales = text("""
        SELECT
            codigo,
            denominacion,
            provincia_nombre,
            localidad,
            domicilio,
            telefono,
            horario_atencion,
            encargado
        FROM datos_gob_registros_seccionales
        ORDER BY provincia_nombre, denominacion
    """)

    try:
        df_seccionales = pd.read_sql(query_seccionales, engine)

        if not df_seccionales.empty:
            st.success(f"✅ {len(df_seccionales)} registros seccionales encontrados")

            # Filtros
            col_f1, col_f2 = st.columns(2)

            with col_f1:
                provincias_seccionales = sorted(df_seccionales['provincia_nombre'].unique())
                provincia_filtro = st.multiselect(
                    "Filtrar por provincia:",
                    options=provincias_seccionales,
                    default=provincias_seccionales[:5] if len(provincias_seccionales) >= 5 else provincias_seccionales,
                    key="seccionales_provincia"
                )

            with col_f2:
                buscar_texto = st.text_input("🔍 Buscar por denominación o localidad:", "")

            # Aplicar filtros
            df_filtrado = df_seccionales.copy()

            if provincia_filtro:
                df_filtrado = df_filtrado[df_filtrado['provincia_nombre'].isin(provincia_filtro)]

            if buscar_texto:
                mask = (
                    df_filtrado['denominacion'].str.contains(buscar_texto, case=False, na=False) |
                    df_filtrado['localidad'].str.contains(buscar_texto, case=False, na=False)
                )
                df_filtrado = df_filtrado[mask]

            st.markdown("---")

            # Métricas
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Registros Seccionales", len(df_filtrado))

            with col2:
                st.metric("Provincias", df_filtrado['provincia_nombre'].nunique())

            with col3:
                st.metric("Localidades", df_filtrado['localidad'].nunique())

            st.markdown("---")

            # Distribución por provincia
            st.markdown("### 🗺️ Distribución por Provincia")

            df_prov_count = df_filtrado['provincia_nombre'].value_counts().reset_index()
            df_prov_count.columns = ['provincia', 'cantidad']

            col_dist1, col_dist2 = st.columns([2, 1])

            with col_dist1:
                fig_dist = px.bar(
                    df_prov_count,
                    x='cantidad',
                    y='provincia',
                    orientation='h',
                    title='Registros Seccionales por Provincia',
                    labels={'provincia': 'Provincia', 'cantidad': 'Cantidad'},
                    text='cantidad',
                    color='cantidad',
                    color_continuous_scale='Teal'
                )
                fig_dist.update_traces(textposition='outside')
                fig_dist.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                st.plotly_chart(fig_dist, use_container_width=True)

            with col_dist2:
                fig_pie_sec = px.pie(
                    df_prov_count.head(10),
                    values='cantidad',
                    names='provincia',
                    title='Top 10 Provincias'
                )
                st.plotly_chart(fig_pie_sec, use_container_width=True)

            st.markdown("---")

            # Tabla de registros
            st.markdown("### 📋 Listado de Registros Seccionales")

            # Formatear columnas para mostrar
            df_display = df_filtrado.copy()
            df_display.columns = ['Código', 'Denominación', 'Provincia', 'Localidad',
                                 'Domicilio', 'Teléfono', 'Horario', 'Encargado']

            st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)

            # Botón de descarga
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar registros (CSV)",
                data=csv,
                file_name=f"registros_seccionales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ No hay datos de registros seccionales")
            st.info("💡 Para cargar el catálogo de registros seccionales, ejecuta el script de carga correspondiente.")

    except Exception as e:
        st.error(f"❌ Error al cargar registros seccionales: {str(e)}")
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
