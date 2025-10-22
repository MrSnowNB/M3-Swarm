#!/usr/bin/env python3
"""
Test script to validate Python imports for Swarm-100
Following Phase 1 Dependency Installation guide
"""

import sys
import os

# Add current directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import asyncio
    print("✅ asyncio imported")
except ImportError as e:
    print(f"❌ asyncio import failed: {e}")

try:
    import psutil
    print("✅ psutil imported")
except ImportError as e:
    print(f"❌ psutil import failed: {e}")

try:
    import yaml as yaml_module  # alias to avoid confusion
    print("✅ pyyaml imported")
except ImportError as e:
    print(f"❌ pyyaml import failed: {e}")

try:
    import ollama
    print(f"✅ ollama imported (version: {getattr(ollama, '__version__', 'unknown')})")

    # Test basic async client creation
    try:
        client = ollama.AsyncClient()
        print("✅ AsyncClient created successfully")
    except Exception as e:
        print(f"⚠️  AsyncClient creation failed: {e}")

except ImportError as e:
    print(f"❌ ollama import failed: {e}")

# Summary
print("\n--- IMPORT VALIDATION COMPLETE ---")
missing = []
try:
    import ollama
except ImportError:
    missing.append("ollama")
try:
    import psutil
except ImportError:
    missing.append("psutil")
try:
    import yaml
except ImportError:
    missing.append("yaml")

if missing:
    print(f"❌ Missing packages: {', '.join(missing)}")
    sys.exit(1)
else:
    print("✅ All required packages imported successfully")
    sys.exit(0)
