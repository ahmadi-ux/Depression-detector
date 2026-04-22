#!/usr/bin/env python3
"""
Runner script to execute all testessays tests sequentially.
Pass through command line arguments to each test.

Usage:
    python run_all_tests.py --test-size 14
    python run_all_tests.py --test-size 5 --max-samples 3
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# List of all test scripts to run
TEST_SCRIPTS = [
    "Llama_8B_groq_zero_shot.py",
    "Llama_70B_groq_zero_shot.py",
    "GPT_20B_groq_zero_shot.py",
    "Gwen_32B_groq_zero_shot.py",
    "test_runner_groq_simple.py",
]

SCRIPT_DIR = Path(__file__).resolve().parent


def run_test(script_name: str, args: list) -> tuple[bool, str]:
    """
    Run a single test script and return success status and output.
    
    Args:
        script_name: Name of the test script to run
        args: Command line arguments to pass to the script
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    script_path = SCRIPT_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args
    
    print(f"\n{'='*80}")
    print(f"Running: {script_name}")
    print(f"{'='*80}")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=SCRIPT_DIR,
            capture_output=False,
            text=True,
            timeout=3600,  # 1 hour timeout per test
        )
        success = result.returncode == 0
        return success, script_name
    except subprocess.TimeoutExpired:
        print(f"ERROR: {script_name} timed out after 1 hour")
        return False, script_name
    except Exception as e:
        print(f"ERROR: Failed to run {script_name}: {e}")
        return False, script_name


def main():
    if len(sys.argv) > 1:
        # Pass through command line arguments
        args = sys.argv[1:]
    else:
        # Default arguments if none provided
        args = ["--test-size", "14"]
    
    print(f"\n{'='*80}")
    print(f"Starting All Tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"Arguments: {' '.join(args)}\n")
    
    results = []
    
    for script_name in TEST_SCRIPTS:
        success, output = run_test(script_name, args)
        results.append((script_name, success))
    
    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    for script_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status}: {script_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Exit with failure if any test failed
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
