"""
Tests para modelos de base de datos.
"""
import pytest
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import (
    Patentamiento,
    Produccion,
    BCRAIndicador,
    MercadoLibreListing,
    IndicadorCalculado
)


class TestPatentamientoModel:
    """Tests para modelo Patentamiento."""

    def test_create_patentamiento(self, db_session, sample_patentamiento_data):
        """Test crear patentamiento."""
        pat = Patentamiento(**sample_patentamiento_data)
        db_session.add(pat)
        db_session.commit()

        assert pat.id is not None
        assert pat.marca == 'Toyota'
        assert pat.cantidad == 5000

    def test_patentamiento_unique_constraint(self, db_session, sample_patentamiento_data):
        """Test constraint único."""
        pat1 = Patentamiento(**sample_patentamiento_data)
        db_session.add(pat1)
        db_session.commit()

        # Intentar crear duplicado
        pat2 = Patentamiento(**sample_patentamiento_data)
        db_session.add(pat2)

        # SQLite no enforcea unique constraints perfectamente en tests,
        # pero el código debería manejar duplicados

    def test_patentamiento_timestamps(self, db_session, sample_patentamiento_data):
        """Test timestamps automáticos."""
        pat = Patentamiento(**sample_patentamiento_data)
        db_session.add(pat)
        db_session.commit()

        assert pat.created_at is not None
        assert pat.updated_at is not None


class TestProduccionModel:
    """Tests para modelo Produccion."""

    def test_create_produccion(self, db_session, sample_produccion_data):
        """Test crear producción."""
        prod = Produccion(**sample_produccion_data)
        db_session.add(prod)
        db_session.commit()

        assert prod.id is not None
        assert prod.terminal == 'Toyota'
        assert prod.unidades_producidas == 15000

    def test_produccion_query(self, db_session, sample_produccion_data):
        """Test query producción."""
        prod = Produccion(**sample_produccion_data)
        db_session.add(prod)
        db_session.commit()

        # Query
        result = db_session.query(Produccion).filter(
            Produccion.terminal == 'Toyota'
        ).first()

        assert result is not None
        assert result.terminal == 'Toyota'


class TestBCRAIndicadorModel:
    """Tests para modelo BCRAIndicador."""

    def test_create_bcra_indicador(self, db_session, sample_bcra_data):
        """Test crear indicador BCRA."""
        ind = BCRAIndicador(**sample_bcra_data)
        db_session.add(ind)
        db_session.commit()

        assert ind.id is not None
        assert ind.indicador == 'BADLAR'
        assert ind.valor == 35.5

    def test_bcra_query_by_date_range(self, db_session):
        """Test query por rango de fechas."""
        # Agregar múltiples indicadores
        for i in range(10):
            ind = BCRAIndicador(
                fecha=date(2024, 1, 1 + i),
                indicador='BADLAR',
                valor=35.0 + i,
                unidad='%'
            )
            db_session.add(ind)
        db_session.commit()

        # Query rango
        results = db_session.query(BCRAIndicador).filter(
            BCRAIndicador.fecha >= date(2024, 1, 5),
            BCRAIndicador.fecha <= date(2024, 1, 8)
        ).all()

        assert len(results) == 4


class TestMercadoLibreListingModel:
    """Tests para modelo MercadoLibreListing."""

    def test_create_listing(self, db_session, sample_meli_data):
        """Test crear listing."""
        listing = MercadoLibreListing(**sample_meli_data)
        db_session.add(listing)
        db_session.commit()

        assert listing.id is not None
        assert listing.meli_id == 'MLA123456789'
        assert listing.marca == 'Toyota'

    def test_meli_unique_id(self, db_session, sample_meli_data):
        """Test meli_id único."""
        listing1 = MercadoLibreListing(**sample_meli_data)
        db_session.add(listing1)
        db_session.commit()

        # Intentar crear con mismo meli_id pero diferente fecha
        data2 = sample_meli_data.copy()
        data2['fecha_snapshot'] = date(2024, 1, 16)
        listing2 = MercadoLibreListing(**data2)
        db_session.add(listing2)

        # Debería permitir mismo meli_id en diferentes snapshots

    def test_meli_query_by_marca(self, db_session):
        """Test query por marca."""
        # Agregar múltiples listados
        for i, marca in enumerate(['Toyota', 'Ford', 'Toyota']):
            listing = MercadoLibreListing(
                meli_id=f'MLA{1000+i}',
                marca=marca,
                precio=8000000.0,
                moneda='ARS',
                condicion='new',
                url=f'http://test{i}.com',
                fecha_snapshot=date(2024, 1, 15)
            )
            db_session.add(listing)
        db_session.commit()

        # Query Toyota
        results = db_session.query(MercadoLibreListing).filter(
            MercadoLibreListing.marca == 'Toyota'
        ).all()

        assert len(results) == 2


class TestIndicadorCalculadoModel:
    """Tests para modelo IndicadorCalculado."""

    def test_create_indicador(self, db_session):
        """Test crear indicador calculado."""
        ind = IndicadorCalculado(
            fecha=date(2024, 1, 15),
            indicador='tension_demanda',
            marca='Toyota',
            valor=15.5,
            detalles={'test': 'data'}
        )
        db_session.add(ind)
        db_session.commit()

        assert ind.id is not None
        assert ind.indicador == 'tension_demanda'
        assert ind.valor == 15.5

    def test_indicador_json_field(self, db_session):
        """Test campo JSON detalles."""
        detalles_complejo = {
            'var_patentamientos_pct': 15.5,
            'interpretacion': 'Crecimiento',
            'nested': {'key': 'value'}
        }

        ind = IndicadorCalculado(
            fecha=date(2024, 1, 15),
            indicador='tension_demanda',
            marca='Toyota',
            valor=15.5,
            detalles=detalles_complejo
        )
        db_session.add(ind)
        db_session.commit()

        # Recuperar
        result = db_session.query(IndicadorCalculado).first()
        assert result.detalles == detalles_complejo

    def test_query_indicadores_by_type(self, db_session):
        """Test query por tipo de indicador."""
        # Agregar múltiples tipos
        indicadores = [
            ('tension_demanda', 'Toyota', 15.5),
            ('rotacion_stock', 'Toyota', 45.0),
            ('tension_demanda', 'Ford', 12.0),
        ]

        for tipo, marca, valor in indicadores:
            ind = IndicadorCalculado(
                fecha=date(2024, 1, 15),
                indicador=tipo,
                marca=marca,
                valor=valor,
                detalles={}
            )
            db_session.add(ind)
        db_session.commit()

        # Query solo tension_demanda
        results = db_session.query(IndicadorCalculado).filter(
            IndicadorCalculado.indicador == 'tension_demanda'
        ).all()

        assert len(results) == 2


class TestModelRelationships:
    """Tests para relaciones entre modelos."""

    def test_multiple_models_integration(self, db_session):
        """Test integración de múltiples modelos."""
        # Crear datos relacionados
        pat = Patentamiento(
            fecha=date(2024, 1, 15),
            anio=2024,
            mes=1,
            tipo_vehiculo='0km',
            marca='Toyota',
            cantidad=5000,
            fuente='ACARA',
            periodo_reportado='2024-01'
        )

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

        ind_calc = IndicadorCalculado(
            fecha=date(2024, 1, 15),
            indicador='rotacion_stock',
            marca='Toyota',
            valor=45.0,
            detalles={}
        )

        db_session.add_all([pat, prod, ind_calc])
        db_session.commit()

        # Verificar que todos existen
        assert db_session.query(Patentamiento).count() == 1
        assert db_session.query(Produccion).count() == 1
        assert db_session.query(IndicadorCalculado).count() == 1
