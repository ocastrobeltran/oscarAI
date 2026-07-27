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

## Reglas de diseño

- Un agente no debe asumir permisos de otro.
- Un agente no debe persistir contexto fuera de los canales definidos.
- El orquestador conserva la autoridad final sobre el flujo.
- Las tareas compuestas deben devolver resultado consolidado y trazable.

## Referencias

- [PM-Agent.md](PM-Agent.md)
- [QA-Agent.md](QA-Agent.md)
- [Meeting-Agent.md](Meeting-Agent.md)
- [Communication-Agent.md](Communication-Agent.md)
- [Documentation-Agent.md](Documentation-Agent.md)
- [Legger-Agent.md](Legger-Agent.md)
