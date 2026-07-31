def generar_reporte_texto(resumen: dict) -> str:
    precios_por_empresa = resumen.get("precios_por_empresa", {})

    detalle_empresas = "\n".join(
        f"{empresa}: {precio}"
        for empresa, precio in precios_por_empresa.items()
    )

    reporte = f"""
==========================================
ÍNDICE DE PRECIOS - ENKI
==========================================

Servicio: {resumen["servicio"]}

Registros relevados:
{resumen["cantidad"]}

Precio mínimo: {resumen["precio_minimo"]}

Precio promedio: {resumen["precio_promedio"]}

Precio máximo: {resumen["precio_maximo"]}
"""

    if detalle_empresas:
        reporte += f"""

Precios por empresa:
{detalle_empresas}
"""

    return reporte
