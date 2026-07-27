# Scope

## En alcance

- Gestión de proyectos y clientes.
- Gestión de documentos y conocimiento.
- Agentes especializados para PM, QA, comunicación, reuniones y documentación.
- Integraciones con Azure DevOps, GitHub, Outlook, OneDrive, Laravel y MCP.
- Persistencia en PostgreSQL, Redis y Qdrant.
- Dashboard ejecutivo y capa API.

## Fuera de alcance inicial

- Entrenamiento propio de modelos fundacionales.
- Sustitución de suites corporativas completas.
- Automatizaciones sin trazabilidad o sin modelo de permisos.
- Almacenamiento de embeddings en PostgreSQL.

## Supuestos

- El despliegue base se realiza con Docker.
- Caddy será el punto de entrada HTTP/HTTPS.
- El sistema podrá crecer hacia Kubernetes solo si la operación lo requiere.

## Dependencias externas

- Servicios de Microsoft 365 y Azure DevOps.
- GitHub como origen de código o documentación.
- Qdrant para búsquedas semánticas.
- APIs externas específicas según cliente o proyecto.
