import re
from typing import Dict, Tuple

from src.dominio.servicios import (
    ServicioCanonico,
    DetalleServicioCanonico,
    CATALOGO_SERVICIOS,
)
from src.normalizacion import normalizar_texto

# ==============================================================================
# MAPEO EXPANDIDO DE SERVICIOS Y CATEGORÍAS IT
# Estructura: 'clave_busqueda': (ServicioCanonico, categoria, subcategoria)
# ==============================================================================

MAPEO_IT_EXPANDIDO: Dict[str, Tuple[ServicioCanonico, str, str]] = {
    # --- SERVICIOS IT Y SOPORTE TÉCNICO ---
    "malware": (ServicioCanonico.MALWARE, "soporte_tecnico", ServicioCanonico.MALWARE.value),
    "virus": (ServicioCanonico.MALWARE, "soporte_tecnico", ServicioCanonico.MALWARE.value),
    "spyware": (ServicioCanonico.MALWARE, "soporte_tecnico", ServicioCanonico.MALWARE.value),
    "troyanos": (ServicioCanonico.MALWARE, "soporte_tecnico", ServicioCanonico.MALWARE.value),

    "formateo": (ServicioCanonico.FORMATEO, "soporte_tecnico", ServicioCanonico.FORMATEO.value),
    "instalacion de so": (ServicioCanonico.FORMATEO, "soporte_tecnico", ServicioCanonico.FORMATEO.value),
    "reinstalacion": (ServicioCanonico.FORMATEO, "soporte_tecnico", ServicioCanonico.FORMATEO.value),

    "mantenimiento": (ServicioCanonico.MANTENIMIENTO, "soporte_tecnico", ServicioCanonico.MANTENIMIENTO.value),
    "limpieza fisica": (ServicioCanonico.MANTENIMIENTO, "soporte_tecnico", ServicioCanonico.MANTENIMIENTO.value),
    "armado de pc": (ServicioCanonico.MANTENIMIENTO, "soporte_tecnico", ServicioCanonico.MANTENIMIENTO.value),

    "redes": (ServicioCanonico.SOPORTE_REDES, "soporte_tecnico", ServicioCanonico.SOPORTE_REDES.value),
    "router": (ServicioCanonico.SOPORTE_REDES, "soporte_tecnico", ServicioCanonico.SOPORTE_REDES.value),
    "soporte de redes": (ServicioCanonico.SOPORTE_REDES, "soporte_tecnico", ServicioCanonico.SOPORTE_REDES.value),
    "switch": (ServicioCanonico.SOPORTE_REDES, "soporte_tecnico", ServicioCanonico.SOPORTE_REDES.value),
    "cableado": (ServicioCanonico.SOPORTE_REDES, "soporte_tecnico", ServicioCanonico.SOPORTE_REDES.value),

    # --- SOFTWARE & LICENCIAMIENTO ---
    "windows 11": (ServicioCanonico.FORMATEO, "software", "licencias_so"),
    "windows 10": (ServicioCanonico.FORMATEO, "software", "licencias_so"),
    "windows server": (ServicioCanonico.DESCONOCIDO, "software", "licencias_servidores"),
    "licencia": (ServicioCanonico.DESCONOCIDO, "software", "licenciamiento"),
    "office 365": (ServicioCanonico.DESCONOCIDO, "software", "saas_ofimatica"),
    "microsoft 365": (ServicioCanonico.DESCONOCIDO, "software", "saas_ofimatica"),
    "antivirus": (ServicioCanonico.MALWARE, "software", "antivirus"),
    "kaspersky": (ServicioCanonico.MALWARE, "software", "antivirus"),
    "eset": (ServicioCanonico.MALWARE, "software", "antivirus"),

    # --- HARDWARE & COMPONENTES ---
    "procesador": (ServicioCanonico.DESCONOCIDO, "hardware", "procesadores"),
    "intel": (ServicioCanonico.DESCONOCIDO, "hardware", "procesadores"),
    "ryzen": (ServicioCanonico.DESCONOCIDO, "hardware", "procesadores"),
    "core i3": (ServicioCanonico.DESCONOCIDO, "hardware", "procesadores"),
    "core i5": (ServicioCanonico.DESCONOCIDO, "hardware", "procesadores"),
    "core i7": (ServicioCanonico.DESCONOCIDO, "hardware", "procesadores"),
    "core i9": (ServicioCanonico.DESCONOCIDO, "hardware", "procesadores"),

    "placa de video": (ServicioCanonico.DESCONOCIDO, "hardware", "placas_de_video"),
    "geforce": (ServicioCanonico.DESCONOCIDO, "hardware", "placas_de_video"),
    "radeon": (ServicioCanonico.DESCONOCIDO, "hardware", "placas_de_video"),
    "rtx": (ServicioCanonico.DESCONOCIDO, "hardware", "placas_de_video"),
    "gtx": (ServicioCanonico.DESCONOCIDO, "hardware", "placas_de_video"),
    "rx ": (ServicioCanonico.DESCONOCIDO, "hardware", "placas_de_video"),

    "memoria ram": (ServicioCanonico.DESCONOCIDO, "hardware", "memorias_ram"),
    "ddr4": (ServicioCanonico.DESCONOCIDO, "hardware", "memorias_ram"),
    "ddr5": (ServicioCanonico.DESCONOCIDO, "hardware", "memorias_ram"),

    "disco solido": (ServicioCanonico.DESCONOCIDO, "hardware", "almacenamiento"),
    "ssd": (ServicioCanonico.DESCONOCIDO, "hardware", "almacenamiento"),
    "nvme": (ServicioCanonico.DESCONOCIDO, "hardware", "almacenamiento"),
    "hdd": (ServicioCanonico.DESCONOCIDO, "hardware", "almacenamiento"),

    "motherboard": (ServicioCanonico.DESCONOCIDO, "hardware", "placas_madre"),
    "mother": (ServicioCanonico.DESCONOCIDO, "hardware", "placas_madre"),

    "fuente": (ServicioCanonico.DESCONOCIDO, "hardware", "fuentes"),
    "gabinete": (ServicioCanonico.DESCONOCIDO, "hardware", "gabinetes"),
    "cooler": (ServicioCanonico.DESCONOCIDO, "hardware", "refrigeracion"),
    "monitor": (ServicioCanonico.DESCONOCIDO, "hardware", "monitores"),
    "notebook": (ServicioCanonico.DESCONOCIDO, "hardware", "notebooks"),
    "laptop": (ServicioCanonico.DESCONOCIDO, "hardware", "notebooks"),
}


class NormalizadorServicios:

    def normalizar(self, texto: str) -> ServicioCanonico:
        texto_limpio = normalizar_texto(texto).lower()

        for clave, (servicio, _, _) in MAPEO_IT_EXPANDIDO.items():
            if clave in texto_limpio:
                return servicio

        return ServicioCanonico.DESCONOCIDO

    def normalizar_avanzado(self, texto: str) -> DetalleServicioCanonico:
        if not texto or not texto.strip():
            return DetalleServicioCanonico(
                categoria="desconocido",
                subcategoria="desconocido",
                nombre_normalizado="",
                confianza=0.0,
                regla_aplicada="input_vacio",
            )

        texto_limpio = normalizar_texto(texto).lower()

        for clave, (servicio, categoria, subcategoria) in MAPEO_IT_EXPANDIDO.items():
            if clave in texto_limpio:
                info = CATALOGO_SERVICIOS.get(servicio)
                
                # Garantiza coincidencia exacta con el enum de dominio para soporte técnico
                subcategoria_final = (
                    servicio.value 
                    if (servicio != ServicioCanonico.DESCONOCIDO and categoria == "soporte_tecnico") 
                    else subcategoria
                )

                nombre_norm = info.nombre if info else (
                    f"{subcategoria_final}: {texto.strip()}" if categoria != "soporte_tecnico" else servicio.value
                )

                return DetalleServicioCanonico(
                    categoria=categoria,
                    subcategoria=subcategoria_final,
                    nombre_normalizado=nombre_norm,
                    confianza=0.95,
                    regla_aplicada=f"alias_{clave}",
                )

        return DetalleServicioCanonico(
            categoria="desconocido",
            subcategoria="desconocido",
            nombre_normalizado=texto.strip(),
            confianza=0.0,
            regla_aplicada="fallback_original",
        )