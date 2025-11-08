"""
Dashboard principal - Streamlit App
Sistema de Inteligencia Comercial del Mercado Automotor
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta, datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.settings import settings
from backend.models import Patentamiento, Produccion, BCRAIndicador, MercadoLibreListing

# Page config
st.set_page_config(
    page_title="Mercado Automotor - Dashboard",
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
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_database_session():
    """Create database session."""
    engine = create_engine(settings.get_database_url_sync())
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

db = get_database_session()

# Sidebar
st.sidebar.markdown("## 🚗 Mercado Automotor")
st.sidebar.markdown("### Sistema de Inteligencia Comercial")
st.sidebar.markdown("---")

# Date range selector
st.sidebar.markdown("### 📅 Período de Análisis")

fecha_desde = st.sidebar.date_input(
    "Desde",
    value=date(2024, 5, 1),
    max_value=date(2024, 11, 5)
)

fecha_hasta = st.sidebar.date_input(
    "Hasta",
    value=date(2024, 11, 5),
    max_value=date(2024, 11, 5)
)

# Main header
st.markdown('<p class="main-header">📊 Dashboard - Mercado Automotor Argentino</p>', unsafe_allow_html=True)
st.markdown(f"**Período de análisis:** {fecha_desde.strftime('%d/%m/%Y')} a {fecha_hasta.strftime('%d/%m/%Y')}")
st.markdown("---")

# Create tabs for each data source
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 INDEC",
    "💰 BCRA",
    "🛒 MercadoLibre",
    "🚗 ACARA",
    "🏭 ADEFA",
    "🚙 DNRPA Patentamientos"
])

# ==================== TAB 1: INDEC ====================
with tab1:
    st.header("📊 Datos INDEC - Instituto Nacional de Estadística y Censos")

    # Load INDEC data
    query = text("""
        SELECT fecha, indicador, valor, unidad, fuente
        FROM bcra_indicadores
        WHERE fuente = 'INDEC'
        AND fecha >= :fecha_desde
        AND fecha <= :fecha_hasta
        ORDER BY fecha DESC, indicador
    """)

    try:
        df_indec = pd.read_sql(query, db.bind, params={
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        })

        if not df_indec.empty:
            st.success(f"✅ {len(df_indec)} registros encontrados")

            # Get unique indicators
            indicadores = df_indec['indicador'].unique()

            # Metrics row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Indicadores disponibles", len(indicadores))
            with col2:
                st.metric("Período", f"{df_indec['fecha'].min()} a {df_indec['fecha'].max()}")
            with col3:
                st.metric("Registros totales", len(df_indec))

            st.markdown("---")

            # Selector de indicador
            indicador_seleccionado = st.selectbox(
                "Seleccionar indicador para visualizar:",
                options=indicadores,
                key="indec_indicator"
            )

            # Filter data for selected indicator
            df_filtered = df_indec[df_indec['indicador'] == indicador_seleccionado].copy()
            df_filtered = df_filtered.sort_values('fecha')

            # Display chart
            col_chart, col_table = st.columns([2, 1])

            with col_chart:
                st.subheader(f"Evolución: {indicador_seleccionado}")
                fig = px.line(
                    df_filtered,
                    x='fecha',
                    y='valor',
                    title=f'{indicador_seleccionado} - Evolución temporal',
                    labels={'fecha': 'Fecha', 'valor': 'Valor'},
                    markers=True
                )
                fig.update_layout(hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)

            with col_table:
                st.subheader("Estadísticas")
                st.metric("Valor actual", f"{df_filtered['valor'].iloc[-1]:,.2f}")
                st.metric("Valor mínimo", f"{df_filtered['valor'].min():,.2f}")
                st.metric("Valor máximo", f"{df_filtered['valor'].max():,.2f}")
                st.metric("Promedio", f"{df_filtered['valor'].mean():,.2f}")

            st.markdown("---")

            # Full data table
            st.subheader("📋 Tabla completa de datos")

            # Format the dataframe for display
            df_display = df_indec.copy()
            df_display['fecha'] = pd.to_datetime(df_display['fecha']).dt.strftime('%d/%m/%Y')
            df_display['valor'] = df_display['valor'].apply(lambda x: f"{x:,.2f}")

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )

            # Download button
            csv = df_indec.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos (CSV)",
                data=csv,
                file_name=f"indec_data_{fecha_desde}_{fecha_hasta}.csv",
                mime="text/csv"
            )

        else:
            st.warning("⚠️ No hay datos de INDEC para el período seleccionado")
            st.info("💡 Ejecuta el script de carga de datos: `python cargar_datos.py`")

    except Exception as e:
        st.error(f"❌ Error cargando datos de INDEC: {str(e)}")

# ==================== TAB 2: BCRA ====================
with tab2:
    st.header("💰 Datos BCRA - Banco Central de la República Argentina")

    # Load BCRA data
    query = text("""
        SELECT fecha, indicador, valor, unidad, fuente
        FROM bcra_indicadores
        WHERE fuente = 'BCRA'
        AND fecha >= :fecha_desde
        AND fecha <= :fecha_hasta
        ORDER BY fecha DESC, indicador
    """)

    try:
        df_bcra = pd.read_sql(query, db.bind, params={
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        })

        if not df_bcra.empty:
            st.success(f"✅ {len(df_bcra)} registros encontrados")

            indicadores = df_bcra['indicador'].unique()

            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Indicadores disponibles", len(indicadores))
            with col2:
                st.metric("Período", f"{df_bcra['fecha'].min()} a {df_bcra['fecha'].max()}")
            with col3:
                st.metric("Registros totales", len(df_bcra))

            st.markdown("---")

            # Selector
            indicador_seleccionado = st.selectbox(
                "Seleccionar indicador BCRA:",
                options=indicadores,
                key="bcra_indicator"
            )

            df_filtered = df_bcra[df_bcra['indicador'] == indicador_seleccionado].copy()
            df_filtered = df_filtered.sort_values('fecha')

            # Chart
            col_chart, col_stats = st.columns([2, 1])

            with col_chart:
                fig = px.line(
                    df_filtered,
                    x='fecha',
                    y='valor',
                    title=f'{indicador_seleccionado}',
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_stats:
                st.subheader("Estadísticas")
                st.metric("Actual", f"{df_filtered['valor'].iloc[-1]:,.2f}")
                st.metric("Mín", f"{df_filtered['valor'].min():,.2f}")
                st.metric("Máx", f"{df_filtered['valor'].max():,.2f}")
                st.metric("Prom", f"{df_filtered['valor'].mean():,.2f}")

            st.markdown("---")
            st.subheader("📋 Datos BCRA")

            df_display = df_bcra.copy()
            df_display['fecha'] = pd.to_datetime(df_display['fecha']).dt.strftime('%d/%m/%Y')
            df_display['valor'] = df_display['valor'].apply(lambda x: f"{x:,.2f}")

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            csv = df_bcra.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV",
                csv,
                f"bcra_data_{fecha_desde}_{fecha_hasta}.csv",
                "text/csv"
            )
        else:
            st.warning("⚠️ No hay datos de BCRA disponibles")
            st.info("💡 La API del BCRA está presentando errores temporales. Los datos se cargarán cuando esté disponible.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ==================== TAB 3: MercadoLibre ====================
with tab3:
    st.header("🛒 Datos MercadoLibre")

    query = text("""
        SELECT *
        FROM mercadolibre_listings
        WHERE fecha_snapshot >= :fecha_desde
        AND fecha_snapshot <= :fecha_hasta
        ORDER BY fecha_snapshot DESC
        LIMIT 1000
    """)

    try:
        df_ml = pd.read_sql(query, db.bind, params={
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        })

        if not df_ml.empty:
            st.success(f"✅ {len(df_ml)} publicaciones encontradas")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Publicaciones", len(df_ml))
            with col2:
                avg_price = df_ml['precio'].mean() if 'precio' in df_ml.columns else 0
                st.metric("Precio promedio", f"${avg_price:,.0f}")
            with col3:
                if 'marca' in df_ml.columns:
                    st.metric("Marcas únicas", df_ml['marca'].nunique())
            with col4:
                if 'modelo' in df_ml.columns:
                    st.metric("Modelos únicos", df_ml['modelo'].nunique())

            st.markdown("---")
            st.subheader("📋 Publicaciones de MercadoLibre")
            st.dataframe(df_ml, use_container_width=True, hide_index=True)

            csv = df_ml.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV",
                csv,
                f"mercadolibre_{fecha_desde}_{fecha_hasta}.csv",
                "text/csv"
            )
        else:
            st.warning("⚠️ No hay datos de MercadoLibre")
            st.info("💡 Configura las credenciales de MercadoLibre API en el archivo `.env` y ejecuta el scraper.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ==================== TAB 4: ACARA ====================
with tab4:
    st.header("🚗 Datos ACARA - Asociación de Concesionarios")

    query = text("""
        SELECT *
        FROM patentamientos
        WHERE fuente = 'ACARA'
        AND fecha >= :fecha_desde
        AND fecha <= :fecha_hasta
        ORDER BY fecha DESC
    """)

    try:
        df_acara = pd.read_sql(query, db.bind, params={
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        })

        if not df_acara.empty:
            st.success(f"✅ {len(df_acara)} registros")
            st.dataframe(df_acara, use_container_width=True)
        else:
            st.warning("⚠️ No hay datos de ACARA")
            st.info("💡 Los datos de ACARA se obtienen mediante scraping. Ejecuta el scraper correspondiente.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ==================== TAB 5: ADEFA ====================
with tab5:
    st.header("🏭 Datos ADEFA - Asociación de Fábricas de Automotores")

    query = text("""
        SELECT *
        FROM produccion
        WHERE fuente = 'ADEFA'
        AND fecha >= :fecha_desde
        AND fecha <= :fecha_hasta
        ORDER BY fecha DESC
    """)

    try:
        df_adefa = pd.read_sql(query, db.bind, params={
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        })

        if not df_adefa.empty:
            st.success(f"✅ {len(df_adefa)} registros")
            st.dataframe(df_adefa, use_container_width=True)
        else:
            st.warning("⚠️ No hay datos de ADEFA")
            st.info("💡 Los datos de ADEFA se obtienen mediante scraping. Ejecuta el scraper correspondiente.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ==================== TAB 6: DNRPA PATENTAMIENTOS ====================
with tab6:
    st.header("🚙 Datos DNRPA - Patentamientos Provinciales")

    # Cargar datos desde PostgreSQL
    query = text("""
        SELECT
            provincia,
            anio,
            mes,
            cantidad,
            tipo_vehiculo
        FROM patentamientos_provincial
        ORDER BY anio DESC, provincia,
            CASE mes
                WHEN 'Ene' THEN 1
                WHEN 'Feb' THEN 2
                WHEN 'Mar' THEN 3
                WHEN 'Abr' THEN 4
                WHEN 'May' THEN 5
                WHEN 'Jun' THEN 6
                WHEN 'Jul' THEN 7
                WHEN 'Ago' THEN 8
                WHEN 'Sep' THEN 9
                WHEN 'Oct' THEN 10
                WHEN 'Nov' THEN 11
                WHEN 'Dic' THEN 12
            END
    """)

    try:
        df_dnrpa_long = pd.read_sql(query, db.bind)

        if not df_dnrpa_long.empty:
            # Transformar de formato largo a ancho (pivot)
            df_dnrpa = df_dnrpa_long.pivot_table(
                index=['provincia', 'anio', 'tipo_vehiculo'],
                columns='mes',
                values='cantidad',
                aggfunc='sum',
                fill_value=0
            ).reset_index()

            # Reordenar columnas de meses
            meses_orden = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            meses_disponibles = [m for m in meses_orden if m in df_dnrpa.columns]

            # Calcular Total
            df_dnrpa['Total'] = df_dnrpa[meses_disponibles].sum(axis=1)

            # Renombrar provincia para compatibilidad
            df_dnrpa = df_dnrpa.rename(columns={'provincia': 'Provincia / Mes'})

            st.success(f"✅ {len(df_dnrpa)} registros cargados desde PostgreSQL")

            # Mostrar información del DataFrame
            st.subheader("📋 Vista previa de datos")
            st.dataframe(df_dnrpa.head(10), use_container_width=True)

            # Métricas básicas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Registros totales", len(df_dnrpa))
            with col2:
                if 'anio' in df_dnrpa.columns:
                    st.metric("Años", f"{df_dnrpa['anio'].min()} - {df_dnrpa['anio'].max()}")
            with col3:
                if 'Provincia / Mes' in df_dnrpa.columns:
                    st.metric("Provincias", df_dnrpa['Provincia / Mes'].nunique())
            with col4:
                if 'Total' in df_dnrpa.columns:
                    total_patentamientos = df_dnrpa['Total'].sum()
                    st.metric("Total patentamientos", f"{total_patentamientos:,.0f}")

            st.markdown("---")

            # Análisis por año
            if 'anio' in df_dnrpa.columns and 'Total' in df_dnrpa.columns:
                st.subheader("📊 Patentamientos por Año")

                # Agrupar por año
                df_por_anio = df_dnrpa.groupby('anio')['Total'].sum().reset_index()
                df_por_anio = df_por_anio.sort_values('anio')

                col_chart, col_stats = st.columns([2, 1])

                with col_chart:
                    fig_anio = px.bar(
                        df_por_anio,
                        x='anio',
                        y='Total',
                        title='Evolución de patentamientos por año',
                        labels={'anio': 'Año', 'Total': 'Patentamientos'},
                        text='Total'
                    )
                    fig_anio.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    st.plotly_chart(fig_anio, use_container_width=True)

                with col_stats:
                    st.markdown("#### Estadísticas")
                    st.metric("Año con más patentamientos",
                             f"{df_por_anio.loc[df_por_anio['Total'].idxmax(), 'anio']:.0f}")
                    st.metric("Máximo", f"{df_por_anio['Total'].max():,.0f}")
                    st.metric("Promedio anual", f"{df_por_anio['Total'].mean():,.0f}")

                    # Variación interanual
                    if len(df_por_anio) > 1:
                        var_ultimos = ((df_por_anio['Total'].iloc[-1] / df_por_anio['Total'].iloc[-2] - 1) * 100)
                        st.metric("Variación último año", f"{var_ultimos:+.1f}%")

            st.markdown("---")

            # Top provincias
            if 'Provincia / Mes' in df_dnrpa.columns and 'Total' in df_dnrpa.columns:
                st.subheader("🏆 Top 10 Provincias")

                # Filtro de año
                if 'anio' in df_dnrpa.columns:
                    anios_disponibles = sorted(df_dnrpa['anio'].unique(), reverse=True)
                    anio_seleccionado = st.selectbox(
                        "Seleccionar año:",
                        options=anios_disponibles,
                        key="dnrpa_year"
                    )

                    df_filtrado = df_dnrpa[df_dnrpa['anio'] == anio_seleccionado].copy()
                else:
                    df_filtrado = df_dnrpa.copy()

                # Top 10
                df_top10 = df_filtrado.nlargest(10, 'Total')[['Provincia / Mes', 'Total']].copy()

                col_top, col_pie = st.columns([1, 1])

                with col_top:
                    fig_top = px.bar(
                        df_top10,
                        x='Total',
                        y='Provincia / Mes',
                        orientation='h',
                        title=f'Top 10 Provincias - {anio_seleccionado if "anio" in df_dnrpa.columns else "Todos los años"}',
                        labels={'Provincia / Mes': 'Provincia', 'Total': 'Patentamientos'},
                        text='Total'
                    )
                    fig_top.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_top, use_container_width=True)

                with col_pie:
                    fig_pie = px.pie(
                        df_top10,
                        values='Total',
                        names='Provincia / Mes',
                        title='Distribución Top 10'
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("---")

            # Evolución mensual
            meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            meses_disponibles = [m for m in meses if m in df_dnrpa.columns]

            if meses_disponibles and 'Provincia / Mes' in df_dnrpa.columns:
                st.subheader("📈 Evolución Mensual por Provincia")

                # Selector de provincias
                provincias_disponibles = df_dnrpa['Provincia / Mes'].unique()
                provincias_seleccionadas = st.multiselect(
                    "Seleccionar provincias para comparar:",
                    options=provincias_disponibles,
                    default=provincias_disponibles[:3] if len(provincias_disponibles) >= 3 else provincias_disponibles,
                    key="dnrpa_provinces"
                )

                if provincias_seleccionadas:
                    # Filtrar por año si está disponible
                    if 'anio' in df_dnrpa.columns:
                        df_mensual = df_dnrpa[
                            (df_dnrpa['Provincia / Mes'].isin(provincias_seleccionadas)) &
                            (df_dnrpa['anio'] == anio_seleccionado)
                        ].copy()
                    else:
                        df_mensual = df_dnrpa[df_dnrpa['Provincia / Mes'].isin(provincias_seleccionadas)].copy()

                    # Transformar a formato largo
                    df_mensual_long = df_mensual.melt(
                        id_vars=['Provincia / Mes'],
                        value_vars=meses_disponibles,
                        var_name='Mes',
                        value_name='Patentamientos'
                    )

                    fig_mensual = px.line(
                        df_mensual_long,
                        x='Mes',
                        y='Patentamientos',
                        color='Provincia / Mes',
                        title=f'Evolución mensual - {anio_seleccionado if "anio" in df_dnrpa.columns else ""}',
                        markers=True,
                        labels={'Mes': 'Mes', 'Patentamientos': 'Cantidad', 'Provincia / Mes': 'Provincia'}
                    )
                    fig_mensual.update_layout(hovermode='x unified')
                    st.plotly_chart(fig_mensual, use_container_width=True)

            st.markdown("---")

            # Tabla completa con filtros
            st.subheader("📋 Datos Completos")

            # Opciones de filtro
            col_f1, col_f2 = st.columns(2)

            with col_f1:
                if 'anio' in df_dnrpa.columns:
                    anios_filtro = st.multiselect(
                        "Filtrar por año:",
                        options=sorted(df_dnrpa['anio'].unique()),
                        default=sorted(df_dnrpa['anio'].unique()),
                        key="dnrpa_filter_years"
                    )
                else:
                    anios_filtro = None

            with col_f2:
                if 'Provincia / Mes' in df_dnrpa.columns:
                    provincias_filtro = st.multiselect(
                        "Filtrar por provincia:",
                        options=sorted(df_dnrpa['Provincia / Mes'].unique()),
                        default=sorted(df_dnrpa['Provincia / Mes'].unique())[:10],
                        key="dnrpa_filter_provinces"
                    )
                else:
                    provincias_filtro = None

            # Aplicar filtros
            df_tabla = df_dnrpa.copy()
            if anios_filtro and 'anio' in df_dnrpa.columns:
                df_tabla = df_tabla[df_tabla['anio'].isin(anios_filtro)]
            if provincias_filtro and 'Provincia / Mes' in df_dnrpa.columns:
                df_tabla = df_tabla[df_tabla['Provincia / Mes'].isin(provincias_filtro)]

            st.dataframe(df_tabla, use_container_width=True, hide_index=True)

            # Botón de descarga
            csv = df_tabla.to_csv(index=False)
            st.download_button(
                "📥 Descargar datos filtrados (CSV)",
                csv,
                f"dnrpa_patentamientos_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )

        else:
            st.warning("⚠️ No hay datos de DNRPA en la base de datos")
            st.info("💡 Para cargar datos de patentamientos:\n\n"
                   "1. Ejecuta el scraping: `python scraping_provincial_historico.py --anio-inicio 2020 --anio-fin 2025`\n"
                   "2. Carga a PostgreSQL: `python cargar_patentamientos_postgresql.py`")

    except Exception as e:
        st.error(f"❌ Error cargando datos DNRPA: {str(e)}")
        st.exception(e)

# Footer
st.markdown("---")
st.markdown("**Mercado Automotor Dashboard** | Desarrollado con Streamlit")
