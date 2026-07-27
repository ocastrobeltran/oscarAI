# Redis

## Rol

Redis funciona como capa de aceleración y coordinación temporal.

## Casos de uso

- Caché de consultas frecuentes.
- Colas cortas de trabajo.
- Sesiones temporales.
- Locks o semáforos simples cuando sea necesario.

## Criterios de uso

- No usar Redis como sistema de verdad.
- Todo dato crítico debe persistir en PostgreSQL o en el almacén correspondiente.
