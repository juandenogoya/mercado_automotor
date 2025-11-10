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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚗 Inscripciones",
    "🔄 Transferencias",
    "💰 Prendas",
    "📍 Registros Seccionales",
    "🔬 Análisis Detallado"
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

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

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
                "🌍 Origen del Vehículo",
                options=["Ambos", "Nacional", "Importado"],
                index=0,
                key="detalle_origen"
            )

        with col_f4:
            tipo_persona_seleccionado = st.selectbox(
                "👤 Tipo de Persona",
                options=["Ambos", "Persona Física", "Persona Jurídica"],
                index=0,
                key="detalle_tipo_persona"
            )

        if not meses_seleccionados_detalle:
            st.warning("⚠️ Selecciona al menos un mes")
        else:
            # Convertir meses a números
            meses_numeros_detalle = [list(MESES_ES.keys())[list(MESES_ES.values()).index(mes)] for mes in meses_seleccionados_detalle]

            st.markdown("---")

            # 3. CONSULTA PRINCIPAL - INSCRIPCIONES CON EDAD
            # Construir filtros WHERE dinámicos
            filtro_origen = ""
            if origen_seleccionado != "Ambos":
                filtro_origen = f"AND UPPER(automotor_origen) = '{origen_seleccionado.upper()}'"

            filtro_tipo_persona = ""
            if tipo_persona_seleccionado == "Persona Física":
                filtro_tipo_persona = "AND UPPER(titular_tipo_persona) = 'FISICA'"
            elif tipo_persona_seleccionado == "Persona Jurídica":
                filtro_tipo_persona = "AND UPPER(titular_tipo_persona) = 'JURIDICA'"

            query_inscripciones_edad = text(f"""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento as edad,
                    automotor_marca_descripcion as marca,
                    automotor_tipo_descripcion as tipo_vehiculo,
                    automotor_origen as origen,
                    titular_tipo_persona as tipo_persona,
                    COUNT(*) as cantidad
                FROM datos_gob_inscripciones
                WHERE EXTRACT(YEAR FROM tramite_fecha) = :anio
                AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                AND tramite_fecha IS NOT NULL
                AND titular_anio_nacimiento IS NOT NULL
                AND titular_anio_nacimiento > 0
                {filtro_origen}
                {filtro_tipo_persona}
                GROUP BY edad, marca, tipo_vehiculo, origen, tipo_persona
                HAVING EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento BETWEEN 18 AND 100
                ORDER BY edad
            """)

            try:
                df_inscripciones = pd.read_sql(query_inscripciones_edad, engine, params={
                    'anio': anio_seleccionado,
                    'meses': meses_numeros_detalle
                })

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
                            COUNT(*) as cantidad_prendas
                        FROM datos_gob_prendas
                        WHERE EXTRACT(YEAR FROM tramite_fecha) = :anio
                        AND EXTRACT(MONTH FROM tramite_fecha) = ANY(:meses)
                        AND tramite_fecha IS NOT NULL
                        AND titular_anio_nacimiento IS NOT NULL
                        AND titular_anio_nacimiento > 0
                        {filtro_origen}
                        {filtro_tipo_persona}
                        GROUP BY edad, marca, tipo_vehiculo, origen, tipo_persona
                        HAVING EXTRACT(YEAR FROM tramite_fecha)::INTEGER - titular_anio_nacimiento BETWEEN 18 AND 100
                        ORDER BY edad
                    """)

                    df_prendas = pd.read_sql(query_prendas_edad, engine, params={
                        'anio': anio_seleccionado,
                        'meses': meses_numeros_detalle
                    })

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

                    # 10. INSIGHTS Y CONCLUSIONES
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
                            df_rangos = df_edad_rangos.groupby('rango_edad')['cantidad'].sum().reset_index()
                            df_rangos = df_rangos.sort_values('cantidad', ascending=False)

                            st.write(f"• **Rango etario más activo:** {df_rangos.iloc[0]['rango_edad']} años")
                            st.write(f"• **Total inscripciones en ese rango:** {format_number(df_rangos.iloc[0]['cantidad'])}")

                            if origen_seleccionado == "Ambos":
                                origen_preferido = df_inscripciones.groupby('origen')['cantidad'].sum().idxmax()
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
