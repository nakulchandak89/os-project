"""
Module 2: Worker Thread Creation
Project: Thread Affinity Management for Multi-Core Processors (Phase 1)

This module handles:
1. Creating a configurable number of worker threads.
2. Managing the lifecycle of worker threads (Creation, Start, Join).
3. Tracking thread metadata (Thread Name, Python Ident, Native OS Thread ID).
"""

import threading
import time
from typing import Callable, List, Optional


def default_sample_task(thread_index: int, duration_sec: float = 0.5) -> None:
    """
    A minimal default task used solely to test and demonstrate
    that worker threads are running and finishing cleanly.
    """
    native_id = getattr(threading, "get_native_id", lambda: "N/A")()
    print(f"  [+] Thread-{thread_index} started (Native OS TID: {native_id})")
    time.sleep(duration_sec)
    print(f"  [-] Thread-{thread_index} finished")


class ThreadManager:
    """
    Manages the creation, startup, and joining of worker threads.
    """

    def __init__(self, num_threads: int = 4):
        """
        Initializes the ThreadManager with the desired number of threads.
        """
        if num_threads < 1:
            raise ValueError("num_threads must be at least 1.")
        self.num_threads = num_threads
        self.threads: List[threading.Thread] = []
        self.thread_info: List[dict] = []

    def create_threads(
        self,
        target_func: Optional[Callable] = None,
        task_args: Optional[tuple] = None
    ) -> List[threading.Thread]:
        """
        Creates N worker threads using the standard threading library.

        Args:
            target_func: Function to execute on each thread. If None, uses default_sample_task.
            task_args: Optional arguments tuple to pass to target_func.

        Returns:
            List of created threading.Thread objects.
        """
        self.threads = []
        self.thread_info = []

        if target_func is None:
            target_func = default_sample_task

        for i in range(self.num_threads):
            name = f"Worker-{i}"
            
            # Pass thread index as first argument if using default_sample_task
            if target_func is default_sample_task:
                args = (i,) if task_args is None else (i, *task_args)
            else:
                args = task_args if task_args is not None else ()

            thread = threading.Thread(
                target=target_func,
                args=args,
                name=name
            )
            self.threads.append(thread)
            self.thread_info.append({
                "index": i,
                "name": name,
                "thread_obj": thread,
                "status": "Created"
            })

        return self.threads

    def start_threads(self) -> None:
        """
        Starts all created worker threads.
        """
        if not self.threads:
            raise RuntimeError("No threads created yet. Call create_threads() first.")

        for info in self.thread_info:
            info["thread_obj"].start()
            info["status"] = "Running"

    def join_threads(self) -> None:
        """
        Waits for all worker threads to complete their execution cleanly.
        """
        for info in self.thread_info:
            info["thread_obj"].join()
            info["status"] = "Completed"

    def display_thread_summary(self) -> None:
        """
        Prints a neat summary table of all managed worker threads.
        """
        print("-" * 60)
        print(f"          WORKER THREAD SUMMARY ({len(self.threads)} Threads)")
        print("-" * 60)
        print(f"{'Index':<8} | {'Thread Name':<15} | {'Native OS TID':<15} | {'Status':<10}")
        print("-" * 60)
        for info in self.thread_info:
            t = info["thread_obj"]
            native_id = getattr(t, "native_id", "N/A")
            status = info["status"]
            print(f"{info['index']:<8} | {info['name']:<15} | {str(native_id):<15} | {status:<10}")
        print("-" * 60)


if __name__ == "__main__":
    # Test Module 2 standalone
    print("Testing Module 2: Worker Thread Creation...")
    manager = ThreadManager(num_threads=4)
    manager.create_threads()
    
    print("\nStarting threads:")
    manager.start_threads()
    
    print("\nWaiting for threads to complete:")
    manager.join_threads()
    
    print("\nFinal thread status:")
    manager.display_thread_summary()
