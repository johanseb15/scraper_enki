class DownloaderError(Exception):
    """Excepción para errores en la descarga HTML."""
    pass


def descargar_html(url: str) -> str:
    try:
        from src.infraestructura.downloader import descargar_html as _descargar
        return _descargar(url)
    except ImportError:
        raise DownloaderError(f"Error al intentar descargar {url}")