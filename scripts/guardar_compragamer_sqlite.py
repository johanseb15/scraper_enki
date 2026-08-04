from datetime import date
from src.infraestructura.persistencia.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.scrapers.compragamer_playwright_scraper import CompraGamerPlaywrightScraper


def main():
    print("Ejecutando scraper de Compra Gamer...")
    scraper = CompraGamerPlaywrightScraper()
    repo = RepositorioSQLiteOfertas()

    ofertas = scraper.obtener_ofertas(fecha_relevamiento=date.today())
    print(f"📦 Procesadas {len(ofertas)} ofertas.")

    guardadas = 0
    for oferta in ofertas:
        if repo.guardar(oferta):
            guardadas += 1

    print(f"💾 Se guardaron {guardadas} nuevas ofertas en la base de datos SQLite.")


if __name__ == "__main__":
    main()