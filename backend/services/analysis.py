from __future__ import annotations

import re
import time
from typing import Any

from fastapi import HTTPException

from .chunker import Chunk, chunk_document, context_from_chunks
from .ollama_client import OllamaClient, OllamaError




def build_chunk_lookup(chunks: list[Chunk]) -> dict[str, Chunk]:
    return {chunk.chunk_id: chunk for chunk in chunks}


def chunk_ref(chunk: Chunk | None, fallback_doc: str = "Documento no identificado") -> dict[str, Any]:
    if not chunk:
        return {
            "document": fallback_doc,
            "chunk_id": "no-identificado",
            "page_estimated": None,
            "section": "No identificada",
            "paragraph_start": None,
            "paragraph_end": None,
            "fragment": "No se pudo asociar el resultado a un chunk fuente. Revisar manualmente.",
        }
    return {
        "document": chunk.document,
        "chunk_id": chunk.chunk_id,
        "page_estimated": chunk.page_estimated,
        "section": chunk.section,
        "paragraph_start": chunk.paragraph_start,
        "paragraph_end": chunk.paragraph_end,
        "fragment": chunk.text[:900] + ("…" if len(chunk.text) > 900 else ""),
    }


def clamp_confidence(value: Any, default: float = 0.70) -> float:
    try:
        number = float(value)
    except Exception:
        number = default
    return max(0.0, min(1.0, number))


def safe_str(value: Any, max_len: int = 4000) -> str:
    return str(value or "").strip()[:max_len]


def split_candidate_sentences(text: str) -> list[str]:
    lines = []
    for raw in (text or "").splitlines():
        line = re.sub(r"^\s*[-*•\d.)]+\s*", "", raw).strip()
        if len(line) >= 35:
            lines.append(line)
    if lines:
        return lines
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if len(s.strip()) >= 35]


def best_chunk_for_text(text: str, chunks: list[Chunk]) -> Chunk | None:
    if not chunks:
        return None
    words = {w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]{4,}", text or "")}
    if not words:
        return chunks[0]
    best = None
    best_score = -1
    for chunk in chunks:
        chunk_words = {w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]{4,}", chunk.text)}
        score = len(words & chunk_words)
        if score > best_score:
            best_score = score
            best = chunk
    return best or chunks[0]


def extract_keywords(text: str, max_terms: int = 12) -> list[str]:
    stopwords = {
        "de", "la", "el", "los", "las", "y", "o", "a", "en", "por", "para", "con",
        "se", "del", "al", "que", "como", "es", "su", "sus", "una", "un", "más", "no",
        "son", "al", "si", "pero", "entre", "sobre", "como", "para", "este", "esta",
    }
    words = [w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{4,}", text or "") if w.lower() not in stopwords]
 
 

def split_raw_statements(text: str, max_items: int = 3) -> list[str]:
    if not text:
        return []
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    if len(parts) >= max_items:
        return parts[:max_items]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        return lines[:max_items]
    return [text.strip()] if text.strip() else []


def _make_summary(idx: int, statement: str, chunk: Chunk | None, confidence: float = 0.55, label_extra: str = "") -> dict[str, Any]:
    source = chunk_ref(chunk)
    if chunk:
        source["evidence_quote"] = chunk.text[:260] + ("…" if len(chunk.text) > 260 else "")
    return {
        "id": f"S{idx}",
        "statement": safe_str(statement, 1200),
        "source": source,
        "confidence": confidence,
        "status": "pending",
        "label": "Salida generada por Ollama local" + (f" · {label_extra}" if label_extra else ""),
    }
def run_full_analysis(
    *,
    model: str,
    doc_a_text: str,
    doc_b_text: str = "",
    doc_a_name: str = "Documento A",
    doc_b_name: str = "Documento B",
    max_chunks_per_document: int = 3,
    ollama_base_url: str = "http://localhost:11434",
    fast_mode: bool = True,
) -> dict[str, Any]:
    """Versión estrita para responder rápido sin fallback local.

    Cambios:
    - Una sola llamada a Ollama para resumen + contradicciones + borrador.
    - Timeout de generación de 5s en modo rápido.
    - Máximo 1 chunk/documento en modo rápido.
    - Sin fallback local: si Ollama no responde, la llamada falla con error.
    """
    started = time.perf_counter()
    phase_times: dict[str, int] = {}
    warnings: list[str] = []

    # Ajustes rápidos y estrictos para máxima probabilidad de respuesta directa.
    client = OllamaClient(
        base_url=ollama_base_url,
        connect_timeout=2,
        generation_timeout=5 if fast_mode else 18,
        num_ctx=1280 if fast_mode else 2048,
        num_predict=220 if fast_mode else 360,
        keep_alive="30m",
    )

    phase_start = time.perf_counter()
    phase_times["verificacion_ollama_ms"] = 0

    phase_start = time.perf_counter()
    if fast_mode:
        effective_max_chunks = 1
        chunk_size = 700
        context_limit = 1600
        warnings.append("Modo rápido estricto activo: 1 chunk por documento y contexto optimizado para Ollama.")
    else:
        effective_max_chunks = min(max_chunks_per_document or 3, 4)
        chunk_size = 1000
        context_limit = 6000

    all_chunks_a = chunk_document(doc_a_text, doc_a_name or "Documento A", max_chars=chunk_size)
    all_chunks_b = chunk_document(doc_b_text, doc_b_name or "Documento B", max_chars=chunk_size) if doc_b_text.strip() else []
    chunks_a = all_chunks_a[:effective_max_chunks]
    chunks_b = all_chunks_b[:effective_max_chunks] if all_chunks_b else []
    chunks = chunks_a + chunks_b
    phase_times["chunking_ms"] = round((time.perf_counter() - phase_start) * 1000)

    if not chunks:
        raise HTTPException(status_code=400, detail="Debe proporcionar texto o cargar al menos un documento con contenido extraíble.")

    if len(all_chunks_a) > len(chunks_a):
        warnings.append(f"{doc_a_name} fue limitado a {len(chunks_a)}/{len(all_chunks_a)} chunks para responder rápido.")
    if all_chunks_b and len(all_chunks_b) > len(chunks_b):
        warnings.append(f"{doc_b_name} fue limitado a {len(chunks_b)}/{len(all_chunks_b)} chunks para responder rápido.")

    context, context_warnings = context_from_chunks(chunks, max_total_chars=context_limit)
    warnings.extend(context_warnings)
    lookup = build_chunk_lookup(chunks)

    summaries: list[dict[str, Any]]
    findings: list[dict[str, Any]]
    draft: str
    parse_status = "unknown"

    phase_start = time.perf_counter()
    selected_chunks = select_top_chunks(chunks_a, num_chunks=3)
    keywords = extract_keywords(doc_a_text, max_terms=12)
    trace_fragments = [
        {
            "chunk_id": chunk.chunk_id,
            "document": chunk.document,
            "page_estimated": chunk.page_estimated,
            "section": chunk.section,
            "paragraph_start": chunk.paragraph_start,
            "paragraph_end": chunk.paragraph_end,
            "text_excerpt": chunk.text[:320],
            "keywords": extract_keywords(chunk.text, max_terms=5),
        }
        for chunk in selected_chunks
    ]

    prompt = _one_shot_prompt(selected_chunks, keywords)
    try:
        raw, elapsed = client.generate_text(
            model,
            prompt,
            temperature=0.1,
            num_predict=120 if fast_mode else 120,
            num_ctx=768 if fast_mode else 1024,
            timeout=8 if fast_mode else 18,
        )
        phase_times["ollama_total_ms"] = elapsed
        parse_status = "plain_text"
        summaries = []
        for idx, statement in enumerate(split_raw_statements(raw, max_items=3), start=1):
            chunk = selected_chunks[idx - 1] if idx - 1 < len(selected_chunks) else None
            summaries.append(_make_summary(idx, statement, chunk, 0.70, "redacción corta"))
        if not summaries:
            raise HTTPException(status_code=502, detail="Ollama no devolvió frases cortas válidas.")
        findings = []
        draft = raw.strip()
    except OllamaError as exc:
        phase_times["ollama_total_ms"] = round((time.perf_counter() - phase_start) * 1000)
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    phase_times["total_ms"] = elapsed_ms
    under_10s = elapsed_ms <= 10000

    return {
        "status": "ok",
        "mvp_notice": (
            "MVP académico en modo rápido estricto. Ollama solo redacta 3 frases cortas a partir de 3 fragmentos locales."
        ),
        "ollama": {
            "base_url": ollama_base_url,
            "model": model,
            "mode": "local_llm_redaction",
            "parse_status": parse_status,
        },
        "meta": {
            "runtime_ms": elapsed_ms,
            "under_10s": under_10s,
            "chunks_a": len(chunks_a),
            "chunks_b": len(chunks_b),
            "doc_a_name": doc_a_name,
            "doc_b_name": doc_b_name,
            "fast_mode": fast_mode,
            "phase_times": phase_times,
        },
        "warnings": warnings,
        "keywords": keywords,
        "trace_fragments": trace_fragments,
        "summaries": summaries,
        "findings": [],
        "draft": draft,
        "metrics": {
            "latencia_objetivo": "<=10s en modo rápido con 3 fragmentos y redacción corta",
            "latencia_resultado_actual": f"{elapsed_ms} ms",
            "estado": "cumplido en esta ejecución" if under_10s else "no cumplido en esta ejecución",
            "nota": "Se usa Ollama solo para redacción corta, no para análisis comparativo."
        },
    }
