"""
Task Router Template - Distributes tasks to available bots
AI Agent: Implement this class to route tasks efficiently across the swarm
"""

import asyncio
from typing import List, Dict, Any, Optional
from collections import deque
import time
from dataclasses import dataclass

# Import after bot_agent.py is implemented
# from core.bot_agent import BotResponse, BotAgent

@dataclass
class Task:
    """Represents a task to be executed"""
    id: str
    prompt: str
    priority: int = 1  # 1=normal, 2=high, 3=urgent
    timeout: Optional[int] = None
    created_at: float = 0

    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()

@dataclass
class TaskResult:
    """Result of executing a task"""
    task_id: str
    bot_id: int
    success: bool
    response: Optional[str]
    response_time: float
    error: Optional[str] = None
    timestamp: float = 0

class TaskRouter:
    """
    Routes tasks to available bots using different strategies

    Strategies implemented:
    - Round Robin: Cycle through bots sequentiall
    - Least Loaded: Send to bot with fewest active tasks
    - Priority Queue: Handle urgent tasks first
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize task router

        Args:
            config: Swarm configuration dictionary
        """
        self.config = config
        self.bots: List[Any] = []  # List of BotAgent instances
        self.task_queues: Dict[int, asyncio.Queue] = {}
        self.round_robin_index = 0

        # Metrics
        self.metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'avg_response_time': 0.0,
            'bot_utilization': {}
        }

        # Task queues by priority
        self.priority_queues = {
            1: deque(),  # normal
            2: deque(),  # high
            3: deque()   # urgent
        }

    def register_bot(self, bot: Any) -> None:
        """
        Register a bot with the router

        Args:
            bot: BotAgent instance
        """
        # TODO: AI Agent - Register bot and create task queue
        # self.bots.append(bot)
        # self.task_queues[bot.bot_id] = asyncio.Queue()
        pass

    def submit_task(self, prompt: str, priority: int = 1, timeout: Optional[int] = None) -> str:
        """
        Submit a task for execution

        Args:
            prompt: Task prompt text
            priority: Task priority (1-3)
            timeout: Optional timeout override

        Returns:
            Task ID string
        """
        task_id = f"task_{int(time.time() * 1000)}_{priority}"
        task = Task(
            id=task_id,
            prompt=prompt,
            priority=priority,
            timeout=timeout
        )

        # Add to appropriate priority queue
        self.priority_queues[priority].append(task)

        print(f"📋 Task {task_id} submitted (priority {priority})")
        return task_id

    def _select_bot_round_robin(self) -> int:
        """Select bot using round-robin strategy"""
        if not self.bots:
            raise RuntimeError("No bots registered")

        bot_id = self.bots[self.round_robin_index % len(self.bots)].bot_id
        self.round_robin_index += 1
        return bot_id

    def _select_bot_least_loaded(self) -> int:
        """Select bot with fewest queued tasks"""
        if not self.bots:
            raise RuntimeError("No bots registered")

        # Find bot with smallest queue
        min_load = float('inf')
        selected_bot_id = self.bots[0].bot_id

        for bot in self.bots:
            queue = self.task_queues.get(bot.bot_id)
            if queue:
                queue_size = queue.qsize()
            else:
                queue_size = 0
            if queue_size < min_load:
                min_load = queue_size
                selected_bot_id = bot.bot_id

        return selected_bot_id

    async def execute_next_task(self) -> Optional[TaskResult]:
        """
        Execute the next available task

        Returns:
            TaskResult or None if no tasks available
        """
        # Check priority queues (urgent first)
        task = None
        for priority in [3, 2, 1]:
            if self.priority_queues[priority]:
                task = self.priority_queues[priority].popleft()
                break

        if not task:
            return None

        # Select bot based on strategy
        strategy = self.config['swarm']['task_distribution']['strategy']

        if strategy == 'round_robin':
            bot_id = self._select_bot_round_robin()
        elif strategy == 'least_loaded':
            bot_id = self._select_bot_least_loaded()
        else:
            # Default to round robin
            bot_id = self._select_bot_round_robin()

        # TODO: AI Agent - Get bot instance and execute task
        # bot = next((b for b in self.bots if b.bot_id == bot_id), None)
        # if not bot:
        #     return TaskResult(
        #         task_id=task.id,
        #         bot_id=bot_id,
        #         success=False,
        #         response=None,
        #         response_time=0,
        #         error="Bot not found",
        #         timestamp=time.time()
        #     )

        # Execute task
        # response = await bot.execute(task.prompt, task.timeout)

        # PLACEHOLDER - Simulate execution
        await asyncio.sleep(0.1)
        response_time = 0.5
        success = True
        response_text = f"Processed: {task.prompt[:50]}"

        result = TaskResult(
            task_id=task.id,
            bot_id=bot_id,
            success=success,
            response=response_text,
            response_time=response_time,
            timestamp=time.time()
        )

        # Update metrics
        self.metrics['total_tasks'] += 1
        if success:
            self.metrics['successful_tasks'] += 1
        else:
            self.metrics['failed_tasks'] += 1

        self.metrics['avg_response_time'] = (
            (self.metrics['avg_response_time'] * (self.metrics['total_tasks'] - 1)) +
            response_time
        ) / self.metrics['total_tasks']

        print(f"✅ Task {task.id} completed by bot {bot_id} ({response_time:.2f}s)")
        return result

    async def process_batch(self, max_tasks: Optional[int] = None) -> List[TaskResult]:
        """
        Process a batch of tasks

        Args:
            max_tasks: Maximum tasks to process (None = all available)

        Returns:
            List of TaskResult objects
        """
        results = []
        tasks_processed = 0

        while tasks_processed < (max_tasks or float('inf')):
            result = await self.execute_next_task()
            if not result:
                break

            results.append(result)
            tasks_processed += 1

            # Small delay between tasks
            await asyncio.sleep(0.01)

        return results

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        total_queued = sum(len(queue) for queue in self.priority_queues.values())

        return {
            'total_queued': total_queued,
            'priority_1_queued': len(self.priority_queues[1]),
            'priority_2_queued': len(self.priority_queues[2]),
            'priority_3_queued': len(self.priority_queues[3]),
            'registered_bots': len(self.bots)
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get router performance metrics"""
        queue_status = self.get_queue_status()
        self.metrics.update(queue_status)

        return self.metrics


# AI Agent Validation Tests:
# 1. Router can register bots correctly
# 2. Task submission works with different priorities
# 3. Round-robin distribution works
# 4. Least-loaded distribution prioritizes less busy bots
# 5. Batch processing executes multiple tasks
# 6. Queue status accurately reports pending tasks
# 7. Metrics track success rates and response times
