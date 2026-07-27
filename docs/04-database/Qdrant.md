# Qdrant

## Rol

Qdrant almacena embeddings y fragmentos semánticos para recuperación contextual.

## Colecciones esperadas

- Documents
- Meetings
- Emails
- TechnicalSolutions
- KnowledgeBase

## Metadatos recomendados

- sourceId
- sourceType
- projectId
- customerId
- language
- tags
- createdAt

## Estrategia de indexación

- Trocear por unidades semánticas.
- Mantener contexto suficiente por fragmento.
- Guardar referencias al origen y versión del contenido.
