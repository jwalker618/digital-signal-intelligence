"""
DSI Test Runner
===============

Convenient test runner with presets for different test scenarios.

Usage:
    python tests/run_tests.py --all              # All tests
    python tests/run_tests.py --cyber            # Cyber model only, alter by model name
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
    parser.add_argument("--aerospace", action="store_true",
                       help="Run aerospace model tests only")
    parser.add_argument("--cyber", action="store_true",
                       help="Run cyber model tests only")
    parser.add_argument("--do", action="store_true",
                       help="Run D&O model tests only")
    parser.add_argument("--energy", action="store_true",
                       help="Run energy model tests only")
    parser.add_argument("--fi", action="store_true",
                       help="Run FI model tests only")
    parser.add_argument("--marine", action="store_true",
                       help="Run marine model tests only")
    parser.add_argument("--pi", action="store_true",
                       help="Run PI model tests only")
    parser.add_argument("--portfolio", action="store_true",
                       help="Run Portfolio model tests only")
    parser.add_argument("--signal", action="store_true",
                       help="Run Signal Collection model tests only")
    parser.add_argument("--website", action="store_true",
                       help="Run Website Discovery model tests only")
    
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
    if args.aerospace:
        pytest_args.append("models/aerospace/tests/")
    elif args.cyber:
        pytest_args.append("models/cyber/tests/")
    elif args.do:
        pytest_args.append("models/d&o/tests/")
    elif args.energy:
        pytest_args.append("models/energy/tests/")
    elif args.fi:
        pytest_args.append("models/financial_insitutions/tests/")
    elif args.marine:
        pytest_args.append("models/marine/tests/")
    elif args.pi:
        pytest_args.append("models/pi/tests/")
    elif args.portfolio:
        pytest_args.append("models/portfolio/tests/")
    elif args.signal_collection:
        pytest_args.append("models/signal_collection/tests/")
    elif args.website_discovery:
        pytest_args.append("models/website_discovery/tests/")        
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
    if args.aerospace:
        description = "Aerospace Model Tests"
    elif args.cyber:
        description = "Cyber Model Tests"
    elif args.do:
        description = "DO Model Tests"
    elif args.energy:
        description = "Energy Model Tests"
    elif args.fi:
        description = "FI Model Tests"
    elif args.marine:
        description = "Marine Model Tests"
    elif args.pi:
        description = "PI Model Tests"
    elif args.portfolio:
        description = "Portfolio Model Tests"
    elif args.signal:
        description = "Signal Collection Model Tests"
    elif args.website:
        description = "Website Discovery Model Tests"        
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
