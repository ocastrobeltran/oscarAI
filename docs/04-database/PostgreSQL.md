# PostgreSQL

## Rol

PostgreSQL es la fuente de verdad para entidades estructuradas, configuración, trazabilidad y auditoría.

## Qué guarda

- Clientes y proyectos.
- Estados de trabajo.
- Configuraciones y preferencias.
- Historial y auditoría.
- Referencias a documentos y artefactos vectorizados.

## Qué no guarda

- Embeddings.
- Archivos binarios pesados.

## Reglas de modelado

- Usar claves primarias estables.
- Auditar cambios importantes.
- Normalizar lo estructural y dejar el contenido semántico fuera.
