#!/usr/bin/env python3
"""
Phase 4: Full Swarm Validation for Swarm-100
AI Agent: Run full swarm test (50-100 bots) for 60 seconds
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path

# Add current directory to import templates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def run_full_swarm_validation(target_bots: int = 50) -> dict:
    """
    Run full swarm validation test

    Args:
        target_bots: Target number of bots to spawn (50 or 100)

    Returns:
        Dict with test results
    """
    print(f"{'='*90}")
    print(f"🎯 PHASE 4: FULL SWARM VALIDATION - {target_bots} BOTS")
    print(f"{'='*90}\n")

    from swarm_manager_template import SwarmManager

    # Initialize swarm manager
    manager = SwarmManager()

    try:
        # Spawn full swarm
        print(f"🚀 Spawning full swarm: {target_bots} bots...")
        start_spawn = time.time()
        spawned = await manager.spawn_swarm(target_bots)
        spawn_time = time.time() - start_spawn

        if spawned == 0:
            return {'success': False, 'error': 'Failed to spawn any bots'}

        spawn_rate = spawned / spawn_time if spawn_time > 0 else 0
        print(".2f"
        # Load configuration for test prompts
        config = manager.config
        test_prompts = config.get('test_prompts', {}).get('complex', [])
        if not test_prompts:
            test_prompts = [
                "Explain the concept of machine learning in 2 sentences.",
                "What are the main differences between Python lists and arrays?",
                "Describe how async programming improves performance.",
                "What is the purpose of requirements.txt in Python projects?",
                "Explain the difference between supervised and unsupervised learning."
            ]

        # Test configuration
        test_duration = 60  # seconds
        batch_size = min(len(manager.bots), 12)  # Tasks per batch
        batches_per_second = min(8, len(manager.bots) // 8)  # Batches per second

        print(f"📊 Test Configuration:")
        print(f"   Duration: {test_duration}s")
        print(f"   Batch Size: {batch_size} tasks/batch")
        print(f"   Batches/Sec: {batches_per_second}")
        print(f"   Expected Throughput: ~{batch_size * batches_per_second} tasks/sec")
        print()

        # Initialize metrics
        total_tasks = 0
        successful_tasks = 0
        failed_tasks = 0
        response_times = []

        start_time = time.time()
        batch_count = 0

        # Run the full swarm test
        while time.time() - start_time < test_duration:
            batch_count += 1

            # Create batch of prompts
            batch_prompts = []
            for i in range(batch_size):
                prompt = test_prompts[i % len(test_prompts)]
                batch_prompts.append(f"{prompt} (Task {batch_count}.{i})")

            # Execute batch across all bots concurrently
            batch_start = time.time()

            tasks = []
            for i, bot in enumerate(manager.bots):
                if i < len(batch_prompts):
                    prompt = batch_prompts[i]
                    task = bot.execute(prompt)
                    tasks.append(task)

            # Wait for all tasks in batch to complete
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process batch results
                batch_success = 0
                batch_fail = 0
                batch_times = []

                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        batch_fail += 1
                        print(f"❌ Task error in batch {batch_count}.{i}: {result}")
                    else:
                        batch_success += 1
                        total_tasks += 1
                        successful_tasks += 1
                        batch_times.append(result.response_time)
                        response_times.append(result.response_time)

                if batch_success > 0:
                    avg_batch_time = sum(batch_times) / len(batch_times)
                    batch_throughput = len(batch_times) / (time.time() - batch_start)
                else:
                    batch_throughput = 0

                elapsed = time.time() - start_time

                if elapsed % 10 < 0.5:  # Report every 10 seconds
                    print(f"⏱️  Elapsed: {elapsed:.1f}s | "
                          f"Batch {batch_count} | "
                          f"Success: {batch_success}/{batch_size} | "
                          f"Avg Time: {avg_batch_time:.3f}s")

            except Exception as e:
                print(f"❌ Batch {batch_count} failed: {e}")
                failed_tasks += batch_size

            # Control pacing to achieve target batches/second
            await asyncio.sleep(1.0 / batches_per_second)

        # Calculate final metrics
        total_time = time.time() - start_time
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        overall_throughput = total_tasks / total_time if total_time > 0 else 0

        avg_response_time = (sum(response_times) / len(response_times)
                           if response_times else 0)

        # Determine test success
        success = success_rate >= 75.0  # 75% success rate requirement

        results = {
            'success': success,
            'target_bots': target_bots,
            'bots_spawned': spawned,
            'spawn_time_seconds': spawn_time,
            'spawn_rate_bots_per_sec': spawn_rate,
            'test_duration_seconds': total_time,
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'success_rate_percent': round(success_rate, 2),
            'overall_throughput_tasks_per_sec': round(overall_throughput, 2),
            'avg_response_time_seconds': round(avg_response_time, 3),
            'batch_count': batch_count,
            'system_limits_reached': spawned < target_bots
        }

        print("
        🎯 FINAL RESULTS"        print(f"{'='*50}")
        print(f"Target Bots: {target_bots}")
        print(f"Bots Spawned: {spawned}")
        print(f"Success Rate: {success_rate:.2f}%")
        print(f"Throughput: {overall_throughput:.2f} tasks/sec")
        print(f"Avg Response Time: {avg_response_time:.3f}s")
        print(f"Total Tasks: {total_tasks}")
        print(f"PHASE 4 {'PASSED' if success else 'FAILED'}")
        print(f"{'='*50}\n")

        # Save Phase 4 checkpoint
        checkpoint = {
            'phase': 'phase_4',
            'timestamp': time.time(),
            'status': 'complete',
            'full_swarm_test': results
        }

        checkpoint_file = '.checkpoints/phase_4_complete.json'
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)

        print(f"💾 Phase 4 checkpoint saved: {checkpoint_file}")

        return results

    finally:
        # Cleanup
        if 'manager' in locals():
            await manager.shutdown()

async def auto_scale_based_on_phase3():
    """Automatically determine target based on Phase 3 results"""

    try:
        with open('.checkpoints/phase_3_complete.json', 'r') as f:
            phase3_data = json.load(f)

        max_validated = phase3_data.get('max_validated_capacity', 12)

        if max_validated >= 24:
            return 100  # Full capacity
        elif max_validated >= 12:
            return 50   # Half capacity
        else:
            return 24   # Minimum validated

    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️  Phase 3 checkpoint not found, defaulting to 50 bots")
        return 50

async def main():
    """Main Phase 4 execution"""
    print("🤖 Swarm-100 Phase 4: Full Swarm Validation")
    print("Based on Phase 3 results, determining optimal swarm size...\n")

    # Auto-scale based on Phase 3 results
    target_bots = await auto_scale_based_on_phase3()

    print(f"🎯 Targeting {target_bots} bots for full swarm validation\n")

    # Run the full swarm test
    results = await run_full_swarm_validation(target_bots)

    # Summary and next steps
    if results['success']:
        print("🎉 Phase 4 SUCCESS: Full swarm at scale validated!")
        print("   Ready for Phase 5: Documentation & Production Deployment")

        if results.get('system_limits_reached', False):
            print("\n⚠️  NOTICE: System limits reached during testing")
            print("   The tested configuration may be the maximum capacity")
    else:
        print("⚠️  Phase 4 INCOMPLETE: Full swarm validation did not meet requirements")
        print("   Consider reducing bot count or investigating system bottlenecks")
        print("   Can proceed with Phase 5 using validated capacity from Phase 3")

if __name__ == "__main__":
    asyncio.run(main())
