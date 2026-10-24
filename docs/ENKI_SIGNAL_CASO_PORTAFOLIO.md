# Vyntrava Technologies | Caso ENKI Signal

**Tipo:** caso demostrativo de inteligencia comercial.  
**Estado:** demostración pública con datos de referencia estáticos; no es un sistema de monitoreo en vivo desde la página.  
**Propósito del caso:** demostrar preservación de contexto comercial, variantes, cantidad, stock y semántica del precio.

## Problema

Comparar comercios por un único precio puede producir conclusiones erróneas si se omiten variantes, cantidades, precios «desde» o disponibilidad. ENKI busca conservar las dimensiones que hacen comparable una observación.

## Qué se puede mostrar

- **Celavie — Top Deportivo:** 15 observaciones reportadas (5 variantes x 3 cantidades). Precio exacto visible por referencia.
- **IdentiBasics — Cotizador:** 6 observaciones reportadas (2 tipos de prenda x 3 cantidades). Importe indicativo «Desde», no cotización final.
- **Total:** 21 registros de muestra reportados para dos fuentes.
- **Interacción pública:** explorar combinaciones, comparar importes indicativos y exportar muestras CSV/JSON desde la vitrina.

**Límite de evidencia:** las 21 observaciones proceden de una corrida local comunicada por su ejecutor; los artefactos originales no están incluidos en esta documentación. No constituyen auditoría independiente, acceso a datos en tiempo real ni prueba de vinculación comercial con los comercios.

## Stack y arquitectura

Núcleo de Enki en Python; backend FastAPI; evidencias y persistencia SQLite; adaptadores de captura y normalización; vitrina estática en GitHub Pages. La web de demostración no requiere ni ejecuta el scraper original. El motor de decisiones económicas es una capacidad distinta del caso e-commerce.

## Qué podría contratar una empresa

Un diagnóstico de fuentes autorizadas, definición de productos/variantes, prueba de captura reproducible, exportación estructurada e instalación documentada. La oferta requiere validación de alcance, frecuencia, permisos y aceptación con datos del cliente. [Detalle orientativo](ENKI_SIGNAL_OFERTA_COMERCIAL.md).

## Métricas y verificación

| Métrica | Estado conocido |
| --- | --- |
| Casos de muestra publicados | 2 |
| Observaciones comunicadas en la demo | 21 |
| Precios exactos en la muestra | 15 |
| Importes indicativos «Desde» | 6 |
| Captura en vivo desde GitHub Pages | No |
| Validación independiente de evidencias originales | Pendiente |
| Número de clientes pagos atribuidos al caso | No verificado |
| Conversión a contacto comercial | Sin instrumentación verificada |

**Próximo gate comercial:** un piloto con una empresa, contrato de campos y alcance, evidencia reproducible y un resultado que permita calcular tiempo ahorrado, precisión y costo de mantenimiento. No publicar métricas comerciales sin medición.

[Explorar la demo](https://johanseb15.github.io/scraper_enki/) · [Solicitar evaluación (formulario público)](https://github.com/johanseb15/scraper_enki/issues/new?template=cotizacion.yml)

> La solicitud de GitHub Issues es pública. No incluir datos sensibles ni accesos.
