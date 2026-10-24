"""ADEL ENKI-001: impedir que puntuación fusione identificadores comerciales."""
from src.normalizadores.normalizador_texto import normalizar_texto


def test_separador_no_fusiona_versiones_de_windows():
    assert normalizar_texto("Windows 10/11") == "windows 10 11"
    assert normalizar_texto("Windows 10/11") != normalizar_texto("Windows 1011")


def test_guion_no_fusiona_modelo_y_version():
    assert normalizar_texto("Servicio técnico - notebook") == "servicio tecnico notebook"


def test_normalizacion_antigua_sigue_valida():
    assert normalizar_texto("  ElimInación de Malware  ") == "eliminacion de malware"
