"""
Main Execution Script (Phase 1 - Modules 1, 2 & 4)
Project: Thread Affinity Management for Multi-Core Processors

This script integrates:
- Module 1: CPU Core Detection (cpu_detection.py)
- Module 2: Worker Thread Creation (thread_manager.py)
- Module 4: Thread Affinity Management (affinity_manager.py)

Usage:
    python main.py [num_threads] [--affinity CONFIG]

CONFIG choices:
    baseline     - No explicit affinity (OS scheduler decides)
    fixed        - Thread i pinned to Core i (requires threads <= cores)
    distributed  - Round-robin placement across all cores
    concentrated - All threads restricted to 1-2 cores

Examples:
    python main.py 4 --affinity baseline
    python main.py 4 --affinity fixed
    python main.py 8 --affinity distributed
    python main.py 4 --affinity concentrated
"""

import argparse
import sys
import threading
from typing import Dict, List

from cpu_detection import detect_cpu_cores, display_cpu_info
from thread_manager import ThreadManager, default_sample_task
from affinity_manager import (
    AffinityConfiguration,
    AffinityError,
    apply_thread_affinity,
    display_affinity_mapping,
    generate_thread_affinity_mapping,
    is_windows,
    verify_thread_affinity,
)


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for thread count and affinity configuration."""
    parser = argparse.ArgumentParser(
        description="Thread Affinity Management for Multi-Core Processors"
    )
    parser.add_argument(
        "num_threads",
        nargs="?",
        type=int,
        default=4,
        help="Number of worker threads (default: 4)",
    )
    parser.add_argument(
        "--affinity",
        type=str,
        choices=["baseline", "fixed", "distributed", "concentrated"],
        default="baseline",
        help="Affinity configuration (default: baseline)",
    )
    return parser.parse_args()


def create_affinity_worker(
    affinity_mapping: Dict[int, List[int]],
    available_core_ids: List[int],
    barrier: threading.Barrier,
    shared_results: Dict[int, dict],
    workload_func,
):
    """
    Build a worker function that applies affinity, verifies it, then
    runs the workload after all workers have completed affinity setup.

    The worker flow is:
        start -> apply affinity -> verify -> barrier -> workload

    If any worker fails affinity application, it signals failure and
    skips the barrier. Other workers detect the failure via shared
    state or barrier timeout and abort the workload cleanly.
    """

    def worker(thread_index: int) -> None:
        thread_name = f"Worker-{thread_index}"
        cores = affinity_mapping.get(thread_index, [])

        # --- Step 1: Apply affinity ---
        try:
            if cores:
                print(f"  [{thread_name}] Applying affinity: cores {cores}")
                set_result = apply_thread_affinity(
                    cores, available_core_ids, thread_name
                )
                verified = verify_thread_affinity(
                    cores, available_core_ids, thread_name,
                    set_return_value=set_result,
                )
                if not verified:
                    raise AffinityError(
                        f"Affinity verification failed for {thread_name}"
                    )
                shared_results[thread_index] = {
                    "cores": cores,
                    "status": "Verified",
                }
            else:
                print(
                    f"  [{thread_name}] No explicit affinity (OS scheduler)"
                )
                shared_results[thread_index] = {
                    "cores": [],
                    "status": "OS Scheduler",
                }
        except AffinityError as exc:
            print(f"  [{thread_name}] ERROR: {exc}")
            shared_results[thread_index] = {
                "cores": cores,
                "status": "Failed",
                "error": str(exc),
            }
            return  # Skip barrier and workload

        # --- Step 2: Barrier - wait for all workers to finish affinity ---
        try:
            barrier.wait(timeout=10.0)
        except threading.BrokenBarrierError:
            print(
                f"  [{thread_name}] Barrier broken - aborting workload"
            )
            return

        # --- Step 3: Check if any thread failed ---
        failed = [
            r for r in shared_results.values()
            if r.get("status") == "Failed"
        ]
        if failed:
            print(
                f"  [{thread_name}] Aborting workload - "
                f"affinity failure on {len(failed)} thread(s)"
            )
            return

        # --- Step 4: Run workload ---
        print(f"  [{thread_name}] Starting workload...")
        workload_func(thread_index)
        print(f"  [{thread_name}] Workload complete")

    return worker


def main() -> None:
    args = parse_arguments()

    print("\n" + "#" * 60)
    print("  THREAD AFFINITY MANAGEMENT SYSTEM - PROTOTYPE (PHASE 1)")
    print("  Demonstrating Module 1, Module 2 & Module 4")
    print("#" * 60 + "\n")

    # ==========================================
    # STEP 1: MODULE 1 - CPU Core Detection
    # ==========================================
    cpu_info = detect_cpu_cores()
    display_cpu_info(cpu_info)
    available_core_ids = cpu_info["core_ids"]

    # ==========================================
    # STEP 2: SELECT AFFINITY CONFIGURATION
    # ==========================================
    configuration = AffinityConfiguration(args.affinity)

    num_threads = args.num_threads
    if num_threads < 1:
        print(f"[!] Invalid thread count '{num_threads}'. Defaulting to 4.")
        num_threads = 4

    print(f"\n[*] Available CPU cores : {cpu_info['logical_cores']}")
    print(f"[*] Core IDs            : {available_core_ids}")
    print(f"[*] Worker threads      : {num_threads}")
    print(f"[*] Selected config     : {configuration.value.upper()}")

    # Warn on non-Windows for non-baseline configs
    if configuration != AffinityConfiguration.BASELINE and not is_windows():
        print("\n[!] WARNING: Non-Windows platform detected.")
        print(
            "[!] Thread affinity (SetThreadAffinityMask) requires Windows."
        )
        print("[!] Affinity will NOT be applied on this system.")

    # ==========================================
    # STEP 3: GENERATE AFFINITY MAPPING
    # ==========================================
    try:
        affinity_mapping = generate_thread_affinity_mapping(
            configuration, num_threads, available_core_ids
        )
    except ValueError as exc:
        print(f"\n[!] Configuration error: {exc}")
        sys.exit(1)

    display_affinity_mapping(configuration, affinity_mapping)

    # ==========================================
    # STEP 4: MODULE 2 - Worker Thread Creation
    # ==========================================
    print(
        f"\n[*] Initializing Thread Manager "
        f"with {num_threads} worker threads..."
    )
    manager = ThreadManager(num_threads=num_threads)

    # Shared state for affinity results (written by workers)
    shared_results: Dict[int, dict] = {}

    # Barrier: all workers must complete affinity before workload begins
    barrier = threading.Barrier(num_threads)

    # Create affinity-aware worker function
    worker_func = create_affinity_worker(
        affinity_mapping=affinity_mapping,
        available_core_ids=available_core_ids,
        barrier=barrier,
        shared_results=shared_results,
        workload_func=default_sample_task,
    )

    # Per-thread args: each worker receives its thread index
    per_thread_args = [(i,) for i in range(num_threads)]

    print("[*] Creating worker threads...")
    manager.create_threads(
        target_func=worker_func,
        per_thread_args=per_thread_args,
    )

    # Attach affinity metadata to thread_info for the summary display
    for info in manager.thread_info:
        idx = info["index"]
        info["assigned_cores"] = affinity_mapping.get(idx, [])
        info["affinity_status"] = "Pending"

    print("[*] Starting all worker threads concurrently...")
    manager.start_threads()

    print("[*] Waiting for all worker threads to finish (join)...")
    manager.join_threads()

    # ==========================================
    # STEP 5: SUMMARY
    # ==========================================
    # Update affinity status in thread_info from shared_results
    for info in manager.thread_info:
        idx = info["index"]
        result = shared_results.get(idx, {})
        info["affinity_status"] = result.get("status", "Unknown")

    print("\n[*] All threads completed successfully!")
    manager.display_thread_summary()

    # Affinity results summary
    print("-" * 60)
    print(f"  AFFINITY RESULTS ({configuration.value.upper()})")
    print("-" * 60)
    for idx in sorted(shared_results.keys()):
        result = shared_results[idx]
        cores = result.get("cores", [])
        status = result.get("status", "Unknown")
        core_str = f"cores {cores}" if cores else "OS scheduler"
        print(f"  Thread {idx}: {status} ({core_str})")
    print("-" * 60)

    # Check for failures
    failed = [
        (idx, r) for idx, r in shared_results.items()
        if r.get("status") == "Failed"
    ]
    if failed:
        print(f"\n[!] {len(failed)} thread(s) had affinity failures:")
        for idx, r in failed:
            print(f"    Thread {idx}: {r.get('error', 'Unknown error')}")
        sys.exit(1)

    print("\n[+] All affinity operations completed successfully.")


if __name__ == "__main__":
    main()
