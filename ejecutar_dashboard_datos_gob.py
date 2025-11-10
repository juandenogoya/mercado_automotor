"""
Script para ejecutar el Dashboard de datos.gob.ar

Ejecuta el dashboard de Streamlit para análisis de trámites automotores.
"""
import subprocess
import sys
from pathlib import Path

def main():
    # Ruta al dashboard
    dashboard_path = Path(__file__).parent / 'frontend' / 'app_datos_gob.py'

    if not dashboard_path.exists():
        print(f"❌ Error: No se encontró el dashboard en {dashboard_path}")
        sys.exit(1)

    print("=" * 80)
    print("🚗 INICIANDO DASHBOARD - Análisis datos.gob.ar")
    print("=" * 80)
    print()
    print("📊 Dashboard: Trámites Automotores DNRPA")
    print("🌐 URL: http://localhost:8501")
    print()
    print("💡 Para detener: Presiona Ctrl+C")
    print("=" * 80)
    print()

    try:
        # Ejecutar Streamlit
        subprocess.run([
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(dashboard_path),
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard cerrado correctamente")
    except Exception as e:
        print(f"\n❌ Error al ejecutar dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
