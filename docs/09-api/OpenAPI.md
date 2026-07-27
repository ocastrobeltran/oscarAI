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

