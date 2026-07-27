# Release Checklist

## Antes de liberar

- Revisar que la documentación afectada esté actualizada.
- Validar contratos de API y modelos relevantes.
- Confirmar secretos y variables de entorno.
- Verificar que las imágenes o artefactos están etiquetados correctamente.
- Confirmar que el plan de rollback existe.

## Durante la liberación

- Activar observabilidad mínima.
- Vigilar errores, latencia y fallos de integración.
- Registrar correlación de cambios relevantes.

## Después de liberar

- Revisar indicadores clave.
- Confirmar que no hay regresiones críticas.
- Actualizar changelog si procede.
- Registrar lecciones aprendidas.
