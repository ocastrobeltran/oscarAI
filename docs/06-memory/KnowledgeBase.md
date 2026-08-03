# KnowledgeBase

## Rol

La base de conocimiento agrupa material curado, validado y listo para recuperación contextual en la plataforma Oscar AI.

## Fuentes

- Reuniones y actas.
- Decisiones arquitectónicas (ADRs).
- Correos y mensajes relevantes.
- Documentos técnicos y manuales extensos.
- Incidencias, guías y soluciones de calidad.

## Ciclo de vida implementado

1. **Ingesta**: Disponibilidad del endpoint `POST /api/v1/documents/ingest` y herramienta OpenClaw `ingest_document`.
2. **Normalización**: Limpieza de texto y extracción de metadatos de proyecto.
3. **Segmentación (Chunking)**: División deslizante configurada (`chunk_size` y `chunk_overlap`) mediante el motor `app/chunking.py`.
4. **Embedding**: Vectorización multiproveedor (Google Gemini `text-embedding-004`, OpenAI, Ollama o Hash).
5. **Indexación**: Almacenamiento granular de trozos (chunks) con metadatos (`chunk_index`, `total_chunks`) en Qdrant.
6. **Recuperación**: Búsqueda semántica cruzada y RAG filtrado por colecciones.
7. **Revisión y Depuración**: Limpieza en cascada en Qdrant al eliminar registros en PostgreSQL.

