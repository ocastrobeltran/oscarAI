# Authentication

## Estrategia

La autenticación debe adaptarse al tipo de consumidor: usuario humano, servicio interno o integración externa.

## Recomendación

- Sesiones o tokens para usuario interactivo.
- Tokens de servicio para automatización.
- Secret management para conexiones sensibles.

## Reglas

- No compartir credenciales entre dominios.
- Rotar secretos cuando haya exposición o cambio de personal.
