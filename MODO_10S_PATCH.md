# Patch modo máximo 10 segundos

Cambios aplicados:

- `/api/analyze` ahora usa **una sola llamada a Ollama** para resumen, contradicciones y borrador.
- En modo rápido se limita a **1 chunk por documento** y contexto reducido.
- Timeout de generación de Ollama: **7 segundos**.
- Timeout de conexión a Ollama: **2 segundos**.
- Si Ollama tarda, no está abierto o el modelo falla, el backend devuelve **fallback local extractivo/heurístico** en vez de dejar la pantalla cargando.
- El frontend aborta la petición después de 12 segundos como protección adicional.
- El botón ahora indica “Analizar en máximo 10s”.

Recomendado para cumplir la latencia:

```bash
ollama pull qwen2.5:1.5b
ollama run qwen2.5:1.5b
```

Nota: este modo prioriza velocidad sobre exhaustividad. Para documentos largos, solo analiza el primer chunk de cada documento en modo rápido.
