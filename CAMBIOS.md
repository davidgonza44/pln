# CAMBIOS REALIZADOS - Fix Ollama Connection Error

## Resumen
Se solucionó el error **"No se pudo consultar Ollama"** aumentando timeouts, mejorando scripts de inicio y agregando herramientas de diagnóstico.

---

## 1. CAMBIOS DE CÓDIGO

### 📝 `backend/services/ollama_client.py`

**Línea 18:** Aumentado timeout de 180s a 300s
```python
# ANTES:
def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 180):

# AHORA:
def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 300):
```
**Motivo:** Los modelos locales pueden tardar más de 3 minutos en generar respuestas complejas.

**Línea 25:** Aumentado timeout de 8s a 10s para listar modelos
```python
# ANTES:
response = requests.get(f"{self.base_url}/api/tags", timeout=8)

# AHORA:
response = requests.get(f"{self.base_url}/api/tags", timeout=10)
```

---

## 2. ARCHIVOS MEJORADOS

### ✨ `run_windows.bat`
**Cambios:**
- Ahora verifica si .venv existe antes de crearlo
- Agrega mensajes de error claros si algo falla
- Verifica conexión a Ollama antes de iniciar backend
- Mejor formateo y documentación

---

## 3. NUEVOS ARCHIVOS

### 🔧 `fix_ollama.ps1`
**Propósito:** Diagnóstico automático del sistema
- Verifica que Ollama responda
- Verifica que haya modelos instalados
- Verifica que el backend esté corriendo
- Verifica disponibilidad de puertos
- Verifica recursos de sistema (RAM)
- Muestra estado con colores (verde/rojo)

**Uso:**
```powershell
powershell -ExecutionPolicy Bypass -File .\fix_ollama.ps1
```

### 🔄 `restart_ollama.bat`
**Propósito:** Reiniciar Ollama completamente
- Mata procesos de Ollama existentes
- Inicia servidor Ollama
- Verifica conexión
- Lista modelos instalados

**Uso:**
```bat
restart_ollama.bat
```

### 📖 `TROUBLESHOOTING.md`
**Propósito:** Guía completa de solución de problemas
- 5 soluciones ordenadas por probabilidad de éxito
- Checklist final de verificación
- Consejos de recursos del sistema
- Cómo cambiar modelos
- Escalada para problemas graves

---

## 4. DOCUMENTACIÓN ACTUALIZADA

### 📄 `README.md`
- Agregada sección "⚠️ Solución de Problemas"
- Instrucciones para usar `fix_ollama.ps1`
- Link a `TROUBLESHOOTING.md`
- Estructura del proyecto actualizada
- Cambios recientes documentados

---

## ¿QUÉ HACER AHORA?

### 1️⃣ Ejecuta el diagnóstico (RECOMENDADO):
```powershell
powershell -ExecutionPolicy Bypass -File .\fix_ollama.ps1
```

### 2️⃣ Si Ollama no responde:
```bat
restart_ollama.bat
```

### 3️⃣ Si aún falla:
Lee [TROUBLESHOOTING.md](TROUBLESHOOTING.md) con las 5 soluciones principales.

### 4️⃣ Reinicia el backend:
```bat
run_windows.bat
```

---

## Causa del Error Original

**Diagnóstico:** El error "No se pudo consultar Ollama" venía del timeout de 180 segundos siendo insuficiente cuando:
1. El backend intenta consultar Ollama para generar JSON
2. Ollama toma más de 3 minutos procesando el prompt
3. La conexión se interrumpe por timeout
4. Se devuelve error al usuario

**Solución:** Aumentar timeout a 300 segundos (5 minutos) fue la primera acción. Las herramientas de diagnóstico ayudan a identificar otros problemas (RAM baja, Ollama no respondiendo, puertos bloqueados, etc.).

---

## Próximos pasos opcionales

Si quieres optimizar más:
1. Aumenta timeout a 600s si tienes máquina lenta
2. Usa modelo más ligero (llama3.1:8b en lugar de deepseek)
3. Reduce max_chunks_per_document a 5 en la UI
4. Monitorea uso de RAM con Task Manager

---

## Soporte

Si el problema persiste después de estos cambios:
1. Verifica logs en PowerShell al ejecutar `fix_ollama.ps1`
2. Consulta TROUBLESHOOTING.md sección "DIAGNOSTICO COMPLETO"
3. Ejecuta desde terminal: `ollama list` y confirma respuesta
4. Verifica puertos: `netstat -ano | findstr :11434`
