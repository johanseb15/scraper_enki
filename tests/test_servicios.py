from src.dominio.servicios import ServicioCanonico


def test_servicio_malware_tiene_identificador_estable():
    assert ServicioCanonico.MALWARE.value == "malware"
