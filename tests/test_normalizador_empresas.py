from src.normalizadores.normalizador_empresas import NormalizadorEmpresas


class TestNormalizadorEmpresas:

    def test_normaliza_nombres_de_empresa_eliminando_ruido_legal_y_tipografico(
        self,
    ):
        normalizador = NormalizadorEmpresas()

        casos = [
            ("Vida Informatica", "Vida Informatica"),
            ("Vida Informática", "Vida Informatica"),
            ("Vida Informatica SRL", "Vida Informatica"),
            ("Vida Informatica S.R.L.", "Vida Informatica"),
            ("  Vida   Informatica  S.A.  ", "Vida Informatica"),
            ("VIDA INFORMATICA srl", "Vida Informatica"),
            ("Soluciones IT S.A.S", "Soluciones It"),
            ("Empresa Álvarez S.A.", "Empresa Alvarez"),
        ]

        for entrada, esperado in casos:
            assert normalizador.normalizar(entrada) == esperado

    def test_preserva_siglas_y_nombres_con_casing_importante(self):
        normalizador = NormalizadorEmpresas()

        casos = [
            ("BairesCloud", "BairesCloud"),
            ("Test IT Services", "Test IT Services"),
            ("Córdoba IT", "Córdoba IT"),
        ]

        for entrada, esperado in casos:
            assert normalizador.normalizar(entrada) == esperado
