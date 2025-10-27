#!/usr/bin/env python3
"""
Load testing script for Phase 3 progressive validation
AI Agent: Run with --bots N --duration D for staged testing
"""

import asyncio
import argparse
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.swarm_manager import ThreadSwarmManager

async def run_load_test(bot_count: int, duration: int):
    """Run load test with specified parameters"""

    print(f"\n{'='*80}")
    print(f"🧪 LOAD TEST: {bot_count} bots for {duration} seconds")
    print(f"{'='*80}\n")

    # Create real SwarmManager with threading
    manager = ThreadSwarmManager()

    results = None
    try:
        # Phase 1: Spawn bots and WAIT for them to be ready
        print("🔧 Phase 1: Warm-up and health verification...")
        ready = await manager.spawn_and_wait_ready(bot_count)
        if not ready:
            raise Exception("Failed to get all bots healthy and ready")
        print("✅ All bots healthy - now idling")

        # Phase 2: Verification period (bots idling but ready)
        print("⏱️ Phase 2: Idling stability check...")
        await asyncio.sleep(5)
        print("✅ Swarm stable during idle period")

        # Phase 3: Run REAL stress test
        print("🚀 Phase 3: Load testing...")
        results = await manager.run_stress_test(
            bot_count=bot_count,
            duration=duration
        )

    finally:
        manager.shutdown()

    if not results:
        results = {'success_rate': 0, 'duration': 0, 'bot_count': bot_count}

    print(f"\nTest Results:")
    print(f"  Bot count: {results['bot_count']}")
    print(f"  Active threads: {results.get('thread_count', 0)}")
    print(f"  Concurrency model: {results.get('concurrency_model', 'unknown')}")

    # Calculate throughput
    throughput = results['successful_tasks'] / results['duration'] if results.get('duration', 0) > 0 else 0.0
    results['throughput'] = float(throughput)  # type: ignore

    # Save results
    output_file = f".checkpoints/load_test_{bot_count}bots.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"✅ TEST COMPLETE")
    print(f"{'='*80}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Throughput: {results['throughput']:.2f} tasks/sec")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}\n")

    # Determine if test passed
    passed = results['success_rate'] >= 80
    return passed

def main():
    parser = argparse.ArgumentParser(description='Swarm load testing')
    parser.add_argument('--bots', type=int, required=True, help='Number of bots')
    parser.add_argument('--duration', type=int, required=True, help='Test duration in seconds')

    args = parser.parse_args()

    passed = asyncio.run(run_load_test(args.bots, args.duration))

    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
