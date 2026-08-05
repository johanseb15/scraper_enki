"""Normalizador de servicios e ítems IT."""

from typing import Union, Tuple
from src.modelos.servicio_canonico import ServicioCanonico
from src.scrapers.compragamer_scraper import OfertaDTO


def _get_canonico(nombre_enum: str, fallback: str) -> str:
    """Obtiene el valor del enum ServicioCanonico de forma segura."""
    if hasattr(ServicioCanonico, nombre_enum):
        return getattr(ServicioCanonico, nombre_enum).value
    return fallback


def _set_attr_safe(obj, name: str, val):
    """Asigna un atributo de manera segura sin fallar en dataclasses congeladas (frozen=True)."""
    try:
        setattr(obj, name, val)
    except Exception:
        try:
            object.__setattr__(obj, name, val)
        except Exception:
            try:
                obj.__dict__[name] = val
            except Exception:
                pass


class NormalizadorServicios:
    """Normaliza títulos y categorías de ofertas raw a categorías canónicas."""

    MAPPING_SUBKATS = {
        "malware": _get_canonico("MALWARE", "malware"),
        "virus": _get_canonico("MALWARE", "malware"),
        "antivirus": _get_canonico("MALWARE", "antivirus"),
        "limpieza": _get_canonico("LIMPIEZA", "limpieza"),
        "formateo": _get_canonico("FORMATEO", "formateo"),
        "formatear": _get_canonico("FORMATEO", "formateo"),
        "reinstalacion": _get_canonico("FORMATEO", "formateo"),
        "windows": _get_canonico("FORMATEO", "formateo"),
        "mantenimiento": _get_canonico("MANTENIMIENTO", "mantenimiento"),
        "preventivo": _get_canonico("MANTENIMIENTO", "mantenimiento"),
        "optimización": _get_canonico("MANTENIMIENTO", "mantenimiento"),
        "optimizacion": _get_canonico("MANTENIMIENTO", "mantenimiento"),
        "redes": _get_canonico("SOPORTE_REDES", _get_canonico("REDES", "soporte_redes")),
        "red": _get_canonico("SOPORTE_REDES", _get_canonico("REDES", "soporte_redes")),
        "router": _get_canonico("SOPORTE_REDES", _get_canonico("REDES", "soporte_redes")),
        "wifi": _get_canonico("SOPORTE_REDES", _get_canonico("REDES", "soporte_redes")),
        "cableado": _get_canonico("SOPORTE_REDES", _get_canonico("REDES", "soporte_redes")),
    }

    def _normalizar_texto(self, texto: str) -> Tuple[str, str]:
        texto_clean = texto.lower().strip()
        for kw, subcat in self.MAPPING_SUBKATS.items():
            if kw in texto_clean:
                return "Soporte Técnico", subcat

        if any(h in texto_clean for h in ["procesador", "placa de video", "motherboard", "ram", "ssd", "disco"]):
            subcat = texto_clean.replace(" ", "_")
            return "Hardware", subcat
        if any(s in texto_clean for s in ["licencia", "software"]):
            subcat = texto_clean.replace(" ", "_")
            return "Software", subcat

        return "General", "otros"

    def normalizar(self, entrada: Union[str, OfertaDTO]) -> Union[Tuple[str, str], OfertaDTO]:
        """Normaliza una cadena de texto o un DTO OfertaDTO."""
        if isinstance(entrada, str):
            return self._normalizar_texto(entrada)

        textos = []
        for attr in ["nombre", "titulo", "titulo_raw", "descripcion", "categoria_raw", "subcategoria_raw"]:
            val = getattr(entrada, attr, None)
            if val and isinstance(val, str):
                textos.append(val)

        texto_busqueda = " ".join(textos) if textos else str(entrada)
        cat_norm, subcat_norm = self._normalizar_texto(texto_busqueda)

        _set_attr_safe(entrada, "categoria_normalizada", cat_norm)
        _set_attr_safe(entrada, "subcategoria_normalizada", subcat_norm)

        nombre_existente = getattr(entrada, "nombre", None) or getattr(entrada, "titulo", None)
        if not nombre_existente:
            nombre_val = getattr(entrada, "titulo_raw", None) or str(entrada)
            _set_attr_safe(entrada, "nombre", nombre_val)
            _set_attr_safe(entrada, "titulo", nombre_val)

        return entrada