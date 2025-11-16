"""
Dashboard principal - Streamlit App
Sistema de Inteligencia Comercial del Mercado Automotor
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.settings import settings
from backend.models import Patentamiento, Produccion, BCRAIndicador, IndicadorCalculado

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


# Helper functions
@st.cache_data(ttl=3600)
def load_patentamientos(fecha_desde, fecha_hasta):
    """Load patentamientos data."""
    query = db.query(Patentamiento).filter(
        Patentamiento.fecha >= fecha_desde,
        Patentamiento.fecha <= fecha_hasta
    )
    df = pd.read_sql(query.statement, db.bind)
    return df


@st.cache_data(ttl=3600)
def load_produccion(fecha_desde, fecha_hasta):
    """Load produccion data."""
    query = db.query(Produccion).filter(
        Produccion.fecha >= fecha_desde,
        Produccion.fecha <= fecha_hasta
    )
    df = pd.read_sql(query.statement, db.bind)
    return df


@st.cache_data(ttl=3600)
def load_bcra_indicadores(fecha_desde, fecha_hasta):
    """Load BCRA indicators."""
    query = db.query(BCRAIndicador).filter(
        BCRAIndicador.fecha >= fecha_desde,
        BCRAIndicador.fecha <= fecha_hasta
    )
    df = pd.read_sql(query.statement, db.bind)
    return df


# Sidebar
st.sidebar.markdown("## 🚗 Mercado Automotor")
st.sidebar.markdown("### Sistema de Inteligencia Comercial")

# Date range selector
st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 Período de Análisis")

fecha_desde = st.sidebar.date_input(
    "Desde",
    value=date.today() - timedelta(days=90),
    max_value=date.today()
)

fecha_hasta = st.sidebar.date_input(
    "Hasta",
    value=date.today(),
    max_value=date.today()
)

# Main page selector
st.sidebar.markdown("---")
page = st.sidebar.selectbox(
    "📊 Seleccionar Dashboard",
    [
        "🏠 Resumen Ejecutivo",
        "📈 Patentamientos",
        "🏭 Producción",
        "💰 Indicadores BCRA",
        "🎯 Indicadores Calculados"
    ]
)

# ==================== MAIN CONTENT ====================

if page == "🏠 Resumen Ejecutivo":
    st.markdown('<p class="main-header">Dashboard Ejecutivo - Mercado Automotor</p>', unsafe_allow_html=True)

    st.markdown(f"**Período:** {fecha_desde} a {fecha_hasta}")

    # KPIs Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Patentamientos 0km",
            value="12,345",
            delta="+15.2%",
            help="Variación vs período anterior"
        )

    with col2:
        st.metric(
            label="Producción Nacional",
            value="45,678",
            delta="-3.1%"
        )

    with col3:
        st.metric(
            label="Precio Promedio ML",
            value="$8.5M",
            delta="+8.3%"
        )

    with col4:
        st.metric(
            label="Tasa BADLAR",
            value="35.5%",
            delta="-2.1%"
        )

    st.markdown("---")

    # Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📊 Evolución Patentamientos 0km")

        # Load data
        try:
            df_pat = load_patentamientos(fecha_desde, fecha_hasta)

            if not df_pat.empty:
                df_0km = df_pat[df_pat['tipo_vehiculo'] == '0km'].groupby('fecha')['cantidad'].sum().reset_index()

                fig = px.line(
                    df_0km,
                    x='fecha',
                    y='cantidad',
                    title='Patentamientos Diarios',
                    labels={'cantidad': 'Unidades', 'fecha': 'Fecha'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de patentamientos para el período seleccionado")

        except Exception as e:
            st.warning(f"No se pudieron cargar datos de patentamientos: {e}")

    with col_right:
        st.subheader("🏭 Top 10 Marcas - Patentamientos")

        try:
            df_pat = load_patentamientos(fecha_desde, fecha_hasta)

            if not df_pat.empty:
                df_top = df_pat[df_pat['tipo_vehiculo'] == '0km'].groupby('marca')['cantidad'].sum().reset_index()
                df_top = df_top.sort_values('cantidad', ascending=False).head(10)

                fig = px.bar(
                    df_top,
                    x='marca',
                    y='cantidad',
                    title='Top 10 Marcas',
                    labels={'cantidad': 'Unidades', 'marca': 'Marca'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos disponibles")

        except Exception as e:
            st.warning(f"No se pudieron cargar datos: {e}")

    # Indicadores Estratégicos
    st.markdown("---")
    st.subheader("🎯 Indicadores Estratégicos")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Tensión de Demanda",
        "Rotación de Stock",
        "Accesibilidad de Compra",
        "Ranking de Atención"
    ])

    with tab1:
        st.markdown("### Índice de Tensión de Demanda")
        st.info("Combina ACARA + Google Trends + BCRA para anticipar caídas de demanda")
        st.markdown("**Status:** En construcción - Datos insuficientes")

    with tab2:
        st.markdown("### Rotación Estimada por Terminal")
        st.info("Compara Producción (ADEFA) vs Patentamientos (ACARA)")
        st.markdown("**Status:** En construcción - Datos insuficientes")

    with tab3:
        st.markdown("### Índice de Accesibilidad de Compra")
        st.info("Relaciona datos de mercado, salarios (INDEC) y financiamiento (BCRA)")
        st.markdown("**Status:** En construcción - Datos insuficientes")

    with tab4:
        st.markdown("### Ranking de Atención de Marca")
        st.info("Analiza volumen de búsquedas y listados activos")
        st.markdown("**Status:** En construcción - Datos insuficientes")


elif page == "📈 Patentamientos":
    st.markdown('<p class="main-header">Análisis de Patentamientos</p>', unsafe_allow_html=True)

    try:
        df_pat = load_patentamientos(fecha_desde, fecha_hasta)

        if not df_pat.empty:
            st.success(f"✓ Cargados {len(df_pat)} registros de patentamientos")

            # Filters
            col1, col2 = st.columns(2)

            with col1:
                tipo_filter = st.selectbox("Tipo de vehículo", ["Todos", "0km", "usado"])

            with col2:
                marcas = df_pat['marca'].dropna().unique().tolist()
                marca_filter = st.selectbox("Marca", ["Todas"] + sorted(marcas))

            # Apply filters
            df_filtered = df_pat.copy()

            if tipo_filter != "Todos":
                df_filtered = df_filtered[df_filtered['tipo_vehiculo'] == tipo_filter]

            if marca_filter != "Todas":
                df_filtered = df_filtered[df_filtered['marca'] == marca_filter]

            # Charts
            st.subheader("Evolución Temporal")
            df_time = df_filtered.groupby(['fecha', 'tipo_vehiculo'])['cantidad'].sum().reset_index()

            fig = px.line(
                df_time,
                x='fecha',
                y='cantidad',
                color='tipo_vehiculo',
                title='Patentamientos por Tipo'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Data table
            st.subheader("Datos Detallados")
            st.dataframe(df_filtered.head(100), use_container_width=True)

        else:
            st.warning("No hay datos de patentamientos para el período seleccionado")

    except Exception as e:
        st.error(f"Error cargando datos: {e}")


elif page == "🏭 Producción":
    st.markdown('<p class="main-header">Análisis de Producción</p>', unsafe_allow_html=True)

    st.info("En construcción - Los datos de ADEFA requieren scraping manual")


elif page == "💰 Indicadores BCRA":
    st.markdown('<p class="main-header">Indicadores Financieros BCRA</p>', unsafe_allow_html=True)

    try:
        df_bcra = load_bcra_indicadores(fecha_desde, fecha_hasta)

        if not df_bcra.empty:
            st.success(f"✓ Cargados {len(df_bcra)} registros de BCRA")

            # Available indicators
            indicadores = df_bcra['indicador'].unique().tolist()
            selected_indicadores = st.multiselect("Indicadores", indicadores, default=indicadores[:3])

            if selected_indicadores:
                df_plot = df_bcra[df_bcra['indicador'].isin(selected_indicadores)]

                fig = px.line(
                    df_plot,
                    x='fecha',
                    y='valor',
                    color='indicador',
                    title='Evolución de Indicadores BCRA'
                )
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(df_plot, use_container_width=True)

        else:
            st.warning("No hay datos de BCRA para el período seleccionado")

    except Exception as e:
        st.error(f"Error cargando datos: {e}")


elif page == "🎯 Indicadores Calculados":
    st.markdown('<p class="main-header">Indicadores Calculados</p>', unsafe_allow_html=True)

    st.info("En construcción - Los indicadores se calcularán automáticamente mediante ETL")

# Footer
st.markdown("---")
st.markdown("**Mercado Automotor** | Sistema de Inteligencia Comercial | Versión 1.0.0")
