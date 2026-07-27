# ADR-006: Caddy como reverse proxy

## Estado

Aceptado

## Contexto

Se requiere publicar servicios HTTPS con administración mínima.

## Decisión

Utilizar Caddy como reverse proxy principal.

## Motivos

- HTTPS automático.
- Configuración sencilla.
- Excelente soporte para Docker.
- Renovación automática de certificados.

## Consecuencias

Caddy será el punto único de entrada para los servicios web de Oscar AI.
