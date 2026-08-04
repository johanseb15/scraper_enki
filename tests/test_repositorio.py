from datetime import date
import pytest
from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.modelos.servicio_precio import ServicioPrecio
from src.repositorio import RepositorioSQLite


def test_guardar_y_obtener_oferta_dto(repositorio_db):
    dto = OfertaDTO(
        servicio_raw="Soporte Técnico",
        precio=15000,
        fecha_relevamiento=date(2026, 4, 10),
        empresa_nombre="TechCorp",
        provincia="Córdoba",
        ciudad="Córdoba",
        fuente="WebScraper",
        moneda="ARS"
    )

    repositorio_db.guardar(dto)
    resultados = repositorio_db.obtener_todos()

    assert len(resultados) == 1
    assert resultados[0].empresa == "TechCorp"
    assert resultados[0].precio_freelance == 15000
    assert resultados[0].fecha_relevamiento == date(2026, 4, 10)


def test_guardar_y_obtener_servicio_precio(repositorio_db):
    servicio = ServicioPrecio(
        empresa="DataNet",
        provincia="Córdoba",
        ciudad="Villa María",
        servicio="Instalación de Redes",
        equipo="Router Cisco",
        precio_freelance=25000,
        precio_local=30000,
        moneda="ARS",
        fecha_relevamiento=date(2026, 5, 12),
        fuente="Manual"
    )

    repositorio_db.guardar(servicio)
    resultados = repositorio_db.obtener_todos()

    assert len(resultados) == 1
    assert resultados[0].servicio == "Instalación de Redes"
    assert resultados[0].precio_local == 30000


def test_uso_de_context_manager():
    with RepositorioSQLite(":memory:") as repo:
        assert repo.conexion is not None
    assert repo.conexion is None


def test_excepcion_al_operar_con_conexion_cerrada(repositorio_db):
    repositorio_db.cerrar()
    with pytest.raises(RuntimeError, match="cerrada"):
        repositorio_db.obtener_todos()