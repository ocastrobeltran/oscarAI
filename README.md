# Oscar AI

Repositorio documental de arquitectura para Oscar AI. Este proyecto organiza la solución como un **Architecture Repository** mantenible, con entregables independientes, referencias cruzadas y un recorrido de lectura pensado para equipos de producto, arquitectura, desarrollo y operación.

## Cómo leerlo

1. Empieza por [docs/00-vision/Vision.md](docs/00-vision/Vision.md), [docs/00-vision/Objectives.md](docs/00-vision/Objectives.md) y [docs/00-vision/Scope.md](docs/00-vision/Scope.md).
2. Continúa con [docs/01-architecture/Architecture.md](docs/01-architecture/Architecture.md) y [docs/01-architecture/TechnologyStack.md](docs/01-architecture/TechnologyStack.md).
3. Revisa las decisiones en [docs/02-adr/ADR-001-Docker.md](docs/02-adr/ADR-001-Docker.md) hasta [docs/02-adr/ADR-007-Redis.md](docs/02-adr/ADR-007-Redis.md).
4. Usa los modelos C4 en [docs/03-c4/Context.md](docs/03-c4/Context.md), [docs/03-c4/Container.md](docs/03-c4/Container.md), [docs/03-c4/Component.md](docs/03-c4/Component.md) y [docs/03-c4/Code.md](docs/03-c4/Code.md).
5. Profundiza en datos, agentes, memoria, integraciones, API y DevOps según el área que estés revisando.
6. Revisa los diagramas operativos en [docs/03-c4/Sequence.md](docs/03-c4/Sequence.md) y [docs/03-c4/State.md](docs/03-c4/State.md).

## Estructura

- [ROADMAP.md](ROADMAP.md): secuencia de entrega de la documentación y del producto.
- [CHANGELOG.md](CHANGELOG.md): histórico de cambios del repositorio documental.
- [docs/](docs): documentación técnica principal.

## Principios del repositorio

- La documentación debe ser trazable y modular.
- Cada documento debe poder leerse de forma autónoma, pero enlazarse con otros entregables.
- Las decisiones arquitectónicas se registran como ADR con contexto, decisión, alternativas y consecuencias.
- Los diagramas se mantienen en Mermaid para facilitar revisión y versionado.

## Estado de la solución

El contenido de este repositorio describe la **arquitectura objetivo** de Oscar AI. La base funcional se apoya en Docker, PostgreSQL, Qdrant, Redis, Caddy, agentes especializados y una capa de integración basada en MCP y APIs nativas cuando corresponda.

## Referencias rápidas

- [docs/01-architecture/Architecture.md](docs/01-architecture/Architecture.md)
- [docs/04-database/ERD.md](docs/04-database/ERD.md)
- [docs/04-database/DomainModel.md](docs/04-database/DomainModel.md)
- [docs/05-agents/Agent-Orchestrator.md](docs/05-agents/Agent-Orchestrator.md)
- [docs/05-agents/Agent-Contracts.md](docs/05-agents/Agent-Contracts.md)
- [docs/06-memory/RAG.md](docs/06-memory/RAG.md)
- [docs/07-integrations/MCP.md](docs/07-integrations/MCP.md)
- [docs/07-integrations/Integration-Strategy.md](docs/07-integrations/Integration-Strategy.md)
- [docs/08-dashboard/UXPrinciples.md](docs/08-dashboard/UXPrinciples.md)
- [docs/10-devops/ReleaseChecklist.md](docs/10-devops/ReleaseChecklist.md)
- [docs/11-development/DocumentationGuide.md](docs/11-development/DocumentationGuide.md)
- [docs/12-templates/README.md](docs/12-templates/README.md)

# oscarAI
