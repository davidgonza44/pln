#!/usr/bin/env python3
"""
Script de prueba para validar mejoras en calidad de afirmaciones y velocidad.
Usa los documentos de muestra en sample_docs/
"""
import json
import time
from backend.services.analysis import run_full_analysis

def load_sample_docs():
    """Carga los documentos de muestra."""
    with open("sample_docs/documento_a.txt", "r", encoding="utf-8") as f:
        doc_a = f.read()
    with open("sample_docs/documento_b.txt", "r", encoding="utf-8") as f:
        doc_b = f.read()
    return doc_a, doc_b

def main():
    print("=" * 70)
    print("PRUEBA DE ANÁLISIS MEJORADO CON MODO RÁPIDO")
    print("=" * 70)
    
    doc_a, doc_b = load_sample_docs()
    
    print(f"\n📄 Documento A ({len(doc_a)} caracteres):")
    print(f"   {doc_a[:150]}...")
    print(f"\n📄 Documento B ({len(doc_b)} caracteres):")
    print(f"   {doc_b[:150]}...")
    
    print("\n" + "=" * 70)
    print("🚀 Iniciando análisis en MODO RÁPIDO (fast_mode=True)...")
    print("=" * 70)
    
    start = time.perf_counter()
    try:
        result = run_full_analysis(
            model="qwen2.5:1.5b",
            doc_a_text=doc_a,
            doc_b_text=doc_b,
            doc_a_name="Política antigua",
            doc_b_name="Manual actualizado",
            max_chunks_per_document=2,
            ollama_base_url="http://localhost:11434",
            fast_mode=True,
        )
        elapsed = time.perf_counter() - start
        
        print(f"\n✅ Análisis completado en {elapsed:.2f}s ({int(elapsed*1000)}ms)")
        
        # Mostrar resumen de resultados
        print("\n" + "=" * 70)
        print("📊 RESULTADOS")
        print("=" * 70)
        
        print(f"\n⏱️  Tiempos:")
        print(f"   Total: {result['meta']['runtime_ms']}ms")
        print(f"   ✓ Bajo 10s: {result['meta']['under_10s']}")
        for phase, ms in result['meta']['phase_times'].items():
            if phase != 'total_ms':
                print(f"   - {phase}: {ms}ms")
        
        print(f"\n📦 Chunks procesados:")
        print(f"   Doc A: {result['meta']['chunks_a']} chunks")
        print(f"   Doc B: {result['meta']['chunks_b']} chunks")
        
        print(f"\n💡 Afirmaciones ({len(result['summaries'])} total):")
        for i, summary in enumerate(result['summaries'], 1):
            print(f"\n   {i}. {summary['statement'][:100]}...")
            print(f"      ID: {summary['id']}")
            print(f"      Confianza: {summary['confidence']:.2f}")
            print(f"      Chunk: {summary['source']['chunk_id']}")
        
        print(f"\n⚠️  Inconsistencias detectadas ({len(result['findings'])} total):")
        for i, finding in enumerate(result['findings'], 1):
            print(f"\n   {i}. [{finding['id']}] {finding['type']}")
            print(f"      {finding['description'][:120]}...")
            print(f"      Confianza: {finding['confidence']:.2f}")
        
        if result['warnings']:
            print(f"\n⚠️  Advertencias:")
            for w in result['warnings']:
                print(f"   - {w}")
        
        print(f"\n📋 Modo: {result['ollama']['mode']}")
        print(f"   Parse status: {result['ollama']['parse_status']}")
        
        print("\n" + "=" * 70)
        print("📄 BORRADOR GENERADO:")
        print("=" * 70)
        print(result['draft'])
        
        # Validaciones
        print("\n" + "=" * 70)
        print("✅ VALIDACIONES")
        print("=" * 70)
        
        checks = [
            (len(result['summaries']) >= 3, f"✓ Mínimo 3 afirmaciones: {len(result['summaries'])}"),
            (result['meta']['under_10s'], f"✓ Respuesta en < 10s: {result['meta']['runtime_ms']}ms"),
            (len(result['findings']) >= 1, f"✓ Al menos 1 inconsistencia: {len(result['findings'])}"),
            (result['ollama']['parse_status'] in ['ok', 'relaxed', 'fallback_extractivo'], 
             f"✓ Parse status válido: {result['ollama']['parse_status']}"),
        ]
        
        for passed, msg in checks:
            symbol = "✅" if passed else "❌"
            print(f"{symbol} {msg}")
        
        all_passed = all(check[0] for check in checks)
        print(f"\n{'🎉 TODAS LAS PRUEBAS PASARON' if all_passed else '⚠️  ALGUNAS PRUEBAS FALLARON'}")
        
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"\n❌ Error después de {elapsed:.2f}s:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
