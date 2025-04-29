import time
import heapq
from typing import Callable, Any, Optional
from agent_tools.ragis_logger import RagisLogger

# Centralized logger for task management actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=[])

class TaskManager:
    """
    Simple priority-based task manager using a min-heap.
    Lower priority numbers are executed first.
    """
    def __init__(self):
        self.queue: list[tuple[int, dict]] = []

    def add_task(self, action: str, params: Optional[dict] = None, priority: int = 5):
        """
        Add a task to the queue.
        Args:
            action: The action name or identifier.
            params: Optional dictionary of parameters for the task.
            priority: Lower numbers run first (default 5).
        """
        task = {
            "priority": -priority,  # Negate for min-heap
            "action": action,
            "params": params or {}
        }
        heapq.heappush(self.queue, (task["priority"], task))
        logger.log("add_task", {
            "action": action,
            "priority": priority,
            "params": params
        })

    def next_task(self) -> Optional[dict]:
        """
        Pop and return the next task from the queue, or None if empty.
        """
        if not self.queue:
            return None
        _, task = heapq.heappop(self.queue)
        logger.log("next_task", {"task": task})
        return task

    def has_tasks(self) -> bool:
        """
        Return True if there are tasks in the queue.
        """
        return len(self.queue) > 0

def with_retry(task_fn: Callable[[], Any], retries: int = 2, delay: float = 1) -> Any:
    """
    Retry a task function up to 'retries' times with a delay between attempts.
    Args:
        task_fn: Callable with no arguments.
        retries: Number of retries (default 2).
        delay: Delay in seconds between retries (default 1).
    Returns:
        The result of task_fn if successful.
    Raises:
        The last exception if all retries fail.
    """
    for attempt in range(retries + 1):
        try:
            return task_fn()
        except Exception as e:
            logger.log("task_retry_error", {
                "attempt": attempt + 1,
                "error": str(e)
            })
            if attempt < retries:
                time.sleep(delay)
            else:
                logger.log("task_failed", {
                    "error": str(e),
                    "retries": retries + 1
                })
                print(f"Task failed after {retries + 1} attempts: {e}")
                raise e