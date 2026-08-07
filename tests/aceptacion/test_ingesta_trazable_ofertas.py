from datetime import date

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.scrapers.vida_informatica_parser import (
    extraer_datos_vida_informatica,
)
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)


def test_extraer_una_fila_sin_perder_sus_precios_originales():
    html = """
    <table>
      <tr>
        <th>Servicio</th>
        <th>Equipo</th>
        <th>Freelance</th>
        <th>Local</th>
      </tr>
      <tr>
        <td>Eliminación de virus y malware</td>
        <td>PC</td>
        <td>$ 15.000</td>
        <td>$ 20.000</td>
      </tr>
    </table>
    """

    (dto,) = extraer_datos_vida_informatica(
        html,
        url_fuente="Vida Informática",
        fecha_relevamiento=date(2026, 8, 7),
    )

    campos_esperados = {
        "servicio_raw": "Eliminación de virus y malware",
        "equipo_raw": "PC",
        "precio_freelance_raw": "$ 15.000",
        "precio_local_raw": "$ 20.000",
        "fuente": "Vida Informática",
        "fecha_relevamiento": date(2026, 8, 7),
    }
    campos_obtenidos = {
        campo: getattr(dto, campo, "<campo ausente>")
        for campo in campos_esperados
    }

    assert campos_obtenidos == campos_esperados


def test_normalizar_el_servicio_sin_reemplazar_su_valor_original():
    dto = OfertaDTO(
        empresa_nombre="VIDA INFORMATICA S.R.L.",
        provincia="Cordoba",
        ciudad="Cba.",
        servicio_raw="Eliminación de virus y malware",
        precio=15000,
        moneda="ARS",
        fuente="Vida Informática",
        fecha_relevamiento=date(2026, 8, 7),
    )

    oferta = ProcesadorOfertas().procesar(dto)

    valores_esperados = {
        "servicio": ServicioCanonico.MALWARE,
        "servicio_raw": "Eliminación de virus y malware",
        "empresa": "Vida Informatica",
        "provincia": "Córdoba",
        "ciudad": "Córdoba",
    }
    valores_obtenidos = {
        "servicio": oferta.servicio,
        "servicio_raw": getattr(oferta, "servicio_raw", "<campo ausente>"),
        "empresa": oferta.empresa.nombre,
        "provincia": oferta.empresa.provincia,
        "ciudad": oferta.empresa.ciudad,
    }

    assert valores_obtenidos == valores_esperados


def test_representar_cada_modalidad_de_precio_como_una_observacion():
    dto = OfertaDTO(
        empresa_nombre="Vida Informatica",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio_raw="Eliminación de virus y malware",
        precio_freelance_raw="$ 15.000",
        precio_local_raw="$ 20.000",
        moneda="ARS",
        fuente="Vida Informática",
        fecha_relevamiento=date(2026, 8, 7),
    )

    observaciones = ProcesadorOfertas().crear_ofertas(dto)

    observaciones_esperadas = [
        {
            "modalidad": "freelance",
            "precio": 15000,
            "moneda": "ARS",
            "precio_raw": "$ 15.000",
            "servicio": ServicioCanonico.MALWARE,
            "servicio_raw": "Eliminación de virus y malware",
            "empresa": "Vida Informatica",
            "fuente": "Vida Informática",
            "fecha_relevamiento": date(2026, 8, 7),
        },
        {
            "modalidad": "local",
            "precio": 20000,
            "moneda": "ARS",
            "precio_raw": "$ 20.000",
            "servicio": ServicioCanonico.MALWARE,
            "servicio_raw": "Eliminación de virus y malware",
            "empresa": "Vida Informatica",
            "fuente": "Vida Informática",
            "fecha_relevamiento": date(2026, 8, 7),
        },
    ]
    observaciones_obtenidas = [
        {
            "modalidad": getattr(oferta, "modalidad", "<campo ausente>"),
            "precio": getattr(oferta.precio, "valor", oferta.precio),
            "moneda": oferta.moneda,
            "precio_raw": getattr(oferta, "precio_raw", "<campo ausente>"),
            "servicio": oferta.servicio,
            "servicio_raw": oferta.servicio_raw,
            "empresa": oferta.empresa.nombre,
            "fuente": oferta.empresa.fuente,
            "fecha_relevamiento": oferta.fecha_relevamiento,
        }
        for oferta in observaciones
    ]

    assert observaciones_obtenidas == observaciones_esperadas


def test_persistir_y_recuperar_ofertas_sin_cambiar_su_significado(tmp_path):
    dto = OfertaDTO(
        empresa_nombre="Vida Informatica",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio_raw="Eliminación de virus y malware",
        precio_freelance_raw="$ 15.000",
        precio_local_raw="$ 20.000",
        moneda="ARS",
        fuente="Vida Informática",
        fecha_relevamiento=date(2026, 8, 7),
    )
    ofertas = ProcesadorOfertas().crear_ofertas(dto)

    with RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "ofertas_trazables.db")
    ) as repositorio:
        for oferta in ofertas:
            repositorio.guardar(oferta)

        recuperadas = repositorio.obtener_todas()

    observaciones_esperadas = [
        {
            "precio": 15000,
            "modalidad": "freelance",
            "precio_raw": "$ 15.000",
            "servicio": ServicioCanonico.MALWARE,
            "servicio_raw": "Eliminación de virus y malware",
            "empresa": "Vida Informatica",
            "provincia": "Córdoba",
            "ciudad": "Córdoba",
            "fuente": "Vida Informática",
            "fecha_relevamiento": date(2026, 8, 7),
        },
        {
            "precio": 20000,
            "modalidad": "local",
            "precio_raw": "$ 20.000",
            "servicio": ServicioCanonico.MALWARE,
            "servicio_raw": "Eliminación de virus y malware",
            "empresa": "Vida Informatica",
            "provincia": "Córdoba",
            "ciudad": "Córdoba",
            "fuente": "Vida Informática",
            "fecha_relevamiento": date(2026, 8, 7),
        },
    ]
    observaciones_obtenidas = [
        {
            "precio": getattr(oferta.precio, "valor", oferta.precio),
            "modalidad": getattr(oferta, "modalidad", "<campo ausente>"),
            "precio_raw": getattr(oferta, "precio_raw", "<campo ausente>"),
            "servicio": oferta.servicio,
            "servicio_raw": getattr(oferta, "servicio_raw", "<campo ausente>"),
            "empresa": oferta.empresa.nombre,
            "provincia": oferta.empresa.provincia,
            "ciudad": getattr(oferta.empresa, "ciudad", "<campo ausente>"),
            "fuente": getattr(
                oferta.empresa,
                "fuente",
                getattr(oferta, "fuente", "<campo ausente>"),
            ),
            "fecha_relevamiento": getattr(
                oferta,
                "fecha_relevamiento",
                getattr(oferta, "fecha", "<campo ausente>"),
            ),
        }
        for oferta in recuperadas
    ]

    assert len(recuperadas) == 2
    assert observaciones_obtenidas == observaciones_esperadas
    assert all(observacion["precio"] != 0 for observacion in observaciones_obtenidas)
    assert all(
        valor not in {None, "", "<campo ausente>", "Desconocido"}
        for observacion in observaciones_obtenidas
        for valor in observacion.values()
    )
