#!/usr/bin/env python3
"""
Threading-based Bot Agent - Z8 Swarm Heartbeat Pattern
Replaces asyncio with threading for true concurrent execution
"""

import threading
import time
import ollama
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BotResponse:
    """Structured response from threading bot execution"""
    bot_id: int
    success: bool
    response: Optional[str]
    response_time: float
    error: Optional[str] = None
    timestamp: float = 0


class ThreadBotAgent:
    """
    Threading-based bot agent with Z8 heartbeat pattern.

    This replaces the asyncio AsyncBotAgent with true threading for concurrent execution.
    Each bot runs in its own thread with heartbeat-based pacing to prevent CPU spikes.
    """

    def __init__(self, bot_id: int, model: str, config: Dict[str, Any]):
        """
        Initialize threading bot agent

        Args:
            bot_id: Unique bot identifier
            model: Ollama model name
            config: Configuration dictionary
        """
        self.bot_id = bot_id
        self.model = model
        self.config = config

        # Ollama client (synchronous for threading)
        host = config.get('ollama_host', 'http://localhost:11434')
        self.client = ollama.Client(host=host)

        # Thread management
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.heartbeat_interval = config.get('heartbeat_interval', 0.1)  # Z8 pattern

        # Synchronization primitives
        self.lock = threading.Lock()
        self.task_queue = []
        self.results = []

        # Metrics tracking (thread-safe)
        self.metrics_lock = threading.Lock()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    def start(self) -> None:
        """
        Start the bot thread with heartbeat loop
        """
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True, name=f"Bot-{self.bot_id}")
        self.thread.start()
        print(f"🧵 Bot {self.bot_id} thread started")

    def stop(self) -> None:
        """
        Gracefully stop the bot thread
        """
        self.running = False
        if self.thread:
            # Wait for thread to finish (timeout after 5s)
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                print(f"⚠️  Bot {self.bot_id} thread did not stop gracefully")
        print(f"🛑 Bot {self.bot_id} thread stopped")

    def _run_loop(self) -> None:
        """
        Main bot execution loop with Z8 heartbeat pattern

        This implements the Z8 pattern: continuous heartbeat with task processing.
        The heartbeat prevents CPU spikes while allowing true concurrent execution.
        """
        while self.running:
            # Check for tasks to process
            task = self._get_next_task()
            if task:
                result = self._execute_task(task)
                self._store_result(result)

            # Z8 Heartbeat: Prevent CPU saturation while maintaining responsiveness
            time.sleep(self.heartbeat_interval)

    def _get_next_task(self) -> Optional[str]:
        """
        Thread-safe task retrieval
        Returns next task from queue or None if empty
        """
        with self.lock:
            if self.task_queue:
                return self.task_queue.pop(0)
        return None

    def _store_result(self, result: BotResponse) -> None:
        """
        Thread-safe result storage
        """
        with self.lock:
            self.results.append(result)

    def _execute_task(self, prompt: str) -> BotResponse:
        """
        Execute single prompt and return structured response

        This is the synchronous Ollama call within the thread.
        """
        start_time = time.time()

        try:
            # Ollama synchronous call (blocking, but in dedicated thread)
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'num_ctx': self.config.get('context_length', 2048),
                    'temperature': self.config.get('temperature', 0.7),
                    'top_k': self.config.get('top_k', 40),
                    'top_p': self.config.get('top_p', 0.9)
                }
            )

            response_time = time.time() - start_time

            # Update metrics (thread-safe)
            with self.metrics_lock:
                self.total_requests += 1
                self.successful_requests += 1

            return BotResponse(
                bot_id=self.bot_id,
                success=True,
                response=response['message']['content'],
                response_time=response_time,
                timestamp=time.time()
            )

        except Exception as e:
            response_time = time.time() - start_time

            # Update metrics for failure (thread-safe)
            with self.metrics_lock:
                self.total_requests += 1
                self.failed_requests += 1

            return BotResponse(
                bot_id=self.bot_id,
                success=False,
                response=None,
                response_time=response_time,
                error=str(e),
                timestamp=time.time()
            )

    def submit_task(self, prompt: str) -> None:
        """
        Thread-safe task submission
        Called from external threads to queue work for this bot
        """
        with self.lock:
            self.task_queue.append(prompt)

    def get_results(self) -> list:
        """
        Thread-safe result retrieval
        Returns accumulated results and clears the queue
        """
        with self.lock:
            results = self.results.copy()
            self.results.clear()
            return results

    def get_metrics(self) -> Dict[str, Any]:
        """
        Thread-safe metrics retrieval
        Returns current performance statistics
        """
        with self.metrics_lock:
            success_rate = (
                self.successful_requests / self.total_requests * 100
                if self.total_requests > 0 else 0
            )

            return {
                'bot_id': self.bot_id,
                'thread_name': self.thread.name if self.thread else 'unknown',
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': round(success_rate, 2),
                'queue_size': len(self.task_queue) if hasattr(self, 'task_queue') else 0,
                'heartbeats_per_second': 1 / self.heartbeat_interval if self.heartbeat_interval > 0 else 0
            }

    def health_check(self) -> bool:
        """
        Verify bot can connect to Ollama service
        """
        try:
            # Quick test call with short prompt
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': 'test'}],
                options={'num_ctx': 100}  # Very short for quick check
            )
            return response is not None
        except Exception:
            return False


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def test_thread_bot_agent():
    """
    Basic validation test for ThreadBotAgent
    Called during Phase 1 implementation
    """
    print("\n🧵 Testing ThreadBotAgent...")

    config = {
        'ollama_host': 'http://localhost:11434',
        'context_length': 2048,
        'temperature': 0.7,
        'heartbeat_interval': 0.05  # Faster for testing
    }

    # Create bot
    bot = ThreadBotAgent(bot_id=99, model='gemma3:270m', config=config)

    # Start bot
    bot.start()
    time.sleep(0.1)  # Let thread start

    # Submit test task
    bot.submit_task("Say 'Hello World'")

    # Wait for processing
    time.sleep(0.5)

    # Check results
    results = bot.get_results()
    if results:
        result = results[0]
        print(f"✅ Task result: success={result.success}, time={result.response_time:.3f}s")
        if result.success:
            print(f"   Response: {result.response}")
    else:
        print("❌ No result received")

    # Check metrics
    metrics = bot.get_metrics()
    print(f"📊 Metrics: {metrics}")
    print(f"🎯 Thread name: {metrics['thread_name']}")

    # Stop bot
    bot.stop()

    print("✅ ThreadBotAgent basic test complete\n")
    return True


if __name__ == "__main__":
    test_thread_bot_agent()
