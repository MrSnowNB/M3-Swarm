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
            # Check if this is an embedding model
            if self.config.get('embedding_only', False):
                # Use embeddings API for nomic-embed-text
                response = self.client.embeddings(
                    model=self.config.get('model', 'nomic-embed-text:137m-v1.5-fp16'),
                    prompt=prompt
                )

                # Convert embedding vector to string representation (as swarm needs response)
                embedding_vector = response['embedding']
                response_text = f"Embedding computed: {len(embedding_vector)} dimensions | first 5: {embedding_vector[:5]}"

            else:
                # Use chat API for conversation models
                response = self.client.chat(
                    model=self.config.get('model', 'gemma3:270m'),
                    messages=[{'role': 'user', 'content': prompt}]
                )
                response_text = response['message']['content']

            with self.lock:
                self.total_tasks += 1
                self.successful_tasks += 1

            return BotResponse(
                bot_id=self.bot_id,
                success=True,
                response=response_text,
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

    def health_check(self) -> bool:
        """Check if bot is healthy and can communicate with Ollama"""
        try:
            test_prompt = "Health check"
            result = self.execute(test_prompt, timeout=5.0)

            if not result.success:
                return False

            # Check response based on model type
            if self.config.get('embedding_only', False):
                # For embeddings, just check if we got a response with valid data
                return bool(result.response and isinstance(result.response, str) and len(result.response) > 0)
            else:
                # For chat models, check for OK response
                return bool(result.response and "OK" in str(result.response).upper())

        except Exception as e:
            # Health checks can fail legitimately - don't let them crash the system
            return False
