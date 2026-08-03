from src.normalizacion import es_mismo_servicio, normalizar_texto
from src.normalizadores import es_mismo_servicio as es_mismo_servicio_normalizador
from src.normalizadores import normalizar_texto as normalizar_texto_normalizador


def test_normalizadores_exponen_las_utilidades_oficiales_de_normalizacion():
    assert normalizar_texto_normalizador(" ElimInación de Malware ") == normalizar_texto(" ElimInación de Malware ")
    assert es_mismo_servicio_normalizador("Eliminación de malware", "virus") is True


def test_normalizar_texto_elimina_acentos_y_espacios():
    texto = "  ElimInación de Malware  "
    assert normalizar_texto(texto) == "eliminacion de malware"


def test_es_mismo_servicio_reconoce_alias_y_subcadenas():
    assert es_mismo_servicio("Eliminación de malware", "virus") is True
    assert es_mismo_servicio("Mantenimiento preventivo", "mantenimiento") is True
