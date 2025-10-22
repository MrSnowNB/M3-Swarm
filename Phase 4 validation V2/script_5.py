
# Gate 4: CPU Core Utilization
cpu_cores_script = '''#!/usr/bin/env python3
"""
GATE 4: CPU Core Utilization Verification
Verify multiple CPU cores are utilized during 24-bot test
"""

import time
import json
import os
import sys
from datetime import datetime

try:
    import psutil
except ImportError:
    print("❌ psutil is required for this test")
    print("   Install: pip install psutil")
    sys.exit(1)

def main():
    print("="*80)
    print("🔬 GATE 4: CPU CORE UTILIZATION VERIFICATION")
    print("="*80)
    print("Measuring per-core CPU usage during 24-bot test...\\n")
    
    results = {
        "gate": "4_cpu_utilization",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "samples": []
    }
    
    try:
        # Import current implementation
        sys.path.insert(0, os.getcwd())
        from core.swarm_manager import SwarmManager
        
        print("📦 Imported SwarmManager")
        print("🚀 Spawning 24 bots...\\n")
        
        # Create manager and spawn 24 bots
        manager = SwarmManager()
        spawned = manager.spawn_swarm(24)
        print(f"✅ {spawned} bots spawned\\n")
        
        # Wait for bots to be active
        time.sleep(2)
        
        # Submit some tasks to ensure bots are working
        print("📤 Submitting tasks to bots...")
        test_prompts = ["Test prompt " + str(i) for i in range(10)]
        for prompt in test_prompts:
            try:
                manager.broadcast_task(prompt)
            except:
                pass  # May not have broadcast_task method
        
        # Sample CPU usage for 60 seconds
        print("\\n📊 Sampling per-core CPU usage (60 samples over 60 seconds)...")
        print("   This will measure actual CPU core utilization...\\n")
        
        core_samples = []
        
        for i in range(60):
            # Get per-core CPU percentage
            per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            sample = {
                "sample_num": i + 1,
                "timestamp": time.time(),
                "per_core_percent": per_core,
                "total_cpu_percent": psutil.cpu_percent()
            }
            
            core_samples.append(sample)
            results["samples"].append(sample)
            
            if (i + 1) % 15 == 0:
                active_cores = sum(1 for cpu in per_core if cpu > 20)
                print(f"  Sample {i+1}: {active_cores} cores active (>20% usage)")
        
        # Shutdown
        print("\\n🛑 Shutting down...")
        manager.shutdown()
        
        # Analyze results
        num_cores = len(core_samples[0]["per_core_percent"])
        
        # Calculate average per-core utilization
        avg_per_core = [0] * num_cores
        for sample in core_samples:
            for i, cpu_pct in enumerate(sample["per_core_percent"]):
                avg_per_core[i] += cpu_pct / len(core_samples)
        
        # Count cores with high utilization (>20% average)
        high_util_threshold = 20.0
        cores_with_high_util = sum(1 for avg in avg_per_core if avg > high_util_threshold)
        
        results["analysis"] = {
            "total_cores": num_cores,
            "avg_per_core_utilization": [round(x, 1) for x in avg_per_core],
            "cores_with_high_utilization": cores_with_high_util,
            "high_utilization_threshold": high_util_threshold,
            "avg_total_cpu": round(sum(s["total_cpu_percent"] for s in core_samples) / len(core_samples), 1)
        }
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        results["error"] = str(e)
        cores_with_high_util = 0
        results["analysis"] = {"cores_with_high_utilization": 0}
    
    # Evaluate results
    pass_threshold = 8
    warning_threshold = 6
    
    results["pass_threshold"] = pass_threshold
    results["warning_threshold"] = warning_threshold
    results["passed"] = cores_with_high_util >= pass_threshold
    
    print(f"\\n{'='*80}")
    print("🖥️  CPU CORE UTILIZATION RESULTS")
    print("="*80)
    print(f"Total cores: {results['analysis'].get('total_cores', 0)}")
    print(f"Cores with >20% avg utilization: {cores_with_high_util}")
    print(f"Expected: >= {pass_threshold} cores active")
    print()
    
    if cores_with_high_util >= 10:
        print("✅ EXCELLENT: All performance cores utilized")
        results["interpretation"] = "EXCELLENT"
    elif cores_with_high_util >= pass_threshold:
        print("✅ GATE 4 PASSED: Multiple cores verified")
        results["interpretation"] = "PASSED"
    elif cores_with_high_util >= warning_threshold:
        print("⚠️  GATE 4 WARNING: Only Ollama cores active?")
        results["interpretation"] = "PARTIAL"
    else:
        print("❌ GATE 4 FAILED: Insufficient core utilization")
        print("   This indicates threading is not utilizing multiple cores")
        results["interpretation"] = "FAILED"
    
    print("="*80)
    
    # Save results
    os.makedirs(".checkpoints", exist_ok=True)
    with open(".checkpoints/gate4_cpu_utilization_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return 0 if results["passed"] else 1

if __name__ == "__main__":
    exit(main())
'''

with open("verify_cpu_cores.py", "w") as f:
    f.write(cpu_cores_script)

print("✅ Created: verify_cpu_cores.py")
print("   → CPU core utilization test (Gate 4)")
