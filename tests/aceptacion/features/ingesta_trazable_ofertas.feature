# language: es

Característica: Ingesta trazable de ofertas de servicios IT
  Como responsable de inteligencia de mercado
  Quiero transformar precios publicados en ofertas comparables
  Para consultar el mercado sin perder el dato original

  Antecedentes:
    Dado que la fuente es "Vida Informática"
    Y la ubicación es provincia "Córdoba" y ciudad "Córdoba"
    Y la fecha de relevamiento es "2026-08-07"

  Escenario: Extraer una fila sin perder sus precios originales
    Dado un documento HTML con la fila:
      | servicio                        | equipo | freelance | local    |
      | Eliminación de virus y malware | PC     | $ 15.000  | $ 20.000 |
    Cuando el scraper procesa el documento
    Entonces produce un DTO con servicio_raw "Eliminación de virus y malware"
    Y conserva equipo_raw "PC"
    Y conserva precio_freelance_raw "$ 15.000"
    Y conserva precio_local_raw "$ 20.000"
    Y conserva la fuente y la fecha de relevamiento

  Escenario: Normalizar el servicio sin reemplazar su valor original
    Dado el DTO extraído para "Eliminación de virus y malware"
    Cuando el procesador normaliza la oferta
    Entonces el servicio canónico es "MALWARE"
    Y servicio_raw continúa siendo "Eliminación de virus y malware"
    Y la empresa canónica es "Vida Informatica"
    Y la provincia y ciudad canónicas son "Córdoba"

  Escenario: Representar cada modalidad de precio como una observación
    Dado un DTO con precio freelance "$ 15.000" y precio local "$ 20.000"
    Cuando el procesador construye las observaciones de mercado
    Entonces produce una oferta de modalidad "freelance" por 15000 "ARS"
    Y produce una oferta de modalidad "local" por 20000 "ARS"
    Y cada oferta conserva su precio_raw correspondiente
    Y ambas ofertas conservan el mismo servicio, empresa, fuente y fecha

  Escenario: Persistir y recuperar ofertas sin cambiar su significado
    Dadas las ofertas freelance y local del servicio "MALWARE"
    Cuando se guardan y recuperan desde SQLite
    Entonces se recuperan 2 ofertas
    Y sus precios, modalidades, valores raw y canónicos son idénticos
    Y no aparecen precios cero ni valores por defecto inventados

  Escenario: Consultar estadísticas del servicio
    Dadas las ofertas persistidas:
      | empresa          | servicio | modalidad | precio |
      | Vida Informatica | MALWARE  | freelance | 15000  |
      | Vida Informatica | MALWARE  | local      | 20000  |
    Cuando consulto la API por "Eliminación de malware"
    Entonces la respuesta tiene estado 200
    Y la cantidad de ofertas es 2
    Y el precio mínimo es 15000
    Y el precio promedio es 17500
    Y el precio máximo es 20000
    Y la empresa "Vida Informatica" está incluida
    Y la ciudad "Córdoba" está incluida

  Escenario: Aislar el fallo de una fuente
    Dado que una fuente falla durante la descarga
    Y otra fuente entrega una oferta válida
    Cuando se ejecuta el pipeline
    Entonces el fallo queda registrado con la fuente y su causa
    Y la oferta válida se procesa y persiste
    Y el pipeline no inventa datos para la fuente fallida

  Escenario: Rechazar una fila incompleta de forma trazable
    Dada una fila sin servicio o sin ningún precio válido
    Cuando el scraper procesa el documento
    Entonces la fila no ingresa al dominio como oferta válida
    Y el rechazo informa la fuente y la razón
    Y no se persiste una oferta con precio cero
