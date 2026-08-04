import httpx
from bs4 import BeautifulSoup
import re

URL_OBJETIVO = "https://www.venex.com.ar"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-AR,es;q=0.9",
}

def inspeccionar_venex():
    print(f"🌍 Conectando a: {URL_OBJETIVO}")
    
    with httpx.Client(headers=headers, follow_redirects=True) as client:
        response = client.get(URL_OBJETIVO, timeout=15.0)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Buscamos elementos que contengan el símbolo '$' para ubicar el contenedor de precio
        elementos_precio = soup.find_all(text=re.compile(r'\$\s*\d+'))
        
        print(f"✅ Se encontraron {len(elementos_precio)} nodos de texto con precios ('$')\n")
        
        # Mostramos las clases CSS de los contenedores de precio encontrados
        clases_precio = set()
        for elem in elementos_precio[:10]:
            parent = elem.parent
            if parent and parent.get("class"):
                clases_precio.add(".".join(parent.get("class")))
        
        print(f"🎯 Clases CSS de precios detectadas en Venex: {list(clases_precio)}\n")
        
        # Intentamos extraer items agrupados (buscando tarjetas de producto)
        # En Venex las tarjetas suelen llamarse .product-box, .product-card, .item o similar
        tarjetas = soup.select(".product-box") or soup.select(".item") or soup.select(".card")
        
        if not tarjetas:
            # Si no detecta la tarjeta por clase genérica, buscamos los contenedores padres de los precios
            tarjetas = [p.find_parent("div") for p in elementos_precio[:10] if p.find_parent("div")]

        print(f"📊 MUESTRA DE DATOS CRUDOS ENCONTRADOS ({len(tarjetas)} tarjetas):\n")
        
        for i, tarjeta in enumerate(tarjetas[:5], 1):
            texto_limpio = " | ".join([line.strip() for line in tarjeta.get_text().split("\n") if line.strip()])
            print(f"Item {i}:")
            print(f"  ↳ Texto crudo: {texto_limpio[:120]}...\n")

if __name__ == "__main__":
    inspeccionar_venex()