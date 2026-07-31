from unittest.mock import patch, MagicMock
import pytest
import requests
from src.downloader import descargar_html, DownloaderError  # DownloaderError todavía no existe

def test_descargar_html_devuelve_string_cuando_la_respuesta_es_exitosa():
    with patch("src.downloader.requests.get") as mock_get:
        mock_respuesta = MagicMock()
        mock_respuesta.status_code = 200
        mock_respuesta.text = "<html>Contenido</html>"
        mock_get.return_value = mock_respuesta

        resultado = descargar_html("https://ejemplo.com")
        
        assert resultado == "<html>Contenido</html>"
        # Verificamos que se use un timeout por defecto para evitar cuelgues infinitos
        args, kwargs = mock_get.call_args
        assert "timeout" in kwargs
        assert kwargs["timeout"] == 10

def test_descargar_html_lanza_downloader_error_en_timeout():
    with patch("src.downloader.requests.get") as mock_get:
        # Simulamos que requests lanza un ConnectTimeout
        mock_get.side_effect = requests.exceptions.Timeout("Timeout de conexión")

        with pytest.raises(DownloaderError) as exc_info:
            descargar_html("https://ejemplo.com")
        
        assert "Error al descargar desde https://ejemplo.com" in str(exc_info.value)

def test_descargar_html_lanza_downloader_error_en_error_http_4xx_o_5xx():
    with patch("src.downloader.requests.get") as mock_get:
        mock_respuesta = MagicMock()
        mock_respuesta.status_code = 404
        # raise_for_status() lanza HTTPError si el código es 4xx o 5xx
        mock_respuesta.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_respuesta

        with pytest.raises(DownloaderError):
            descargar_html("https://ejemplo.com")

def test_descargar_html_envia_user_agent_en_los_headers():
    with patch("src.downloader.requests.get") as mock_get:
        mock_respuesta = MagicMock()
        mock_respuesta.status_code = 200
        mock_get.return_value = mock_respuesta

        descargar_html("https://ejemplo.com")

        args, kwargs = mock_get.call_args
        assert "headers" in kwargs
        assert "User-Agent" in kwargs["headers"]
        assert "Mozilla" in kwargs["headers"]["User-Agent"]

def test_descargar_html_reintenta_en_caso_de_error_temporal_y_logra_conectar():
    with patch("src.downloader.requests.get") as mock_get:
        # Definimos efectos secundarios secuenciales: un fallo y luego un éxito
        mock_fallo = requests.exceptions.Timeout("Fallo de conexión temporal")
        mock_exito = MagicMock(status_code=200, text="<html>Contenido reintentado</html>")
        mock_get.side_effect = [mock_fallo, mock_exito]

        # Parcheamos time.sleep para que el test no se demore físicamente
        with patch("src.downloader.time.sleep") as mock_sleep:
            resultado = descargar_html("https://ejemplo.com")

            assert resultado == "<html>Contenido reintentado</html>"
            # Verificamos que se haya llamado exactamente 2 veces a la red
            assert mock_get.call_count == 2
            # Verificamos que esperó antes de reintentar
            mock_sleep.assert_called_once_with(2)
