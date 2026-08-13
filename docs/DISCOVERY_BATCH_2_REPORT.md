# Enki Discovery Batch #2

Jurisdicciones trabajadas:
- Mendoza
- Tucumán
- Entre Ríos
- Neuquén

Objetivo: llevar cada jurisdicción a >=10 candidatos reales, preservando proveedores sin precio público y separando referencias/marketplaces de proveedores independientes.

Nuevas filas: 38

Cobertura objetivo tras merge:
- Mendoza: 10 (DMR existente + 9 nuevas)
- Tucumán: 10 (CiroWhite existente + 9 nuevas)
- Entre Ríos: 10 nuevas
- Neuquén: 10 nuevas

Nuevas fuentes PRICE_VISIBLE + PROVIDER:
- Viciadero (Tucumán)
- PDA Servicios Informáticos (Neuquén)

PRICE_VISIBLE no proveedor independiente:
- Vida Informática Zona 2 (REFERENCE)
- Vida Informática Zona 6 (REFERENCE)
- DSX/TiendaCores (AGGREGATOR; precio explícitamente advertido como posiblemente desactualizado)

Criterio:
- NO_PRICE_VISIBLE no entra al acquisition batch.
- REFERENCE/AGGREGATOR se conserva para research/provenance pero no cuenta como proveedor independiente.
- No se inventó ningún precio ni se promovió un placeholder $0 a evidencia económica.
