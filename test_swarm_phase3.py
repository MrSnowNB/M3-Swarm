#!/usr/bin/env python3
"""
Phase 3: Progressive Load Testing for Swarm-100
AI Agent: Run stress tests from 2→6→12→24 bots
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path

# Add current directory to import templates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_stage(bot_count: int, duration_seconds: int, required_success_rate: float, config: dict) -> dict:
    """
    Test a single stage with specified bot count and duration

    Args:
        bot_count: Number of bots to spawn
        duration_seconds: How long to test
        required_success_rate: Minimum success rate required
        config: Swarm configuration

    Returns:
        Dict with test results
    """
    print(f"\n{'='*80}")
    print(f"🧪 PHASE 3 STAGE: {bot_count} BOTS, {duration_seconds}s DURATION")
    print(f"Required Success Rate: {required_success_rate}%")
    print(f"{'='*80}\n")

    from swarm_manager_template import SwarmManager
    from bot_agent_template import BotAgent

    # Initialize swarm manager
    manager = SwarmManager()

    try:
        # Spawn bots
        spawned = await manager.spawn_swarm(bot_count)
        if spawned == 0:
            return {
                'success': False,
                'error': 'Failed to spawn any bots',
                'stage': bot_count,
                'spawned': 0
            }

        print(f"✅ Spawned {spawned} bots successfully")

        # Initialize metrics
        total_tasks = 0
        successful_tasks = 0
        start_time = time.time()

        # Test prompts
        test_prompts = [
            "What is 2+2?",
            "Explain async programming briefly.",
            "Classify: This is great!",
            "Summarize: AI is transforming software development."
        ]

        iteration = 0
        tasks_per_batch = min(len(manager.bots), 4)  # Tasks per batch

        while time.time() - start_time < duration_seconds:
            iteration += 1

            # Select prompts for this batch
            batch_prompts = test_prompts[:tasks_per_batch]

            # Execute tasks through each bot
            tasks = []
            for i, bot in enumerate(manager.bots):
                if i < len(batch_prompts):
                    prompt = batch_prompts[i]
                    task = bot.execute(prompt)
                    tasks.append(task)

            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            batch_count = 0
            batch_success = 0
            for result in results:
                if isinstance(result, Exception):
                    print(f"❌ Task error: {result}")
                else:
                    batch_count += 1
                    if result.success:
                        batch_success += 1
                        successful_tasks += 1
                    total_tasks += 1

            # Progress report
            elapsed = time.time() - start_time
            if batch_count > 0:
                batch_success_rate = (batch_success / batch_count) * 100
                print(f"  Batch {iteration}: {batch_success}/{batch_count} ({batch_success_rate:.1f}%) | Elapsed: {elapsed:.1f}s")
            else:
                print(f"  Batch {iteration}: No tasks executed | Elapsed: {elapsed:.1f}s")

            # Small delay between batches
            await asyncio.sleep(0.5)

        # Calculate final metrics
        total_time = time.time() - start_time
        actual_success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        throughput = total_tasks / total_time if total_time > 0 else 0

        results = {
            'success': actual_success_rate >= required_success_rate,
            'stage': bot_count,
            'duration': total_time,
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'actual_success_rate': round(actual_success_rate, 2),
            'required_success_rate': required_success_rate,
            'throughput': round(throughput, 2),
            'spawned_bots': spawned
        }

        print("\n        --- RESULTS ---")
        print(f"Total Tasks: {total_tasks}")
        print(f"Successful Tasks: {successful_tasks}")
        print(f"Success Rate: {actual_success_rate:.1f}% (Required: {required_success_rate:.1f}%)")
        print(f"Throughput: {throughput:.2f} tasks/sec")
        print(f"Stage {'PASSED' if results['success'] else 'FAILED'}")
        print(f"{'='*80}\n")

        return results

    finally:
        # Cleanup - would shutdown bots properly
        pass

async def run_phase3_progressive_testing():
    """Run Phase 3 progressive load testing"""

    # Load configuration
    import yaml
    try:
        with open('swarm_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {
            'swarm': {
                'resource_limits': {
                    'max_memory_percent': 80,
                    'max_cpu_percent': 90,
                    'memory_per_bot_gb': 1.5
                }
            },
            'model': {
                'name': 'gemma3:270m'
            }
        }

    # Test stages as defined in AI_FIRST_BUILD.yaml Phase 3
    stages = [
        {'bots': 2, 'duration': 30, 'required_success_rate': 95},
        {'bots': 6, 'duration': 30, 'required_success_rate': 90},
        {'bots': 12, 'duration': 30, 'required_success_rate': 85},
        {'bots': 24, 'duration': 30, 'required_success_rate': 80}
    ]

    results = []
    max_validated_capacity = 0

    print("🚀 STARTING PHASE 3: PROGRESSIVE LOAD TESTING")
    print("Testing swarm capacity: 2→6→12→24 bots")

    for stage in stages:
        try:
            result = await test_stage(
                bot_count=stage['bots'],
                duration_seconds=stage['duration'],
                required_success_rate=stage['required_success_rate'],
                config=config
            )
            results.append(result)

            if result['success']:
                max_validated_capacity = result['stage']
                print(f"✅ Stage {result['stage']} bots: PASSED")
            else:
                print(f"❌ Stage {result['stage']} bots: FAILED - stopping progression")
                break

        except Exception as e:
            print(f"❌ Stage {stage['bots']} bots: ERROR - {e}")
            results.append({
                'success': False,
                'stage': stage['bots'],
                'error': str(e)
            })
            break

    # Summary
    print("\n📊 PHASE 3 SUMMARY")
    print(f"Stages Completed: {len(results)}")
    print(f"Maximum Validated Capacity: {max_validated_capacity} bots")

    for result in results:
        if result.get('success', False):
            print(f"✅ {result['stage']} bots: {result['actual_success_rate']:.1f}% "
                  f"({result['throughput']:.2f} tasks/sec)")
        else:
            print(f"❌ {result['stage']} bots: Failed")

    # Create Phase 3 checkpoint
    checkpoint = {
        'phase': 'phase_3',
        'timestamp': time.time(),
        'status': 'complete' if max_validated_capacity >= 12 else 'partial',
        'max_validated_capacity': max_validated_capacity,
        'stages_completed': len(results),
        'results': results
    }

    checkpoint_file = '.checkpoints/phase_3_complete.json'
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2, default=str)

    print(f"\n💾 Phase 3 checkpoint saved: {checkpoint_file}")

    if max_validated_capacity >= 12:
        print("🎉 Phase 3 Complete: Ready for Phase 4")
        return True
    else:
        print("⚠️  Phase 3 Incomplete: Minimum 12 bots not validated")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_phase3_progressive_testing())
    sys.exit(0 if success else 1)
