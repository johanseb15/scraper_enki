from scripts import ingestar_todo
from src import main as main_modulo
from src.api import main as api_modulo
from src.metricas import MetricasEjecucion
from src.pipeline import PipelineOfertas


class _RepositorioCapturado:
    rutas = []

    def __init__(self, ruta_db):
        self.ruta_db = str(ruta_db)
        self.rutas.append(self.ruta_db)


class _PipelineSinTrabajo:
    def __init__(self, **kwargs):
        self.metricas = MetricasEjecucion()

    def ejecutar(self):
        return []


def _ruta_resuelta_por_main(monkeypatch, ruta_db=None):
    _RepositorioCapturado.rutas = []
    monkeypatch.setattr(
        main_modulo,
        "RepositorioSQLiteOfertas",
        _RepositorioCapturado,
    )
    monkeypatch.setattr(main_modulo, "PipelineOfertas", _PipelineSinTrabajo)
    monkeypatch.setattr(
        main_modulo,
        "generar_resumen_servicio",
        lambda ofertas, servicio: {},
    )
    monkeypatch.setattr(
        main_modulo,
        "generar_reporte_texto",
        lambda resumen: "reporte",
    )

    argumentos = {"scrapers": [object()]}
    if ruta_db is not None:
        argumentos["ruta_db"] = ruta_db
    main_modulo.ejecutar(**argumentos)

    return _RepositorioCapturado.rutas[0]


def _ruta_resuelta_por_ingesta(monkeypatch, ruta_db=None):
    _RepositorioCapturado.rutas = []
    monkeypatch.setattr(
        ingestar_todo,
        "RepositorioSQLiteOfertas",
        _RepositorioCapturado,
    )
    monkeypatch.setattr(ingestar_todo, "PipelineOfertas", _PipelineSinTrabajo)

    argumentos = {"scrapers": [object()]}
    if ruta_db is not None:
        argumentos["db_path"] = ruta_db
    ingestar_todo.ejecutar_ingesta(**argumentos)

    return _RepositorioCapturado.rutas[0]


def test_api_main_y_pipeline_comparten_default_runtime(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("ENKI_DB_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    ruta_api = api_modulo.obtener_repositorio().ruta_db
    ruta_main = _ruta_resuelta_por_main(monkeypatch)
    ruta_pipeline = PipelineOfertas().repositorio.ruta_db

    assert ruta_api == ruta_main == ruta_pipeline == "enki_ofertas.db"


def test_enki_db_path_aplica_a_api_main_y_pipeline(tmp_path, monkeypatch):
    ruta_configurada = str(tmp_path / "mercado_configurado.db")
    monkeypatch.setenv("ENKI_DB_PATH", ruta_configurada)

    ruta_api = api_modulo.obtener_repositorio().ruta_db
    ruta_main = _ruta_resuelta_por_main(monkeypatch)
    ruta_pipeline = PipelineOfertas().repositorio.ruta_db
    ruta_ingesta = _ruta_resuelta_por_ingesta(monkeypatch)

    assert (
        ruta_api
        == ruta_main
        == ruta_pipeline
        == ruta_ingesta
        == ruta_configurada
    )


def test_ruta_explicita_de_main_precede_al_entorno(tmp_path, monkeypatch):
    ruta_entorno = str(tmp_path / "entorno.db")
    ruta_explicita = str(tmp_path / "explicita.db")
    monkeypatch.setenv("ENKI_DB_PATH", ruta_entorno)

    ruta_main = _ruta_resuelta_por_main(monkeypatch, ruta_explicita)
    ruta_ingesta = _ruta_resuelta_por_ingesta(monkeypatch, ruta_explicita)

    assert ruta_main == ruta_explicita
    assert ruta_ingesta == ruta_explicita
