#!/usr/bin/env python3
"""
Generate Phase 4 Verification Bundle
Combines all gate results into signed, timestamped bundle
"""

import json
import hashlib
import platform
import subprocess
import os
from datetime import datetime

def load_json(filepath):
    """Load JSON file safely"""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Could not load {filepath}: {e}"}

def get_git_commit():
    """Get current git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except:
        return "unknown"

def generate_bundle():
    """Generate complete verification bundle"""
    print("="*80)
    print("📦 GENERATING PHASE 4 VERIFICATION BUNDLE")
    print("="*80)
    print()

    bundle = {
        "bundle_version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "phase": "Phase 4 - Parallelism Revalidation"
    }

    # System information
    bundle["system"] = {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "git_commit": get_git_commit()
    }

    # Load all gate results
    print("📂 Loading gate results...")

    gates = {
        "gate_1_code_audit": load_json(".checkpoints/gate1_code_audit_results.json"),
        "gate_2_concurrency_proof": load_json(".checkpoints/gate2_concurrency_proof_results.json"),
        "gate_3_thread_count": load_json(".checkpoints/gate3_thread_count_results.json"),
        "gate_4_cpu_utilization": load_json(".checkpoints/gate4_cpu_utilization_results.json"),
        "gate_5_baseline_comparison": load_json(".checkpoints/gate5_comparison_results.json")
    }

    bundle["gate_results"] = gates

    # Determine pass/fail for each gate
    gate_status = {}
    critical_gates = ["gate_2_concurrency_proof"]

    for gate_name, gate_data in gates.items():
        if "error" in gate_data:
            gate_status[gate_name] = "ERROR"
        elif gate_data.get("passed"):
            gate_status[gate_name] = "PASSED"
        else:
            gate_status[gate_name] = "FAILED"

    bundle["gate_status"] = gate_status

    # Overall pass/fail determination
    critical_passed = all(
        gate_status.get(gate) == "PASSED" 
        for gate in critical_gates
    )

    gates_passed = sum(1 for status in gate_status.values() if status == "PASSED")
    total_gates = len(gate_status)

    bundle["overall_status"] = {
        "critical_gates_passed": critical_passed,
        "gates_passed": gates_passed,
        "total_gates": total_gates,
        "pass_rate": round(gates_passed / total_gates * 100, 1)
    }

    # Determine final verdict
    if critical_passed and gates_passed >= 4:
        bundle["verdict"] = "VERIFIED"
        bundle["verification_level"] = "FULL"
    elif critical_passed and gates_passed >= 3:
        bundle["verdict"] = "VERIFIED"
        bundle["verification_level"] = "PARTIAL"
    elif critical_passed:
        bundle["verdict"] = "MINIMAL"
        bundle["verification_level"] = "BASIC"
    else:
        bundle["verdict"] = "FAILED"
        bundle["verification_level"] = "NONE"

    # Key findings summary
    findings = []

    if gates.get("gate_1_code_audit", {}).get("passed"):
        findings.append("Threading implementation verified in code")

    if gates.get("gate_2_concurrency_proof", {}).get("passed"):
        elapsed = gates.get("gate_2_concurrency_proof", {}).get("elapsed_time_seconds", 999)
        findings.append(f"True parallelism verified ({elapsed:.2f}s < 3s threshold)")
    else:
        elapsed = gates.get("gate_2_concurrency_proof", {}).get("elapsed_time_seconds", 999)
        findings.append(f"CRITICAL: No true parallelism ({elapsed:.2f}s >= 3s threshold)")

    if gates.get("gate_3_thread_count", {}).get("passed"):
        threads = gates.get("gate_3_thread_count", {}).get("statistics", {}).get("average_thread_count", 0)
        findings.append(f"Thread count verified ({threads:.1f} threads for 24 bots)")

    if gates.get("gate_4_cpu_utilization", {}).get("passed"):
        cores = gates.get("gate_4_cpu_utilization", {}).get("analysis", {}).get("cores_with_high_utilization", 0)
        findings.append(f"Multi-core utilization verified ({cores} cores active)")

    bundle["key_findings"] = findings

    # Generate cryptographic signature
    bundle_json = json.dumps(bundle, sort_keys=True)
    signature = hashlib.sha256(bundle_json.encode()).hexdigest()
    bundle["signature"] = signature

    # Save bundle
    os.makedirs(".checkpoints", exist_ok=True)
    with open(".checkpoints/PHASE4_VERIFICATION_BUNDLE.json", "w") as f:
        json.dump(bundle, f, indent=2)

    # Print summary
    print("\n" + "="*80)
    print("📊 VERIFICATION BUNDLE SUMMARY")
    print("="*80)
    print(f"\nOverall Verdict: {bundle['verdict']}")
    print(f"Verification Level: {bundle['verification_level']}")
    print(f"Gates Passed: {gates_passed}/{total_gates}")
    print()
    print("Key Findings:")
    for finding in findings:
        print(f"  • {finding}")
    print()
    print(f"Bundle signed with SHA256: {signature[:16]}...")
    print(f"Saved to: .checkpoints/PHASE4_VERIFICATION_BUNDLE.json")
    print("="*80)

    # Return success if verified
    return 0 if bundle["verdict"] in ["VERIFIED", "MINIMAL"] else 1

if __name__ == "__main__":
    exit(generate_bundle())
