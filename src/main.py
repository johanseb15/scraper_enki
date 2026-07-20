from src.scrapers.vida_informatica import VidaInformaticaScraper
from src.repositorio import RepositorioSQLite
from src.reporte import generar_resumen_servicio
from src.presentacion import generar_reporte_texto


def ejecutar(ruta_db: str = "enki.db"):
    scraper = VidaInformaticaScraper()
    servicios = scraper.obtener_servicios()

    repo = RepositorioSQLite(ruta_db)
    for servicio in servicios:
        repo.guardar(servicio)

    datos = repo.obtener_todos()
    resumen = generar_resumen_servicio(datos, "Eliminación de malware")
    reporte = generar_reporte_texto(resumen)

    print(reporte)
    return reporte


if __name__ == "__main__":
    ejecutar()