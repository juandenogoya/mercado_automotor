"""
Script para verificar configuración de credenciales de MercadoLibre.
"""

import sys
from pathlib import Path

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config.settings import settings


def verify_credentials():
    """Verifica que las credenciales estén configuradas correctamente."""

    print("=" * 80)
    print("🔍 VERIFICACIÓN DE CREDENCIALES - MERCADOLIBRE")
    print("=" * 80)

    issues = []
    warnings = []

    # Verificar Client ID
    print("\n1️⃣ Client ID (MERCADOLIBRE_CLIENT_ID)")
    if settings.mercadolibre_client_id:
        print(f"   ✅ Configurado: {settings.mercadolibre_client_id[:10]}...{settings.mercadolibre_client_id[-4:]}")

        # Validaciones básicas
        if len(settings.mercadolibre_client_id) < 10:
            warnings.append("Client ID parece muy corto")
        if ' ' in settings.mercadolibre_client_id:
            issues.append("Client ID contiene espacios (no debería)")
    else:
        print("   ❌ NO configurado")
        issues.append("MERCADOLIBRE_CLIENT_ID no está configurado en .env")

    # Verificar Client Secret
    print("\n2️⃣ Client Secret (MERCADOLIBRE_CLIENT_SECRET)")
    if settings.mercadolibre_client_secret:
        print(f"   ✅ Configurado: {settings.mercadolibre_client_secret[:6]}...{settings.mercadolibre_client_secret[-4:]}")

        # Validaciones básicas
        if len(settings.mercadolibre_client_secret) < 20:
            warnings.append("Client Secret parece muy corto")
        if ' ' in settings.mercadolibre_client_secret:
            issues.append("Client Secret contiene espacios (no debería)")
    else:
        print("   ❌ NO configurado")
        issues.append("MERCADOLIBRE_CLIENT_SECRET no está configurado en .env")

    # Verificar archivo .env
    print("\n3️⃣ Archivo .env")
    env_file = Path(".env")
    if env_file.exists():
        print(f"   ✅ Encontrado: {env_file.absolute()}")
    else:
        print("   ⚠️ No encontrado")
        warnings.append("Archivo .env no existe (se usan valores por defecto)")

    # Verificar .gitignore
    print("\n4️⃣ Archivo .gitignore")
    gitignore_file = Path(".gitignore")
    if gitignore_file.exists():
        content = gitignore_file.read_text()

        env_ignored = ".env" in content
        tokens_ignored = ".meli_tokens.json" in content or "*.json" in content

        if env_ignored:
            print("   ✅ .env está en .gitignore")
        else:
            print("   ⚠️ .env NO está en .gitignore")
            warnings.append(".env debería estar en .gitignore para no subir credenciales a Git")

        if tokens_ignored:
            print("   ✅ .meli_tokens.json está ignorado")
        else:
            print("   ⚠️ .meli_tokens.json NO está en .gitignore")
            warnings.append(".meli_tokens.json debería estar en .gitignore")
    else:
        print("   ⚠️ .gitignore no encontrado")
        warnings.append(".gitignore no existe")

    # Verificar rate limit
    print("\n5️⃣ Rate Limit")
    print(f"   ℹ️ Configurado: {settings.mercadolibre_rate_limit} requests/min")

    # Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN")
    print("=" * 80)

    if not issues and not warnings:
        print("\n✅ TODO CORRECTO - Credenciales configuradas correctamente")
        print("\n🚀 Próximo paso: Ejecutar autenticación OAuth2")
        print("   python backend/auth/mercadolibre_oauth.py")
        return True

    if warnings:
        print(f"\n⚠️ {len(warnings)} Advertencias:")
        for w in warnings:
            print(f"   • {w}")

    if issues:
        print(f"\n❌ {len(issues)} Problemas encontrados:")
        for i in issues:
            print(f"   • {i}")

        print("\n📚 Para configurar credenciales:")
        print("   1. Ver GUIA_REGISTRO_MERCADOLIBRE_DEVELOPER.md")
        print("   2. Crear aplicación en https://developers.mercadolibre.com.ar/")
        print("   3. Agregar credenciales al archivo .env")

        return False

    return True


if __name__ == "__main__":
    success = verify_credentials()
    sys.exit(0 if success else 1)
