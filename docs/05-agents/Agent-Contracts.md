# Agent Contracts

## Convención común

Cada agente debe declarar propósito, entradas, salidas, límites y criterios de éxito.

## Contrato mínimo

| Campo | Descripción |
| --- | --- |
| Name | Identificador del agente |
| Purpose | Problema que resuelve |
| Inputs | Contexto que consume |
| Outputs | Artefactos que produce |
| Tools | Integraciones o utilidades permitidas |
| Constraints | Límites de actuación |
| Success Criteria | Qué significa una ejecución correcta |

## Integración con OpenClaw y API REST

Los agentes se integran mediante manifiestos de OpenClaw (`openclaw.yaml`) y se exponen en la API REST para su descubrimiento y ejecución directa:

- `GET /api/v1/agents`: Devuelve la lista de agentes registrados y sus herramientas asociadas.
- `GET /api/v1/agents/{id}`: Devuelve la especificación y contrato de un agente en particular.
- `POST /api/v1/agents/{id}/run`: Ejecuta una solicitud contra el agente, invocando las herramientas vectoriales de Qdrant y la base de datos relacional para consolidar una respuesta estructurada con citas.

## Referencias

- [openclaw.yaml](../../openclaw.yaml)
- [Documentation-Agent.md](Documentation-Agent.md)
- [PM-Agent.md](PM-Agent.md)
- [QA-Agent.md](QA-Agent.md)
- [Meeting-Agent.md](Meeting-Agent.md)
- [Communication-Agent.md](Communication-Agent.md)
- [Legger-Agent.md](Legger-Agent.md)

