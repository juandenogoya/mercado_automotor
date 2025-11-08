"""
Tests para cálculo de indicadores estratégicos.
"""
import pytest
from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.analytics.indicadores import (
    calcular_tension_demanda,
    calcular_rotacion_stock,
    calcular_accesibilidad_compra,
    calcular_ranking_atencion,
    guardar_indicadores
)
from backend.models import (
    Patentamiento,
    Produccion,
    BCRAIndicador,
    MercadoLibreListing,
    IndicadorCalculado
)


@pytest.fixture
def db_with_patentamientos(db_session):
    """Database con datos de patentamientos."""
    # Período actual
    for i in range(30):
        fecha = date(2024, 1, 1) + timedelta(days=i)
        pat = Patentamiento(
            fecha=fecha,
            anio=2024,
            mes=1,
            tipo_vehiculo='0km',
            marca='Toyota',
            cantidad=100 + i,  # Creciente
            fuente='ACARA',
            periodo_reportado='2024-01'
        )
        db_session.add(pat)

    # Período anterior
    for i in range(30):
        fecha = date(2023, 12, 1) + timedelta(days=i)
        pat = Patentamiento(
            fecha=fecha,
            anio=2023,
            mes=12,
            tipo_vehiculo='0km',
            marca='Toyota',
            cantidad=90 + i,  # Menor
            fuente='ACARA',
            periodo_reportado='2023-12'
        )
        db_session.add(pat)

    db_session.commit()
    return db_session


@pytest.fixture
def db_with_bcra(db_session):
    """Database con datos de BCRA."""
    # Tasa BADLAR actual
    for i in range(30):
        fecha = date(2024, 1, 1) + timedelta(days=i)
        ind = BCRAIndicador(
            fecha=fecha,
            indicador='BADLAR',
            valor=35.0 + (i * 0.1),  # Creciente
            unidad='%'
        )
        db_session.add(ind)

    # Tasa BADLAR anterior
    for i in range(30):
        fecha = date(2023, 12, 1) + timedelta(days=i)
        ind = BCRAIndicador(
            fecha=fecha,
            indicador='BADLAR',
            valor=33.0 + (i * 0.1),
            unidad='%'
        )
        db_session.add(ind)

    db_session.commit()
    return db_session


@pytest.fixture
def db_with_produccion(db_session):
    """Database con datos de producción."""
    prod = Produccion(
        fecha=date(2024, 1, 15),
        anio=2024,
        mes=1,
        terminal='Toyota',
        unidades_producidas=15000,
        unidades_exportadas=5000,
        fuente='ADEFA',
        periodo_reportado='2024-01'
    )
    db_session.add(prod)
    db_session.commit()
    return db_session


@pytest.fixture
def db_with_mercadolibre(db_session):
    """Database con datos de MercadoLibre."""
    for i in range(10):
        listing = MercadoLibreListing(
            meli_id=f'MLA{1000+i}',
            marca='Toyota',
            modelo='Corolla',
            anio=2023,
            precio=8000000.0 + (i * 100000),
            moneda='ARS',
            condicion='new',
            kilometros=0,
            url=f'https://mercadolibre.com.ar/item{i}',
            fecha_snapshot=date(2024, 1, 15)
        )
        db_session.add(listing)

    db_session.commit()
    return db_session


class TestTensionDemanda:
    """Tests para Índice de Tensión de Demanda."""

    def test_calcular_con_datos(self, db_with_patentamientos, db_with_bcra):
        """Test cálculo con datos completos."""
        db = db_with_patentamientos

        indicadores = calcular_tension_demanda(
            db=db,
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 1, 30)
        )

        assert len(indicadores) > 0
        assert all(ind['indicador'] == 'tension_demanda' for ind in indicadores)
        assert all('valor' in ind for ind in indicadores)
        assert all('detalles' in ind for ind in indicadores)

    def test_calcular_sin_datos(self, db_session):
        """Test cálculo sin datos."""
        indicadores = calcular_tension_demanda(
            db=db_session,
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 1, 30)
        )

        assert len(indicadores) == 0

    def test_estructura_indicador(self, db_with_patentamientos, db_with_bcra):
        """Test estructura del indicador."""
        db = db_with_patentamientos

        indicadores = calcular_tension_demanda(
            db=db,
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 1, 30)
        )

        if indicadores:
            ind = indicadores[0]
            assert 'fecha' in ind
            assert 'indicador' in ind
            assert 'marca' in ind
            assert 'valor' in ind
            assert 'detalles' in ind
            assert 'var_patentamientos_pct' in ind['detalles']
            assert 'interpretacion' in ind['detalles']


class TestRotacionStock:
    """Tests para Rotación de Stock."""

    def test_calcular_con_datos(self, db_with_patentamientos, db_with_produccion):
        """Test cálculo con datos completos."""
        db = db_with_patentamientos

        indicadores = calcular_rotacion_stock(
            db=db,
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 1, 30)
        )

        assert len(indicadores) > 0
        assert all(ind['indicador'] == 'rotacion_stock' for ind in indicadores)

    def test_estructura_indicador(self, db_with_patentamientos, db_with_produccion):
        """Test estructura del indicador."""
        db = db_with_patentamientos

        indicadores = calcular_rotacion_stock(
            db=db,
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 1, 30)
        )

        if indicadores:
            ind = indicadores[0]
            assert 'valor' in ind  # Días de stock
            assert 'detalles' in ind
            assert 'terminal' in ind['detalles']
            assert 'produccion_mensual' in ind['detalles']
            assert 'interpretacion' in ind['detalles']
            assert 'alerta' in ind['detalles']


class TestAccesibilidadCompra:
    """Tests para Índice de Accesibilidad de Compra."""

    def test_calcular_con_datos(self, db_with_mercadolibre, db_with_bcra):
        """Test cálculo con datos completos."""
        db = db_with_mercadolibre

        indicadores = calcular_accesibilidad_compra(
            db=db,
            fecha=date(2024, 1, 15),
            salario_promedio=1_000_000.0
        )

        assert len(indicadores) > 0
        assert all(ind['indicador'] == 'accesibilidad_compra' for ind in indicadores)

    def test_estructura_indicador(self, db_with_mercadolibre, db_with_bcra):
        """Test estructura del indicador."""
        db = db_with_mercadolibre

        indicadores = calcular_accesibilidad_compra(
            db=db,
            fecha=date(2024, 1, 15),
            salario_promedio=1_000_000.0
        )

        if indicadores:
            ind = indicadores[0]
            assert 'valor' in ind  # IAC
            assert 'detalles' in ind
            assert 'precio_promedio' in ind['detalles']
            assert 'cuota_mensual' in ind['detalles']
            assert 'pct_salario' in ind['detalles']
            assert 'interpretacion' in ind['detalles']

    def test_diferentes_salarios(self, db_with_mercadolibre, db_with_bcra):
        """Test con diferentes salarios."""
        db = db_with_mercadolibre

        # Salario bajo
        ind_bajo = calcular_accesibilidad_compra(db, date(2024, 1, 15), 500_000.0)

        # Salario alto
        ind_alto = calcular_accesibilidad_compra(db, date(2024, 1, 15), 2_000_000.0)

        if ind_bajo and ind_alto:
            # Salario más alto debería resultar en IAC mayor
            assert ind_alto[0]['valor'] > ind_bajo[0]['valor']


class TestRankingAtencion:
    """Tests para Ranking de Atención."""

    def test_calcular_con_datos(self, db_with_mercadolibre, db_with_patentamientos):
        """Test cálculo con datos completos."""
        db = db_with_mercadolibre

        indicadores = calcular_ranking_atencion(
            db=db,
            fecha=date(2024, 1, 15),
            top_n=10
        )

        assert len(indicadores) > 0
        assert len(indicadores) <= 10
        assert all(ind['indicador'] == 'ranking_atencion' for ind in indicadores)

    def test_ordenamiento(self, db_with_mercadolibre, db_with_patentamientos):
        """Test que el ranking esté ordenado."""
        db = db_with_mercadolibre

        indicadores = calcular_ranking_atencion(
            db=db,
            fecha=date(2024, 1, 15),
            top_n=5
        )

        if len(indicadores) >= 2:
            # Verificar orden descendente
            for i in range(len(indicadores) - 1):
                assert indicadores[i]['valor'] >= indicadores[i+1]['valor']

    def test_estructura_indicador(self, db_with_mercadolibre, db_with_patentamientos):
        """Test estructura del indicador."""
        db = db_with_mercadolibre

        indicadores = calcular_ranking_atencion(
            db=db,
            fecha=date(2024, 1, 15),
            top_n=5
        )

        if indicadores:
            ind = indicadores[0]
            assert 'valor' in ind  # Score
            assert 'detalles' in ind
            assert 'listados_ml' in ind['detalles']
            assert 'ranking_posicion' in ind['detalles']
            assert 'categoria' in ind['detalles']


class TestGuardarIndicadores:
    """Tests para guardar indicadores."""

    def test_guardar_indicadores(self, db_session):
        """Test guardar indicadores en BD."""
        indicadores = [
            {
                'fecha': date(2024, 1, 15),
                'indicador': 'tension_demanda',
                'marca': 'Toyota',
                'valor': 15.5,
                'detalles': {'test': 'data'}
            },
            {
                'fecha': date(2024, 1, 15),
                'indicador': 'rotacion_stock',
                'marca': 'Ford',
                'valor': 45.0,
                'detalles': {'test': 'data'}
            }
        ]

        saved_count = guardar_indicadores(db_session, indicadores)

        assert saved_count == 2

        # Verificar en BD
        count = db_session.query(IndicadorCalculado).count()
        assert count == 2

    def test_guardar_duplicados(self, db_session):
        """Test guardar indicadores duplicados (debería actualizar)."""
        indicador = {
            'fecha': date(2024, 1, 15),
            'indicador': 'tension_demanda',
            'marca': 'Toyota',
            'valor': 15.5,
            'detalles': {'test': 'data'}
        }

        # Primera vez
        saved_count_1 = guardar_indicadores(db_session, [indicador])
        assert saved_count_1 == 1

        # Segunda vez con valor diferente
        indicador['valor'] = 20.0
        saved_count_2 = guardar_indicadores(db_session, [indicador])

        # No debería crear nuevo, solo actualizar
        count = db_session.query(IndicadorCalculado).count()
        assert count == 1

        # Verificar valor actualizado
        ind = db_session.query(IndicadorCalculado).first()
        assert ind.valor == 20.0
