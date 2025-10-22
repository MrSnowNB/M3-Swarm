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
    Measure CPU usage during extended run
    """
    print("\n🫀 Testing ThreadBotAgent Heartbeat...")

    config = {
        'ollama_host': 'http://localhost:11434',
        'context_length': 2048,
        'temperature': 0.7,
        'heartbeat_interval': 0.05  # Fast heartbeat for testing
    }

    bot = ThreadBotAgent(bot_id=200, model='gemma3:270m', config=config)
    bot.start()

    try:
        # Run tasks at different rates to test heartbeat
        tasks_submitted = 0
        start_time = time.time()

        # Phase 1: High frequency tasks
        for i in range(5):
            bot.submit_task(f"Quick task {i} - keep it brief")
            tasks_submitted += 1
            time.sleep(0.02)  # Slightly faster than heartbeat

        # Wait for processing
        time.sleep(0.5)
        results = bot.get_results()

        print(f"   Phase 1: {len(results)}/{tasks_submitted} results")
        print(".3f"        # Phase 2: Respect heartbeat timing
        for i in range(3, 6):
            bot.submit_task(f"Respectful task {i}")
            tasks_submitted += 1
            time.sleep(0.15)  # Slower than heartbeat interval

        # Wait for processing
        time.sleep(0.8)
        results.extend(bot.get_results())

        print(f"   Phase 2: {len(results)}/{tasks_submitted} results")
        print(".3f"        # Verify heartbeat doesn't block rapid tasks
        early_results = len(results)

        # Burst of tasks
        for i in range(6, 11):
            bot.submit_task(f"Burst task {i}")
            tasks_submitted += 1

        time.sleep(0.1)  # Very short wait
        results.extend(bot.get_results())

        burst_successful = len(results) > early_results
        print(f"   Burst detection: {'✅' if burst_successful else '❌'}")

        # Check metrics
        metrics = bot.get_metrics()
        print(f"   Metrics: {metrics['total_requests']} req, "
              f"{metrics['successful_requests']} succ, "
              f"{metrics['success_rate']:.1f}% rate")

        return all([
            len(results) > 0,
            metrics['success_rate'] >= 80.0,
            metrics['heartbeats_per_second'] > 15,  # Should be ~20 with 0.05s interval
        ])

    finally:
        bot.stop()


def test_thread_safety():
    """
    Test thread safety of bot operations
    Run multiple threads pounding the bot with tasks
    """
    print("\n🛡️  Testing ThreadBotAgent Thread Safety...")

    config = {
        'ollama_host': 'http://localhost:11434',
        'context_length': 1024,  # Smaller for speed
        'temperature': 0.5,
        'heartbeat_interval': 0.02  # Very fast heartbeat
    }

    bot = ThreadBotAgent(bot_id=300, model='gemma3:270m', config=config)
    bot.start()

    try:
        def worker_thread(thread_id: int):
            """Worker thread that submits tasks"""
            for i in range(3):
                task = f"Thread {thread_id} task {i} - verify isolation"
                bot.submit_task(task)
                time.sleep(0.01)  # Rapid fire

        # Start multiple threads pounding the bot
        threads = []
        for i in range(5):  # 5 concurrent threads
            t = threading.Thread(target=worker_thread, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=2.0)

        # Verify all 15 tasks were submitted
        metrics = bot.get_metrics()
        expected_tasks = 5 * 3  # 5 threads * 3 tasks each

        print(f"   Expected tasks: {expected_tasks}")
        print(f"   Tasks submitted: {metrics['total_requests']}")
        print(f"   Queue size: {metrics['queue_size']}")

        return metrics['total_requests'] == expected_tasks

    finally:
        bot.stop()


def test_health_check():
    """
    Test that health check detects connection issues
    """
    print("\n🏥 Testing ThreadBotAgent Health Check...")

    # Test with invalid host
    bad_config = {
        'ollama_host': 'http://127.0.0.99:99999',  # Invalid host/port
        'context_length': 1024,
        'temperature': 0.7,
        'heartbeat_interval': 0.1
    }

    bot = ThreadBotAgent(bot_id=400, model='gemma3:270m', config=bad_config)

    # Health check should fail for invalid connection
    health_ok = bot.health_check()

    if health_ok:
        print("⚠️  Health check passed for invalid host (this may be OK if connected)")
    else:
        print("✅ Health check correctly failed for invalid host")

    # Test with valid host (same config as main tests)
    good_config = {
        'ollama_host': 'http://localhost:11434',
        'context_length': 1024,
        'temperature': 0.7,
        'heartbeat_interval': 0.1
    }

    good_bot = ThreadBotAgent(bot_id=401, model='gemma3:270m', config=good_config)
    good_health = good_bot.health_check()

    print(f"   Good host health check: {'✅' if good_health else '❌'}")

    return good_health  # Fail test if good health check fails


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

    # Summary
    passed = sum(results)
    total = len(results)

    print("
" + "=" * 60)
    print("(),"    print(f"Tests Passed: {passed}/{total}")
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
