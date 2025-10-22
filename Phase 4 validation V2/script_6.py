
# Gate 5: Baseline Comparison and Final Bundle Generator
baseline_comparison_script = '''#!/usr/bin/env python3
"""
GATE 5: Baseline Comparison
Compare threading implementation vs asyncio baseline
"""

import json
import os
from datetime import datetime

def load_json(filepath):
    """Load JSON file safely"""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load {filepath}: {e}")
        return None

def main():
    print("="*80)
    print("🔬 GATE 5: BASELINE COMPARISON")
    print("="*80)
    print("Comparing threading vs asyncio performance...\\n")
    
    results = {
        "gate": "5_baseline_comparison",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Load baseline data
    asyncio_baseline = load_json(".checkpoints/baseline_asyncio.json")
    threading_baseline = load_json(".checkpoints/baseline_threading.json")
    
    # Load gate results
    gate1 = load_json(".checkpoints/gate1_code_audit_results.json")
    gate2 = load_json(".checkpoints/gate2_concurrency_proof_results.json")
    gate3 = load_json(".checkpoints/gate3_thread_count_results.json")
    gate4 = load_json(".checkpoints/gate4_cpu_utilization_results.json")
    
    # Compare key metrics
    comparisons = {}
    
    if gate1:
        comparisons["code_model"] = {
            "asyncio_lines": gate1.get("checks", {}).get("asyncio_line_count", 0),
            "threading_lines": gate1.get("checks", {}).get("threading_line_count", 0),
            "threading_dominant": gate1.get("summary", {}).get("threading_dominant", False)
        }
    
    if gate2:
        comparisons["concurrency_proof"] = {
            "elapsed_time": gate2.get("elapsed_time_seconds", 999),
            "passed": gate2.get("passed", False),
            "interpretation": gate2.get("interpretation", "UNKNOWN")
        }
    
    if gate3:
        comparisons["thread_count"] = {
            "average_threads": gate3.get("statistics", {}).get("average_thread_count", 0),
            "expected": gate3.get("statistics", {}).get("expected_threads", 24),
            "passed": gate3.get("passed", False)
        }
    
    if gate4:
        comparisons["cpu_cores"] = {
            "cores_utilized": gate4.get("analysis", {}).get("cores_with_high_utilization", 0),
            "total_cores": gate4.get("analysis", {}).get("total_cores", 14),
            "passed": gate4.get("passed", False)
        }
    
    results["comparisons"] = comparisons
    
    # Determine overall improvement
    improvements = []
    
    if comparisons.get("code_model", {}).get("threading_dominant"):
        improvements.append("Threading code dominant over asyncio")
    
    if comparisons.get("concurrency_proof", {}).get("passed"):
        improvements.append("True parallelism verified (< 3s)")
    
    if comparisons.get("thread_count", {}).get("passed"):
        improvements.append("Thread count matches bot count")
    
    if comparisons.get("cpu_cores", {}).get("passed"):
        improvements.append("Multiple CPU cores utilized (>= 8)")
    
    results["improvements"] = improvements
    results["passed"] = len(improvements) >= 3
    
    print("📊 Comparison Results:\\n")
    for improvement in improvements:
        print(f"  ✅ {improvement}")
    
    if len(improvements) < 3:
        print("\\n⚠️  Less than 3 improvements detected")
        results["passed"] = False
    
    print(f"\\n{'='*80}")
    if results["passed"]:
        print("✅ GATE 5 PASSED: Threading shows significant improvements")
    else:
        print("❌ GATE 5 FAILED: Threading does not show expected improvements")
    print("="*80)
    
    # Save results
    os.makedirs(".checkpoints", exist_ok=True)
    with open(".checkpoints/gate5_comparison_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return 0 if results["passed"] else 1

if __name__ == "__main__":
    exit(main())
'''

with open("verify_baseline_comparison.py", "w") as f:
    f.write(baseline_comparison_script)

print("✅ Created: verify_baseline_comparison.py")
print("   → Baseline comparison (Gate 5)")
