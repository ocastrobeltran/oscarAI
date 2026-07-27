# ADR-002: PostgreSQL como base de datos principal

## Estado

Aceptado

## Contexto

Oscar AI almacena entidades estructuradas: proyectos, clientes, agentes, configuraciones, historial y auditoría.

## Decisión

Adoptar PostgreSQL como base de datos relacional principal.

## Justificación

- Madurez y estabilidad.
- Soporte JSON/JSONB.
- Buen equilibrio entre estructura y flexibilidad.

## Alcance

No almacenará embeddings; esos vivirán en Qdrant.
