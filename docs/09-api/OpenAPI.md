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

- `GET /api/v1` devuelve las rutas disponibles.
- `GET /api/v1/clients`, `GET /api/v1/projects` y `GET /api/v1/meetings` devuelven listados.
- `GET /api/v1/clients/{id}`, `GET /api/v1/projects/{id}` y `GET /api/v1/meetings/{id}` devuelven un elemento.
- `POST /api/v1/clients`, `POST /api/v1/projects` y `POST /api/v1/meetings` crean elementos.
- `PUT /api/v1/clients/{id}`, `PUT /api/v1/projects/{id}` y `PUT /api/v1/meetings/{id}` actualizan elementos.
- `DELETE /api/v1/clients/{id}`, `DELETE /api/v1/projects/{id}` y `DELETE /api/v1/meetings/{id}` eliminan elementos.
- `GET /api/v1/search?q=...` devuelve resultados semánticos sobre reuniones indexadas en Qdrant.


