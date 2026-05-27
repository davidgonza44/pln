from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import requests


class OllamaError(Exception):
    def __init__(self, message: str, status_code: int = 503, *, error_type: str = "ollama_error"):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type


@dataclass
class OllamaResult:
    raw: str
    parsed: Any | None
    elapsed_ms: int
    parse_status: str
    parse_error: str = ""


_LAST_ERROR: dict[str, Any] = {"message": "", "type": "", "at": ""}


def set_last_error(message: str, error_type: str = "error") -> None:
    _LAST_ERROR.update({"message": message, "type": error_type, "at": time.strftime("%Y-%m-%d %H:%M:%S")})


def get_last_error() -> dict[str, Any]:
    return dict(_LAST_ERROR)


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        *,
        connect_timeout: int = 10,
        generation_timeout: int = 180,
        num_ctx: int = 2048,
        num_predict: int = 300,
        keep_alive: str = "30m",
    ):
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.connect_timeout = connect_timeout
        self.generation_timeout = generation_timeout
        self.num_ctx = num_ctx
        self.num_predict = num_predict
        self.keep_alive = keep_alive

    def list_models(self) -> list[str]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.connect_timeout)
        except requests.RequestException as exc:
            msg = (
                f"Ollama no está disponible en {self.base_url}. Abra Ollama o ejecute 'ollama serve'. "
                f"Detalle técnico: {exc.__class__.__name__}."
            )
            set_last_error(msg, "ollama_unavailable")
            raise OllamaError(msg, 503, error_type="ollama_unavailable") from exc
        if response.status_code >= 400:
            msg = f"Ollama respondió /api/tags con HTTP {response.status_code}: {response.text[:250]}"
            set_last_error(msg, "ollama_http")
            raise OllamaError(msg, 503, error_type="ollama_http")
        data = response.json()
        models = []
        for model in data.get("models", []):
            name = model.get("name") or model.get("model")
            if name:
                models.append(name)
        return models

    def ensure_model(self, model: str) -> None:
        model = (model or "").strip()
        if not model:
            raise OllamaError("Debe seleccionar un modelo de Ollama.", 400, error_type="model_empty")
        models = self.list_models()
        normalized = {m.split(":")[0]: m for m in models}
        if model in models or model.split(":")[0] in normalized:
            return
        installed = ", ".join(models) if models else "ninguno"
        msg = (
            f"El modelo '{model}' no está instalado en Ollama. Modelos instalados: {installed}. "
            f"Ejecute: ollama pull {model}"
        )
        set_last_error(msg, "model_not_installed")
        raise OllamaError(msg, 404, error_type="model_not_installed")

    def generate_text(
        self,
        model: str,
        prompt: str,
        *,
        temperature: float = 0.15,
        num_predict: int | None = None,
        num_ctx: int | None = None,
        timeout: int | None = None,
        format_json: bool = False,
    ) -> tuple[str, int]:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx or self.num_ctx,
                "num_predict": num_predict if num_predict is not None else self.num_predict,
            },
        }
        if format_json:
            payload["format"] = "json"
        started = time.perf_counter()
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout or self.generation_timeout,
            )
        except requests.Timeout as exc:
            msg = (
                "Timeout consultando Ollama. Ollama está activo, pero el modelo tardó demasiado. "
                "Reduzca el tamaño del prompt, use menos chunks o pruebe otro modelo."
            )
            set_last_error(msg, "timeout")
            raise OllamaError(msg, 504, error_type="timeout") from exc
        except requests.RequestException as exc:
            msg = (
                "No se pudo consultar Ollama en /api/generate. "
                "Verifique que Ollama siga abierto y que el backend use la URL correcta. "
                f"Detalle técnico: {exc.__class__.__name__}."
            )
            set_last_error(msg, "generate_connection")
            raise OllamaError(msg, 503, error_type="generate_connection") from exc
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            msg = f"Ollama devolvió HTTP {response.status_code} en /api/generate: {response.text[:500]}"
            set_last_error(msg, "generate_http")
            raise OllamaError(msg, response.status_code, error_type="generate_http")
        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            msg = f"Ollama respondió, pero no fue JSON HTTP válido: {response.text[:300]}"
            set_last_error(msg, "ollama_invalid_http_json")
            raise OllamaError(msg, 502, error_type="ollama_invalid_http_json") from exc
        raw = str(data.get("response", "") or "").strip()
        if not raw:
            msg = "Ollama respondió vacío. Reduzca el prompt o pruebe otro modelo."
            set_last_error(msg, "empty_response")
            raise OllamaError(msg, 502, error_type="empty_response")
        return raw, elapsed_ms

    def generate_structured(
        self,
        model: str,
        prompt: str,
        *,
        temperature: float = 0.15,
        num_predict: int | None = None,
        format_json: bool = True,
    ) -> OllamaResult:
        raw, elapsed_ms = self.generate_text(
            model,
            prompt,
            temperature=temperature,
            num_predict=num_predict,
            format_json=format_json,
        )
        parsed, status, err = parse_json_relaxed(raw)
        return OllamaResult(raw=raw, parsed=parsed, elapsed_ms=elapsed_ms, parse_status=status, parse_error=err)

    def quick_test(self, model: str) -> dict[str, Any]:
        started = time.perf_counter()
        self.ensure_model(model)
        raw, elapsed = self.generate_text(
            model,
            "Responde solo: OK",
            temperature=0.0,
            num_predict=10,
            timeout=60,
            format_json=False,
        )
        return {
            "ok": True,
            "model": model,
            "response": raw[:120],
            "elapsed_ms": elapsed,
            "total_elapsed_ms": round((time.perf_counter() - started) * 1000),
            "options": {
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
                "temperature_default": 0.15,
                "keep_alive": self.keep_alive,
            },
        }


def parse_json_relaxed(text: str) -> tuple[Any | None, str, str]:
    text = (text or "").strip()
    if not text:
        return None, "empty", "Respuesta vacía del modelo."
    try:
        return json.loads(text), "json_puro", ""
    except json.JSONDecodeError as exc:
        first_error = str(exc)

    # Markdown fences: ```json { ... } ```
    fence = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, flags=re.S | re.I)
    if fence:
        try:
            return json.loads(fence.group(1)), "json_en_markdown", ""
        except json.JSONDecodeError as exc:
            first_error = str(exc)

    # Balanced object/array substring. This recovers prose before/after JSON.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if 0 <= start < end:
            candidate = text[start:end + 1]
            try:
                return json.loads(candidate), "json_extraido", ""
            except json.JSONDecodeError as exc:
                first_error = str(exc)

    return None, "texto_libre", first_error


def parse_json_object(text: str) -> dict[str, Any] | list[Any]:
    parsed, status, err = parse_json_relaxed(text)
    if parsed is None:
        raise ValueError(err or "No se encontró JSON válido en la respuesta del modelo.")
    return parsed
