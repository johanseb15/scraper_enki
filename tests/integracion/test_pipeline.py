from datetime import date
from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas
from src.pipeline import PipelineOfertas
from src.scrapers.base import BaseScraper


class FakeScraper(BaseScraper):
    def obtener_servicios(self) -> list[OfertaDTO]:
        return [
            OfertaDTO(
                empresa_nombre="Test IT Services",
                provincia="Córdoba",
                ciudad="Córdoba",
                fuente="https://test-it.com",
                servicio_raw="Formateo e Instalación de Sistema Operativo",
                precio=15000,
                moneda="ARS",
                fecha_relevamiento=date.today(),
            )
        ]


def test_pipeline_completo_con_base_temporal(tmp_path):
    # 1. Setup de base SQLite en directorio temporal
    db_file = str(tmp_path / "test_pipeline.db")
    repositorio = RepositorioSQLiteOfertas(ruta_db=db_file)
    scraper_fake = FakeScraper()

    # 2. Inicializar Pipeline con inyección de fakes/mocks
    pipeline = PipelineOfertas(
        scrapers=[scraper_fake],
        repositorio=repositorio,
    )

    # 3. Ejecutar pipeline
    ofertas_guardadas = pipeline.ejecutar()

    # 4. Validar persistencia real en la DB
    assert len(ofertas_guardadas) == 1
    
    todas_en_db = repositorio.obtener_todas()
    assert len(todas_en_db) == 1
    assert todas_en_db[0].empresa.nombre == "Test IT Services"
    assert todas_en_db[0].precio == 15000
    assert todas_en_db[0].empresa.provincia == "Córdoba"