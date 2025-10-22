#!/usr/bin/env python3
"""
CRITICAL RESEARCH VALIDATION: Phase 1 - 12-Bot Scaling
Implementation of CRITICAL_RESEARCH_VALIDATION.yaml

EXECUTION RULES:
- 100% GREEN tests required before proceeding
- Autonomous debugging enabled
- Evidence capture mandatory
- Abort conditions enforced
"""

import time
import json
import subprocess
import os
import sys
try:
    import psutil
except ImportError:
    psutil = None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_gate_0():
    """Verify Gate 0 baseline clearance"""
    gate_file = ".checkpoints/gate_0_baseline_verified.json"
    if not os.path.exists(gate_file):
        print("❌ GATE BLOCKED: .checkpoints/gate_0_baseline_verified.json not found")
        print("Run baseline_verification.py first")
        return False

    with open(gate_file) as f:
        gate = json.load(f)

    if gate.get("status") != "PASSED_ALLOW_PHASE_1":
        print("❌ GATE BLOCKED: Baseline verification failed")
        return False

    print("✅ GATE CLEARED: Baseline verification confirmed")
    return True

def pre_phase_1_validation():
    """Check pre-conditions for Phase 1 execution"""
    print("=" * 60)
    print("🔍 PRE-PHASE 1 VALIDATION")
    print("=" * 60)

    issues = []

    # Check OLLAMA_NUM_PARALLEL
    ollama_parallel = os.environ.get("OLLAMA_NUM_PARALLEL", "1")
    try:
        ollama_parallel_int = int(ollama_parallel)
        if ollama_parallel_int < 10:
            issues.append({
                "severity": "CRITICAL",
                "issue": f"OLLAMA_NUM_PARALLEL={ollama_parallel_int} < 10 required",
                "action": "export OLLAMA_NUM_PARALLEL=10"
            })
    except:
        issues.append({
            "severity": "CRITICAL",
            "issue": "OLLAMA_NUM_PARALLEL not set or invalid",
            "action": "export OLLAMA_NUM_PARALLEL=10"
        })

    # Check swarm_config.yaml exists
    if not os.path.exists("config/swarm_config.yaml"):
        issues.append({
            "severity": "ERROR",
            "issue": "config/swarm_config.yaml not found",
            "action": "Ensure swarm configuration exists"
        })

    # Check baseline checkpoint
    if not os.path.exists(".checkpoints/gate_0_baseline_verified.json"):
        issues.append({
            "severity": "BLOCKER",
            "issue": "Baseline checkpoint missing",
            "action": "Run baseline_verification.py"
        })

    # Ollama service check
    ollama_check = subprocess.run(["curl", "-s", "http://localhost:11434/api/tags"],
                                  capture_output=True, text=True, timeout=5)
    if ollama_check.returncode != 0:
        issues.append({
            "severity": "CRITICAL",
            "issue": "Ollama service not responding on localhost:11434",
            "action": "Start Ollama: ollama serve"
        })

    if issues:
        print("❌ PRE-VALIDATION FAILED:")
        for issue in issues:
            print(f"  {issue['severity']}: {issue['issue']}")
            print(f"    ACTION: {issue['action']}")

        # Try auto-recovery for some issues
        critical_found = any(i['severity'] == 'CRITICAL' for i in issues)
        blocker_found = any(i['severity'] == 'BLOCKER' for i in issues)

        if blocker_found:
            print("\n❌ BLOCKER ISSUE: Cannot proceed")
            return False

        if critical_found:
            print("\n🔧 ATTEMPTING AUTO-RECOVERY...")

            # Try to fix OLLAMA_NUM_PARALLEL
            os.environ["OLLAMA_NUM_PARALLEL"] = "10"
            os.environ["OLLAMA_MAX_QUEUE"] = "256"
            print("  ✅ Set OLLAMA_NUM_PARALLEL=10")

            # Try to restart Ollama
            print("  🔄 Restarting Ollama...")
            subprocess.run(["pkill", "ollama"], capture_output=True)
            time.sleep(2)
            subprocess.run(["ollama", "serve"], capture_output=True)
            time.sleep(3)

            # Re-check
            ollama_check = subprocess.run(["curl", "-s", "http://localhost:11434/api/tags"],
                                        capture_output=True, text=True, timeout=3)
            if ollama_check.returncode == 0:
                print("  ✅ Ollama recovered")
                return True
            else:
                print("  ❌ Auto-recovery failed")
                return False

        return False

    print("✅ PRE-VALIDATION PASSED: Ready for Phase 1")
    return True

def test_12_001_spawn_verification():
    """TEST_12_001: Spawn 12 bots in 3 chunks"""
    print("=" * 60)
    print("🧪 TEST_12_001: SPAWN 12 BOTS IN 3 CHUNKS")
    print("=" * 60)

    try:
        from core.swarm_manager import SwarmManager  # type: ignore

        manager = SwarmManager()
        spawned = 0
        chunk_size = 4

        print("🚀 Spawning 12 bots in 3 chunks (4 bots each)...")

        for chunk_id in range(3):
            print(f"\n📦 Chunk {chunk_id+1}/3:")
            chunk_start = time.time()

            for bot_offset in range(chunk_size):
                bot_id = chunk_id * chunk_size + bot_offset
                print(f"  🤖 Bot {bot_id:2d}: Starting...")

                success = manager.spawn_bot(bot_id)
                spawned += 1 if success else 0

                time.sleep(0.05)  # Within-chunk stagger

            chunk_elapsed = time.time() - chunk_start
            print(f"  ⏱️  Chunk completed in {chunk_elapsed:.1f}s")
            time.sleep(0.1)  # Between-chunk stagger

        print("\n📊 SPAWN RESULTS:")
        print(f"  Expected: 12 bots")
        print(f"  Spawned:  {spawned} bots")
        print(f"  Success Rate: ({spawned}/12 bots) {round(spawned / 12 * 100, 1)}%")
        passed = spawned == 12

        result = {
            "test": "TEST_12_001",
            "expected": 12,
            "spawned": spawned,
            "success_rate": round(spawned / 12 * 100, 1),
            "passed": passed,
            "chunks_used": 3,
            "chunk_size": 4,
            "timestamp": time.time()
        }

        os.makedirs(".checkpoints", exist_ok=True)
        with open(".checkpoints/test_12bot_spawn_result.json", "w") as f:
            json.dump(result, f, indent=2)

        if manager and hasattr(manager, 'shutdown'):
            manager.shutdown()

        if passed:
            print("✅ TEST PASSED: All 12 bots spawned successfully")
            return True
        else:
            print("❌ TEST FAILED: Not all bots spawned")
            return False

    except Exception as e:
        print(f"❌ EXECUTION ERROR: {e}")
        result = {
            "test": "TEST_12_001",
            "error": str(e),
            "passed": False,
            "timestamp": time.time()
        }
        with open(".checkpoints/test_12bot_spawn_result.json", "w") as f:
            json.dump(result, f, indent=2)
        return False

def main():
    """Main execution for Phase 1"""
    print("=" * 80)
    print("🔴 CRITICAL RESEARCH VALIDATION: PHASE 1 - 12-BOT SCALING")
    print("=" * 80)
    print("\nMISSION: Validate scaling from 4→12 bots (100% tests required)")
    print("CRITICAL: ALL 4 tests must pass or phase FAILS\n")

    # Verify prerequisites
    if not verify_gate_0():
        print("\n❌ PHASE ABORTED: Gate 0 not cleared")
        sys.exit(1)

    if not pre_phase_1_validation():
        print("\n❌ PHASE ABORTED: Pre-validation failed")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("🚀 PHASE 1 EXECUTION STARTED")
    print("=" * 80)

    # Initialize results tracking
    test_results = []
    phase_passed = True

    # TEST 1: Spawn verification
    print("\n" + "🧪 EXECUTING TEST_12_001...")
    if test_12_001_spawn_verification():
        test_results.append(True)
        print("✅ TEST_12_001 PASSED")
    else:
        test_results.append(False)
        phase_passed = False
        print("❌ TEST_12_001 FAILED")

    # Phase outcome
    print("\n" + "=" * 80)
    if phase_passed and len(test_results) == 1:  # Only ran first test yet
        print("🎯 PHASE 1 STATUS: STARTED - 25% COMPLETE")
        print("Next: TEST_12_002 (Thread count verification)")
    else:
        print("❌ PHASE 1 STATUS: REQUIRES ATTENTION")
        print("Some tests failed - autonomous debugging may help")

    print("=" * 80)

if __name__ == "__main__":
    main()
