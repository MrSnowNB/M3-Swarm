'''
Threading Swarm Manager - REAL PARALLEL SWARM
Uses threading for TRUE concurrent execution across multiple CPU cores
'''
import asyncio
import threading
import time
from typing import List, Dict, Any, Optional
from core.bot_agent_threading_FIXED import ThreadBotAgent, BotResponse


class ThreadSwarmManager:
    '''Manages swarm of truly parallel bot threads'''

    def __init__(self, config_path: str = "config/swarm_config.yaml"):
        # Load config synchronously for compatibility
        import yaml
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.bots: List[ThreadBotAgent] = []

        # Z8 pattern configuration
        self.heartbeat_interval = self.config.get('swarm', {}).get('heartbeat_interval', 0.1)
        self.spawn_stagger = self.config.get('swarm', {}).get('spawn_stagger_seconds', 0.05)

    def spawn_bot(self, bot_id: int) -> bool:
        '''Spawn single bot thread'''
        try:
            bot = ThreadBotAgent(
                bot_id=bot_id,
                config={
                    'ollama_host': self.config['ollama']['host'],
                    'model': self.config['model']['name'],
                    'heartbeat_interval': self.heartbeat_interval
                }
            )

            bot.start()
            self.bots.append(bot)

            print(f"✅ Bot {bot_id} thread started")
            return True

        except Exception as e:
            print(f"❌ Failed to spawn bot {bot_id}: {e}")
            return False

    async def spawn_swarm(self, count: int) -> int:
        '''
        Spawn bots with staggered timing (Z8 pattern)
        This prevents thundering herd and smooths CPU load
        '''
        print(f"\n🚀 Spawning {count} REAL PARALLEL bot threads...")
        print(f"   Heartbeat: {self.heartbeat_interval}s (CPU smoothing)")
        print(f"   Stagger: {self.spawn_stagger}s (prevents spike)\n")

        successful = 0
        for i in range(count):
            if self.spawn_bot(i):
                successful += 1

            # Stagger spawn to prevent initial CPU spike (Z8 pattern)
            if i < count - 1:  # Don't sleep after last bot
                time.sleep(self.spawn_stagger)

        print(f"\n✅ {successful}/{count} bot threads spawned")
        print(f"   Total OS threads: {threading.active_count()}\n")

        return successful

    async def spawn_swarm_staggered(self, count: int) -> int:
        '''Alias for spawn_swarm for backward compatibility'''
        return await self.spawn_swarm(count)

    async def spawn_and_wait_ready(self, count: int, health_timeout: int = 10) -> bool:
        '''
        Spawn bots and verify all are ready with healthy Ollama connections
        Returns True only if ALL bots pass health checks
        '''
        print(f"\n🚀 Spawning {count} bots and verifying health...")
        print(f"   Health timeout: {health_timeout}s per bot")
        print(f"   Heartbeat: {self.heartbeat_interval}s (CPU smoothing)")
        print(f"   Stagger: {self.spawn_stagger}s (prevents spike)\n")

        # Spawn bots
        spawned = await self.spawn_swarm(count)
        if spawned != count:
            print(f"\n❌ Failed to spawn all {count} bots (got {spawned})")
            return False

        # Wait for warm-up/stabilization
        print("⏳ Allowing bots to stabilize...")
        time.sleep(2)

        # Verify all bots pass health checks
        print("🔍 Running health checks on all bots...")
        healthy_count = 0

        for i, bot in enumerate(self.bots):
            try:
                healthy = await bot.health_check()
                if healthy:
                    healthy_count += 1
                    print(f"✅ Bot {i} health check PASSED")
                else:
                    print(f"❌ Bot {i} health check FAILED")
            except Exception as e:
                print(f"❌ Bot {i} health check ERROR: {e}")

        if healthy_count == count:
            print(f"\n🎉 ALL {count} BOTS HEALTHY AND READY!\n")
            return True
        else:
            print(f"\n❌ Only {healthy_count}/{count} bots healthy. Aborting.")
            return False

    def broadcast_task(self, prompt: str):
        '''Send task to ALL bots simultaneously (TRUE PARALLEL EXECUTION)'''
        for bot in self.bots:
            bot.submit_task(prompt)

    def collect_results(self, timeout=5.0) -> List[BotResponse]:
        '''Collect results from all bots'''
        results = []
        deadline = time.time() + timeout

        for bot in self.bots:
            remaining = deadline - time.time()
            if remaining > 0:
                result = bot.get_result(timeout=remaining)
                if result:
                    results.append(result)

        return results

    async def execute_task_batch(self, prompts: List[str]) -> List[Any]:
        '''
        Execute batch of tasks across the swarm
        This ensures compatibility with existing async interface
        '''
        # Broadcast all prompts simultaneously
        for prompt in prompts:
            self.broadcast_task(prompt)

        # Collect results
        results = self.collect_results(timeout=10.0)

        # Convert to expected format (list of responses)
        responses = []
        for result in results:
            if result.success:
                responses.append({
                    'success': True,
                    'response': result.response,
                    'response_time': result.response_time,
                    'bot_id': result.bot_id
                })
            else:
                responses.append({
                    'success': False,
                    'error': result.error,
                    'response_time': result.response_time,
                    'bot_id': result.bot_id
                })

        return responses

    async def run_parallel_test(self, prompts: List[str], duration: int) -> Dict[str, Any]:
        '''
        Run TRUE parallel test
        All bots execute simultaneously on different CPU cores
        '''
        print(f"\n{'='*80}")
        print(f"🧪 TRUE PARALLEL TEST: {len(self.bots)} bots, {duration}s")
        print(f"{'='*80}\n")

        start_time = time.time()
        total_iterations = 0
        all_results = []

        while time.time() - start_time < duration:
            # Broadcast prompts to ALL bots simultaneously
            for prompt in prompts:
                self.broadcast_task(prompt)

            # Collect results (bots processed in parallel)
            results = self.collect_results(timeout=2.0)
            all_results.extend(results)

            total_iterations += 1
            elapsed = time.time() - start_time
            print(f"  Iteration {total_iterations} | Results: {len(results)} | "
                  f"Elapsed: {elapsed:.1f}s")

            # Small pause between iterations
            if elapsed < duration:
                time.sleep(0.5)

        # Collect final results
        final_results = self.collect_results(timeout=2.0)
        all_results.extend(final_results)

        # Calculate metrics
        successful = sum(1 for r in all_results if r.success)
        success_rate = (successful / len(all_results) * 100) if all_results else 0

        print(f"\n{'='*80}")
        print(f"✅ PARALLEL TEST COMPLETE")
        print(f"{'='*80}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Total results: {len(all_results)}")
        print(f"Active threads: {threading.active_count()}")
        print(f"{'='*80}\n")

        return {
            'bot_count': len(self.bots),
            'duration': time.time() - start_time,
            'total_results': len(all_results),
            'successful': successful,
            'success_rate': success_rate,
            'concurrency_model': 'threading',
            'thread_count': threading.active_count()
        }

    def get_swarm_metrics(self) -> Dict[str, Any]:
        '''Aggregate metrics from all bots'''
        bot_metrics = [bot.get_metrics() for bot in self.bots]

        total_requests = sum(m['total_tasks'] for m in bot_metrics)
        successful_requests = sum(m['successful_tasks'] for m in bot_metrics)

        return {
            'total_bots': len(self.bots),
            'active_bots': sum(1 for b in self.bots if b.running),
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'aggregate_success_rate': (
                successful_requests / total_requests * 100
                if total_requests > 0 else 0
            ),
            'per_bot_metrics': bot_metrics,
            'concurrency_model': 'threading',
            'active_threads': threading.active_count()
        }

    def shutdown(self):
        '''Stop all bot threads'''
        print(f"\n🛑 Shutting down {len(self.bots)} bot threads...")
        for bot in self.bots:
            bot.stop()
        print("✅ All threads stopped\n")

    async def run_stress_test(self, bot_count: int, duration: int, batch_size: int = 4) -> Dict[str, Any]:
        '''
        Run stress test with specified parameters
        Compatibility interface for existing tests
        '''
        # Spawn bots if needed
        if len(self.bots) == 0:
            await self.spawn_swarm(bot_count)

        # Create test prompts
        test_prompts = [
            "Explain async programming briefly.",
            "What is 2+2?",
            "Classify this sentiment: This is great!",
            "Summarize: AI is transforming software development."
        ]

        results = await self.run_parallel_test(test_prompts, duration)
        return {
            'duration': results['duration'],
            'total_tasks': results['total_results'],
            'successful_tasks': results['successful'],
            'success_rate': results['success_rate'],
            'concurrency_model': 'threading',
            'thread_count': results['thread_count'],
            'bot_count': results['bot_count']
        }
