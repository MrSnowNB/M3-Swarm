
# 7. Create utility files and test scripts

# check_resources.py
check_resources = '''#!/usr/bin/env python3
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
    print(f"\\nPython Version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 10):
        print("❌ FAIL: Python 3.10+ required")
        return False
    print("✅ PASS: Python version OK")
    
    # Check architecture
    arch = platform.machine()
    print(f"\\nArchitecture: {arch}")
    if 'arm64' not in arch.lower():
        print("⚠️  WARNING: Not ARM64, may have different performance characteristics")
    else:
        print("✅ PASS: ARM64 architecture detected")
    
    # Check memory
    memory = psutil.virtual_memory()
    total_gb = memory.total / (1024 ** 3)
    available_gb = memory.available / (1024 ** 3)
    
    print(f"\\nTotal Memory: {total_gb:.2f} GB")
    print(f"Available Memory: {available_gb:.2f} GB")
    
    if available_gb < 10:
        print("❌ FAIL: Less than 10GB available memory")
        return False
    print("✅ PASS: Sufficient memory available")
    
    # Check CPU
    cpu_count = psutil.cpu_count(logical=True)
    print(f"\\nCPU Count: {cpu_count}")
    if cpu_count < 4:
        print("⚠️  WARNING: Less than 4 CPUs detected")
    else:
        print("✅ PASS: Sufficient CPU cores")
    
    # Check disk space
    disk = psutil.disk_usage('/')
    free_gb = disk.free / (1024 ** 3)
    print(f"\\nDisk Space Free: {free_gb:.2f} GB")
    if free_gb < 5:
        print("⚠️  WARNING: Less than 5GB disk space")
    else:
        print("✅ PASS: Sufficient disk space")
    
    print("\\n" + "="*80)
    print("✅ RESOURCE CHECK COMPLETE")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = check_resources()
    sys.exit(0 if success else 1)
'''

with open("swarm_macos/utils/check_resources.py", "w") as f:
    f.write(check_resources)

print("✅ Created: utils/check_resources.py")

# test_ollama_connection.py
test_ollama = '''#!/usr/bin/env python3
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
    print("\\n" + "="*80)
    print("🔌 OLLAMA CONNECTION TEST")
    print("="*80)
    
    try:
        # Create client
        client = ollama.Client(host='http://localhost:11434')
        print("\\n✅ Ollama client created")
        
        # List models
        models = client.list()
        print(f"\\n📋 Available models: {len(models.get('models', []))}")
        
        for model in models.get('models', []):
            print(f"  - {model['name']}")
        
        # Check for gemma3:270m
        model_names = [m['name'] for m in models.get('models', [])]
        if 'gemma3:270m' in model_names:
            print("\\n✅ gemma3:270m is available")
        else:
            print("\\n⚠️  gemma3:270m not found. Run: ollama pull gemma3:270m")
        
        print("\\n" + "="*80)
        print("✅ OLLAMA CONNECTION SUCCESS")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"\\n❌ Connection failed: {e}")
        print("\\n💡 Make sure Ollama is running: ollama serve")
        print("="*80)
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
'''

with open("swarm_macos/tests/test_ollama_connection.py", "w") as f:
    f.write(test_ollama)

print("✅ Created: tests/test_ollama_connection.py")

# diagnostics.py
diagnostics = '''"""
Diagnostic utilities for error detection and recovery
AI Agent: Use these functions to monitor and diagnose issues
"""

import psutil
import time
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class DiagnosticResult:
    """Result of diagnostic check"""
    check_name: str
    status: str  # OK | WARNING | ERROR
    message: str
    data: Dict[str, Any]
    timestamp: float

class SystemDiagnostics:
    """Monitor and diagnose system health"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.history: List[DiagnosticResult] = []
        self.logger = logging.getLogger(__name__)
    
    def check_memory_pressure(self) -> DiagnosticResult:
        """Check if system is under memory pressure"""
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        available_gb = memory.available / (1024 ** 3)
        
        max_threshold = self.config.get('swarm', {}).get('resource_limits', {}).get('max_memory_percent', 80)
        
        if percent_used > max_threshold:
            status = "ERROR"
            message = f"Memory usage {percent_used:.1f}% exceeds threshold {max_threshold}%"
        elif percent_used > max_threshold * 0.8:
            status = "WARNING"
            message = f"Memory usage {percent_used:.1f}% approaching threshold"
        else:
            status = "OK"
            message = f"Memory usage {percent_used:.1f}% is healthy"
        
        result = DiagnosticResult(
            check_name="memory_pressure",
            status=status,
            message=message,
            data={
                'percent_used': percent_used,
                'available_gb': available_gb,
                'threshold': max_threshold
            },
            timestamp=time.time()
        )
        
        self.history.append(result)
        return result
    
    def check_cpu_load(self) -> DiagnosticResult:
        """Check CPU utilization"""
        cpu_percent = psutil.cpu_percent(interval=1)
        max_threshold = self.config.get('swarm', {}).get('resource_limits', {}).get('max_cpu_percent', 90)
        
        if cpu_percent > max_threshold:
            status = "ERROR"
            message = f"CPU usage {cpu_percent:.1f}% exceeds threshold"
        elif cpu_percent > max_threshold * 0.8:
            status = "WARNING"
            message = f"CPU usage {cpu_percent:.1f}% approaching threshold"
        else:
            status = "OK"
            message = f"CPU usage {cpu_percent:.1f}% is healthy"
        
        result = DiagnosticResult(
            check_name="cpu_load",
            status=status,
            message=message,
            data={'cpu_percent': cpu_percent, 'threshold': max_threshold},
            timestamp=time.time()
        )
        
        self.history.append(result)
        return result
    
    def recommend_scaling(self, current_bots: int, success_rate: float) -> Dict[str, Any]:
        """Recommend scaling action based on current state"""
        memory_check = self.check_memory_pressure()
        cpu_check = self.check_cpu_load()
        
        recommendation = {
            'action': 'maintain',
            'suggested_bots': current_bots,
            'reason': 'System performing well'
        }
        
        # Check for problems
        if memory_check.status == "ERROR" or cpu_check.status == "ERROR":
            recommendation['action'] = 'scale_down'
            recommendation['suggested_bots'] = max(2, current_bots // 2)
            recommendation['reason'] = 'Resource exhaustion detected'
        
        elif success_rate < 0.75:
            recommendation['action'] = 'scale_down'
            recommendation['suggested_bots'] = max(2, int(current_bots * 0.75))
            recommendation['reason'] = f'Low success rate: {success_rate:.1%}'
        
        elif (memory_check.status == "OK" and 
              cpu_check.status == "OK" and 
              success_rate > 0.9):
            recommendation['action'] = 'scale_up'
            recommendation['suggested_bots'] = current_bots + 2
            recommendation['reason'] = 'System has capacity for more bots'
        
        return recommendation
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        recent_checks = self.history[-10:] if len(self.history) > 10 else self.history
        
        error_count = sum(1 for c in recent_checks if c.status == "ERROR")
        warning_count = sum(1 for c in recent_checks if c.status == "WARNING")
        
        if error_count > 0:
            health = "CRITICAL"
        elif warning_count > 3:
            health = "DEGRADED"
        else:
            health = "HEALTHY"
        
        return {
            'overall_health': health,
            'recent_errors': error_count,
            'recent_warnings': warning_count,
            'total_checks': len(self.history)
        }
'''

with open("swarm_macos/utils/diagnostics.py", "w") as f:
    f.write(diagnostics)

print("✅ Created: utils/diagnostics.py")
