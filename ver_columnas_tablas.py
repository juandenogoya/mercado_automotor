"""Script temporal para ver columnas de las tablas."""
from sqlalchemy import create_engine, inspect
import sys
from pathlib import Path

sys.path.append('.')
from backend.config.settings import settings

engine = create_engine(settings.get_database_url_sync())
inspector = inspect(engine)

print('\n=== Tabla IPC ===')
for col in inspector.get_columns('ipc'):
    print(f'  - {col["name"]}: {col["type"]}')

print('\n=== Tabla BADLAR ===')
for col in inspector.get_columns('badlar'):
    print(f'  - {col["name"]}: {col["type"]}')

print('\n=== Tabla TIPO_CAMBIO ===')
for col in inspector.get_columns('tipo_cambio'):
    print(f'  - {col["name"]}: {col["type"]}')

print('\n=== Tabla INDICADORES_CALCULADOS ===')
if 'indicadores_calculados' in inspector.get_table_names():
    for col in inspector.get_columns('indicadores_calculados'):
        print(f'  - {col["name"]}: {col["type"]}')
else:
    print('  (tabla no existe)')

engine.dispose()
