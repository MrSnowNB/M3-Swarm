'''
Threading Bot Agent - REAL PARALLELISM
This implementation uses OS threads for true concurrent execution
'''
import threading
import time
import ollama
from typing import Optional, Dict, Any
from queue import Queue


class BotResponse:
    """Standardized response format for threading implementation"""
    def __init__(self, bot_id: int, success: bool = False, response: Optional[str] = None,
                 response_time: float = 0.0, error: Optional[str] = None):
        self.bot_id = bot_id
        self.success = success
        self.response = response
        self.response_time = response_time
        self.error = error
        self.timestamp = time.time()


class ThreadBotAgent:
    '''Bot that runs in dedicated OS thread'''

    def __init__(self, bot_id: int, config: Dict[str, Any]):
        self.bot_id = bot_id
        self.config = config
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Thread-safe communication
        self.task_queue = Queue()
        self.result_queue = Queue()

        # Ollama client (thread-safe)
        self.client = ollama.Client(host=config.get('ollama_host', 'http://localhost:11434'))

        # Metrics (thread-safe with lock)
        self.lock = threading.Lock()
        self.total_tasks = 0
        self.successful_tasks = 0

        # Heartbeat for CPU smoothing (Z8 pattern)
        self.heartbeat_interval = config.get('heartbeat_interval', 0.1)

    def start(self):
        '''Start bot thread - TRUE CONCURRENT EXECUTION'''
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._bot_loop, daemon=True, name=f"Bot-{self.bot_id}")
        self.thread.start()
        print(f"✅ Bot {self.bot_id} thread started (OS thread ID: {self.thread.ident})")

    def stop(self):
        '''Stop bot thread gracefully'''
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        print(f"🛑 Bot {self.bot_id} thread stopped")

    def _bot_loop(self):
        '''Main bot loop - runs continuously in dedicated thread'''
        while self.running:
            # Check for task (non-blocking)
            try:
                task = self.task_queue.get(timeout=0.1)
                result = self._execute_task(task)
                self.result_queue.put(result)
            except:
                pass  # No task available

            # Heartbeat pause to prevent CPU spikes (Z8 pattern)
            time.sleep(self.heartbeat_interval)

    def _execute_task(self, prompt: str) -> BotResponse:
        '''Execute task synchronously (releases GIL during I/O)'''
        start = time.time()

        try:
            # Ollama call releases GIL - allows true parallelism
            response = self.client.chat(
                model=self.config.get('model', 'gemma3:270m'),
                messages=[{'role': 'user', 'content': prompt}]
            )

            with self.lock:
                self.total_tasks += 1
                self.successful_tasks += 1

            return BotResponse(
                bot_id=self.bot_id,
                success=True,
                response=response['message']['content'],
                response_time=time.time() - start
            )

        except Exception as e:
            with self.lock:
                self.total_tasks += 1

            return BotResponse(
                bot_id=self.bot_id,
                success=False,
                error=str(e),
                response_time=time.time() - start
            )

    def execute(self, prompt: str, timeout: Optional[float] = None) -> BotResponse:
        '''Synchronous interface for threading implementation'''
        self.submit_task(prompt)
        timeout_val = timeout or 5.0
        result = self.get_result(timeout_val)
        if result:
            return result
        return BotResponse(
            bot_id=self.bot_id,
            success=False,
            error="Task timeout",
            response_time=timeout_val
        )

    def submit_task(self, prompt: str):
        '''Submit task to bot (thread-safe)'''
        self.task_queue.put(prompt)

    def get_result(self, timeout=1.0) -> Optional[BotResponse]:
        '''Get result from bot (thread-safe)'''
        try:
            return self.result_queue.get(timeout=timeout)
        except:
            return None

    def get_metrics(self) -> Dict[str, Any]:
        '''Get bot metrics (thread-safe)'''
        with self.lock:
            return {
                'bot_id': self.bot_id,
                'total_tasks': self.total_tasks,
                'successful_tasks': self.successful_tasks,
                'success_rate': (self.successful_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0,
                'queue_size': self.task_queue.qsize()
            }

    async def health_check(self) -> bool:
        """Check if bot is healthy and can communicate with Ollama"""
        try:
            # Simple health check for compatibility with async interface
            result = self.execute("Health check: respond with OK", timeout=3.0)
            return bool(result.success and result.response and "OK" in str(result.response).upper())
        except:
            return False
