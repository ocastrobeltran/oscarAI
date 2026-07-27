# RAG

## Objetivo

Combinar recuperación semántica y generación para responder con contexto real y no solo con inferencia genérica.

## Pipeline lógico

```mermaid
flowchart LR
    Q[Consulta] --> N[Normalización]
    N --> R[Recuperación en Qdrant]
    R --> F[Filtrado por metadatos]
    F --> P[Prompt contextual]
    P --> G[Generación]
    G --> V[Validación y trazabilidad]
```

## Buenas prácticas

- Recuperar poco pero relevante.
- Priorizar fuentes curadas.
- Incluir referencias al origen.
- Evitar que la respuesta oculte incertidumbre.

## Estado actual en Oscar AI

- Qdrant se usa como colección `meetings` para indexar resúmenes de reuniones.
- La búsqueda semántica inicial está soportada por `/search?q=...`.
- El embedding actual es ligero y determinista; puede sustituirse por embeddings reales cuando el stack de modelos esté disponible.

