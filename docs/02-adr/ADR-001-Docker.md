# ADR-001: Docker como estándar de despliegue

## Estado

Aceptado

## Contexto

Se requiere una plataforma portable, reproducible y desacoplada del sistema operativo.

## Decisión

Todos los servicios deben ejecutarse mediante contenedores Docker y orquestarse con Docker Compose durante el desarrollo.

## Consecuencias

### Positivas

- Despliegues reproducibles.
- Menor fricción entre equipos y entornos.
- Aislamiento de dependencias.

### Negativas

- Curva inicial de aprendizaje.
- Consumo adicional de recursos.
