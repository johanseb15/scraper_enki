from typing import Optional, Any
from enum import Enum

class ServicioCanonico(Enum):
    FIBRA_OPTICA = "fibra_optica"
    INTERNET_CABLE = "internet_cable"
    OTRO = "otro"

class NormalizadorOfertas:
    def __init__(self, mapeo_servicios: Optional[dict] = None):
        self.mapeo_servicios = mapeo_servicios or {}

    def determinar_servicio(self, raw_text: str) -> ServicioCanonico:
        """Determina el servicio canónico a partir del texto crudo."""
        texto_lower = raw_text.lower()
        
        for clave, servicio in self.mapeo_servicios.items():
            if clave.lower() in texto_lower:
                return servicio

        if "fibra" in texto_lower:
            return ServicioCanonico.FIBRA_OPTICA
        if "cable" in texto_lower or "coaxial" in texto_lower:
            return ServicioCanonico.INTERNET_CABLE
            
        return ServicioCanonico.OTRO

    def normalizar(self, oferta_raw: Any) -> Optional[Any]:
        """
        Normaliza una oferta. Si el servicio no es reconocido o se clasifica
        como OTRO, retorna None según el contrato esperado por las pruebas.
        """
        titulo = getattr(oferta_raw, 'titulo', '') or (oferta_raw.get('titulo', '') if isinstance(oferta_raw, dict) else '')
        servicio = self.determinar_servicio(titulo)

        # Contrato de negocio: si no coincide con ningún servicio canónico válido, descartar
        if servicio == ServicioCanonico.OTRO:
            return None

        # Si la oferta es válida, retorna el objeto normalizado
        if hasattr(oferta_raw, 'copiar_con'):
            return oferta_raw.copiar_con(servicio=servicio)

        if isinstance(oferta_raw, dict):
            oferta_copia = oferta_raw.copy()
            oferta_copia['servicio'] = servicio
            return oferta_copia

        return oferta_raw