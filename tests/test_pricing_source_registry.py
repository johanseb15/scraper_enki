from src.aplicacion.pricing_source_registry import (
    cargar_fuentes_pricing_csv,
    cargar_registry_pricing_csv,
    seleccionar_fuentes_pricing,
)


HEADER = (
    "source,provider,url,province,city,"
    "discovery_status,price_visibility,"
    "source_kind,notes"
)


def test_carga_registry_v2_completo(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        "\n".join(
            [
                HEADER,
                (
                    "tecnico_cordoba,Técnico Córdoba,"
                    "https://cordoba.example/precios,"
                    "Córdoba,Córdoba,"
                    "VERIFIED,PRICE_VISIBLE,PROVIDER,"
                    "Tarifario público"
                ),
                (
                    "tecnico_mendoza,Técnico Mendoza,"
                    "https://mendoza.example/servicios,"
                    "Mendoza,Mendoza,"
                    "DISCOVERED,UNKNOWN,PROVIDER,"
                    "Pendiente de verificar"
                ),
            ]
        ),
        encoding="utf-8",
    )

    fuentes = cargar_registry_pricing_csv(
        archivo
    )

    assert len(fuentes) == 2

    assert fuentes[0].source == "tecnico_cordoba"
    assert fuentes[0].provider == "Técnico Córdoba"
    assert fuentes[0].province == "Córdoba"
    assert fuentes[0].discovery_status == "VERIFIED"
    assert fuentes[0].price_visibility == "PRICE_VISIBLE"
    assert fuentes[0].source_kind == "PROVIDER"
    assert fuentes[0].notes == "Tarifario público"
    assert fuentes[0].acquisition_eligible is True

    assert fuentes[1].acquisition_eligible is False


def test_batch_recibe_solo_proveedores_verificados_con_precio(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        "\n".join(
            [
                HEADER,
                (
                    "visible,Visible,"
                    "https://visible.example/precios,"
                    "Córdoba,Córdoba,"
                    "VERIFIED,PRICE_VISIBLE,PROVIDER,"
                ),
                (
                    "sin_precio,Sin Precio,"
                    "https://noprice.example,"
                    "Córdoba,Córdoba,"
                    "VERIFIED,NO_PRICE_VISIBLE,PROVIDER,"
                ),
                (
                    "agregador,Agregador,"
                    "https://aggregator.example,"
                    "Córdoba,Córdoba,"
                    "VERIFIED,PRICE_VISIBLE,AGGREGATOR,"
                ),
                (
                    "descubierto,Descubierto,"
                    "https://discovered.example,"
                    "Córdoba,Córdoba,"
                    "DISCOVERED,PRICE_VISIBLE,PROVIDER,"
                ),
            ]
        ),
        encoding="utf-8",
    )

    fuentes = cargar_fuentes_pricing_csv(
        archivo
    )

    assert len(fuentes) == 1
    assert fuentes[0].source == "visible"


def test_seleccion_preserva_contrato_fuente_pricing(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        (
            HEADER
            + "\n"
            + "fuente_a,Proveedor A,"
            + "https://a.example/precios,"
            + "Santa Fe,Rosario,"
            + "VERIFIED,PRICE_VISIBLE,PROVIDER,"
            + "Precio visible"
        ),
        encoding="utf-8",
    )

    registry = cargar_registry_pricing_csv(
        archivo
    )
    pricing = seleccionar_fuentes_pricing(
        registry
    )

    assert len(pricing) == 1
    assert pricing[0].source == "fuente_a"
    assert pricing[0].provider == "Proveedor A"
    assert pricing[0].url == "https://a.example/precios"
    assert pricing[0].province == "Santa Fe"
    assert pricing[0].city == "Rosario"


def test_ignora_filas_vacias(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        (
            HEADER
            + "\n"
            + "fuente_a,Proveedor A,"
            + "https://a.example/precios,"
            + "Córdoba,Córdoba,"
            + "VERIFIED,PRICE_VISIBLE,PROVIDER,"
            + "\n\n"
        ),
        encoding="utf-8",
    )

    fuentes = cargar_registry_pricing_csv(
        archivo
    )

    assert len(fuentes) == 1


def test_rechaza_campos_obligatorios_faltantes(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        (
            HEADER
            + "\n"
            + ",Proveedor A,"
            + "https://a.example/precios,"
            + "Córdoba,Córdoba,"
            + "VERIFIED,PRICE_VISIBLE,PROVIDER,"
        ),
        encoding="utf-8",
    )

    try:
        cargar_registry_pricing_csv(
            archivo
        )
    except ValueError as exc:
        assert "source" in str(exc)
    else:
        raise AssertionError(
            "Se esperaba ValueError"
        )


def test_source_debe_ser_unico(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        "\n".join(
            [
                HEADER,
                (
                    "fuente_a,Proveedor A,"
                    "https://a.example/precios,"
                    "Córdoba,Córdoba,"
                    "VERIFIED,PRICE_VISIBLE,PROVIDER,"
                ),
                (
                    "fuente_a,Proveedor B,"
                    "https://b.example/precios,"
                    "Mendoza,Mendoza,"
                    "VERIFIED,PRICE_VISIBLE,PROVIDER,"
                ),
            ]
        ),
        encoding="utf-8",
    )

    try:
        cargar_registry_pricing_csv(
            archivo
        )
    except ValueError as exc:
        assert "fuente_a" in str(exc)
    else:
        raise AssertionError(
            "Se esperaba ValueError"
        )


def test_rechaza_estado_desconocido(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        (
            HEADER
            + "\n"
            + "fuente_a,Proveedor A,"
            + "https://a.example/precios,"
            + "Córdoba,Córdoba,"
            + "INVENTADO,PRICE_VISIBLE,PROVIDER,"
        ),
        encoding="utf-8",
    )

    try:
        cargar_registry_pricing_csv(
            archivo
        )
    except ValueError as exc:
        assert "discovery_status" in str(exc)
        assert "INVENTADO" in str(exc)
    else:
        raise AssertionError(
            "Se esperaba ValueError"
        )


def test_rechaza_source_kind_desconocido(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        (
            HEADER
            + "\n"
            + "fuente_a,Proveedor A,"
            + "https://a.example/precios,"
            + "Córdoba,Córdoba,"
            + "VERIFIED,PRICE_VISIBLE,OTRO,"
        ),
        encoding="utf-8",
    )

    try:
        cargar_registry_pricing_csv(
            archivo
        )
    except ValueError as exc:
        assert "source_kind" in str(exc)
        assert "OTRO" in str(exc)
    else:
        raise AssertionError(
            "Se esperaba ValueError"
        )
