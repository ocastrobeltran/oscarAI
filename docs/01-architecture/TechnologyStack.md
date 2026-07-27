# Technology Stack

## Plataforma base

- Docker para empaquetado y desarrollo local.
- Docker Compose para la orquestación base.
- Caddy como reverse proxy y terminación HTTPS.

## Datos

- PostgreSQL como base principal relacional.
- Redis para caché, colas y sesiones.
- Qdrant para almacenamiento vectorial y recuperación semántica.

## Inteligencia y automatización

- Orquestador de agentes como capa de coordinación.
- RAG para recuperación contextual.
- MCP para integración uniforme con herramientas externas.

## Frontend y API

- Dashboard web para supervisión operativa y ejecutiva.
- API REST para consumo interno y externo controlado.
- OpenAPI para contrato y pruebas de integración.

## Observabilidad y operación

- Logs estructurados.
- Trazas de acciones relevantes.
- Auditoría de decisiones y cambios de estado.

## Referencias

- [Deployment.md](Deployment.md)
- [../07-integrations/MCP.md](../07-integrations/MCP.md)
- [../09-api/OpenAPI.md](../09-api/OpenAPI.md)
