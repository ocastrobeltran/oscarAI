# Permissions

## Objetivo

Definir un criterio simple para autorizar integraciones y evitar permisos excesivos.

## Reglas

- Una integración solo recibe los permisos que necesita.
- Los permisos de lectura y escritura se separan cuando sea posible.
- Las credenciales de servicio no se reutilizan entre dominios.
- Cualquier permiso elevado debe quedar documentado y justificado.

## Niveles

| Nivel | Descripción |
| --- | --- |
| Read-only | Solo consulta datos |
| Operational | Puede ejecutar acciones controladas |
| Administrative | Cambia configuración o acceso |

## Referencias

- [MCP.md](MCP.md)
- [Integration-Strategy.md](Integration-Strategy.md)
