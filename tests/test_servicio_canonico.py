from src.modelos.servicio_canonico import ServicioCanonico


def test_servicio_canonico_valores_validos():
    assert isinstance(ServicioCanonico.INTERNET.value, str)
    assert ServicioCanonico.INTERNET.value == "Internet"


def test_todos_los_valores_son_strings():
    for miembro in ServicioCanonico:
        assert isinstance(miembro.value, str)