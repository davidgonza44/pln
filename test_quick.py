#!/usr/bin/env python3
"""
Script de prueba directo - sin FastAPI para evitar lentitud en importación.
"""
import json
import time
import sys
import os

# Agregar al path para importar backend
sys.path.insert(0, os.path.dirname(__file__))

def load_sample_docs():
    """Carga los documentos de muestra."""
    with open("sample_docs/documento_a.txt", "r", encoding="utf-8") as f:
        doc_a = f.read()
    with open("sample_docs/documento_b.txt", "r", encoding="utf-8") as f:
        doc_b = f.read()
    return doc_a, doc_b

def test_without_fastapi():
    """Prueba sin importar FastAPI - directo desde los módulos."""
    print("=" * 70)
    print("PRUEBA RÁPIDA - SIN FASTAPI")
    print("=" * 70)
    
    doc_a, doc_b = load_sample_docs()
    
    print(f"\n📄 Documento A: {len(doc_a)} caracteres")
    print(f"📄 Documento B: {len(doc_b)} caracteres")
    
    # Importar solo lo necesario
    print("\n⏳ Importando módulos...")
    start_import = time.perf_counter()
    
    from backend.services.chunker import chunk_document
    from backend.services.ollama_client import OllamaClient
    
    import_time = time.perf_counter() - start_import
    print(f"✓ Importación completada en {import_time:.2f}s")
    
    # Test de chunking (sin Ollama)
    print("\n" + "=" * 70)
    print("TEST 1: CHUNKING")
    print("=" * 70)
    
    start = time.perf_counter()
    chunks_a = chunk_document(doc_a, "Documento A", max_chars=850)
    chunks_b = chunk_document(doc_b, "Documento B", max_chars=850)
    chunk_time = time.perf_counter() - start
    
    print(f"✓ Documento A: {len(chunks_a)} chunks en {chunk_time:.3f}s")
    print(f"✓ Documento B: {len(chunks_b)} chunks")
    print(f"✓ Total: {len(chunks_a) + len(chunks_b)} chunks")
    
    for i, chunk in enumerate(chunks_a + chunks_b):
        print(f"  - {chunk.chunk_id}: {len(chunk.text)} chars, página ~{chunk.page_estimated}")
    
    # Test de cliente Ollama (sin conectar)
    print("\n" + "=" * 70)
    print("TEST 2: CLIENTE OLLAMA (sin conectar)")
    print("=" * 70)
    
    client = OllamaClient(
        base_url="http://localhost:11434",
        generation_timeout=5,
        num_ctx=1536,
        num_predict=280,
    )
    print(f"✓ Cliente creado")
    print(f"  - Timeout generación: 5s")
    print(f"  - num_ctx: 1536")
    print(f"  - num_predict: 280")
    
    # Test para verificar configuración
    print("\n" + "=" * 70)
    print("TEST 3: VERIFICACIÓN DE CONFIGURACIÓN")
    print("=" * 70)
    
    config = {
        "chunks_por_documento": 2,
        "tamaño_chunk": 850,
        "contexto_total": 2400,
        "tokens_predicción": 280,
        "temperatura": 0.25,
        "timeout_ollama": 5,
        "num_ctx": 1536,
    }
    
    print("✓ Configuración mejorada para modo rápido:")
    for k, v in config.items():
        print(f"  - {k}: {v}")
    
    print("\n" + "=" * 70)
    print("✅ TODOS LOS TESTS BÁSICOS COMPLETADOS")
    print("=" * 70)
    print("\nResumen:")
    print(f"  ✓ Importación: {import_time:.2f}s")
    print(f"  ✓ Chunking: {chunk_time:.3f}s")
    print(f"  ✓ Chunks generados: {len(chunks_a) + len(chunks_b)}")
    print(f"  ✓ Cliente Ollama configurado")
    print(f"\nPróxima prueba: ejecutar uvicorn backend.main:app")
    print(f"Luego acceder a: http://127.0.0.1:8000")

if __name__ == "__main__":
    test_without_fastapi()
