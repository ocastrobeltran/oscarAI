# Security

## Postura de seguridad

Oscar AI debe operar con el principio de mínimo privilegio y con separación explícita entre credenciales, datos estructurados y memoria semántica.

## Controles principales

- Autenticación por identidad y tokens según integración.
- Autorización por rol, dominio y operación.
- Segregación de secretos y configuración.
- Auditoría de acciones relevantes.
- Validación de entradas y contratos.

## Riesgos relevantes

- Exposición de tokens en integraciones externas.
- Indexación accidental de datos sensibles en Qdrant.
- Acceso no controlado a memorias compartidas.
- Backups sin cifrado o sin rotación.

## Medidas recomendadas

- Cifrar en tránsito y en reposo donde aplique.
- Segmentar roles de lectura y escritura.
- Registrar eventos críticos con contexto suficiente.
- Revisar permisos de MCP e integraciones con criterio de allowlist.

## Referencias

- [../07-integrations/MCP.md](../07-integrations/MCP.md)
- [../06-memory/Memory.md](../06-memory/Memory.md)
- [../10-devops/Backup.md](../10-devops/Backup.md)
