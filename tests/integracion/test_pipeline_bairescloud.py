from datetime import date
from src.scrapers.baires_cloud import extraer_precios_bairescloud
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.aplicacion.oferta_factory import OfertaFactory
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas

HTML_MOCK = """
<table>
    <thead>
        <tr><th>Servicio</th><th>Equipo</th><th>Precio</th></tr>
    </thead>
    <tbody>
        <tr>
            <td>Formateo e Instalación SO</td>
            <td>Notebook / PC</td>
            <td>$ 25.000,00</td>
        </tr>
    </tbody>
</table>
"""

def test_pipeline_real_genera_y_persiste_oferta(tmp_path):
    # 1. Setup Base de datos de prueba
    db_file = str(tmp_path / "test_enki.db")
    repositorio = RepositorioSQLiteOfertas(ruta_db=db_file)
    procesador = ProcesadorOfertas(factory=OfertaFactory(), repositorio=repositorio)

    # 2. HTML -> Parser -> DTOs
    dtos = extraer_precios_bairescloud(HTML_MOCK, fecha_relevamiento=date.today())
    assert len(dtos) == 1

    # 3. DTO -> Procesador (Dominio) -> Persistencia
    ofertas_procesadas = procesador.ejecutar(dtos)
    assert len(ofertas_procesadas) == 1

    # 4. Verificación en el Repositorio
    guardadas = repositorio.obtener_todas()
    assert len(guardadas) == 1
    assert guardadas[0].empresa.nombre == "BairesCloud"
    assert guardadas[0].precio == 25000