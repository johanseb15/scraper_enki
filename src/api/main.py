from fastapi import FastAPI, Depends, Query

from src.configuracion_runtime import resolver_ruta_db_ofertas
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.reporte import generar_resumen_servicio
from src.normalizadores.normalizador_servicios import NormalizadorServicios

app = FastAPI(
    title="Enki API",
    version="0.1.0",
)


def obtener_repositorio() -> RepositorioSQLiteOfertas:
    return RepositorioSQLiteOfertas(
        ruta_db=resolver_ruta_db_ofertas()
    )


@app.get("/servicios/{nombre_servicio}")
def consultar_servicio(
    nombre_servicio: str,
    provincia: str | None = Query(default=None),
    ciudad: str | None = Query(default=None),
    repo: RepositorioSQLiteOfertas = Depends(obtener_repositorio),
):
    servicios = repo.obtener_todas()
    servicio_canonico = NormalizadorServicios().normalizar(nombre_servicio)

    servicios_filtrados = [
        servicio
        for servicio in servicios
        if servicio.servicio == servicio_canonico
    ]

    if provincia:
        servicios_filtrados = [
            servicio
            for servicio in servicios_filtrados
            if (servicio.empresa.provincia or "").lower() == provincia.lower()
        ]

    if ciudad:
        servicios_filtrados = [
            servicio
            for servicio in servicios_filtrados
            if (servicio.empresa.ciudad or "").lower() == ciudad.lower()
        ]

    resumen = generar_resumen_servicio(
        servicios_filtrados,
        nombre_servicio,
    )

    resumen["empresas"] = [
        {
            "empresa": servicio.empresa.nombre,
            "precio": servicio.precio,
        }
        for servicio in servicios_filtrados
    ]

    resumen["ciudades"] = sorted(
        {
            servicio.empresa.ciudad
            for servicio in servicios_filtrados
            if servicio.empresa.ciudad
        }
    )

    resumen["provincias"] = sorted(
        {
            servicio.empresa.provincia
            for servicio in servicios_filtrados
            if servicio.empresa.provincia
        }
    )

    return resumen
