# OpenAPI

## Objetivo

Documentar el contrato REST para consumo interno y validación automática.

## Endpoints esperados

- `/health`
- `/projects`
- `/customers`
- `/documents`
- `/meetings`
- `/agents`
- `/search`

## Reglas

- Versionar el contrato.
- Generar ejemplos realistas.
- Mantener alineación con el modelo de dominio.

## Esqueleto de contrato

```yaml
openapi: 3.1.0
info:
	title: Oscar AI API
	version: 1.0.0
paths:
	/health:
		get:
			summary: Health check
	/projects:
		get:
			summary: List projects
	/search:
		post:
			summary: Search knowledge base
```

## Estado actual de implementación

- `GET /openapi.json` y `GET /api/v1/openapi.json` devuelven el esquema formal OpenAPI 3.1.0 para OpenClaw.
- `GET /api/v1` devuelve las rutas disponibles.
- `GET /api/v1/clients`, `GET /api/v1/projects`, `GET /api/v1/meetings` y `GET /api/v1/documents` devuelven listados.
- `GET /api/v1/clients/{id}`, `GET /api/v1/projects/{id}`, `GET /api/v1/meetings/{id}` y `GET /api/v1/documents/{id}` devuelven un elemento.
- `POST /api/v1/clients`, `POST /api/v1/projects`, `POST /api/v1/meetings` y `POST /api/v1/documents` crean elementos.
- `PUT /api/v1/clients/{id}`, `PUT /api/v1/projects/{id}`, `PUT /api/v1/meetings/{id}` y `PUT /api/v1/documents/{id}` actualizan elementos.
- `DELETE /api/v1/clients/{id}`, `DELETE /api/v1/projects/{id}`, `DELETE /api/v1/meetings/{id}` y `DELETE /api/v1/documents/{id}` eliminan elementos (limpiando referencias tanto en Postgres como en Qdrant).
- `GET /api/v1/search?q=...&type=all|meetings|documents` devuelve resultados semánticos sobre reuniones y/o documentos indexados en colecciones de Qdrant.



