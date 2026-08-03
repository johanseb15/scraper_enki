from datetime import date

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas
from src.dominio.servicios import ServicioCanonico


def test_pipeline_real_crea_oferta_y_persistencia(tmp_path):
    db_path = str(tmp_path / "pipeline_e2e.db")
    repositorio = RepositorioSQLiteOfertas(ruta_db=db_path)
    procesador = ProcesadorOfertas(repositorio=repositorio)

    dto = OfertaDTO(
        empresa_nombre="VIDA INFORMATICA S.R.L.",
        provincia="Cordoba",
        ciudad="Cba.",
        fuente="https://vidainformatica.com.ar",
        servicio_raw="Eliminación de virus y malware",
        precio=15000,
        moneda="ARS",
        fecha_relevamiento=date(2026, 2, 1),
    )

    oferta = procesador.procesar(dto)

    assert oferta is not None
    assert oferta.empresa.nombre == "Vida Informatica"
    assert oferta.servicio == ServicioCanonico.MALWARE
    assert oferta.precio.valor == 15000
    assert oferta.precio.moneda == "ARS"
    assert oferta.empresa.provincia == "Córdoba"
    assert oferta.empresa.ciudad == "Córdoba"

    ofertas_persistidas = repositorio.obtener_todas()
    assert len(ofertas_persistidas) == 1
    assert ofertas_persistidas[0].empresa.nombre == "Vida Informatica"
    assert ofertas_persistidas[0].servicio == ServicioCanonico.MALWARE
