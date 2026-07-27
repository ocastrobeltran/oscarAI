# ADR-005: MCP como estándar para integraciones

## Estado

Aceptado

## Contexto

Se requiere una forma uniforme de conectar herramientas externas.

## Decisión

Priorizar servidores MCP para las integraciones que lo soporten; usar APIs nativas cuando no exista un servidor MCP adecuado.

## Integraciones previstas

- Azure DevOps
- GitHub
- Outlook
- Filesystem
- PostgreSQL
- Docker
- Calendar

## Beneficios

- Menor acoplamiento.
- Herramientas reutilizables.
- Sustitución sencilla de proveedores.
