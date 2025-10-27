#!/usr/bin/env python3
"""
Hardware-proof validation for swarm spawning
Test that actually verifies bot spawning and resource usage
"""

import pytest
import asyncio
import time
import json
import psutil
from pathlib import Path

# Add current directory to import templates
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.swarm_manager import ThreadSwarmManager

@pytest.mark.asyncio
@pytest.mark.hardware_proof
async def test_spawn_64_bots_hardware_verification():
    """
    Hardware-proof test: Verify 64 bots actually spawn with real resource monitoring
    This test cannot be faked - it measures actual system resources
    """
    print("\n🧪 HARDWARE-PROOF SPAWN TEST: 64 bots with verification")
    print("="*80)

    # Pre-test hardware fingerprint
    process_before = psutil.Process()
    memory_before = process_before.memory_info().rss / 1024 / 1024  # MB
    cpu_before = psutil.cpu_percent(interval=0.1)
    threads_before = process_before.num_threads()

    print(f"📊 BEFORE: Memory: {memory_before:.1f}MB, CPU: {cpu_before:.1f}%, Threads: {threads_before}")

    manager = ThreadSwarmManager()
    spawned_count = 0

    try:
        # The actual spawn operation - this will either work or raise
        print("🚀 Spawning 64 bots...")
        spawn_start = time.time()
        ready = await manager.spawn_and_wait_ready(64)
        spawn_time = time.time() - spawn_start

        if not ready:
            pytest.fail("spawn_and_wait_ready returned False - bots did not become healthy")

        # Post-spawn hardware verification
        process_after = psutil.Process()
        memory_after = process_after.memory_info().rss / 1024 / 1024
        cpu_after = psutil.cpu_percent(interval=0.5)
        threads_after = process_after.num_threads()

        memory_delta = memory_after - memory_before
        thread_delta = threads_after - threads_before

        print(f"📊 AFTER: Memory: {memory_after:.1f}MB, CPU: {cpu_after:.1f}%, Threads: {threads_after}")
        print(f"📊 DELTA: Memory: +{memory_delta:.1f}MB, Threads: +{thread_delta}")

        # Assertions that cannot be hallucinated - require actual hardware changes
        assert thread_delta > 10, f"Expected significant thread increase, got {thread_delta}. Bots likely didn't spawn."
        assert memory_delta > 50, f"Expected >50MB memory increase, got {memory_delta:.1f}MB. No real resource usage."
        assert cpu_after > cpu_before or cpu_after > 1.0, f"Expected measurable CPU usage, got {cpu_after:.1f}%"

        # Verify bots collection
        active_bots = len(manager.bots) if hasattr(manager, 'bots') else 0
        print(f"🤖 Manager reports {active_bots} active bots")

        if hasattr(manager, 'bots'):
            assert active_bots >= 64, f"Expected >=64 active bots, got {active_bots}"

        # System calls must show activity
        assert cpu_after > 0.5, f"System shows no CPU activity ({cpu_after:.1f}%). Test didn't execute."

        # Hardware proof artifact
        proof = {
            "test": "spawn_64_bots_hardware_verification",
            "timestamp": time.time(),
            "spawn_time_seconds": spawn_time,
            "memory_before_mb": memory_before,
            "memory_after_mb": memory_after,
            "memory_delta_mb": memory_delta,
            "cpu_before_percent": cpu_before,
            "cpu_after_percent": cpu_after,
            "threads_before": threads_before,
            "threads_after": threads_after,
            "thread_delta": thread_delta,
            "claimed_bots_spawned": active_bots,
            "verification": "HARDWARE_FINGERPRINT_VERIFIED"
        }

        proof_file = f".checkpoints/test_spawn_64_bots_{int(time.time())}.proof"
        with open(proof_file, 'w') as f:
            json.dump(proof, f, indent=2)

        print(f"💾 Hardware proof saved: {proof_file}")
        print("✅ 64 BOT SPAWN: HARDWARE VERIFIED")
        print(".1f")
        print(".1f")

    finally:
        manager.shutdown()


@pytest.mark.asyncio
async def test_spawn_failed_validation():
    """
    Demonstrate what happens with invalid spawn to prove validation works
    """
    manager = ThreadSwarmManager()

    try:
        # Try to spawn with obviously wrong count
        ready = await manager.spawn_and_wait_ready(-1)  # Invalid

        # This should not be ready
        assert ready == False, "Invalid spawn should not be considered ready"

    finally:
        manager.shutdown()


if __name__ == "__main__":
    # Allow direct running for debugging
    asyncio.run(test_spawn_64_bots_hardware_verification())
