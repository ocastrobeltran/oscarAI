# Error Model

## Objetivo

Normalizar cómo la API informa errores para facilitar consumo, soporte y observabilidad.

## Formato recomendado

```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "The requested project does not exist.",
    "correlationId": "01J...",
    "details": []
  }
}
```

## Reglas

- El código debe ser estable y legible.
- El mensaje debe ser útil sin exponer secretos.
- El correlationId debe permitir trazabilidad end-to-end.
- Los detalles no deben duplicar información sensible.
