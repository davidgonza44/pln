from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str
    document: str
    page_estimated: int
    section: str
    paragraph_start: int
    paragraph_end: int
    text: str
    char_start: int
    char_end: int


def normalize_text(text: str) -> str:
    text = (text or "").replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_paragraphs(text: str) -> list[tuple[int, str, int]]:
    """Returns tuples: paragraph_number, paragraph_text, char_start."""
    text = normalize_text(text)
    if not text:
        return []

    parts: list[tuple[int, str, int]] = []
    cursor = 0
    for idx, raw in enumerate(re.split(r"\n\s*\n", text), start=1):
        p = raw.strip()
        if not p:
            continue
        start = text.find(p, cursor)
        if start < 0:
            start = cursor
        cursor = start + len(p)
        parts.append((idx, p, start))
    return parts


def guess_section(text_before: str, fallback: str = "Sección no identificada") -> str:
    lines = [line.strip() for line in text_before.splitlines() if line.strip()]
    for line in reversed(lines[-20:]):
        if len(line) <= 90 and not re.search(r"[.!?;:]$", line):
            return line
        if re.match(r"^(cap[ií]tulo|secci[oó]n|manual|pol[ií]tica|procedimiento|art[ií]culo|anexo)\b", line, re.I):
            return line[:90]
    return fallback


def estimate_page(char_start: int, chars_per_page: int = 1800) -> int:
    return max(1, int(char_start // chars_per_page) + 1)


def chunk_document(text: str, document_label: str, max_chars: int = 1200) -> list[Chunk]:
    text = normalize_text(text)
    paragraphs = split_paragraphs(text)
    chunks: list[Chunk] = []
    if not paragraphs:
        return chunks

    current: list[tuple[int, str, int]] = []
    current_len = 0

    def flush() -> None:
        nonlocal current, current_len
        if not current:
            return
        paragraph_start = current[0][0]
        paragraph_end = current[-1][0]
        char_start = current[0][2]
        combined = "\n\n".join(p for _, p, _ in current).strip()
        char_end = char_start + len(combined)
        section = guess_section(text[:char_start])
        chunk_no = len(chunks) + 1
        prefix = "A" if document_label.lower().endswith("a") or document_label.lower() == "documento a" else "B"
        if not document_label.lower().startswith("documento"):
            prefix = "D"
        chunks.append(
            Chunk(
                chunk_id=f"{prefix}-{chunk_no:03d}",
                document=document_label,
                page_estimated=estimate_page(char_start),
                section=section,
                paragraph_start=paragraph_start,
                paragraph_end=paragraph_end,
                text=combined,
                char_start=char_start,
                char_end=char_end,
            )
        )
        current = []
        current_len = 0

    for paragraph in paragraphs:
        _, p_text, _ = paragraph
        extra_len = len(p_text) + 2
        if current and current_len + extra_len > max_chars:
            flush()
        if len(p_text) > max_chars:
            # Split unusually long paragraphs.
            start_idx = 0
            para_no, _, para_start = paragraph
            prefix = "A" if document_label.lower().endswith("a") or document_label.lower() == "documento a" else "B"
            if not document_label.lower().startswith("documento"):
                prefix = "D"
            while start_idx < len(p_text):
                part = p_text[start_idx:start_idx + max_chars].strip()
                chunks.append(
                    Chunk(
                        chunk_id=f"{prefix}-{len(chunks)+1:03d}",
                        document=document_label,
                        page_estimated=estimate_page(para_start + start_idx),
                        section=guess_section(text[:para_start]),
                        paragraph_start=para_no,
                        paragraph_end=para_no,
                        text=part,
                        char_start=para_start + start_idx,
                        char_end=para_start + start_idx + len(part),
                    )
                )
                start_idx += max_chars
            continue
        current.append(paragraph)
        current_len += extra_len

    flush()
    return chunks


def context_from_chunks(chunks: list[Chunk], max_total_chars: int = 12000) -> tuple[str, list[str]]:
    warnings: list[str] = []
    parts: list[str] = []
    total = 0
    included = 0
    for chunk in chunks:
        header = (
            f"[CHUNK {chunk.chunk_id}]\n"
            f"Documento: {chunk.document}\n"
            f"Página estimada: {chunk.page_estimated}\n"
            f"Sección: {chunk.section}\n"
            f"Párrafos: {chunk.paragraph_start}-{chunk.paragraph_end}\n"
            f"Texto:\n{chunk.text}\n"
        )
        if total + len(header) > max_total_chars:
            warnings.append(
                "El contexto enviado al LLM fue limitado para evitar saturar el modelo local; "
                "para producción se requiere map-reduce/RAG por lotes."
            )
            break
        parts.append(header)
        total += len(header)
        included += 1
    if included < len(chunks):
        warnings.append(f"Se incluyeron {included}/{len(chunks)} chunks en la llamada principal a Ollama.")
    return "\n---\n".join(parts), warnings
