"""
Main Execution Script (Phase 1 Prototype - Modules 1 & 2)
Project: Thread Affinity Management for Multi-Core Processors

This script integrates:
- Module 1: CPU Core Detection (cpu_detection.py)
- Module 2: Worker Thread Creation (thread_manager.py)

(Note: Modules 3, 4, 5, and 6 will be added in subsequent steps.)
"""

import sys
from cpu_detection import detect_cpu_cores, display_cpu_info
from thread_manager import ThreadManager


def main():
    print("\n" + "#" * 60)
    print("  THREAD AFFINITY MANAGEMENT SYSTEM - PROTOTYPE (PHASE 1)")
    print("  Demonstrating Module 1 & Module 2")
    print("#" * 60 + "\n")

    # ==========================================
    # STEP 1: MODULE 1 - CPU Core Detection
    # ==========================================
    cpu_info = detect_cpu_cores()
    display_cpu_info(cpu_info)

    # ==========================================
    # STEP 2: MODULE 2 - Worker Thread Creation
    # ==========================================
    # Configure number of threads (e.g. 4 threads, or passed via CLI argument)
    if len(sys.argv) > 1:
        try:
            num_threads = int(sys.argv[1])
        except ValueError:
            print(f"[!] Invalid thread count argument '{sys.argv[1]}'. Defaulting to 4.")
            num_threads = 4
    else:
        # Default to 4 threads for demonstration
        num_threads = 4

    print(f"\n[*] Initializing Thread Manager with {num_threads} worker threads...")
    manager = ThreadManager(num_threads=num_threads)

    print("[*] Creating worker threads...")
    manager.create_threads()

    print("[*] Starting all worker threads concurrently...")
    manager.start_threads()

    print("[*] Waiting for all worker threads to finish (join)...")
    manager.join_threads()

    print("\n[*] All threads completed successfully!")
    manager.display_thread_summary()


if __name__ == "__main__":
    main()
