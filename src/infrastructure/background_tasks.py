"""Background task queue for non-critical operations."""

import asyncio
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Background task representation."""
    
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Initialize created_at if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()


class TaskQueue:
    """
    Background task queue for non-critical operations.
    
    Executes tasks asynchronously without blocking main operations.
    Useful for audit logging, cache warming, notifications, etc.
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize task queue.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.queue: asyncio.Queue = asyncio.Queue()
        self.tasks: Dict[str, Task] = {}
        self.workers: List[asyncio.Task] = []
        self._running = False
        self._task_counter = 0
    
    async def start(self) -> None:
        """Start background workers."""
        if self._running:
            return
        
        self._running = True
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]
        logger.info(f"Started {self.max_workers} background workers")
    
    async def stop(self) -> None:
        """Stop background workers gracefully."""
        self._running = False
        
        # Wait for queue to be empty
        await self.queue.join()
        
        # Cancel workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Stopped all background workers")
    
    async def enqueue(
        self,
        name: str,
        func: Callable,
        *args: Any,
        **kwargs: Any
    ) -> str:
        """
        Enqueue a task for background execution.
        
        Args:
            name: Task name for identification
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Task ID
        """
        self._task_counter += 1
        task_id = f"{name}_{self._task_counter}_{int(datetime.now().timestamp())}"
        
        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs
        )
        
        self.tasks[task_id] = task
        await self.queue.put(task)
        
        logger.debug(f"Enqueued task {task_id}: {name}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """
        Get task status.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        return self.tasks.get(task_id)
    
    async def _worker(self, worker_id: int) -> None:
        """
        Background worker that processes tasks from the queue.
        
        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                # Execute task
                await self._execute_task(task, worker_id)
                
                # Mark task as done
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                # No task available, continue waiting
                continue
            except asyncio.CancelledError:
                # Worker cancelled, exit gracefully
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _execute_task(self, task: Task, worker_id: int) -> None:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            worker_id: Worker identifier
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        logger.debug(f"Worker {worker_id} executing task {task.id}: {task.name}")
        
        try:
            # Execute the task function
            if asyncio.iscoroutinefunction(task.func):
                await task.func(*task.args, **task.kwargs)
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    task.func,
                    *task.args
                )
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            duration = (task.completed_at - task.started_at).total_seconds()
            logger.debug(
                f"Worker {worker_id} completed task {task.id} in {duration:.2f}s"
            )
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            logger.error(
                f"Worker {worker_id} failed task {task.id}: {e}",
                exc_info=True
            )


# Global task queue instance
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """
    Get global task queue instance.
    
    Returns:
        TaskQueue instance
    """
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue


async def start_background_workers() -> None:
    """Start background workers (call at application startup)."""
    queue = get_task_queue()
    await queue.start()


async def stop_background_workers() -> None:
    """Stop background workers (call at application shutdown)."""
    queue = get_task_queue()
    await queue.stop()
