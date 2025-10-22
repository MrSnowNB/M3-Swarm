#!/usr/bin/env python3
"""
Test ThreadBotAgent - Validate threading heartbeat pattern
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.thread_bot_agent import ThreadBotAgent, test_thread_bot_agent


def test_thread_bot_agent_heartbeat():
    """
    Test that bot heartbeat prevents CPU saturation
    """
    print("\n🫀 Testing ThreadBotAgent Heartbeat...")

    config = {
        'ollama_host': 'http://localhost:11434',
        'context_length': 2048,
        'temperature': 0.7,
        'heartbeat_interval': 0.05
    }

    bot = ThreadBotAgent(bot_id=200, model='gemma3:270m', config=config)
    bot.start()

    try:
        tasks_submitted = 0
        start_time = time.time()

        # Phase 1: High frequency tasks
        for i in range(5):
            bot.submit_task(f"Quick task {i} - keep it brief")
            tasks_submitted += 1
            time.sleep(0.02)

        time.sleep(0.5)
        results = bot.get_results()
        timing = time.time() - start_time
        print(f"   Phase 1: {len(results)}/{tasks_submitted} results in {timing:.3f}s")

        # Phase 2: Respect heartbeat timing
        for i in range(3, 6):
            bot.submit_task(f"Respectful task {i}")
            tasks_submitted += 1
            time.sleep(0.15)

        time.sleep(0.8)
        results.extend(bot.get_results())
        timing2 = time.time() - start_time - timing
        print(f"   Phase 2: {len(results)}/{tasks_submitted} results in {timing2:.3f}s")

        # Burst test
        early_results = len(results)
        for i in range(6, 11):
            bot.submit_task(f"Burst task {i}")
            tasks_submitted += 1

        time.sleep(0.1)
        results.extend(bot.get_results())
        burst_successful = len(results) > early_results
        print(f"   Burst detection: {'✅' if burst_successful else '❌'}")

        # Check metrics
        metrics = bot.get_metrics()
        req = metrics['total_requests']
        succ = metrics['successful_requests']
        rate = metrics['success_rate']
        print(f"   Metrics: {req} req, {succ} succ, {rate:.1f}% rate")

        return all([
            len(results) > 0,
            rate >= 80.0,
            metrics.get('heartbeats_per_second', 0) > 15,
        ])

    finally:
        bot.stop()


def test_thread_safety():
    """Test thread safety"""
    print("\n🛡️  Testing ThreadBotAgent Thread Safety...")

    config = {
        'ollama_host': 'http://localhost:11434',
        'context_length': 1024,
        'temperature': 0.5,
        'heartbeat_interval': 0.02
    }

    bot = ThreadBotAgent(bot_id=300, model='gemma3:270m', config=config)
    bot.start()

    try:
        def worker_thread(thread_id: int):
            for i in range(3):
                task = f"Thread {thread_id} task {i} - verify isolation"
                bot.submit_task(task)
                time.sleep(0.01)

        threads = []
        for i in range(5):
            t = threading.Thread(target=worker_thread, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=2.0)

        metrics = bot.get_metrics()
        expected = 5 * 3
        submitted = metrics['total_requests']
        queue = metrics['queue_size']

        print(f"   Expected tasks: {expected}")
        print(f"   Tasks submitted: {submitted}")
        print(f"   Queue size: {queue}")

        return submitted == expected

    finally:
        bot.stop()


def test_health_check():
    """Test health check functionality"""
    print("\n🏥 Testing ThreadBotAgent Health Check...")

    bad_config = {
        'ollama_host': 'http://127.0.0.99:99999',
        'context_length': 1024,
        'temperature': 0.7,
        'heartbeat_interval': 0.1
    }

    bot = ThreadBotAgent(bot_id=400, model='gemma3:270m', config=bad_config)
    health_ok = bot.health_check()

    if health_ok:
        print("⚠️  Health check passed for invalid host (unexpected)")
    else:
        print("✅ Health check correctly failed for invalid host")

    good_config = {
        'ollama_host': 'http://localhost:11434',
        'context_length': 1024,
        'temperature': 0.7,
        'heartbeat_interval': 0.1
    }

    good_bot = ThreadBotAgent(bot_id=401, model='gemma3:270m', config=good_config)
    good_health = good_bot.health_check()

    print(f"   Good host health check: {'✅' if good_health else '❌'}")

    return good_health


def main():
    """Run all ThreadBotAgent tests"""
    print("=" * 60)
    print("🧵 THREADBOTAGENT VALIDATION SUITE")
    print("=" * 60)

    tests = [
        ("Basic Functionality", test_thread_bot_agent),
        ("Heartbeat Pattern", test_thread_bot_agent_heartbeat),
        ("Thread Safety", test_thread_safety),
        ("Health Check", test_health_check),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🏃 Running: {test_name}")
        try:
            result = test_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"Result: {status}")
            results.append(result)
        except Exception as e:
            print(f"Result: ❌ ERROR - {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"🎯 Results Summary: {passed}/{total} tests passed")
    print(f"Success Rate: {passed/total*100:.1f}%" if total > 0 else "N/A")

    if passed == total:
        print("🎉 ALL TESTS PASSED - ThreadBotAgent ready for integration")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Review threading implementation")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
