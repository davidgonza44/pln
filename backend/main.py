from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .services.analysis import run_full_analysis
from .services.extractor import ExtractionError, extract_text_from_file
from .services.ollama_client import OllamaClient, OllamaError, get_last_error

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="MVP PLN IA con Ollama Local",
    description="Backend local para extracción documental, análisis con Ollama y trazabilidad.",
    version="1.0.0-mvp",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _warmup_ollama() -> None:
    """Precarga el modelo en memoria al arrancar para que la primera consulta no tarde extra."""
    try:
        models = OllamaClient().list_models()
        if not models:
            return
        model = next((m for m in models if "qwen2.5" in m), models[0])
        requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": "OK", "stream": False, "keep_alive": "30m"},
            timeout=30,
        )
    except Exception:
        pass


threading.Thread(target=_warmup_ollama, daemon=True).start()


class AnalyzeRequest(BaseModel):
    model: str = Field(default="qwen2.5:1.5b", description="Modelo local instalado en Ollama.")
    ollama_base_url: str = Field(default="http://localhost:11434")
    doc_a_text: str = ""
    doc_b_text: str = ""
    doc_a_name: str = "Documento A"
    doc_b_name: str = "Documento B"
    max_chunks_per_document: int = Field(default=3, ge=1, le=30)
    fast_mode: bool = Field(default=True, description="Limita chunks/salida para responder más rápido con modelos pequeños.")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    status = {"backend": "ok", "ollama": "unavailable", "models": [], "detail": ""}
    client = OllamaClient()
    try:
        models = client.list_models()
        status.update({"ollama": "ok", "models": models})
    except OllamaError as exc:
        status["detail"] = str(exc)
    return status


@app.get("/api/models")
def models() -> dict:
    client = OllamaClient()
    try:
        return {"models": client.list_models()}
    except OllamaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@app.post("/api/extract")
async def extract(file: UploadFile = File(...), doc_label: Optional[str] = Form(default="Documento")) -> dict:
    content = await file.read()
    try:
        result = extract_text_from_file(file.filename or "archivo", content)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "filename": result.filename,
        "extension": result.extension,
        "text": result.text,
        "detail": result.detail,
        "warnings": result.warnings,
        "doc_label": doc_label,
    }



@app.get("/api/diagnostics")
def diagnostics(model: str = "qwen2.5:1.5b", ollama_base_url: str = "http://localhost:11434") -> dict:
    """Diagnóstico específico para diferenciar Ollama caído, modelo faltante, timeout y errores de formato."""
    import platform
    import sys
    import time

    client = OllamaClient(base_url=ollama_base_url, generation_timeout=60)
    started = time.perf_counter()
    result = {
        "backend": "ok",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "ollama_base_url": ollama_base_url,
        "selected_model": model,
        "models": [],
        "model_installed": False,
        "llm_test": None,
        "options": {
            "num_ctx": client.num_ctx,
            "num_predict": client.num_predict,
            "keep_alive": client.keep_alive,
            "stream": False,
            "format_json": "relaxed/fallback",
        },
        "last_error": get_last_error(),
    }
    try:
        models = client.list_models()
        result["models"] = models
        result["model_installed"] = model in models or model.split(":")[0] in {m.split(":")[0] for m in models}
        if result["model_installed"]:
            result["llm_test"] = client.quick_test(model)
        else:
            result["llm_test"] = {"ok": False, "detail": f"Modelo no instalado: {model}"}
    except OllamaError as exc:
        result["llm_test"] = {"ok": False, "detail": str(exc), "type": exc.error_type, "status_code": exc.status_code}
    result["diagnostics_elapsed_ms"] = round((time.perf_counter() - started) * 1000)
    result["last_error"] = get_last_error()
    return result

@app.post("/api/analyze")
def analyze(payload: AnalyzeRequest) -> dict:
    return run_full_analysis(
        model=payload.model.strip(),
        doc_a_text=payload.doc_a_text,
        doc_b_text=payload.doc_b_text,
        doc_a_name=payload.doc_a_name,
        doc_b_name=payload.doc_b_name,
        max_chunks_per_document=payload.max_chunks_per_document,
        ollama_base_url=payload.ollama_base_url,
        fast_mode=payload.fast_mode,
    )
