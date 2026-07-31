import time
import requests

class DownloaderError(Exception):
    """Excepción personalizada para aislar los errores de infraestructura de red."""
    pass

def descargar_html(url: str) -> str:
    """
    Descarga el contenido HTML de una URL de forma segura.
    Garantiza el uso de timeouts, agentes de usuario estándar, reintentos
    ante fallas temporales y encapsula excepciones de red.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        )
    }
    
    max_intentos = 3
    segundos_espera = 2
    
    for intento in range(max_intentos):
        try:
            respuesta = requests.get(url, headers=headers, timeout=10)
            respuesta.raise_for_status()
            return respuesta.text
            
        except requests.exceptions.RequestException as e:
            # Si ya agotamos todos los intentos, lanzamos la excepción de dominio
            if intento == max_intentos - 1:
                raise DownloaderError(f"Error al descargar desde {url} tras {max_intentos} intentos: {e}") from e
            
            # Si quedan intentos, esperamos el tiempo de backoff antes de volver a empezar
            time.sleep(segundos_espera)
