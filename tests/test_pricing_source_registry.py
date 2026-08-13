from pathlib import Path

from src.aplicacion.pricing_source_registry import (
    cargar_fuentes_pricing_csv,
)


def test_carga_fuentes_desde_csv(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        "\n".join(
            [
                "source,provider,url,province,city",
                (
                    "tecnico_cordoba,Técnico Córdoba,"
                    "https://cordoba.example/precios,"
                    "Córdoba,Córdoba"
                ),
                (
                    "tecnico_mendoza,Técnico Mendoza,"
                    "https://mendoza.example/precios,"
                    "Mendoza,Mendoza"
                ),
            ]
        ),
        encoding="utf-8",
    )

    fuentes = cargar_fuentes_pricing_csv(
        archivo
    )

    assert len(fuentes) == 2

    assert fuentes[0].source == "tecnico_cordoba"
    assert fuentes[0].provider == "Técnico Córdoba"
    assert fuentes[0].url == "https://cordoba.example/precios"
    assert fuentes[0].province == "Córdoba"
    assert fuentes[0].city == "Córdoba"

    assert fuentes[1].source == "tecnico_mendoza"


def test_ignora_filas_vacias(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        (
            "source,provider,url,province,city\n"
            "fuente_a,Proveedor A,"
            "https://a.example/precios,"
            "Córdoba,Córdoba\n"
            "\n"
        ),
        encoding="utf-8",
    )

    fuentes = cargar_fuentes_pricing_csv(
        archivo
    )

    assert len(fuentes) == 1


def test_rechaza_campos_obligatorios_faltantes(tmp_path):
    archivo = tmp_path / "sources.csv"

    archivo.write_text(
        (
            "source,provider,url,province,city\n"
            ",Proveedor A,"
            "https://a.example/precios,"
            "Córdoba,Córdoba\n"
        ),
        encoding="utf-8",
    )

    try:
        cargar_fuentes_pricing_csv(
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
        (
            "source,provider,url,province,city\n"
            "fuente_a,Proveedor A,"
            "https://a.example/precios,"
            "Córdoba,Córdoba\n"
            "fuente_a,Proveedor B,"
            "https://b.example/precios,"
            "Mendoza,Mendoza\n"
        ),
        encoding="utf-8",
    )

    try:
        cargar_fuentes_pricing_csv(
            archivo
        )
    except ValueError as exc:
        assert "fuente_a" in str(exc)
    else:
        raise AssertionError(
            "Se esperaba ValueError"
        )