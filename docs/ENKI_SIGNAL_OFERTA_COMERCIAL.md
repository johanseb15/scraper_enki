# ENKI Signal — Oferta comercial orientativa

**Marca:** Vyntrava Technologies  
**Producto en demostración:** ENKI Signal — monitor de precios con variantes, cantidades, stock y evidencia.  
**Estado:** MVP operativo reportado y vitrina estática pública. La integración con cada cliente requiere revisión y pruebas de aceptación.

## Problema que resuelve

El precio en e-commerce no es un único número por producto. Según la tienda puede depender de talle, color, capacidad, configuración, cantidad, disponibilidad y condiciones del pedido. Una planilla manual pierde esa información o confunde precios «desde» con precios confirmados.

## Servicio que puede contratarse

**Diagnóstico técnico:** identificar sitios de interés y productos representativos, validar condiciones de acceso, definir campos y criterios de aceptación.

**Implementación acotada:** configurar adaptadores por fuente autorizada, capturar las combinaciones acordadas, clasificar precios exactos/indicativos y stock disponible/desconocido, exportar CSV/JSON y mantener historial SQLite. Documentar operación y errores.

**Puesta en marcha:** instalar en el entorno acordado y verificar la ejecución en una muestra de productos del cliente. La programación recurrente es opcional y su frecuencia depende de las restricciones de las fuentes.

**Evolución opcional:** más fuentes/productos, reportes específicos y mantenimiento ante cambios de las webs. Se cotiza por separado.

## Qué entregamos y qué no prometemos

**Entregables a definir por contrato:** scripts/adaptadores acordados, configuración, instrucciones Windows, reportes estructurados, evidencia de aceptación y soporte de corrección pactado.

**No garantizamos:** compatibilidad universal, acceso a sitios que restringen la automatización, superación de bloqueos/CAPTCHA, precios definitivos cuando solo se publica «desde», ni stock cuando la página no informa disponibilidad.

**Propiedad intelectual:** las librerías y componentes preexistentes de Vyntrava requieren condiciones de licencia o entrega expresas por escrito; no se transfiere automáticamente todo Enki por una adaptación. Las condiciones finales se pactan antes de comenzar.

## Casos ilustrativos reportados (2026-10-24)

| Fuente | Observaciones | Escenario | Precisión |
| --- | ---: | --- | --- |
| Celavie — Top Deportivo ART 7403 | 15 | 5 variantes × cantidades 1, 2, 3. Precio unitario ARS 13.000; precio total y stock observados | Precio visible en página según el reporte |
| IdentiBasics — Cotizador | 6 | Remera/buzo × cantidades 3, 5, 10. Precios escalonados | Importes **«Desde»**, no cotizaciones finales; stock desconocido |

Estos datos son una reconstrucción de los resultados **comunicados por el ejecutor local**. Las evidencias HTML/SQLite/JSON originales permanecen en la notebook del desarrollador, no en esta rama. No son datos en tiempo real ni una auditoría independiente, y no hay afiliación con esos comercios.

## Cómo solicitar un diagnóstico

[**Abrir solicitud comercial pública en GitHub**](https://github.com/johanseb15/scraper_enki/issues/new?template=cotizacion.yml)

> **Privacidad:** GitHub Issues es público. No escribir datos confidenciales, personales, claves, accesos ni información de competidores no pública.

No se publican tarifas universales: el alcance, los sitios, los productos, la frecuencia y la modalidad de entrega determinan la cotización. Sin compromiso automático.

## Enlaces

- [Demo interactiva / sitio preparado para GitHub Pages](https://johanseb15.github.io/scraper_enki/)
- [Código público de la vitrina](https://github.com/johanseb15/scraper_enki/tree/gh-pages)
- [Repositorio del desarrollo Enki](https://github.com/johanseb15/scraper_enki)

© 2026 Vyntrava Technologies.
