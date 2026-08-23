# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

from datetime import date
from src.infraestructura.scrapers.compragamer_playwright_scraper import (
    CompraGamerPlaywrightScraper,
)


def main():
    print("Iniciando navegador headless para capturar API de Compra Gamer...")
    scraper = CompraGamerPlaywrightScraper()

    try:
        ofertas = scraper.obtener_ofertas(fecha_relevamiento=date.today())
        print(f"✅ Se extrajeron exitosamente {len(ofertas)} ofertas.\n")

        print("--- Muestra de los primeros 10 productos ---")
        for idx, dto in enumerate(ofertas[:10], start=1):
            print(f"{idx:02d}. [{dto.moneda} ${dto.precio:,.0f}] {dto.servicio_raw}")
            print(f"    Origen: {dto.empresa_nombre} ({dto.ciudad}, {dto.provincia})\n")

    except Exception as e:
        print(f"❌ Error al ejecutar Playwright Scraper: {e}")


if __name__ == "__main__":
    main()
