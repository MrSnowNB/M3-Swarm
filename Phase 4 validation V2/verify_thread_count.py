#!/usr/bin/env python3
"""
GATE 3: Thread Count Verification
Verify thread count matches bot count during execution
"""

import time
import json
import os
import sys
import threading
from datetime import datetime

try:
    import psutil
except ImportError:
    print("⚠️  psutil not installed, using threading.active_count() only")
    psutil = None

def main():
    print("="*80)
    print("🔬 GATE 3: THREAD COUNT VERIFICATION")
    print("="*80)
    print("Verifying thread count during 24-bot test...\n")

    results = {
        "gate": "3_thread_count",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "samples": []
    }

    try:
        # Import current implementation
        sys.path.insert(0, os.getcwd())
        from core.swarm_manager import SwarmManager

        print("📦 Imported SwarmManager")
        print("🚀 Spawning 24 bots...\n")

        # Create manager
        manager = SwarmManager()

        # Get initial thread count
        initial_threads = threading.active_count()
        if psutil:
            initial_process_threads = psutil.Process().num_threads()

        print(f"Initial threads: {initial_threads}")

        # Spawn 24 bots
        spawned = manager.spawn_swarm(24)
        print(f"\n✅ {spawned} bots spawned")

        # Wait a moment for all threads to start
        time.sleep(2)

        # Sample thread count multiple times
        print("\n📊 Sampling thread count (30 samples over 30 seconds)...")
        samples = []

        for i in range(30):
            thread_count = threading.active_count()

            sample = {
                "sample_num": i + 1,
                "threading_active_count": thread_count,
                "timestamp": time.time()
            }

            if psutil:
                sample["psutil_num_threads"] = psutil.Process().num_threads()

            samples.append(sample)
            results["samples"].append(sample)

            if (i + 1) % 10 == 0:
                print(f"  Sample {i+1}: {thread_count} threads")

            time.sleep(1)

        # Calculate statistics
        thread_counts = [s["threading_active_count"] for s in samples]
        avg_threads = sum(thread_counts) / len(thread_counts)
        min_threads = min(thread_counts)
        max_threads = max(thread_counts)

        results["statistics"] = {
            "average_thread_count": round(avg_threads, 1),
            "min_thread_count": min_threads,
            "max_thread_count": max_threads,
            "expected_threads": 24,
            "bot_count": spawned
        }

        # Shutdown
        print("\n🛑 Shutting down...")
        manager.shutdown()

    except Exception as e:
        print(f"❌ Error during test: {e}")
        results["error"] = str(e)
        avg_threads = 0

    # Evaluate results
    pass_threshold = 24
    warning_threshold = 20

    results["pass_threshold"] = pass_threshold
    results["warning_threshold"] = warning_threshold
    results["passed"] = avg_threads >= pass_threshold

    print(f"\n{'='*80}")
    print("📊 THREAD COUNT RESULTS")
    print("="*80)
    print(f"Average threads: {avg_threads:.1f}")
    print(f"Min threads: {min_threads}")
    print(f"Max threads: {max_threads}")
    print(f"Expected: >= {pass_threshold} threads")
    print()

    if avg_threads >= pass_threshold:
        print("✅ GATE 3 PASSED: Thread count verified")
        results["interpretation"] = "VERIFIED"
    elif avg_threads >= warning_threshold:
        print("⚠️  GATE 3 WARNING: Most threads present but some missing")
        results["interpretation"] = "PARTIAL"
    else:
        print("❌ GATE 3 FAILED: Thread count too low")
        print("   This indicates threading is not being used correctly")
        results["interpretation"] = "FAILED"

    print("="*80)

    # Save results
    os.makedirs(".checkpoints", exist_ok=True)
    with open(".checkpoints/gate3_thread_count_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0 if results["passed"] else 1

if __name__ == "__main__":
    exit(main())
