from src.dominio.modelos.servicio_dominio import ServicioDominio
from src.dominio.servicios import ServicioCanonico


class CatalogoServicios:
    def __init__(self, servicios: list[ServicioDominio] | None = None):
        self._servicios = servicios or self._cargar_catalogo_base()

    def obtener_por_canonico(self, canonico: ServicioCanonico) -> ServicioDominio | None:
        for s in self._servicios:
            if s.id == canonico:
                return s
        return None

    def resolver_desde_raw(self, texto_raw: str) -> ServicioDominio | None:
        if not texto_raw or not texto_raw.strip():
            return None
        for servicio in self._servicios:
            if servicio.coincide_con(texto_raw):
                return servicio
        return None

    def _cargar_catalogo_base(self) -> list[ServicioDominio]:
        return [
            ServicioDominio(
                id=ServicioCanonico.MALWARE,
                nombre_display="Eliminación de Malware y Virus",
                categoria="Seguridad IT",
                sinonimos=(
                    "malware",
                    "virus",
                    "spyware",
                    "desinfeccion",
                    "limpieza de virus",
                    "remocion de virus",
                    "antivirus",
                    "remocion de malware",
                ),
            ),
            ServicioDominio(
                id=ServicioCanonico.FORMATEO,
                nombre_display="Formateo e instalación de SO",
                categoria="Software",
                sinonimos=(
                    "formateo",
                    "instalación de so",
                    "instalacion de so",
                    "windows 11",
                ),
            ),
            ServicioDominio(
                id=ServicioCanonico.MANTENIMIENTO,
                nombre_display="Mantenimiento preventivo",
                categoria="Hardware",
                sinonimos=(
                    "mantenimiento",
                    "limpieza física",
                    "limpieza fisica",
                ),
            ),
            ServicioDominio(
                id=ServicioCanonico.SOPORTE_REDES,
                nombre_display="Diagnóstico y soporte de redes",
                categoria="Conectividad",
                sinonimos=(
                    "soporte de redes",
                    "redes",
                    "router",
                ),
            ),
            ServicioDominio(
                id=ServicioCanonico.SOPORTE_TECNICO,
                nombre_display="Soporte Técnico Informático",
                categoria="Soporte",
                sinonimos=(
                    "soporte",
                    "mantenimiento pc",
                    "reparacion de pc",
                    "asistencia tecnica",
                    "mesa de ayuda",
                    "helpdesk",
                ),
            ),
        ]
