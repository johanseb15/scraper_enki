from datetime import datetime, timezone

from src.infraestructura.scrapers.generic_price_extractor import (
    EXTRACTOR_VERSION,
    extraer_observaciones_precio_genericas,
)


URL = "https://ejemplo.com/servicio-tecnico"
RETRIEVED_AT = datetime(
    2026, 8, 13, 10, 30, tzinfo=timezone.utc
)


def _extraer(html: str):
    return extraer_observaciones_precio_genericas(
        html,
        source="ejemplo",
        provider="Ejemplo Técnico",
        source_url=URL,
        raw_document_id=1,
        retrieved_at=RETRIEVED_AT,
    )


def test_extrae_precio_desde_tabla_html():
    html = """
    <html>
      <body>
        <table>
          <tr>
            <th>Servicio</th>
            <th>Precio</th>
          </tr>
          <tr>
            <td>Formateo e instalación de Windows</td>
            <td>$35.000</td>
          </tr>
        </table>
      </body>
    </html>
    """

    observaciones = _extraer(html)

    assert len(observaciones) == 1

    observacion = observaciones[0]

    assert (
        observacion.economic_object_raw
        == "Formateo e instalación de Windows"
    )
    assert observacion.price_raw == "$35.000"
    assert observacion.price_value == 35000
    assert observacion.currency_raw == "ARS"

    assert observacion.source == "ejemplo"
    assert observacion.provider_raw == "Ejemplo Técnico"
    assert observacion.source_url == URL
    assert observacion.raw_document_id == 1
    assert observacion.extractor_version == EXTRACTOR_VERSION


def test_extrae_precio_desde_card_html():
    html = """
    <html>
      <body>
        <div class="service-card">
          <h3>Limpieza y mantenimiento de notebook</h3>
          <p>Servicio en taller</p>
          <strong>$ 42.500,00</strong>
        </div>
      </body>
    </html>
    """

    observaciones = _extraer(html)

    assert len(observaciones) == 1

    observacion = observaciones[0]

    assert observacion.price_raw == "$ 42.500,00"
    assert observacion.price_value == 42500
    assert observacion.currency_raw == "ARS"

    assert "Limpieza y mantenimiento de notebook" in (
        observacion.economic_object_raw
    )


def test_no_convierte_consultar_en_precio():
    html = """
    <html>
      <body>
        <div>
          <span>Reparación motherboard</span>
          <strong>Consultar</strong>
        </div>
      </body>
    </html>
    """

    observaciones = _extraer(html)

    assert observaciones == []


def test_no_inventa_scope_semantico():
    html = """
    <html>
      <body>
        <div class="servicio">
          <h3>Instalación de sistema operativo</h3>
          <span>$50.000</span>
        </div>
      </body>
    </html>
    """

    observaciones = _extraer(html)

    assert len(observaciones) == 1

    observacion = observaciones[0]

    assert observacion.device_type_raw == "UNKNOWN"
    assert observacion.operating_system_raw == "UNKNOWN"
    assert observacion.backup_raw == "UNKNOWN"
    assert observacion.drivers_raw == "UNKNOWN"
    assert observacion.programs_raw == "UNKNOWN"
    assert observacion.license_raw == "UNKNOWN"
    assert observacion.modality_raw == "UNKNOWN"
    assert observacion.comparable_status == "INDETERMINATE"


def test_precio_argentino_con_coma_de_miles():
    html = """
    <div class="servicio">
      <span>Formateo PC</span>
      <strong>$40,000</strong>
    </div>
    """

    observaciones = _extraer(html)

    assert len(observaciones) == 1
    assert observaciones[0].price_raw == "$40,000"
    assert observaciones[0].price_value == 40000


def test_precio_argentino_con_punto_de_miles():
    html = """
    <div class="servicio">
      <span>Limpieza Notebook</span>
      <strong>$40.000</strong>
    </div>
    """

    observaciones = _extraer(html)

    assert len(observaciones) == 1
    assert observaciones[0].price_value == 40000


def test_precio_argentino_con_centavos():
    html = """
    <div class="servicio">
      <span>Instalación de Windows</span>
      <strong>$ 42.120,00</strong>
    </div>
    """

    observaciones = _extraer(html)

    assert len(observaciones) == 1
    assert observaciones[0].price_value == 42120


def test_no_duplica_precio_por_contenedores_ancestros():
    html = """
    <div class="pagina">
      <section class="servicio">
        <h3>Formateo</h3>
        <strong>$35.000</strong>
      </section>
    </div>
    """

    observaciones = _extraer(html)

    assert len(observaciones) == 1
    assert observaciones[0].price_value == 35000
    assert "Formateo" in observaciones[0].economic_object_raw


def test_contexto_no_es_toda_la_pagina():
    html = """
    <div class="pagina">
      <div class="servicio">
        <h3>Formateo e instalación de Windows</h3>
        <strong>$35.000</strong>
      </div>

      <div class="servicio">
        <h3>Limpieza de notebook</h3>
        <strong>$45.000</strong>
      </div>

      <div class="servicio">
        <h3>Eliminación de malware</h3>
        <strong>$30.000</strong>
      </div>
    </div>
    """

    observaciones = _extraer(html)

    assert len(observaciones) == 3

    primera = next(
        observacion
        for observacion in observaciones
        if observacion.price_value == 35000
    )

    assert (
        primera.economic_object_raw
        == "Formateo e instalación de Windows"
    )
    assert "Limpieza de notebook" not in (
        primera.economic_object_raw
    )
    assert "Eliminación de malware" not in (
        primera.economic_object_raw
    )

def test_no_acepta_precio_partido_por_markup_como_escalar_menor():
    html = '<div class="servicio"><h3>Mantenimiento preventivo</h3><div class="precio"><strong>$45</strong><span>.000</span></div></div>'

    observaciones = _extraer(html)

    assert observaciones == []

