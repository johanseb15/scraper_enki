from src.presentacion import generar_reporte_texto


def test_generar_reporte_texto():

    resumen = {
        "servicio": "Eliminación de malware",
        "cantidad": 3,
        "precio_minimo": 28000,
        "precio_promedio": 30666,
        "precio_maximo": 34000,
    }

    reporte = generar_reporte_texto(resumen)

    assert "Eliminación de malware" in reporte
    assert "Registros relevados" in reporte
    assert "Registros relevados:\n3" in reporte
    assert "28000" in reporte
    assert "30666" in reporte
    assert "34000" in reporte