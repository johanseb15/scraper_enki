import json
from types import SimpleNamespace

from scripts.run_specific_scrapers_live import (
    construir_grupos_scrapers,
    ejecutar_scrapers_especificos,
)


def test_catalogo_activa_todos_los_scrapers_especificos_sin_mezclar_mercados():
    grupos = construir_grupos_scrapers()

    assert [
        scraper.__class__.__name__
        for scraper in grupos["local_services"]
    ] == [
        "BairesCloudScraper",
        "VidaInformaticaScraper",
        "CiroWhiteScraper",
        "DMRScraper",
        "ReedScraper",
    ]
    assert [
        scraper.__class__.__name__
        for scraper in grupos["reference_products"]
    ] == [
        "VenexScraper",
        "CompraGamerScraper",
    ]


def test_runner_persiste_grupos_separados_y_declara_limite_de_admision(
    tmp_path,
):
    repositorios = []

    class FakeRepository:
        def __init__(self, path):
            self.ruta_db = path
            repositorios.append(path)

    class FakePipeline:
        def __init__(self, *, scrapers, repositorio):
            self.scrapers = scrapers
            self.repositorio = repositorio
            self.metricas = SimpleNamespace(exitosos=[], fallidos=[])

        def ejecutar(self):
            nombres = [item.__class__.__name__ for item in self.scrapers]
            self.metricas.exitosos = nombres[:-1]
            self.metricas.fallidos = nombres[-1:]
            return [object()] * len(self.metricas.exitosos)

    run_dir = ejecutar_scrapers_especificos(
        out_dir=tmp_path,
        run_id="run-test",
        pipeline_type=FakePipeline,
        repository_type=FakeRepository,
    )

    manifest = json.loads(
        (run_dir / "specific_scraper_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["schema_version"] == "specific-live-scrapers-v1"
    assert manifest["diagnostic_only"] is True
    assert "RAW" in manifest["admission_reason"]
    assert set(manifest["groups"]) == {
        "local_services",
        "reference_products",
    }
    assert manifest["groups"]["local_services"]["sources_attempted"] == 5
    assert manifest["groups"]["reference_products"]["sources_attempted"] == 2
    assert repositorios == [
        run_dir / "local_services.db",
        run_dir / "reference_products.db",
    ]
