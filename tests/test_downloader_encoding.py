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
