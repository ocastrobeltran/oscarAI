# Observability

## Objetivo

Medir, explicar y depurar el comportamiento del sistema sin depender solo de inspección manual.

## Señales

- Logs estructurados.
- Métricas operativas.
- Trazas de solicitudes.
- Eventos de auditoría.

## Eventos críticos

- Inicio y fin de procesos asíncronos.
- Fallos de integración.
- Cambios de estado relevantes.
- Reintentos y degradaciones.

## Convenciones

- Toda operación crítica debe portar correlationId.
- Los errores deben mantener contexto suficiente para soporte.
- Los eventos de negocio deben ser distinguibles de los eventos técnicos.
