from fastapi import FastAPI

app = FastAPI()


@app.get("/servicios/{nombre_servicio}")
def consultar_servicio(nombre_servicio: str):
    return {
        "servicio": nombre_servicio,
        "precio_minimo": 29816,
        "precio_promedio": 33862,
        "precio_maximo": 46000,
    }