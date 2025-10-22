#!/usr/bin/env python3
"""
Resource checker for Phase 0 validation
AI Agent: Run this to validate system resources before build
"""

import psutil
import platform
import sys

def check_resources():
    """Validate system has sufficient resources for swarm"""

    print("="*80)
    print("🔍 SYSTEM RESOURCE CHECK")
    print("="*80)

    # Check Python version
    py_version = sys.version_info
    print(f"\nPython Version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 10):
        print("❌ FAIL: Python 3.10+ required")
        return False
    print("✅ PASS: Python version OK")

    # Check architecture
    arch = platform.machine()
    print(f"\nArchitecture: {arch}")
    if 'arm64' not in arch.lower():
        print("⚠️  WARNING: Not ARM64, may have different performance characteristics")
    else:
        print("✅ PASS: ARM64 architecture detected")

    # Check memory
    memory = psutil.virtual_memory()
    total_gb = memory.total / (1024 ** 3)
    available_gb = memory.available / (1024 ** 3)

    print(f"\nTotal Memory: {total_gb:.2f} GB")
    print(f"Available Memory: {available_gb:.2f} GB")

    if available_gb < 10:
        print("❌ FAIL: Less than 10GB available memory")
        return False
    print("✅ PASS: Sufficient memory available")

    # Check CPU
    cpu_count = psutil.cpu_count(logical=True)
    print(f"\nCPU Count: {cpu_count}")
    if cpu_count < 4:
        print("⚠️  WARNING: Less than 4 CPUs detected")
    else:
        print("✅ PASS: Sufficient CPU cores")

    # Check disk space
    disk = psutil.disk_usage('/')
    free_gb = disk.free / (1024 ** 3)
    print(f"\nDisk Space Free: {free_gb:.2f} GB")
    if free_gb < 5:
        print("⚠️  WARNING: Less than 5GB disk space")
    else:
        print("✅ PASS: Sufficient disk space")

    print("\n" + "="*80)
    print("✅ RESOURCE CHECK COMPLETE")
    print("="*80)

    return True

if __name__ == "__main__":
    success = check_resources()
    sys.exit(0 if success else 1)
