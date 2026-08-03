# REST

## Propósito

La API REST expone operaciones controladas para dashboard, integraciones y automatización.

## Reglas

- Recursos consistentes.
- Respuestas predecibles.
- Errores normalizados.
- Versionado explícito.

## Superficie actual

- `/health`
- `/openapi.json`
- `/docs` (Swagger UI Interactivo)
- `/redoc` (Documentación ReDoc)
- `/api/v1`
- `/api/v1/openapi.json`
- `/api/v1/clients`
- `/api/v1/projects`
- `/api/v1/meetings`
- `/api/v1/documents`
- `/api/v1/documents/ingest` (Ingesta y segmentación de documentos extensos)
- `/api/v1/tasks`
- `/api/v1/knowledge-items`
- `/api/v1/memory-entries`
- `/api/v1/audit-events` (Registro de auditoría de peticiones)
- `/api/v1/integrations/status` (Estado de conectores externos)
- `/api/v1/integrations/github/sync` (Sincronización de issues de GitHub)
- `/api/v1/integrations/azure-devops/sync` (Sincronización de Work Items de Azure DevOps)
- `/api/v1/integrations/outlook/ingest` (Ingesta de correos de Outlook)
- `/api/v1/search?q=...&type=all|meetings|documents|knowledge_items|memory_entries`
- `/api/v1/agents`
- `/api/v1/agents/{id}`
- `/api/v1/agents/{id}/run`

## Operaciones soportadas

- `GET` list and detail by id.
- `POST` create resources and run agent queries (`POST /api/v1/agents/{id}/run`).
- `PUT` update resources by id.
- `DELETE` remove resources by id (with automatic vector index cleanup).

## Compatibilidad temporal

Mientras la API madura, también existen alias directos sin versión para facilitar pruebas rápidas:

- `/clients`
- `/projects`
- `/meetings`
- `/documents`
- `/tasks`
- `/knowledge-items`
- `/memory-entries`
- `/agents`
- `/search?q=...`

## Estado de implementación

La API fue migrada exitosamente al framework **FastAPI** con servidor **Uvicorn** y esquemas de validación **Pydantic**. Genera documentación Swagger UI dinámica en `/docs` y ReDoc en `/redoc`, y sirve el manifiesto `openclaw.yaml` para integración nativa con motores de agentes (como OpenClaw).




