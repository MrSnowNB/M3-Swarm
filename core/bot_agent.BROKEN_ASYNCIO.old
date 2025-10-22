"""
Bot Agent Template - Single bot instance for Swarm-100
AI Agent: Implement this class following the template structure
"""

import asyncio
import time
import ollama
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class BotResponse:
    """Structured response from bot execution"""
    bot_id: int
    success: bool
    response: Optional[str]
    response_time: float
    error: Optional[str] = None
    timestamp: float = 0

class BotAgent:
    """
    Single bot agent that can execute prompts via Ollama

    AI Agent Implementation Notes:
    - This bot must be async-capable
    - Handle errors gracefully without crashing
    - Log all actions for debugging
    - Support timeout configuration
    - Track metrics (response time, success/failure)
    - Implement retry logic for failed requests
    """

    def __init__(self, bot_id: int, model: str, config: Dict[str, Any]):
        """
        Initialize bot agent

        Args:
            bot_id: Unique identifier for this bot
            model: Ollama model name (e.g., "gemma3:270m")
            config: Configuration dict with timeout, context_length, etc.
        """
        self.bot_id = bot_id
        self.model = model
        self.config = config

        # Initialize Ollama async client from config
        host = config.get('ollama_host', 'http://localhost:11434')
        self.client = ollama.AsyncClient(host=host)

        # Metrics tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0

        # Retry configuration from config
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay_seconds', 2)

    async def execute(self, prompt: str, timeout: Optional[int] = None) -> BotResponse:
        """
        Execute a single prompt and return response with retry logic

        Args:
            prompt: Text prompt to send to model
            timeout: Optional timeout in seconds (overrides config)

        Returns:
            BotResponse with success status and result

        AI Agent Implementation:
        1. Start timer
        2. Implement retry logic with exponential backoff
        3. Call Ollama async API with prompt
        4. Handle timeout properly
        5. Catch and log any exceptions
        6. Update metrics
        7. Return structured BotResponse
        """
        start_time = time.time()
        timeout = timeout or self.config.get('timeout', 30)
        retry_count = 0
        last_error = None

        while retry_count <= self.max_retries:
            try:
                # Implement async Ollama call with timeout and options from config
                response = await asyncio.wait_for(
                    self.client.chat(
                        model=self.model,
                        messages=[{'role': 'user', 'content': prompt}],
                        options={
                            'num_ctx': self.config.get('context_length', 2048),
                            'temperature': self.config.get('temperature', 0.7),
                            'top_k': self.config.get('top_k', 40),
                            'top_p': self.config.get('top_p', 0.9)
                        }
                    ),
                    timeout=timeout
                )

                # Extract response text from Ollama response
                response_text = response.get('message', {}).get('content', '')
                if not response_text:
                    raise ValueError("Empty response from Ollama")

                response_time = time.time() - start_time

                # Update metrics
                self.total_requests += 1
                self.successful_requests += 1
                self.total_response_time += response_time

                return BotResponse(
                    bot_id=self.bot_id,
                    success=True,
                    response=response_text,
                    response_time=response_time,
                    timestamp=time.time()
                )

            except asyncio.TimeoutError as e:
                last_error = f"Timeout after {timeout}s"
                if retry_count < self.max_retries:
                    print(f"⚠️  Bot {self.bot_id} retry {retry_count + 1}/{self.max_retries} for timeout")
                    await asyncio.sleep(self.retry_delay * (2 ** retry_count))  # Exponential backoff
                    retry_count += 1
                    continue
                break

            except Exception as e:
                last_error = str(e)
                if retry_count < self.max_retries:
                    print(f"⚠️  Bot {self.bot_id} retry {retry_count + 1}/{self.max_retries} for error: {last_error}")
                    await asyncio.sleep(self.retry_delay * (2 ** retry_count))  # Exponential backoff
                    retry_count += 1
                    continue
                break

        # All retries exhausted
        response_time = time.time() - start_time
        self.total_requests += 1
        self.failed_requests += 1

        # Update metrics for retry attempts
        self.total_response_time += response_time

        return BotResponse(
            bot_id=self.bot_id,
            success=False,
            response=None,
            response_time=response_time,
            error=f"Failed after {self.max_retries} retries: {last_error}",
            timestamp=time.time()
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Return bot performance metrics"""
        avg_response_time = (
            self.total_response_time / self.total_requests 
            if self.total_requests > 0 else 0
        )

        success_rate = (
            self.successful_requests / self.total_requests * 100 
            if self.total_requests > 0 else 0
        )

        return {
            'bot_id': self.bot_id,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time
        }

    async def health_check(self) -> bool:
        """Check if bot is healthy and can communicate with Ollama"""
        try:
            # TODO: AI Agent - Implement actual health check
            # Test with minimal prompt
            response = await self.execute("test", timeout=5)
            return response.success
        except Exception:
            return False


# AI Agent Validation Tests:
# 1. Bot can be initialized with config
# 2. Bot can execute single prompt successfully
# 3. Bot handles timeout correctly
# 4. Bot handles errors without crashing
# 5. Bot metrics are tracked accurately
# 6. Health check works
