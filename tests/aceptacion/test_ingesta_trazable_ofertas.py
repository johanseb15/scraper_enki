from datetime import date

from fastapi.testclient import TestClient

from src.api.main import app, obtener_repositorio
from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.scrapers.vida_informatica_parser import (
    extraer_datos_vida_informatica,
)
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.pipeline import PipelineOfertas
from src.infraestructura.scrapers.base import BaseScraper


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


def test_consultar_estadisticas_del_servicio(tmp_path):
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
        ruta_db=str(tmp_path / "ofertas_consultables.db")
    ) as repositorio:
        for oferta in ofertas:
            repositorio.guardar(oferta)

        app.dependency_overrides[obtener_repositorio] = lambda: repositorio
        try:
            respuesta = TestClient(app).get(
                "/servicios/Eliminación de malware"
            )
        finally:
            app.dependency_overrides.clear()

    assert respuesta.status_code == 200

    datos = respuesta.json()
    assert datos["cantidad"] == 2
    assert datos["precio_minimo"] == 15000
    assert datos["precio_promedio"] == 17500
    assert datos["precio_maximo"] == 20000
    assert any(
        empresa["empresa"] == "Vida Informatica"
        for empresa in datos["empresas"]
    )
    assert "Córdoba" in datos["ciudades"]


def test_aislar_el_fallo_de_una_fuente(tmp_path, caplog):
    class ScraperQueFalla(BaseScraper):
        fuente = "Fuente Fallida"

        def obtener_servicios(self) -> list[OfertaDTO]:
            raise RuntimeError("fallo durante la descarga")

    class ScraperValido(BaseScraper):
        fuente = "Fuente Válida"

        def obtener_servicios(self) -> list[OfertaDTO]:
            return [
                OfertaDTO(
                    empresa_nombre="Vida Informatica",
                    provincia="Córdoba",
                    ciudad="Córdoba",
                    servicio_raw="Eliminación de malware",
                    precio=15000,
                    moneda="ARS",
                    fuente=self.fuente,
                    fecha_relevamiento=date(2026, 8, 8),
                )
            ]

    repositorio = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "pipeline_resiliente.db")
    )
    pipeline = PipelineOfertas(
        scrapers=[ScraperQueFalla(), ScraperValido()],
        repositorio=repositorio,
    )

    caplog.set_level("ERROR", logger="src.pipeline")
    ofertas_procesadas = pipeline.ejecutar()
    ofertas_persistidas = repositorio.obtener_todas()

    assert len(ofertas_procesadas) == 1
    assert len(ofertas_persistidas) == 1
    assert ofertas_persistidas[0].empresa.fuente == "Fuente Válida"
    assert ofertas_persistidas[0].precio == 15000
    assert all(
        oferta.empresa.fuente != "Fuente Fallida"
        for oferta in ofertas_persistidas
    )
    assert any(
        "Fuente Fallida" in registro.getMessage()
        and "fallo durante la descarga" in registro.getMessage()
        for registro in caplog.records
    )


def test_rechazar_una_fila_incompleta_de_forma_trazable(tmp_path):
    html = """
    <table>
      <tr>
        <th>Servicio</th>
        <th>Equipo</th>
        <th>Freelance</th>
        <th>Local</th>
      </tr>
      <tr>
        <td></td>
        <td>PC</td>
        <td>$ 15.000</td>
        <td>$ 20.000</td>
      </tr>
      <tr>
        <td>Eliminación de malware</td>
        <td>PC</td>
        <td>sin precio</td>
        <td>$ 0</td>
      </tr>
    </table>
    """
    fuente = "Vida Informática"
    rechazos: list[RechazoIngesta] = []

    dtos = extraer_datos_vida_informatica(
        html,
        url_fuente=fuente,
        fecha_relevamiento=date(2026, 8, 8),
        rechazos=rechazos,
    )
    repositorio = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "rechazos_trazables.db")
    )
    procesador = ProcesadorOfertas(repositorio=repositorio)
    ofertas_validas = [
        oferta
        for dto in dtos
        for oferta in procesador.crear_ofertas(dto)
    ]
    ofertas_persistidas = repositorio.obtener_todas()

    assert ofertas_validas == []
    assert ofertas_persistidas == []
    assert not any(oferta.precio == 0 for oferta in ofertas_persistidas)
    assert rechazos == [
        RechazoIngesta(fuente=fuente, razon="sin servicio"),
        RechazoIngesta(
            fuente=fuente,
            razon="sin ningún precio válido",
        ),
    ]
