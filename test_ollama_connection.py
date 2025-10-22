#!/usr/bin/env python3
"""
Test Ollama connection for Phase 1 validation
AI Agent: Run this to verify Ollama is accessible
"""

import sys

try:
    import ollama
    print("✅ ollama package imported successfully")
except ImportError as e:
    print(f"❌ Failed to import ollama: {e}")
    sys.exit(1)

def test_connection():
    """Test connection to Ollama service"""
    print("\n" + "="*80)
    print("🔌 OLLAMA CONNECTION TEST")
    print("="*80)

    try:
        # Create client
        client = ollama.Client(host='http://localhost:11434')
        print("\n✅ Ollama client created")

        # List models
        response = client.list()
        models_list = response.models
        print(f"\n📋 Available models: {len(models_list)}")

        for model in models_list:
            print(f"  - {model.model} ({model.details.parameter_size}, {model.details.quantization_level})")

        # Check for gemma3:270m
        model_names = [m.model for m in models_list]
        if 'gemma3:270m' in model_names:
            print("\n✅ gemma3:270m is available")
        else:
            print("\n⚠️  gemma3:270m not found. Run: ollama pull gemma3:270m")

        print("\n" + "="*80)
        print("✅ OLLAMA CONNECTION SUCCESS")
        print("="*80)
        return True

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\n💡 Make sure Ollama is running: ollama serve")
        print("="*80)
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
