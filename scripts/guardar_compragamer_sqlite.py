"""Entry point compatible para la ingesta de ofertas de CompraGamer."""

from scripts.ingestar_todo import ejecutar_ingesta


def main(db_path: str = "enki.db") -> int:
    guardadas = ejecutar_ingesta(db_path=db_path)
    print(f"Se guardaron {guardadas} ofertas en la base de datos SQLite.")
    return guardadas


if __name__ == "__main__":
    main()
