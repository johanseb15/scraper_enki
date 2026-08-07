# src/aplicacion/procesador_ofertas.py

from src.modelos.precio import Precio

class ProcesadorOfertas:
    def __init__(self, normalizador_ubicaciones=None, normalizador_empresas=None, normalizador_servicios=None):
        self.normalizador_ubicaciones = normalizador_ubicaciones
        self.normalizador_empresas = normalizador_empresas
        self.normalizador_servicios = normalizador_servicios

    def procesar(self, dto):
        """
        Procesa un DTO de oferta, aplicando normalizaciones y estructurando los datos
        de manera compatible con los modelos y repositorios.
        """
        # Asegurar el manejo seguro del precio y su conversión a objeto Precio si es necesario
        precio_raw = getattr(dto, 'precio', None) or getattr(dto, 'precio_raw', 0.0)
        
        if isinstance(precio_raw, (int, float)):
            precio_obj = Precio(valor=float(precio_raw), moneda=getattr(dto, 'moneda', 'ARS'))
        elif isinstance(precio_raw, Precio):
            precio_obj = precio_raw
        else:
            # Intento básico de conversión si viene como string u otro formato
            try:
                valor_limpio = float(str(precio_raw).replace('$', '').replace(',', '').strip())
            except (ValueError, TypeError):
                valor_limpio = 0.0
            precio_obj = Precio(valor=valor_limpio, moneda=getattr(dto, 'moneda', 'ARS'))

        # Normalización de empresa / proveedor
        nombre_empresa = getattr(dto, 'empresa_nombre', None) or getattr(dto, 'empresa', 'Desconocida')
        if self.normalizador_empresas and hasattr(self.normalizador_empresas, 'normalizar'):
            nombre_empresa = self.normalizador_empresas.normalizar(nombre_empresa)

        # Normalización de servicio
        nombre_servicio = getattr(dto, 'servicio_raw', None) or getattr(dto, 'servicio', '')
        if self.normalizador_servicios and hasattr(self.normalizador_servicios, 'normalizar'):
            nombre_servicio = self.normalizador_servicios.normalizar(nombre_servicio)

        return {
            "empresa": nombre_empresa,
            "provincia": getattr(dto, 'provincia', ''),
            "ciudad": getattr(dto, 'ciudad', ''),
            "servicio": nombre_servicio,
            "precio": precio_obj,          # Expone el objeto Precio completo con su atributo .valor
            "valor_precio": precio_obj.valor, # Atenuante directo por si se requiere el float plano
            "moneda": precio_obj.moneda,
            "url": getattr(dto, 'url', ''),
            "fuente": getattr(dto, 'fuente', '')
        }

    def crear_oferta(self, dto, fecha_relevamiento=None):
        """
        Crea la estructura final de la oferta lista para ser persistida.
        """
        datos_procesados = self.procesar(dto)
        datos_procesados["fecha_relevamiento"] = fecha_relevamiento
        return datos_procesados