# ERD

## Entidades principales

- Customer
- Project
- Document
- Meeting
- Agent
- Integration
- Task
- AuditEvent
- KnowledgeItem
- MemoryEntry

```mermaid
erDiagram
    CUSTOMER ||--o{ PROJECT : owns
    PROJECT ||--o{ DOCUMENT : contains
    PROJECT ||--o{ MEETING : has
    PROJECT ||--o{ TASK : tracks
    AGENT ||--o{ TASK : executes
    INTEGRATION ||--o{ AUDITEVENT : produces
    PROJECT ||--o{ KNOWLEDGEITEM : curates
    PROJECT ||--o{ MEMORYENTRY : retains
```

## Notas

- KnowledgeItem representa conocimiento curado para RAG o documentación.
- MemoryEntry representa elementos de memoria persistente o contextual.

