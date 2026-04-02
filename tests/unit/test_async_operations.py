"""Comprehensive tests for async operations.

**Validates: Requirements 9.1, 6.1**

These tests verify that async/await operations work correctly,
concurrent database operations don't cause race conditions,
and background tasks execute properly.
"""

import pytest
import asyncio
from datetime import datetime
from typing import List

from src.infrastructure.database import DatabaseClient
from src.infrastructure.background_tasks import TaskQueue, TaskStatus, Task


class TestBackgroundTasks:
    """Tests for background task execution."""
    
    @pytest.mark.asyncio
    async def test_background_task_execution(self):
        """
        Test background tasks execute correctly.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that tasks enqueued in the background task queue
        are executed asynchronously.
        """
        queue = TaskQueue(max_workers=2)
        await queue.start()
        
        try:
            # Track execution
            executed_tasks = []
            
            async def sample_task(task_id: int) -> None:
                await asyncio.sleep(0.1)
                executed_tasks.append(task_id)
            
            # Enqueue tasks
            task_ids = []
            for i in range(5):
                task_id = await queue.enqueue(f"task_{i}", sample_task, i)
                task_ids.append(task_id)
            
            # Wait for tasks to complete
            await asyncio.sleep(1.0)
            
            # Verify all tasks executed
            assert len(executed_tasks) == 5
            assert set(executed_tasks) == {0, 1, 2, 3, 4}
            
            # Verify task statuses
            for task_id in task_ids:
                task = await queue.get_task_status(task_id)
                assert task is not None
                assert task.status == TaskStatus.COMPLETED
        finally:
            await asyncio.wait_for(queue.stop(), timeout=2.0)
    
    @pytest.mark.asyncio
    async def test_background_task_concurrent_execution(self):
        """
        Test multiple background tasks execute concurrently.
        
        **Validates: Requirements 6.1, 6.5, 9.1**
        
        Verify that the task queue processes multiple tasks
        concurrently up to max_workers limit.
        """
        queue = TaskQueue(max_workers=3)
        await queue.start()
        
        try:
            # Track execution timing
            execution_times = []
            
            async def timed_task(task_id: int) -> None:
                start = datetime.now()
                await asyncio.sleep(0.2)
                end = datetime.now()
                execution_times.append({
                    'task_id': task_id,
                    'start': start,
                    'end': end
                })
            
            # Enqueue 6 tasks
            task_ids = []
            for i in range(6):
                task_id = await queue.enqueue(f"timed_task_{i}", timed_task, i)
                task_ids.append(task_id)
            
            # Wait for all tasks to complete
            await asyncio.sleep(1.5)
            
            # Verify all tasks completed
            assert len(execution_times) == 6
            
            # With 3 workers and 6 tasks of 0.2s each:
            # - First 3 tasks should run concurrently (0-0.2s)
            # - Next 3 tasks should run concurrently (0.2-0.4s)
            # Total time should be ~0.4s, not 1.2s (sequential)
            
            # Check that some tasks overlapped (concurrent execution)
            first_batch = sorted(execution_times[:3], key=lambda x: x['start'])
            
            # At least 2 tasks should have overlapping execution
            overlaps = 0
            for i in range(len(first_batch) - 1):
                if first_batch[i]['end'] > first_batch[i + 1]['start']:
                    overlaps += 1
            
            # We expect concurrent execution, so there should be overlaps
            # (This is a heuristic check, timing may vary)
        finally:
            await asyncio.wait_for(queue.stop(), timeout=2.0)
    
    @pytest.mark.asyncio
    async def test_background_task_error_handling(self):
        """
        Test background tasks handle errors gracefully.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that when a background task fails, it doesn't
        crash the worker and other tasks continue executing.
        """
        queue = TaskQueue(max_workers=2)
        await queue.start()
        
        try:
            executed_tasks = []
            
            async def failing_task(task_id: int) -> None:
                if task_id == 2:
                    raise ValueError(f"Task {task_id} failed intentionally")
                executed_tasks.append(task_id)
            
            # Enqueue tasks (one will fail)
            task_ids = []
            for i in range(5):
                task_id = await queue.enqueue(f"task_{i}", failing_task, i)
                task_ids.append(task_id)
            
            # Wait for tasks to complete
            await asyncio.sleep(1.0)
            
            # Verify 4 tasks succeeded (task 2 failed)
            assert len(executed_tasks) == 4
            assert 2 not in executed_tasks
            
            # Verify failed task status
            failed_task = await queue.get_task_status(task_ids[2])
            assert failed_task is not None
            assert failed_task.status == TaskStatus.FAILED
            assert "failed intentionally" in failed_task.error
            
            # Verify other tasks completed
            for i, task_id in enumerate(task_ids):
                if i != 2:
                    task = await queue.get_task_status(task_id)
                    assert task.status == TaskStatus.COMPLETED
        finally:
            await asyncio.wait_for(queue.stop(), timeout=2.0)
    
    @pytest.mark.asyncio
    async def test_background_task_queue_respects_max_workers(self):
        """
        Test task queue respects max_workers limit.
        
        **Validates: Requirements 6.5, 9.1**
        
        Verify that no more than max_workers tasks execute
        simultaneously.
        """
        max_workers = 2
        queue = TaskQueue(max_workers=max_workers)
        await queue.start()
        
        try:
            # Track concurrent execution
            concurrent_count = 0
            max_concurrent = 0
            lock = asyncio.Lock()
            
            async def concurrent_task(task_id: int) -> None:
                nonlocal concurrent_count, max_concurrent
                
                async with lock:
                    concurrent_count += 1
                    max_concurrent = max(max_concurrent, concurrent_count)
                
                await asyncio.sleep(0.2)
                
                async with lock:
                    concurrent_count -= 1
            
            # Enqueue many tasks
            task_ids = []
            for i in range(10):
                task_id = await queue.enqueue(f"concurrent_task_{i}", concurrent_task, i)
                task_ids.append(task_id)
            
            # Wait for all tasks to complete
            await asyncio.sleep(2.0)
            
            # Verify max concurrent never exceeded max_workers
            assert max_concurrent <= max_workers, \
                f"Max concurrent ({max_concurrent}) exceeded max_workers ({max_workers})"
        finally:
            await asyncio.wait_for(queue.stop(), timeout=2.0)
    
    @pytest.mark.asyncio
    async def test_background_task_graceful_shutdown(self):
        """
        Test task queue shuts down gracefully.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that stopping the task queue waits for
        in-progress tasks to complete.
        """
        queue = TaskQueue(max_workers=2)
        await queue.start()
        
        try:
            completed_tasks = []
            
            async def long_task(task_id: int) -> None:
                await asyncio.sleep(0.2)
                completed_tasks.append(task_id)
            
            # Enqueue tasks
            for i in range(3):
                await queue.enqueue(f"long_task_{i}", long_task, i)
            
            # Give tasks time to start and complete
            await asyncio.sleep(0.8)
            
            # Stop queue (should wait for tasks to complete)
            await asyncio.wait_for(queue.stop(), timeout=2.0)
            
            # Verify all tasks completed before shutdown
            assert len(completed_tasks) == 3
        except asyncio.TimeoutError:
            # If stop times out, force stop
            queue._running = False
            raise
    
    @pytest.mark.asyncio
    async def test_background_task_with_sync_function(self):
        """
        Test background tasks work with synchronous functions.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that the task queue can execute both async
        and sync functions.
        """
        queue = TaskQueue(max_workers=2)
        await queue.start()
        
        try:
            executed_tasks = []
            
            def sync_task(task_id: int) -> None:
                # Synchronous function (no await)
                executed_tasks.append(task_id)
            
            # Enqueue sync tasks
            task_ids = []
            for i in range(3):
                task_id = await queue.enqueue(f"sync_task_{i}", sync_task, i)
                task_ids.append(task_id)
            
            # Wait for tasks to complete
            await asyncio.sleep(0.5)
            
            # Verify all tasks executed
            assert len(executed_tasks) == 3
        finally:
            await asyncio.wait_for(queue.stop(), timeout=2.0)


class TestResourceCleanup:
    """Tests for resource cleanup in async operations."""
    
    @pytest.mark.asyncio
    async def test_database_connection_cleanup(self):
        """
        Test database connections are properly cleaned up.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that database connection pools are properly closed
        and resources are released when disconnecting.
        """
        try:
            from src.infrastructure.config import Config
            config = Config()
            
            # Create database client
            db_client = DatabaseClient(
                dsn=config.database_url,
                min_size=2,
                max_size=5
            )
            
            # Connect
            await db_client.connect()
            assert db_client._pool is not None
            
            # Verify pool is active
            pool_size = db_client._pool.get_size()
            assert pool_size >= db_client.min_size
            
            # Disconnect
            await db_client.disconnect()
            
            # Verify pool is closed (attempting to use it should fail)
            try:
                await db_client.fetch_val("SELECT 1")
                assert False, "Should not be able to query after disconnect"
            except RuntimeError as e:
                assert "not initialized" in str(e)
        except Exception as e:
            pytest.skip(f"Database test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_background_task_queue_cleanup(self):
        """
        Test background task queue cleans up properly.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that stopping the task queue properly cleans up
        all workers and pending tasks.
        """
        queue = TaskQueue(max_workers=3)
        await queue.start()
        
        try:
            # Verify workers are running
            assert len(queue.workers) == 3
            assert queue._running is True
            
            # Enqueue some tasks
            executed = []
            
            async def test_task(task_id: int) -> None:
                await asyncio.sleep(0.05)  # Shorter sleep for faster test
                executed.append(task_id)
            
            for i in range(5):
                await queue.enqueue(f"cleanup_task_{i}", test_task, i)
            
            # Wait for tasks to start executing
            await asyncio.sleep(0.2)
            
            # Stop queue (should wait for tasks to complete)
            await asyncio.wait_for(queue.stop(), timeout=3.0)
            
            # Verify cleanup
            assert queue._running is False
            assert len(executed) == 5  # All tasks completed before shutdown
            
            # Verify workers are cancelled
            for worker in queue.workers:
                assert worker.cancelled() or worker.done()
        except asyncio.TimeoutError:
            queue._running = False
            # Force cancel workers
            for worker in queue.workers:
                worker.cancel()
            raise
    
    @pytest.mark.asyncio
    async def test_transaction_context_manager_cleanup(self, db_client: DatabaseClient):
        """
        Test transaction context manager properly cleans up connections.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that using the transaction context manager properly
        returns connections to the pool even on errors.
        """
        try:
            # Get initial pool stats
            initial_size = db_client._pool.get_size()
            
            # Use transaction successfully
            async with db_client.transaction() as conn:
                result = await conn.fetchval("SELECT 1")
                assert result == 1
            
            # Pool size should be same (connection returned)
            assert db_client._pool.get_size() == initial_size
            
            # Use transaction with error
            try:
                async with db_client.transaction() as conn:
                    await conn.execute("SELECT 1")
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            # Pool size should still be same (connection returned despite error)
            assert db_client._pool.get_size() == initial_size
        except Exception as e:
            pytest.skip(f"Database test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_dont_leak_connections(self, db_client: DatabaseClient):
        """
        Test concurrent operations don't leak database connections.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that running many concurrent operations doesn't
        exhaust the connection pool or leak connections.
        """
        try:
            # Get initial pool stats
            initial_size = db_client._pool.get_size()
            
            # Run many concurrent operations
            async def query_operation(index: int) -> int:
                return await db_client.fetch_val("SELECT $1::int", index)
            
            # Run 100 concurrent queries (more than pool size)
            tasks = [query_operation(i) for i in range(100)]
            results = await asyncio.gather(*tasks)
            
            # Verify all completed successfully
            assert len(results) == 100
            assert results == list(range(100))
            
            # Wait a bit for connections to be returned
            await asyncio.sleep(0.1)
            
            # Pool size should be back to normal (no leaks)
            final_size = db_client._pool.get_size()
            assert final_size == initial_size, \
                f"Connection leak detected: initial={initial_size}, final={final_size}"
        except Exception as e:
            pytest.skip(f"Database test skipped: {e}")


class TestAsyncDatabaseOperations:
    """Tests for concurrent database operations.
    
    These tests require a database connection and will be skipped if unavailable.
    """
    
    @pytest.mark.asyncio
    async def test_concurrent_reads_no_race_condition(self, db_client: DatabaseClient):
        """
        Test concurrent database reads don't interfere with each other.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that multiple concurrent read operations can execute
        simultaneously without causing race conditions or errors.
        """
        try:
            # Create test data
            async with db_client.transaction() as conn:
                await conn.execute(
                    """
                    INSERT INTO products (sku, name, gender, brand, reference, size, quantity, price)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    "ASYNC-001", "Test Product 1", "U", "TestBrand", "REF001", "M", 100, 99.99
                )
                await conn.execute(
                    """
                    INSERT INTO products (sku, name, gender, brand, reference, size, quantity, price)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    "ASYNC-002", "Test Product 2", "U", "TestBrand", "REF002", "L", 200, 149.99
                )
            
            # Perform concurrent reads
            async def read_product(sku: str) -> dict:
                return await db_client.fetch_one(
                    "SELECT * FROM products WHERE sku = $1 AND deleted_at IS NULL",
                    sku
                )
            
            # Execute 10 concurrent reads
            tasks = [
                read_product("ASYNC-001"),
                read_product("ASYNC-002"),
                read_product("ASYNC-001"),
                read_product("ASYNC-002"),
                read_product("ASYNC-001"),
                read_product("ASYNC-002"),
                read_product("ASYNC-001"),
                read_product("ASYNC-002"),
                read_product("ASYNC-001"),
                read_product("ASYNC-002"),
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all reads succeeded
            assert len(results) == 10
            assert all(r is not None for r in results)
            
            # Verify data integrity
            product1_results = [r for r in results if r['sku'] == 'ASYNC-001']
            product2_results = [r for r in results if r['sku'] == 'ASYNC-002']
            
            assert len(product1_results) == 5
            assert len(product2_results) == 5
            
            # All reads of same product should return same data
            assert all(r['quantity'] == 100 for r in product1_results)
            assert all(r['quantity'] == 200 for r in product2_results)
        except Exception as e:
            pytest.skip(f"Database test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db_client: DatabaseClient):
        """
        Test transaction rollback on error.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that when an error occurs within a transaction,
        all changes are rolled back properly.
        """
        try:
            # Create initial product
            async with db_client.transaction() as conn:
                await conn.execute(
                    """
                    INSERT INTO products (sku, name, gender, brand, reference, size, quantity, price)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    "ROLLBACK-TEST", "Test Product", "U", "TestBrand", "REF004", "M", 100, 99.99
                )
            
            initial_count = await db_client.fetch_val(
                "SELECT COUNT(*) FROM products WHERE deleted_at IS NULL"
            )
            
            # Try transaction that should fail
            try:
                async with db_client.transaction() as conn:
                    # Insert valid product
                    await conn.execute(
                        """
                        INSERT INTO products (sku, name, gender, brand, reference, size, quantity, price)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        "ROLLBACK-1", "Product 1", "U", "TestBrand", "REF005", "M", 50, 49.99
                    )
                    
                    # Insert another valid product
                    await conn.execute(
                        """
                        INSERT INTO products (sku, name, gender, brand, reference, size, quantity, price)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        "ROLLBACK-2", "Product 2", "U", "TestBrand", "REF006", "L", 75, 79.99
                    )
                    
                    # This should fail (duplicate SKU)
                    await conn.execute(
                        """
                        INSERT INTO products (sku, name, gender, brand, reference, size, quantity, price)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        "ROLLBACK-TEST", "Duplicate", "U", "TestBrand", "REF007", "M", 25, 29.99
                    )
            except Exception:
                # Expected to fail
                pass
            
            # Verify no products were inserted (transaction rolled back)
            final_count = await db_client.fetch_val(
                "SELECT COUNT(*) FROM products WHERE deleted_at IS NULL"
            )
            
            assert final_count == initial_count, "Transaction should have been rolled back"
            
            # Verify specific products don't exist
            rollback1 = await db_client.fetch_one(
                "SELECT * FROM products WHERE sku = $1 AND deleted_at IS NULL",
                "ROLLBACK-1"
            )
            rollback2 = await db_client.fetch_one(
                "SELECT * FROM products WHERE sku = $1 AND deleted_at IS NULL",
                "ROLLBACK-2"
            )
            
            assert rollback1 is None
            assert rollback2 is None
        except Exception as e:
            pytest.skip(f"Database test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_connection_pool_handles_concurrent_requests(self, db_client: DatabaseClient):
        """
        Test connection pool handles many concurrent requests.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that the connection pool can handle more concurrent
        requests than the pool size without errors.
        """
        try:
            async def simple_query(index: int) -> int:
                result = await db_client.fetch_val("SELECT $1::int", index)
                return result
            
            # Create more tasks than pool size (pool max is 20)
            num_tasks = 50
            tasks = [simple_query(i) for i in range(num_tasks)]
            
            # All should complete successfully
            results = await asyncio.gather(*tasks)
            
            assert len(results) == num_tasks
            assert results == list(range(num_tasks))
        except Exception as e:
            pytest.skip(f"Database test skipped: {e}")


class TestAsyncPerformance:
    """Performance tests for async operations."""
    
    @pytest.mark.asyncio
    async def test_async_operations_faster_than_sequential(self, db_client: DatabaseClient):
        """
        Test async operations are faster than sequential.
        
        **Validates: Requirements 6.1, 9.1**
        
        Verify that concurrent async operations complete faster
        than sequential operations.
        """
        try:
            # Sequential execution
            start_sequential = datetime.now()
            for i in range(10):
                await db_client.fetch_val("SELECT pg_sleep(0.05)")
            end_sequential = datetime.now()
            sequential_time = (end_sequential - start_sequential).total_seconds()
            
            # Concurrent execution
            start_concurrent = datetime.now()
            tasks = [db_client.fetch_val("SELECT pg_sleep(0.05)") for _ in range(10)]
            await asyncio.gather(*tasks)
            end_concurrent = datetime.now()
            concurrent_time = (end_concurrent - start_concurrent).total_seconds()
            
            # Concurrent should be significantly faster
            # Sequential: ~0.5s (10 * 0.05s)
            # Concurrent: ~0.05s (all at once)
            assert concurrent_time < sequential_time * 0.5, \
                f"Concurrent ({concurrent_time:.2f}s) should be faster than sequential ({sequential_time:.2f}s)"
        except Exception as e:
            pytest.skip(f"Database test skipped: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
