# MVP PLN IA con Ollama local y FastAPI — versión rápida/robusta

Este proyecto convierte el prototipo HTML de **“Procesamiento Inteligente de Lenguaje Natural con IA”** en un MVP con backend **FastAPI** y motor LLM local mediante **Ollama**. Esta versión incluye un patch para evitar el error:

> “Ollama respondió, pero no generó afirmaciones resumidas con el formato esperado.”

Ahora el backend acepta respuestas JSON puras, JSON dentro de texto, listas con viñetas o texto libre. Si el modelo responde fuera del formato esperado, el sistema genera una **salida degradada útil** en lugar de romper el análisis.

## Qué hace

- Carga texto pegado o archivos `.txt`, `.docx`, `.pdf` textual y `.xlsx`.
- Extrae texto en un backend local con FastAPI.
- Divide los documentos en chunks pequeños.
- Consulta Ollama local en `http://localhost:11434`.
- Genera:
  - resumen automático trazable;
  - detección preliminar de inconsistencias entre Documento A y Documento B;
  - borrador documental editable;
  - control humano: aceptar, editar o rechazar afirmaciones.
- Muestra tiempos por fase: verificación, chunking, resumen, contradicciones, borrador y parsing.
- Incluye endpoint de diagnóstico: `GET /api/diagnostics`.

## Qué NO afirma

Este MVP **no certifica** todavía:

- fidelidad semántica superior al 90%;
- tasa de alucinación inferior al 3%;
- latencia menor a 5 segundos para documentos de 50 páginas;
- procesamiento validado de 200 páginas;
- cumplimiento WCAG 2.1 auditado;
- cumplimiento legal definitivo.

Esas métricas siguen siendo **objetivos de validación futura**.

---

## 1. Instalar Ollama

Verifica que Ollama funcione:

```bash
ollama --version
```

Ollama debe quedar escuchando en:

```text
http://localhost:11434
```

Si no está activo:

```bash
ollama serve
```

---

## 2. Modelo recomendado para responder rápido

Para una laptop común y respuestas en menos tiempo:

```bash
ollama pull qwen2.5:1.5b
```

Si quieres mejor formato JSON, pero un poco más lento:

```bash
ollama pull qwen2.5:3b
```

`qwen2.5:1.5b` es rápido, pero puede fallar más que un modelo grande al devolver JSON exacto. Por eso este patch agrega parsing robusto y fallback.

---

## 3. Precargar el modelo para evitar demora inicial

La primera consulta puede tardar porque Ollama carga el modelo en memoria. Puedes precargarlo así:

```bash
curl http://localhost:11434/api/generate -d "{\"model\":\"qwen2.5:1.5b\",\"prompt\":\"Responde solo OK\",\"stream\":false,\"keep_alive\":\"30m\"}"
```

También puedes hacerlo manualmente:

```bash
ollama run qwen2.5:1.5b
```

Escribe:

```text
Responde solo OK
```

Luego sal con:

```text
/bye
```

---

## 4. Ejecutar FastAPI

Desde la carpeta raíz del proyecto:

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Instala dependencias:

```bash
pip install -r requirements.txt
```

Ejecuta:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Abre:

```text
http://127.0.0.1:8000
```

---

## 5. Configuración recomendada para demo rápida

En el frontend usa:

```text
Modelo: qwen2.5:1.5b
Modo rápido: activado
Chunks máximos por documento: 2
Documentos: 1 a 2 páginas cada uno
PDF escaneado: evitar en la demo
```

El modo rápido limita el texto enviado a Ollama y reduce la salida con:

```text
num_ctx = 2048
num_predict aproximado = 240 a 300
stream = false
keep_alive = 30m
```

---

## 6. Diagnóstico rápido

Desde el navegador presiona **“Diagnóstico rápido”**.

También puedes abrir:

```text
http://127.0.0.1:8000/api/diagnostics?model=qwen2.5:1.5b
```

Devuelve:

- estado del backend;
- URL de Ollama;
- modelo seleccionado;
- modelos instalados;
- prueba corta con el LLM;
- tiempo de respuesta;
- opciones usadas;
- último error real del backend.

Prueba Ollama manualmente:

```bash
curl http://localhost:11434/api/tags
```

```bash
curl http://localhost:11434/api/generate -d "{\"model\":\"qwen2.5:1.5b\",\"prompt\":\"Responde solo OK\",\"stream\":false}"
```

---

## 7. Por qué tardaba tanto

Las causas típicas eran:

1. El backend enviaba demasiado texto o demasiados chunks.
2. El prompt pedía muchas tareas en una sola respuesta.
3. `num_predict` podía permitir salidas demasiado largas.
4. La primera llamada cargaba el modelo en memoria.
5. El modelo pequeño tardaba intentando producir JSON estricto.
6. El sistema hacía fallar todo si la respuesta no venía exactamente como se esperaba.

Este patch reduce el tiempo porque:

- activa **modo rápido** por defecto;
- limita chunks a 2 por documento;
- usa chunks más cortos;
- pide máximo 3 afirmaciones de resumen;
- separa resumen, contradicciones y borrador;
- limita la salida del modelo;
- mantiene `keep_alive: 30m`;
- agrega fallback si el JSON no es perfecto.

---

## 8. Estructura del proyecto

```text
pln_ollama_mvp/
├── backend/
│   ├── main.py                 # FastAPI app + /api/diagnostics
│   ├── services/
│   │   ├── analysis.py         # Análisis, fallback, tiempos y modo rápido
│   │   ├── chunker.py          # Fragmentación de documentos
│   │   ├── extractor.py        # Extracción TXT/DOCX/PDF textual/XLSX
│   │   └── ollama_client.py    # Cliente Ollama con timeout, parsing robusto y errores específicos
│   └── static/
│       ├── index.html          # Frontend
│       ├── styles.css
│       └── app.js              # Modo rápido, diagnóstico y mensajes claros
├── sample_docs/
├── requirements.txt
├── run_windows.bat
├── run_unix.sh
├── GUIA_EXPOSICION.md
└── README.md
```

---

## 9. Cómo defenderlo en clase

Frase recomendada:

> “Este módulo es un MVP académico que usa Ollama localmente como motor de IA, por lo que no envía documentos a ChatGPT ni a servicios externos. El patch mejora la robustez porque ya no falla si el modelo pequeño no devuelve JSON perfecto; en ese caso genera una salida degradada y exige validación humana. Las métricas del informe siguen siendo objetivos, no resultados certificados.”

---

## 10. Próximas mejoras técnicas

Para una versión productiva faltan:

- OCR para PDF escaneados;
- búsqueda semántica con embeddings y vector DB;
- soporte de más de dos documentos;
- dataset de evaluación;
- pruebas formales de fidelidad, alucinación, precisión de contradicciones y latencia;
- autenticación, roles, logs y cifrado en reposo;
- auditoría WCAG 2.1;
- empaquetado con Docker, Electron o Tauri.
