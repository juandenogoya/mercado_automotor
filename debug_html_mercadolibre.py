"""
Script de debugging para inspeccionar el HTML de MercadoLibre
y encontrar los selectores correctos
"""
import requests
from bs4 import BeautifulSoup
import time
import random

def inspect_mercadolibre_html():
    """Descarga y analiza el HTML de MercadoLibre"""

    # User-Agent realista
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    url = "https://listado.mercadolibre.com.ar/vehiculos/autos-camionetas-y-4x4/toyota"

    print(f"🔍 Descargando HTML de: {url}\n")

    try:
        response = requests.get(url, headers=headers, timeout=30)

        print(f"📊 Status: {response.status_code}")
        print(f"📏 Tamaño respuesta: {len(response.content)} bytes")
        print(f"🗂️  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"🗜️  Content-Encoding: {response.headers.get('Content-Encoding', 'N/A')}")
        print(f"📝 Encoding detectado: {response.encoding}\n")

        if response.status_code != 200:
            print(f"❌ Error: Status {response.status_code}")
            return

        # Verificar si el contenido está comprimido correctamente
        html_text = response.text

        # Verificar primeros caracteres para detectar si es binario/corrupto
        first_chars = html_text[:100]
        is_binary = any(ord(c) < 32 and c not in '\n\r\t' for c in first_chars[:20])

        if is_binary:
            print("🚨 ADVERTENCIA: Contenido parece estar corrupto o mal descomprimido")
            print(f"   Primeros bytes: {response.content[:50]}\n")

            # Intentar forzar encoding
            print("🔄 Intentando con diferentes encodings...\n")

            for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
                try:
                    response.encoding = encoding
                    html_text = response.text
                    if '<html' in html_text.lower() or '<!doctype' in html_text.lower():
                        print(f"✅ Éxito con encoding: {encoding}\n")
                        break
                except:
                    continue
            else:
                print("❌ No se pudo decodificar correctamente\n")
                return

        # Guardar HTML para inspección
        with open('mercadolibre_debug.html', 'w', encoding='utf-8') as f:
            f.write(html_text)
        print("💾 HTML guardado en: mercadolibre_debug.html\n")

        # Verificar que sea HTML válido
        if '<html' not in html_text.lower() and '<!doctype' not in html_text.lower():
            print("⚠️ ADVERTENCIA: El contenido no parece ser HTML válido")
            print(f"   Primeros 500 caracteres:\n{html_text[:500]}\n")

        # Parsear con BeautifulSoup
        soup = BeautifulSoup(html_text, 'html.parser')

        print("="*80)
        print("🔎 ANÁLISIS DE ESTRUCTURA HTML")
        print("="*80)

        # 1. Buscar diferentes posibles contenedores de items
        print("\n1️⃣ Buscando contenedores principales:\n")

        selectors_to_try = [
            ('ol.ui-search-layout', 'Lista de búsqueda'),
            ('div.ui-search-result', 'Resultado individual'),
            ('li.ui-search-layout__item', 'Item de búsqueda'),
            ('div.shops__layout', 'Layout de tiendas'),
            ('article', 'Articles'),
            ('div[class*="item"]', 'Divs con "item"'),
            ('div[class*="product"]', 'Divs con "product"'),
            ('div[class*="card"]', 'Divs con "card"'),
        ]

        for selector, description in selectors_to_try:
            elements = soup.select(selector)
            if elements:
                print(f"   ✅ {description} ({selector}): {len(elements)} elementos encontrados")
            else:
                print(f"   ❌ {description} ({selector}): 0 elementos")

        # 2. Buscar clases que contengan "search", "item", "product"
        print("\n2️⃣ Clases CSS encontradas (primeras 50):\n")

        all_classes = set()
        for element in soup.find_all(class_=True):
            for cls in element.get('class', []):
                all_classes.add(cls)

        relevant_classes = [cls for cls in all_classes if any(
            keyword in cls.lower()
            for keyword in ['search', 'item', 'product', 'card', 'listing', 'result', 'vehicle', 'auto']
        )]

        for i, cls in enumerate(sorted(relevant_classes)[:50], 1):
            print(f"   {i}. {cls}")

        # 3. Buscar títulos de vehículos
        print("\n3️⃣ Buscando títulos de vehículos:\n")

        title_selectors = [
            'h2.ui-search-item__title',
            'h2.poly-component__title',
            'a.ui-search-link',
            'h2',
            'a[title]',
        ]

        for selector in title_selectors:
            titles = soup.select(selector)
            if titles:
                print(f"   ✅ {selector}: {len(titles)} títulos")
                if len(titles) > 0:
                    print(f"      Ejemplo: {titles[0].get_text(strip=True)[:80]}...")
            else:
                print(f"   ❌ {selector}: 0 títulos")

        # 4. Buscar precios
        print("\n4️⃣ Buscando precios:\n")

        price_selectors = [
            'span.andes-money-amount__fraction',
            'span.price-tag-fraction',
            'div.ui-search-price',
            'span[class*="price"]',
        ]

        for selector in price_selectors:
            prices = soup.select(selector)
            if prices:
                print(f"   ✅ {selector}: {len(prices)} precios")
                if len(prices) > 0:
                    print(f"      Ejemplo: {prices[0].get_text(strip=True)}")
            else:
                print(f"   ❌ {selector}: 0 precios")

        # 5. Verificar si hay CAPTCHA o bloqueo
        print("\n5️⃣ Verificando señales de bloqueo:\n")

        html_lower = html_text.lower()

        blocking_signals = {
            'captcha': 'captcha' in html_lower,
            'cloudflare': 'cloudflare' in html_lower,
            'robot': 'robot' in html_lower or 'bot' in html_lower,
            'forbidden': 'forbidden' in html_lower or 'acceso denegado' in html_lower,
        }

        for signal, detected in blocking_signals.items():
            status = "🚨 DETECTADO" if detected else "✅ No detectado"
            print(f"   {status}: {signal}")

        # 6. Mostrar primeros 2000 caracteres del HTML
        print("\n6️⃣ Primeros 2000 caracteres del HTML:\n")
        print("-"*80)
        print(html_text[:2000])
        print("-"*80)

        # 7. Buscar scripts de React/JavaScript
        print("\n7️⃣ Verificando si es una SPA (Single Page Application):\n")

        scripts = soup.find_all('script')
        print(f"   Total de scripts: {len(scripts)}")

        react_detected = any('react' in script.get('src', '').lower() for script in scripts if script.get('src'))
        print(f"   React detectado: {'🚨 SÍ (contenido dinámico!)' if react_detected else '✅ No'}")

        # 8. Buscar divs con id que puedan contener datos
        print("\n8️⃣ IDs relevantes encontrados:\n")

        ids = [elem.get('id') for elem in soup.find_all(id=True)]
        relevant_ids = [id for id in ids if any(
            keyword in id.lower()
            for keyword in ['root', 'app', 'main', 'search', 'content', 'results']
        )]

        for id in relevant_ids[:20]:
            print(f"   • {id}")

        print("\n" + "="*80)
        print("✅ Análisis completo")
        print("="*80)
        print("\n💡 PRÓXIMOS PASOS:")
        print("   1. Revisar mercadolibre_debug.html en tu navegador")
        print("   2. Usar DevTools (F12) para inspeccionar la estructura real")
        print("   3. Buscar el contenedor de items manualmente")
        print("   4. Si es SPA con React, necesitaremos Selenium/Playwright")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_mercadolibre_html()
