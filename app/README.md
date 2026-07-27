# App Service

Servicio HTTP mínimo para validar la integración base de Oscar AI.

## Endpoints

- `GET /` devuelve información básica del servicio.
- `GET /health` devuelve el estado del servicio y sus dependencias.
- `GET /clients` lista clientes persistidos en PostgreSQL.
- `GET /projects` lista proyectos persistidos en PostgreSQL.
- `GET /meetings` lista reuniones persistidas en PostgreSQL.

## Objetivo

Este contenedor sirve como primer backend funcional detrás de Caddy mientras se desarrolla la aplicación real.

## Dependencias validadas

- PostgreSQL
- Redis
- Qdrant

## Esquema inicial

- `clients`: código, nombre y fecha de creación.
- `projects`: cliente, código, nombre, estado y fecha de creación.
- `meetings`: proyecto, título, resumen y fecha de reunión.
