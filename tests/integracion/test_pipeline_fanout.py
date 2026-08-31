from datetime import date

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.pipeline import PipelineOfertas
from src.reporte import generar_resumen_servicio
from src.infraestructura.scrapers.base import BaseScraper


class ScraperFilaConModalidades(BaseScraper):
    fuente = "Vida Informática"

    def obtener_servicios(self) -> list[OfertaDTO]:
        return [
            OfertaDTO(
                empresa_nombre="Vida Informatica",
                provincia="Córdoba",
                ciudad="Córdoba",
                servicio_raw="Eliminación de virus y malware",
                precio_freelance_raw="$ 15.000",
                precio_local_raw="$ 20.000",
                moneda="ARS",
                fuente=self.fuente,
                fecha_relevamiento=date(2026, 8, 8),
            )
        ]


def test_pipeline_persiste_una_observacion_por_modalidad(tmp_path):
    repositorio = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "fanout_pipeline.db")
    )
    procesador = ProcesadorOfertas(repositorio=repositorio)
    pipeline = PipelineOfertas(
        scrapers=[ScraperFilaConModalidades()],
        repositorio=repositorio,
        procesador=procesador,
    )

    ofertas = pipeline.ejecutar()
    persistidas = repositorio.obtener_todas()
    resumen = generar_resumen_servicio(
        persistidas,
        "Eliminación de malware",
    )

    assert len(ofertas) == 2
    assert len(persistidas) == 2
    assert [
        (oferta.modalidad, oferta.precio.valor, oferta.precio_raw)
        for oferta in persistidas
    ] == [
        ("freelance", 15000, "$ 15.000"),
        ("local", 20000, "$ 20.000"),
    ]
    assert all(
        oferta.servicio == ServicioCanonico.MALWARE
        and oferta.servicio_raw == "Eliminación de virus y malware"
        and oferta.empresa.nombre == "Vida Informatica"
        and oferta.empresa.provincia == "Córdoba"
        and oferta.empresa.ciudad == "Córdoba"
        and oferta.empresa.fuente == "Vida Informática"
        and oferta.fecha_relevamiento == date(2026, 8, 8)
        and oferta.moneda == "ARS"
        for oferta in persistidas
    )
    assert resumen["cantidad"] == 2
    assert resumen["precio_minimo"] == 15000
    assert resumen["precio_promedio"] == 17500
    assert resumen["precio_maximo"] == 20000
    assert pipeline.metricas.exitosos == ["ScraperFilaConModalidades"]
    assert pipeline.metricas.fallidos == []
    assert pipeline.metricas.total == 1
