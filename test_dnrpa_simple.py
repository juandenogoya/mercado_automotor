"""
Test acceso básico a DNRPA
"""
import requests
import urllib3
import time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
})
session.verify = False

print("🧪 Test de acceso básico a DNRPA")
print("=" * 80)

# Test 1: Página principal
print("\n1️⃣ Intentando acceder a la página principal...")
try:
    response = session.get('https://www.dnrpa.gov.ar/', timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Acceso exitoso")
        print(f"   Content-Length: {len(response.content)} bytes")
except Exception as e:
    print(f"   ❌ Error: {e}")

time.sleep(2)

# Test 2: Portal estadísticas
print("\n2️⃣ Intentando acceder al portal de estadísticas...")
try:
    response = session.get('https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/', timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Acceso exitoso")
except Exception as e:
    print(f"   ❌ Error: {e}")

time.sleep(2)

# Test 3: Página del formulario
print("\n3️⃣ Intentando acceder al formulario de trámites...")
try:
    response = session.get(
        'https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php',
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Acceso exitoso")
        print(f"   Cookies: {list(session.cookies.keys())}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ Test completado")
