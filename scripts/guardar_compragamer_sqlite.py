"""Entry point compatible para la ingesta de ofertas de CompraGamer."""

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

from scripts.ingestar_todo import ejecutar_ingesta


def main(db_path: str | None = None) -> int:
    guardadas = ejecutar_ingesta(db_path=db_path)
    print(f"Se guardaron {guardadas} ofertas en la base de datos SQLite.")
    return guardadas


if __name__ == "__main__":
    main()
