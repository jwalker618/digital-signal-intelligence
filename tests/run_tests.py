"""
DSI Test Runner
===============

Convenient test runner with presets for different test scenarios.

Usage:
    python tests/run_tests.py --all              # All tests
    python tests/run_tests.py --cyber            # Cyber model only
    python tests/run_tests.py --structural       # Structural tests only
    python tests/run_tests.py --actuarial        # Actuarial tests only
    python tests/run_tests.py --coverage         # With coverage report
    python tests/run_tests.py --quick            # Quick smoke tests
"""

import argparse
import sys
import subprocess
from pathlib import Path


def run_pytest(args_list, description):
    """Run pytest with given arguments."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}\n")

    cmd = ["pytest"] + args_list
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="DSI Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Test selection
    parser.add_argument("--all", action="store_true",
                       help="Run all tests")
    parser.add_argument("--cyber", action="store_true",
                       help="Run cyber model tests only")
    parser.add_argument("--fi", action="store_true",
                       help="Run FI model tests only")
    parser.add_argument("--do", action="store_true",
                       help="Run D&O model tests only")
    parser.add_argument("--energy", action="store_true",
                       help="Run energy model tests only")
    parser.add_argument("--marine", action="store_true",
                       help="Run marine model tests only")
    parser.add_argument("--pi", action="store_true",
                       help="Run PI model tests only")
    parser.add_argument("--aerospace", action="store_true",
                       help="Run aerospace model tests only")

    # Test type selection
    parser.add_argument("--structural", action="store_true",
                       help="Run structural tests only")
    parser.add_argument("--functional", action="store_true",
                       help="Run functional tests only")
    parser.add_argument("--actuarial", action="store_true",
                       help="Run actuarial validity tests only")

    # Output options
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage report")
    parser.add_argument("--html", action="store_true",
                       help="Generate HTML coverage report")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--quick", action="store_true",
                       help="Quick smoke tests (structural only)")

    # Markers
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests")
    parser.add_argument("--no-slow", action="store_true",
                       help="Skip slow tests")

    args = parser.parse_args()

    # Build pytest arguments
    pytest_args = []

    # Verbosity
    if args.verbose or not args.quick:
        pytest_args.append("-v")

    # Model selection
    if args.cyber:
        pytest_args.append("models/cyber/tests/")
    elif args.fi:
        pytest_args.append("models/financial_institutions/tests/")
    elif args.do:
        pytest_args.append("models/d&o/tests/")
    elif args.energy:
        pytest_args.append("models/energy/tests/")
    elif args.marine:
        pytest_args.append("models/marine/tests/")
    elif args.pi:
        pytest_args.append("models/pi/tests/")
    elif args.aerospace:
        pytest_args.append("models/aerospace/tests/")
    elif args.all:
        pytest_args.append("models/")
    else:
        # Default: all tests
        pytest_args.append("models/")

    # Test type filtering
    if args.structural or args.quick:
        pytest_args.extend(["-k", "structure"])
    elif args.functional:
        pytest_args.extend(["-k", "functional"])
    elif args.actuarial:
        pytest_args.extend(["-k", "actuarial"])

    # Markers
    if args.integration:
        pytest_args.extend(["-m", "integration"])
    elif args.no_slow:
        pytest_args.extend(["-m", "not slow"])

    # Coverage
    if args.coverage or args.html:
        pytest_args.extend([
            "--cov=models",
            "--cov-report=term-missing",
        ])

        if args.html:
            pytest_args.append("--cov-report=html")
            print("HTML coverage report will be in: htmlcov/index.html")

    # Run tests
    description = "DSI Tests"
    if args.cyber:
        description = "Cyber Model Tests"
    elif args.actuarial:
        description = "Actuarial Validity Tests"
    elif args.structural:
        description = "Structural Tests"
    elif args.quick:
        description = "Quick Smoke Tests"

    returncode = run_pytest(pytest_args, description)

    # Summary
    print(f"\n{'='*70}")
    if returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
