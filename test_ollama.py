#!/usr/bin/env python
"""Diagnostic script to test Ollama connection and JSON generation."""

import requests
import json
import sys

def test_ollama():
    print("=" * 60)
    print("OLLAMA DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing Ollama health endpoint...")
    try:
        resp = requests.get("http://localhost:11434", timeout=5)
        print(f"   ✓ Ollama responds: {resp.status_code}")
        print(f"   Content: {resp.text}")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False
    
    # Test 2: List models
    print("\n2. Checking installed models...")
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = resp.json().get("models", [])
        print(f"   ✓ Found {len(models)} models:")
        for m in models:
            name = m.get("name") or m.get("model")
            print(f"     - {name}")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False
    
    # Test 3: Simple text generation
    print("\n3. Testing simple text generation (30s timeout)...")
    payload = {
        "model": "qwen2.5:7b",
        "prompt": "Say hello in Spanish",
        "stream": False,
    }
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        print(f"   ✓ Response code: {resp.status_code}")
        data = resp.json()
        if data.get("response"):
            print(f"   Response: {data['response'][:100]}...")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False
    
    # Test 4: JSON format generation (CRITICAL TEST)
    print("\n4. Testing JSON format generation (60s timeout)...")
    payload = {
        "model": "qwen2.5:7b",
        "prompt": 'Return ONLY valid JSON: {"message": "hello"}',
        "stream": False,
        "format": "json",
    }
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        print(f"   ✓ Response code: {resp.status_code}")
        data = resp.json()
        response_text = data.get("response", "")
        print(f"   Response: {response_text[:200]}...")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response_text)
            print(f"   ✓ Valid JSON detected: {parsed}")
        except:
            print(f"   ✗ Not valid JSON (expected for this test)")
    except requests.Timeout:
        print(f"   ✗ TIMEOUT after 60s - Ollama is too slow or not responding")
        return False
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_ollama()
    sys.exit(0 if success else 1)
