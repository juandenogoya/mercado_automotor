"""
Módulo de autenticación OAuth2 para MercadoLibre API.
Implementa flujo OAuth2 con PKCE (Proof Key for Code Exchange).

Documentación oficial:
https://developers.mercadolibre.com.ar/es_ar/autenticacion-y-autorizacion
"""

import json
import hashlib
import base64
import secrets
import webbrowser
import ssl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse
import http.server
import socketserver
import threading
import time

import requests
from loguru import logger

from backend.config.settings import settings


class MercadoLibreAuth:
    """
    Gestor de autenticación OAuth2 para MercadoLibre API.

    Implementa:
    - OAuth2 Authorization Code Flow con PKCE
    - Almacenamiento seguro de tokens
    - Refresh automático de tokens
    - Validación de tokens
    """

    # URLs de autenticación para Argentina
    AUTH_URL = "https://auth.mercadolibre.com.ar/authorization"
    TOKEN_URL = "https://api.mercadolibre.com/oauth/token"

    # Configuración
    SCOPES = ["offline_access", "read"]

    def __init__(self, token_file: Optional[str] = None):
        """
        Inicializa el gestor de autenticación.

        Args:
            token_file: Path al archivo donde guardar los tokens
        """
        self.client_id = settings.mercadolibre_client_id
        self.client_secret = settings.mercadolibre_client_secret
        self.redirect_uri = settings.mercadolibre_redirect_uri

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "MERCADOLIBRE_CLIENT_ID y MERCADOLIBRE_CLIENT_SECRET deben estar configurados en .env"
            )

        # Archivo para almacenar tokens
        self.token_file = Path(token_file or ".meli_tokens.json")

        # Tokens actuales
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._user_id: Optional[str] = None

        # Cargar tokens existentes si hay
        self._load_tokens()

        logger.info("MercadoLibre Auth inicializado")

    def _generate_code_verifier(self) -> str:
        """
        Genera code_verifier para PKCE.

        Returns:
            String aleatorio de 128 caracteres
        """
        return base64.urlsafe_b64encode(secrets.token_bytes(96)).decode('utf-8').rstrip('=')

    def _generate_code_challenge(self, verifier: str) -> str:
        """
        Genera code_challenge a partir del verifier.

        Args:
            verifier: Code verifier generado

        Returns:
            SHA256 hash del verifier en base64
        """
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

    def get_authorization_url(self) -> tuple[str, str]:
        """
        Genera URL de autorización y code_verifier.

        Returns:
            Tupla (authorization_url, code_verifier)
        """
        # Generar PKCE parameters
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)

        # State para CSRF protection
        state = secrets.token_urlsafe(32)

        # Construir URL de autorización
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'state': state,
            'scope': ' '.join(self.SCOPES)
        }

        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"

        return auth_url, code_verifier

    def _create_ssl_context(self) -> ssl.SSLContext:
        """
        Crea contexto SSL con certificado auto-firmado para localhost.

        Returns:
            Contexto SSL configurado
        """
        # Importar función de creación de certificados
        try:
            from backend.auth.create_ssl_cert import create_cert_with_cryptography
        except ImportError:
            logger.error("No se pudo importar create_ssl_cert")
            raise

        # Crear certificado auto-firmado
        cert_dir = Path(__file__).parent
        cert_file, key_file = create_cert_with_cryptography(cert_dir)

        # Crear contexto SSL
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(certfile=str(cert_file), keyfile=str(key_file))

        return context

    def _start_callback_server(self) -> Dict[str, str]:
        """
        Inicia servidor HTTPS temporal para recibir el callback de OAuth2.

        Returns:
            Diccionario con parámetros del callback (code, state)
        """
        callback_params = {}

        class CallbackHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                # Parsear query parameters
                query = urlparse(self.path).query
                params = parse_qs(query)

                # Guardar parámetros
                callback_params['code'] = params.get('code', [None])[0]
                callback_params['state'] = params.get('state', [None])[0]
                callback_params['error'] = params.get('error', [None])[0]

                # Responder al navegador
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                if callback_params.get('code'):
                    html = """
                    <html>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>✅ Autenticación Exitosa</h1>
                        <p>Ya podés cerrar esta ventana y volver a la terminal.</p>
                    </body>
                    </html>
                    """
                else:
                    error = callback_params.get('error', 'unknown')
                    html = f"""
                    <html>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>❌ Error de Autenticación</h1>
                        <p>Error: {error}</p>
                        <p>Cerrá esta ventana y revisá la terminal.</p>
                    </body>
                    </html>
                    """

                self.wfile.write(html.encode())

            def log_message(self, format, *args):
                # Silenciar logs del servidor HTTP
                pass

        # Determinar puerto del servidor local
        # ngrok redirige a localhost:8080, así que siempre usamos ese puerto localmente
        # independientemente del puerto en la URL pública
        from urllib.parse import urlparse as url_parse
        parsed_url = url_parse(self.redirect_uri)

        # Si la URL tiene un puerto explícito (ej: localhost:8080), usarlo
        # Si no (ej: ngrok sin puerto), usar 8080 por defecto
        if parsed_url.port:
            port = parsed_url.port
        else:
            # URL sin puerto explícito (como ngrok) - usar 8080 localmente
            port = 8080

        logger.info(f"Iniciando servidor de callback local en puerto {port}")
        logger.info(f"Esperando redirección desde: {self.redirect_uri}")

        with socketserver.TCPServer(("", port), CallbackHandler) as httpd:
            # Solo usar SSL si la URL es localhost (no ngrok)
            # ngrok maneja HTTPS y redirige a HTTP local
            use_ssl = 'localhost' in self.redirect_uri or '127.0.0.1' in self.redirect_uri

            if use_ssl:
                # Envolver con SSL para localhost
                try:
                    ssl_context = self._create_ssl_context()
                    httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
                    logger.info(f"Servidor de callback HTTPS iniciado en puerto {port}")
                except Exception as e:
                    logger.error(f"Error configurando SSL: {e}")
                    logger.info(f"Usando servidor HTTP en puerto {port}")
            else:
                # ngrok maneja HTTPS, servidor local usa HTTP
                logger.info(f"Servidor de callback HTTP iniciado en puerto {port} (ngrok maneja HTTPS)")

            # Esperar callback (timeout 5 minutos)
            timeout = 300
            start_time = time.time()

            while not callback_params and (time.time() - start_time) < timeout:
                httpd.handle_request()
                time.sleep(0.1)

        return callback_params

    def authorize(self) -> bool:
        """
        Ejecuta el flujo completo de autorización OAuth2.

        Returns:
            True si la autorización fue exitosa, False en caso contrario
        """
        logger.info("Iniciando flujo de autorización OAuth2")

        # Generar URL de autorización
        auth_url, code_verifier = self.get_authorization_url()

        print("\n" + "=" * 80)
        print("🔐 AUTORIZACIÓN MERCADOLIBRE")
        print("=" * 80)
        print("\nSe va a abrir una ventana del navegador para autorizar la aplicación.")
        print("\nSi no se abre automáticamente, copiá y pegá esta URL en tu navegador:")
        print(f"\n{auth_url}\n")
        print("Esperando autorización...")
        print("=" * 80 + "\n")

        # Abrir navegador
        webbrowser.open(auth_url)

        # Iniciar servidor de callback
        callback_params = self._start_callback_server()

        # Verificar respuesta
        if callback_params.get('error'):
            logger.error(f"Error en autorización: {callback_params['error']}")
            return False

        if not callback_params.get('code'):
            logger.error("No se recibió código de autorización")
            return False

        # Intercambiar código por tokens
        auth_code = callback_params['code']
        success = self._exchange_code_for_token(auth_code, code_verifier)

        if success:
            logger.info("✅ Autorización completada exitosamente")
            self._save_tokens()
        else:
            logger.error("❌ Falló el intercambio de código por token")

        return success

    def _exchange_code_for_token(self, code: str, code_verifier: str) -> bool:
        """
        Intercambia el authorization code por access token.

        Args:
            code: Authorization code recibido
            code_verifier: Code verifier usado en la autorización

        Returns:
            True si el intercambio fue exitoso
        """
        logger.info("Intercambiando código por access token")

        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()

            # Guardar tokens
            self._access_token = token_data['access_token']
            self._refresh_token = token_data.get('refresh_token')

            # Calcular expiración
            expires_in = token_data.get('expires_in', 21600)  # 6 horas por defecto
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            # User ID
            self._user_id = str(token_data.get('user_id', ''))

            logger.info(f"Access token obtenido (expira: {self._token_expires_at})")
            logger.info(f"User ID: {self._user_id}")

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False

    def refresh_access_token(self) -> bool:
        """
        Refresca el access token usando el refresh token.

        Returns:
            True si el refresh fue exitoso
        """
        if not self._refresh_token:
            logger.error("No hay refresh token disponible")
            return False

        logger.info("Refrescando access token")

        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self._refresh_token
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()

            # Actualizar tokens
            self._access_token = token_data['access_token']
            self._refresh_token = token_data.get('refresh_token')  # Nuevo refresh token

            # Calcular expiración
            expires_in = token_data.get('expires_in', 21600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            logger.info(f"Access token refrescado (expira: {self._token_expires_at})")

            # Guardar nuevos tokens
            self._save_tokens()

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al refrescar token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False

    def get_access_token(self) -> Optional[str]:
        """
        Obtiene un access token válido.

        Refresca automáticamente si está expirado.

        Returns:
            Access token válido o None si no se pudo obtener
        """
        # Si no hay token, debe autorizarse primero
        if not self._access_token:
            logger.warning("No hay access token. Ejecutar authorize() primero.")
            return None

        # Verificar si está expirado (con 5 min de margen)
        if self._token_expires_at:
            expires_soon = datetime.now() + timedelta(minutes=5)

            if expires_soon >= self._token_expires_at:
                logger.info("Token expirando pronto, refrescando...")

                if not self.refresh_access_token():
                    logger.error("No se pudo refrescar el token")
                    return None

        return self._access_token

    def _save_tokens(self):
        """Guarda tokens en archivo JSON."""
        if not self._access_token:
            return

        token_data = {
            'access_token': self._access_token,
            'refresh_token': self._refresh_token,
            'expires_at': self._token_expires_at.isoformat() if self._token_expires_at else None,
            'user_id': self._user_id,
            'updated_at': datetime.now().isoformat()
        }

        try:
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)

            logger.debug(f"Tokens guardados en {self.token_file}")

        except Exception as e:
            logger.error(f"Error al guardar tokens: {e}")

    def _load_tokens(self):
        """Carga tokens desde archivo JSON."""
        if not self.token_file.exists():
            logger.debug("No hay archivo de tokens")
            return

        try:
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)

            self._access_token = token_data.get('access_token')
            self._refresh_token = token_data.get('refresh_token')
            self._user_id = token_data.get('user_id')

            # Parsear fecha de expiración
            expires_at_str = token_data.get('expires_at')
            if expires_at_str:
                self._token_expires_at = datetime.fromisoformat(expires_at_str)

            logger.info("Tokens cargados desde archivo")

            # Verificar si está expirado
            if self._token_expires_at and datetime.now() >= self._token_expires_at:
                logger.warning("Token cargado está expirado, se refrescará automáticamente")

        except Exception as e:
            logger.error(f"Error al cargar tokens: {e}")

    def is_authenticated(self) -> bool:
        """
        Verifica si hay autenticación válida.

        Returns:
            True si hay access token válido
        """
        return self.get_access_token() is not None

    def clear_tokens(self):
        """Elimina tokens guardados."""
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None
        self._user_id = None

        if self.token_file.exists():
            self.token_file.unlink()
            logger.info("Tokens eliminados")


# Script de ejemplo para autenticación
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Agregar backend al path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from backend.config.logger import setup_logger

    setup_logger()

    print("=" * 80)
    print("🔐 AUTENTICACIÓN MERCADOLIBRE - OAuth2")
    print("=" * 80)

    # Verificar credenciales
    if not settings.mercadolibre_client_id or not settings.mercadolibre_client_secret:
        print("\n❌ ERROR: Credenciales no configuradas")
        print("\nPor favor configurar en .env:")
        print("  MERCADOLIBRE_CLIENT_ID=tu_client_id")
        print("  MERCADOLIBRE_CLIENT_SECRET=tu_client_secret")
        print("\nVer GUIA_REGISTRO_MERCADOLIBRE_DEVELOPER.md para más información")
        sys.exit(1)

    print("\n✅ Credenciales encontradas")
    print(f"   Client ID: {settings.mercadolibre_client_id[:10]}...")

    # Crear gestor de autenticación
    auth = MercadoLibreAuth()

    # Verificar si ya está autenticado
    if auth.is_authenticated():
        print("\n✅ Ya estás autenticado!")
        print(f"   User ID: {auth._user_id}")
        print(f"   Token expira: {auth._token_expires_at}")

        print("\n¿Querés re-autenticar? (s/N): ", end='')
        response = input().strip().lower()

        if response != 's':
            print("\n✅ Usando autenticación existente")
            sys.exit(0)
        else:
            auth.clear_tokens()

    # Ejecutar flujo de autorización
    print("\n🚀 Iniciando flujo de autorización...")

    if auth.authorize():
        print("\n" + "=" * 80)
        print("✅ AUTENTICACIÓN EXITOSA")
        print("=" * 80)
        print(f"\n📊 Detalles:")
        print(f"   User ID: {auth._user_id}")
        print(f"   Token expira: {auth._token_expires_at}")
        print(f"   Tokens guardados en: {auth.token_file}")
        print("\n✅ Ya podés usar la API de MercadoLibre!")
        print("\nEjecutá: python test_mercadolibre_authenticated.py")
        print("=" * 80)
    else:
        print("\n❌ Error en autenticación")
        print("Revisar logs para más detalles")
        sys.exit(1)
