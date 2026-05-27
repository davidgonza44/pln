# ⚠️ SOLUCIÓN RÁPIDA - Error "No se pudo consultar Ollama"

## EL PROBLEMA REAL

**Tu diagnóstico mostró:**
- ✅ Ollama SÍ está corriendo
- ✅ Modelos SÍ están instalados
- ❌ **Backend NO está corriendo en puerto 8000**

El error que ves es porque el frontend no puede conectar con tu backend. El backend es lo que comunica con Ollama.

---

## SOLUCIÓN EN 30 SEGUNDOS

### Opción 1: Script simplificado (RECOMENDADO)
```bat
start.bat
```
Este script hace todo automáticamente y te dice qué está pasando.

### Opción 2: Manual
1. Abre terminal en la carpeta del proyecto
2. Ejecuta:
```bat
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

---

## VERIFICACIÓN

Cuando el backend esté corriendo, verás:
```
Uvicorn running on http://127.0.0.1:8000
```

Luego:
1. Abre en el navegador: **http://localhost:8000**
2. El diagnóstico debe decir "Ollama activo" y mostrar los modelos
3. Ahora SÍ puedes usar "Analizar con Ollama"

---

## ¿POR QUÉ TARDABA TANTO?

Ollama genera respuestas complejas que pueden tomar:
- Simple: 10-30 segundos
- Moderado: 30-120 segundos
- Complejo (50 páginas): 2-5 minutos

Aumentamos el timeout a **600 segundos (10 minutos)** para dar suficiente tiempo.

---

## CHECKLIST FINAL

- [ ] Ejecuté `start.bat` o `.\run_windows.bat`
- [ ] Terminal muestra "Uvicorn running on http://127.0.0.1:8000"
- [ ] Abrí http://localhost:8000 en navegador
- [ ] Ollama aparece como "activo" en la página
- [ ] Puedo ver modelos como "qwen2.5:7b"
- [ ] Pegué un documento y presioné "Analizar con Ollama"

Si todo funciona: **¡Listo! Ya puedes usar el MVP**

Si aún falla: Abre PowerShell en la carpeta y ejecuta:
```powershell
powershell -ExecutionPolicy Bypass -File .\fix_ollama.ps1
```
Para diagnóstico detallado.

---

## TIP: Monitorea desde otra terminal

Mientras está corriendo el backend, puedes verificar el estado en otra terminal:
```powershell
curl http://localhost:8000/api/health
```

Debe responder JSON con `"ollama":"ok"` y los modelos disponibles.
