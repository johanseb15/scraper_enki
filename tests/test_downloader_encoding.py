from src.infraestructura.downloader import descargar_html


class RespuestaSinCharset:
    status_code = 200
    encoding = "ISO-8859-1"
    apparent_encoding = "utf-8"
    content = "Diagnóstico en San Miguel de Tucumán – $35.000".encode("utf-8")

    @property
    def text(self):
        return self.content.decode(self.encoding)

    def raise_for_status(self):
        return None


def test_downloader_preserva_utf8_cuando_el_servidor_omite_charset(monkeypatch):
    respuesta = RespuestaSinCharset()
    monkeypatch.setattr(
        "src.infraestructura.downloader.requests.get",
        lambda *_args, **_kwargs: respuesta,
    )

    html = descargar_html("https://fuente.test")

    assert html == "Diagnóstico en San Miguel de Tucumán – $35.000"
    assert respuesta.encoding == "utf-8"

def test_downloader_no_desactiva_verificacion_tls(monkeypatch):
    respuesta = RespuestaSinCharset()
    llamadas = []

    def fake_get(*_args, **kwargs):
        llamadas.append(kwargs)
        return respuesta

    monkeypatch.setattr(
        "src.infraestructura.downloader.requests.get",
        fake_get,
    )

    descargar_html("https://fuente.test")

    assert llamadas
    assert llamadas[0].get("verify") is not False


def test_downloader_acepta_cliente_http_inyectado_sin_verify_false():
    respuesta = RespuestaSinCharset()
    llamadas = []

    class SessionFake:
        def get(self, *_args, **kwargs):
            llamadas.append(kwargs)
            return respuesta

    descargar_html("https://fuente.test", session=SessionFake())

    assert llamadas
    assert llamadas[0].get("verify") is not False
