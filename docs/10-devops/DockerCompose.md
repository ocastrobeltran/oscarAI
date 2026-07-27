# Docker Compose

## Rol

Docker Compose define el entorno local y la composición de servicios de la plataforma.

## Servicios base

- Caddy.
- PostgreSQL.
- Redis.
- Qdrant.
- Core de Oscar AI.

## Buenas prácticas

- Separar perfiles por entorno si la complejidad crece.
- Persistir datos de los servicios con estado.
- Evitar secretos hardcodeados.

## Configuración relacionada

- [../../docker-compose.yml](../../docker-compose.yml)
- [../../.env.example](../../.env.example)

