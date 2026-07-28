from fastapi import FastAPI, Depends, Query

from src.repositorio import RepositorioSQLite
from src.reporte import generar_resumen_servicio
from src.normalizacion import es_mismo_servicio


app = FastAPI(
    title="Enki API",
    version="0.1.0"
)


def obtener_repositorio():
    return RepositorioSQLite("enki.db")


@app.get("/servicios/{nombre_servicio}")
def consultar_servicio(
    nombre_servicio: str,
    provincia: str | None = Query(default=None),
    ciudad: str | None = Query(default=None),
    repo: RepositorioSQLite = Depends(obtener_repositorio)
):
    servicios = repo.obtener_todos()

    # Aplicamos filtros geográficos si existen
    servicios_filtrados = [
        servicio
        for servicio in servicios
        if es_mismo_servicio(
            servicio.servicio,
            nombre_servicio
        )
    ]

    if provincia:
        servicios_filtrados = [
            servicio
            for servicio in servicios_filtrados
            if servicio.provincia.lower() == provincia.lower()
        ]

    if ciudad:
        servicios_filtrados = [
            servicio
            for servicio in servicios_filtrados
            if servicio.ciudad.lower() == ciudad.lower()
        ]

    resumen = generar_resumen_servicio(
        servicios_filtrados,
        nombre_servicio
    )

    resumen["empresas"] = [
        {
            "empresa": servicio.empresa,
            "precio": servicio.precio_local
        }
        for servicio in servicios_filtrados
    ]

    resumen["ciudades"] = list(
        {
            servicio.ciudad
            for servicio in servicios_filtrados
        }
    )

    resumen["provincias"] = list(
        {
            servicio.provincia
            for servicio in servicios_filtrados
        }
    )

    return resumen