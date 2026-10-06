"""
Module 1: CPU Core Detection
Project: Thread Affinity Management for Multi-Core Processors (Phase 1)

This module handles:
1. Detecting the number of logical and physical CPU cores.
2. Generating the list of valid CPU core IDs (e.g., [0, 1, 2, ...]).
3. Providing clear functions to display CPU hardware details.
"""

import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def detect_cpu_cores() -> dict:
    """
    Detects available CPU cores on the current system.

    Returns:
        dict: A dictionary containing:
            - 'logical_cores': Total number of logical execution cores.
            - 'physical_cores': Number of physical hardware cores (if available).
            - 'core_ids': List of 0-indexed core IDs [0, 1, ..., N-1].
    """
    # Attempt to get logical and physical core counts
    if PSUTIL_AVAILABLE:
        logical_cores = psutil.cpu_count(logical=True)
        physical_cores = psutil.cpu_count(logical=False)
    else:
        logical_cores = os.cpu_count()
        physical_cores = None

    # Fallback if detection returned None
    if logical_cores is None or logical_cores < 1:
        logical_cores = 1

    # Generate core IDs list: [0, 1, 2, ..., logical_cores - 1]
    core_ids = list(range(logical_cores))

    return {
        "logical_cores": logical_cores,
        "physical_cores": physical_cores,
        "core_ids": core_ids
    }


def get_available_core_ids() -> list:
    """
    Convenience function to get just the list of valid core IDs.
    
    Returns:
        list of int: e.g. [0, 1, 2, 3]
    """
    cpu_info = detect_cpu_cores()
    return cpu_info["core_ids"]


def display_cpu_info(cpu_info: dict = None) -> None:
    """
    Prints a clear, formatted summary of the detected CPU cores.
    """
    if cpu_info is None:
        cpu_info = detect_cpu_cores()

    print("=" * 60)
    print("           MODULE 1: CPU CORE DETECTION RESULTS")
    print("=" * 60)
    print(f"  * Logical CPU Cores : {cpu_info['logical_cores']}")
    if cpu_info['physical_cores'] is not None:
        print(f"  * Physical CPU Cores: {cpu_info['physical_cores']}")
    else:
        print("  * Physical CPU Cores: Not available (using logical count)")
    print(f"  * Available Core IDs: {cpu_info['core_ids']}")
    print("=" * 60)


if __name__ == "__main__":
    # Test Module 1 standalone
    info = detect_cpu_cores()
    display_cpu_info(info)
