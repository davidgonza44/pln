# Solución de Problemas - MVP PLN Ollama

## Problema: "Error: No se pudo consultar Ollama"

Este error ocurre cuando el backend no puede conectarse a Ollama para generar análisis. Aquí están las soluciones ordenadas por probabilidad:

### ✓ VERIFICACIÓN RÁPIDA (Haz esto primero)

```powershell
# 1. Abre PowerShell y ejecuta:
curl http://localhost:11434

# Debe responder: "Ollama is running"
# Si NO responde, Ollama no está activo

# 2. Verifica que tienes modelos
ollama list

# Debe mostrar modelos como qwen2.5:7b, llama3, etc.
# Si está vacío, ejecuta: ollama pull qwen2.5:7b
```

---

## SOLUCIÓN 1: Reinicia Ollama (60% de probabilidad de resolver)

**En Windows:**
1. Busca el icono de Ollama en la **bandeja del sistema** (esquina inferior derecha)
2. Haz clic derecho → "Quit" (Salir)
3. Espera 3 segundos
4. Abre la aplicación Ollama nuevamente
5. Espera a que cargue (2-3 segundos)
6. Verifica: `curl http://localhost:11434`

**Desde terminal (alternativa):**
```powershell
# Script automático para reiniciar Ollama:
restart_ollama.bat
```

---

## SOLUCIÓN 2: Reinicia el Backend (25% de probabilidad)

```powershell
# 1. Abre una terminal en la carpeta del proyecto
cd c:\ruta\a\pln_ollama_mvp

# 2. Ejecuta el script de inicio mejorado
.\run_windows.bat

# El script ahora verifica automáticamente Ollama y mejora manejo de errores
```

---

## SOLUCIÓN 3: Aumenta los Timeouts (10% de probabilidad)

Si Ollama responde pero **muy lentamente**, aumenta el timeout:

**Archivo:** `backend/services/ollama_client.py`

Línea 18 (ya se aumentó de 180 a 300 segundos):
```python
def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 300):
```

Puedes aumentarlo más si es necesario:
```python
timeout: int = 600  # 10 minutos (máximo recomendado)
```

---

## SOLUCIÓN 4: Verifica Recursos del Sistema (3% de probabilidad)

Si Ollama se comporta lentamente o se cuelga:

1. **Memoria disponible:** Ollama necesita al menos 4GB de RAM libre
   ```powershell
   Get-WmiObject win32_operatingsystem | select FreePhysicalMemory
   ```

2. **GPU disponible:** Si tienes GPU NVIDIA/AMD, asegúrate de que Ollama la esté usando
   ```powershell
   ollama list  # Verifica el estado
   ```

3. **Puerto 11434 en uso:** Verifica que nadie más está usando ese puerto
   ```powershell
   netstat -ano | findstr :11434
   ```

---

## SOLUCIÓN 5: Cambia de Modelo (2% de probabilidad)

Algunos modelos son más pesados. Intenta con uno más ligero:

```powershell
# Desinstalar modelo pesado
ollama rm deepseek-r1:latest

# Instalar modelo ligero
ollama pull qwen2.5:7b
ollama pull llama3:8b

# Después, en la UI, selecciona el nuevo modelo
```

---

## DIAGNÓSTICO COMPLETO

Crea un archivo `diagnose.py` en la carpeta del proyecto:

```python
import requests
import subprocess

print("=== OLLAMA DIAGNOSTIC ===\n")

# 1. Check health
try:
    r = requests.get("http://localhost:11434", timeout=5)
    print("✓ Ollama health:", r.text)
except Exception as e:
    print("✗ Ollama connection failed:", e)
    exit(1)

# 2. Check models
try:
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    models = [m.get("name") for m in r.json().get("models", [])]
    print(f"✓ Models installed: {len(models)}")
    for m in models:
        print(f"  - {m}")
except Exception as e:
    print("✗ Failed to list models:", e)

# 3. Test simple generation (30s timeout)
print("\nTesting generation (30s timeout)...")
try:
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen2.5:7b", "prompt": "test", "stream": False},
        timeout=30
    )
    print(f"✓ Generation works: {r.status_code}")
except requests.Timeout:
    print("✗ Generation TIMEOUT - Ollama is too slow or stuck")
except Exception as e:
    print(f"✗ Generation failed: {e}")
```

Ejecuta con:
```powershell
python diagnose.py
```

---

## ESCALADA: Si nada funciona

1. **Reinstala Ollama:**
   - Ve a https://ollama.ai
   - Descarga e instala nuevamente
   - Reinicia Windows

2. **Reinstala modelos:**
   ```powershell
   ollama pull qwen2.5:7b
   ```

3. **Verifica logs de Ollama:**
   - En Windows, busca: `C:\Users\{tu usuario}\.ollama\logs`

4. **Contacta soporte:**
   - Sube los logs a un issue de GitHub

---

## CHECKLIST FINAL

- [ ] Ollama está abierto (`curl http://localhost:11434` responde)
- [ ] Hay modelos instalados (`ollama list` muestra modelos)
- [ ] Backend está corriendo (`curl http://localhost:8000/api/health` responde con JSON)
- [ ] Puerto 8000 está libre (no conflictua con otra aplicación)
- [ ] Tienes suficiente RAM (mínimo 4GB libre)

Si todos los checks pasan pero aún tienes el error, **el problema está en el timeout de generación**. Prueba:

```powershell
# Aumenta timeout a 10 minutos en backend/services/ollama_client.py
# Línea 18: timeout: int = 600
```

Luego reinicia el backend con `.\run_windows.bat`
