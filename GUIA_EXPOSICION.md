# Guion breve de exposición — MVP PLN IA con Ollama local

## 1. Apertura — 30 segundos

El objetivo del proyecto es reducir el tiempo de revisión de documentos largos sin perder verificabilidad. El sistema ayuda a resumir, comparar y generar borradores, pero mantiene al usuario como supervisor final.

## 2. Cambio técnico principal — 45 segundos

La versión anterior podía fallar cuando Ollama respondía fuera del JSON esperado. Esta versión usa un backend FastAPI con parsing robusto: acepta JSON puro, JSON dentro de texto, listas o texto libre. Si el modelo pequeño no respeta el formato exacto, el sistema genera una salida degradada y no se detiene.

## 3. Privacidad y soberanía de datos — 40 segundos

Los documentos se procesan localmente. El navegador envía el texto al backend local y el backend consulta Ollama en `localhost:11434`. No se envían documentos a ChatGPT, Claude ni Gemini.

## 4. Velocidad de respuesta — 45 segundos

Para la demostración se recomienda `qwen2.5:1.5b`, modo rápido activo y máximo 2 chunks por documento. Esto reduce el texto enviado al modelo y limita la longitud de la respuesta. La primera consulta puede tardar porque Ollama carga el modelo; por eso se recomienda precargarlo.

## 5. Demostración — 2 minutos

1. Mostrar que Ollama está activo.
2. Seleccionar `qwen2.5:1.5b`.
3. Ejecutar “Diagnóstico rápido”.
4. Cargar Documento A y Documento B.
5. Activar modo rápido y usar 2 chunks por documento.
6. Ejecutar análisis.
7. Mostrar resumen trazable, contradicciones y borrador.
8. Mostrar los tiempos por fase.

## 6. Supervisión humana — 45 segundos

Cada afirmación puede aceptarse, editarse o rechazarse. Esto demuestra que la IA no decide sola; el usuario mantiene control humano antes de incorporar la salida al documento final.

## 7. Marco legal y ético — 45 segundos

La interfaz incluye transparencia sobre contenido generado por IA local, supervisión humana, privacidad local y accesibilidad inicial. No se afirma cumplimiento legal definitivo, sino evidencia parcial del MVP.

## 8. Limitaciones honestas — 45 segundos

La calidad depende del modelo local y del hardware. `qwen2.5:1.5b` es rápido, pero puede tener menor calidad y peor JSON que modelos mayores. Las métricas de fidelidad mayor al 90%, alucinación menor al 3% y latencia menor a 5 segundos son objetivos pendientes de validación.

## 9. Cierre — 20 segundos

Este MVP es defendible porque usa un LLM local real, no envía documentos a la nube, mantiene trazabilidad y supervisión humana, y ahora maneja errores de formato sin romper la demostración.
