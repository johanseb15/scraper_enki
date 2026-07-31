import pytest

from src.dominio.normalizador_empresas import NormalizadorEmpresas


class TestNormalizadorEmpresas:

    @pytest.mark.parametrize(
        "nombre_crudo, nombre_esperado",
        [
            ("Vida Informatica", "Vida Informatica"),
            ("Vida Informática", "Vida Informatica"),
            ("Vida Informatica SRL", "Vida Informatica"),
            ("Vida Informatica S.R.L.", "Vida Informatica"),
            ("  Vida   Informatica  S.A.  ", "Vida Informatica"),
            ("VIDA INFORMATICA srl", "Vida Informatica"),
            ("Soluciones IT S.A.S", "Soluciones It"),
        ]
    )
    def test_normaliza_nombres_de_empresa_eliminando_ruido_legal_y_tipografico(
        self,
        nombre_crudo,
        nombre_esperado
    ):
        # Arrange
        normalizador = NormalizadorEmpresas()

        # Act
        resultado = normalizador.normalizar(nombre_crudo)

        # Assert
        assert resultado == nombre_esperado