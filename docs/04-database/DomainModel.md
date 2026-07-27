# Domain Model

## Núcleo del dominio

Oscar AI se organiza alrededor de cinco conceptos principales:

- Customer: entidad cliente o cuenta.
- Project: contenedor de trabajo, seguimiento y contexto.
- Document: artefacto versionable y recuperable.
- Meeting: evento que produce acuerdos y tareas.
- Agent: unidad especializada de ejecución.

## Relaciones

```mermaid
classDiagram
    class Customer
    class Project
    class Document
    class Meeting
    class Task
    class Agent
    class Integration

    Customer "1" --> "many" Project
    Project "1" --> "many" Document
    Project "1" --> "many" Meeting
    Project "1" --> "many" Task
    Agent "1" --> "many" Task
    Integration "1" --> "many" Task
```

## Reglas de dominio

- Un proyecto pertenece a un cliente.
- Un documento puede tener múltiples versiones, pero una sola versión activa.
- Una reunión puede generar tareas, decisiones y material de conocimiento.
- Una tarea puede ser ejecutada o enriquecida por uno o más agentes.
