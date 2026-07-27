# ADR-007: Redis como capa de caché y coordinación temporal

## Estado

Aceptado

## Contexto

Oscar AI necesita reducir latencia, manejar colas cortas y gestionar estados temporales sin contaminar el modelo relacional principal.

## Decisión

Adoptar Redis como capa de caché, coordinación temporal y soporte de colas ligeras.

## Alcance

- Caché de consultas frecuentes.
- Sesiones temporales.
- Locks y coordinación ligera.
- Colas de trabajo de corta vida.

## Consecuencias

- Menor carga sobre PostgreSQL.
- Mayor agilidad para procesos asíncronos.
- La información crítica sigue persistiendo en PostgreSQL o Qdrant.
