#!/usr/bin/env python3
"""
Debug script to see Ollama API response format
"""

import ollama

client = ollama.Client(host='http://localhost:11434')
models = client.list()
print("Full API response:")
print(models)
print("\nType:", type(models))
try:
    print("Keys:", models.keys())  # type: ignore
except (AttributeError, TypeError):
    print("Keys: No keys method")
