# Oscar AI

## Documento de Arquitectura Técnica v1.0

> Documento base de arquitectura del proyecto Oscar AI.

## 1. Visión

Oscar AI es una plataforma personal de IA orientada a la gestión de
proyectos, QA, documentación y automatización. El sistema estará
compuesto por agentes especializados, memoria persistente, integraciones
mediante MCP/API y una arquitectura desacoplada basada en Docker.

## 2. Objetivos

-   Centralizar la información de proyectos.
-   Automatizar tareas repetitivas.
-   Integrar Azure DevOps, Outlook, GitHub y Legger.
-   Mantener memoria organizacional.
-   Ser independiente del proveedor de IA.

## 3. Principios

-   **AI Agnostic**
-   **Docker First**
-   **API First**
-   **Security First**
-   **Memory First**
-   **Modularidad**

## 4. Arquitectura

``` text
Usuario
   │
Dashboard Web
   │
API Gateway
   │
Oscar AI Core
├── Agentes
├── Automatización (n8n)
├── Memoria (Qdrant)
├── PostgreSQL
├── Redis
└── Integraciones (MCP)
        ├── Azure DevOps
        ├── Outlook
        ├── GitHub
        ├── Laravel
        ├── Calendar
        └── Filesystem
```

## 5. Componentes

### Reverse Proxy

-   Caddy
-   HTTPS automático
-   Proxy inverso

### Oscar AI Core

-   Orquestación
-   Gestión de agentes
-   Gestión de herramientas

### PostgreSQL

-   Clientes
-   Proyectos
-   Configuración
-   Historial

### Redis

-   Caché
-   Colas
-   Sesiones

### Qdrant

Base vectorial para: - Actas - Correos - PDFs - Word - Excel - Reuniones

### n8n

Motor de automatización.

## 6. Agentes

### PM Agent

-   Estado de proyectos
-   Riesgos
-   Seguimiento
-   Cronograma

### QA Agent

-   Casos de prueba
-   Cypress
-   Playwright
-   Lighthouse
-   JMeter

### Documentation Agent

-   Actas
-   Soluciones técnicas
-   Minutas

### Communication Agent

-   Outlook
-   Teams
-   WhatsApp

### Meeting Agent

-   Resúmenes
-   Compromisos
-   Tareas

### Legger Agent

-   Consulta de proyectos
-   Clientes
-   Tickets

## 7. Integraciones

-   Azure DevOps
-   Outlook
-   GitHub
-   OneDrive
-   Laravel API
-   Calendario
-   Sistema de archivos

## 8. Modelo de Datos

### Cliente

-   id
-   nombre
-   contacto
-   correo

### Proyecto

-   id
-   código
-   nombre
-   cliente
-   estado
-   riesgo

### Documento

-   id
-   proyecto
-   tipo
-   versión

### Reunión

-   id
-   proyecto
-   fecha
-   resumen

## 9. Roadmap

### Sprint 1

-   Infraestructura
-   Docker
-   Git
-   Base del proyecto

### Sprint 2

-   Oscar AI Core
-   API
-   Dashboard

### Sprint 3

-   Base de conocimiento
-   Qdrant

### Sprint 4

-   Azure DevOps
-   Outlook
-   GitHub

### Sprint 5

-   PM Agent
-   QA Agent

### Sprint 6

-   Dashboard ejecutivo

## 10. Visión

Oscar AI evolucionará como un asistente ejecutivo con memoria,
automatización y agentes especializados, preparado para crecer sin
depender de una única plataforma de IA.
