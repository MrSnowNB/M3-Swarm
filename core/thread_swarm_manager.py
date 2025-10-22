#!/usr/bin/env python3
"""
Threading Swarm Manager - Z8 Staggered Heartbeat Pattern
Replaces asyncio SwarmManager with true concurrent threading
"""

import threading
import time
import yaml
import psutil
from typing import List, Dict, Any
from core.thread_bot_agent import ThreadBotAgent, BotResponse


class ThreadSwarmManager:
    """
    Threading-based swarm manager with Z8 staggered heartbeat pattern.

    Replaces asyncio SwarmManager with true concurrent execution.
    All bots run simultaneously with heartbeat pacing to prevent thundering herd.
    """

    def __init__(self, config_path: str = "config/swarm_config.yaml"):
        """
        Initialize threading swarm manager

        Args:
            config_path: Path to swarm configuration YAML
        """
        self.config = self._load_config(config_path)
        self.bots: List[ThreadBotAgent] = []
        self.running = False

        # Z8 Heartbeat pattern configuration
        self.heartbeat_interval = self.config.get('swarm', {}).get('heartbeat_interval', 0.1)
        self.spawn_stagger = self.config.get('swarm', {}).get('spawn_stagger_seconds', 0.05)

        print("🔧 ThreadSwarmManager initialized:")
        print(f"   Heartbeat: {self.heartbeat_interval}s")
        print(f"   Spawn stagger: {self.spawn_stagger}s")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        """
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback configuration for threading
            print(f"⚠️ Config file {config_path} not found, using defaults")
            return {
                'model': {'name': 'gemma3:270m'},
                'ollama': {'host': 'http://localhost:11434', 'num_parallel': 10},
                'swarm': {
                    'heartbeat_interval': 0.1,
                    'spawn_stagger_seconds': 0.05
                }
            }

    def spawn_bot(self, bot_id: int) -> int:
        """
        Spawn single bot thread with health check

        Args:
            bot_id: Unique bot identifier

        Returns:
            1 if spawned successfully, 0 if failed
        """
        try:
            # Create bot with threading configuration
            bot_config = {
                'ollama_host': self.config['ollama']['host'],
                'context_length': self.config.get('model', {}).get('context_length', 2048),
                'temperature': self.config.get('model', {}).get('temperature', 0.7),
                'top_k': self.config.get('model', {}).get('top_k', 40),
                'top_p': self.config.get('model', {}).get('top_p', 0.9),
                'heartbeat_interval': self.heartbeat_interval
            }

            bot = ThreadBotAgent(
                bot_id=bot_id,
                model=self.config['model']['name'],
                config=bot_config
            )

            # Health check before adding to swarm
            if not bot.health_check():
                print(f"❌ Bot {bot_id} health check failed")
                return 0

            # Start the bot thread
            bot.start()

            # Small delay to let thread initialize
            time.sleep(0.01)

            self.bots.append(bot)

            # Validate thread is running
            if not bot.thread or not bot.thread.is_alive():
                print(f"❌ Bot {bot_id} thread did not start properly")
                return 0

            print(f"✅ Bot {bot_id} spawned and verified")
            return 1

        except Exception as e:
            print(f"❌ Failed to spawn bot {bot_id}: {e}")
            return 0

    def spawn_swarm_staggered(self, count: int) -> int:
        """
        Spawn multiple bots with Z8 staggered timing to prevent thundering herd.

        This implements the Z8 pattern: staggered spawns prevent initial CPU spike
        while allowing all bots to achieve true concurrency.

        Args:
            count: Number of bots to spawn

        Returns:
            Number of successfully spawned bots
        """
        print(f"\n🚀 Spawning {count} bots with staggered starts...")
        print(f"   Pattern: Z8 heartbeat stabilization")
        print(f"   Heartbeat: {self.heartbeat_interval}s")
        print(f"   Spawn stagger: {self.spawn_stagger}s")
        print()

        successful = 0

        # Record starting time for staggered spawning
        start_time = time.time()

        for i in range(count):
            successful += self.spawn_bot(i)

            # Z8 Staggered spawn: Prevent CPU thundering herd
            # Each bot starts with small delay to smooth initial resource usage
            if i < count - 1:  # Don't delay after last bot
                time.sleep(self.spawn_stagger)

        spawn_duration = time.time() - start_time

        print("\n✅ Swarm spawn complete:")
        print(f"   Total requested: {count}")
        print(f"   Successful spawns: {successful}")
        print(f"   Spawn rate: {successful/spawn_duration:.1f} bots/sec")
        print(f"   All threads verified alive: {self._all_threads_alive()}")
        print()

        return successful

    def broadcast_task(self, prompt: str) -> None:
        """
        Send task to all bots simultaneously (true concurrent execution)

        This is where threading provides the key advantage over asyncio:
        All bots process the same task truly simultaneously.

        Args:
            prompt: Task prompt to send to all bots
        """
        for bot in self.bots:
            bot.submit_task(prompt)

    def collect_results(self) -> List[BotResponse]:
        """
        Collect results from all bots

        Returns:
            List of all BotResponse objects from all active bots
        """
        all_results = []
        for bot in self.bots:
            results = bot.get_results()
            all_results.extend(results)
        return all_results

    def get_swarm_metrics(self) -> Dict[str, Any]:
        """
        Aggregate metrics from all bots
        Returns:
            Comprehensive swarm performance metrics
        """
        bot_metrics = [bot.get_metrics() for bot in self.bots]

        total_requests = sum(m['total_requests'] for m in bot_metrics)
        successful_requests = sum(m['successful_requests'] for m in bot_metrics)
        failed_requests = sum(m['failed_requests'] for m in bot_metrics)

        active_threads = sum(1 for b in self.bots if b.running)

        return {
            'architecture': 'threading',
            'total_bots': len(self.bots),
            'active_bots': active_threads,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'aggregate_success_rate': (
                successful_requests / total_requests * 100
                if total_requests > 0 else 0
            ),
            'per_bot_metrics': bot_metrics,
            'heartbeat_interval': self.heartbeat_interval,
            'spawn_stagger': self.spawn_stagger,
            'threads_alive': active_threads == len(self.bots)
        }

    def shutdown(self) -> None:
        """
        Gracefully shutdown all bot threads
        """
        print(f"\n🛑 Shutting down {len(self.bots)} bot threads...")

        shutdown_threads = []
        for bot in self.bots:
            t = threading.Thread(target=bot.stop)
            t.start()
            shutdown_threads.append(t)

        # Wait for all shutdowns to complete (with timeout)
        for t in shutdown_threads:
            t.join(timeout=10.0)

        # Verify all threads are stopped
        still_alive = [b.bot_id for b in self.bots if b.thread and b.thread.is_alive()]
        if still_alive:
            print(f"⚠️ Threads still alive: {still_alive}")
        else:
            print("✅ All bot threads gracefully shutdown")

        self.bots.clear()
        self.running = False

    def _all_threads_alive(self) -> bool:
        """Check if all bot threads are alive"""
        return all(bot.thread and bot.thread.is_alive() for bot in self.bots)


def test_thread_swarm_manager():
    """
    Basic validation test for ThreadSwarmManager
    Called during Phase 1 implementation
    """
    print("\n🧫 Testing ThreadSwarmManager...")

    # Create manager with test config
    manager = ThreadSwarmManager('config/swarm_config.yaml')

    try:
        # Test spawning small swarm
        spawned = manager.spawn_swarm_staggered(2)

        if spawned != 2:
            print(f"❌ Expected 2 bots spawned, got {spawned}")
            return False

        # Verify threads are alive
        if not manager._all_threads_alive():
            print("❌ Not all bot threads are alive")
            return False

        # Test broadcast
        manager.broadcast_task("Hello from all bots!")

        # Wait for processing
        time.sleep(0.5)

        # Collect results
        results = manager.collect_results()
        if not results:
            print("❌ No results collected from broadcast")
            return False

        print(f"✅ Broadcast successful: {len(results)} responses")

        # Check swarm metrics
        metrics = manager.get_swarm_metrics()
        print(f"📊 Swarm metrics: {metrics}")

    finally:
        manager.shutdown()

    print("✅ ThreadSwarmManager basic test complete\n")
    return True


if __name__ == "__main__":
    test_thread_swarm_manager()
