from fastapi import FastAPI, Depends

from src.repositorio import RepositorioSQLite
from src.reporte import generar_resumen_servicio


app = FastAPI(
    title="Enki API",
    version="0.1.0"
)


def obtener_repositorio():
    return RepositorioSQLite("enki.db")


@app.get("/servicios/{nombre_servicio}")
def consultar_servicio(
    nombre_servicio: str,
    repo: RepositorioSQLite = Depends(obtener_repositorio)
):
    servicios = repo.obtener_todos()

    resumen = generar_resumen_servicio(
        servicios,
        nombre_servicio
    )

    servicios_filtrados = [
        servicio
        for servicio in servicios
        if servicio.servicio.lower() == nombre_servicio.lower()
    ]

    resumen["empresas"] = [
        {
            "empresa": servicio.empresa,
            "precio": servicio.precio_local
        }
        for servicio in servicios_filtrados
    ]

    return resumen