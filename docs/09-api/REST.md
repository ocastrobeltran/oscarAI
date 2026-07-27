# REST

## Propósito

La API REST expone operaciones controladas para dashboard, integraciones y automatización.

## Reglas

- Recursos consistentes.
- Respuestas predecibles.
- Errores normalizados.
- Versionado explícito.

## Superficie actual

- `/api/v1`
- `/api/v1/clients`
- `/api/v1/projects`
- `/api/v1/meetings`
- `/api/v1/search?q=...`

## Operaciones soportadas

- `GET` list and detail by id.
- `POST` create resources.
- `PUT` update resources by id.
- `DELETE` remove resources by id.

## Compatibilidad temporal

Mientras la API madura, también existen alias directos sin versión para facilitar pruebas rápidas:

- `/clients`
- `/projects`
- `/meetings`
- `/search?q=...`

## Estado de implementación

La API ya es funcional para el conjunto semilla del dominio y usa las rutas directas y versionadas en paralelo mientras madura la estructura final.

