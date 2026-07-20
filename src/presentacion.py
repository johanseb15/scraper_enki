def generar_reporte_texto(resumen: dict) -> str:
    return f"""
==========================================
ÍNDICE DE PRECIOS - ENKI
==========================================

Servicio: {resumen["servicio"]}

f"Registros relevados:\n{resumen['cantidad']}\n\n"

Precio mínimo: {resumen["precio_minimo"]}

Precio promedio: {resumen["precio_promedio"]}

Precio máximo: {resumen["precio_maximo"]}
"""