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


# Configuration - test paths based on your project structure
TEST_BASE_DIR = Path(__file__).parent.parent
MODEL_TEST_PATHS = {
    "aerospace": "models/aerospace/tests/",
    "cyber": "models/cyber/tests/",
    "do": "models/do/tests/",
    "energy": "models/energy/tests/",
    "fi": "models/financial_institutions/tests/",
    "marine": "models/marine/tests/",
    "pi": "models/pi/tests/",
    "portfolio": "models/portfolio/tests/",
    "signal": "models/signal_collection/tests/",
    "website": "models/website_discovery/tests/",
}

def find_test_path(model_name: str) -> str:
    """Find the test path for a given model, handling variations."""
    # Direct match
    if model_name in MODEL_TEST_PATHS:
        return MODEL_TEST_PATHS[model_name]
    
    # Try to find a matching directory
    base_path = TEST_BASE_DIR / "models"
    if base_path.exists():
        for subdir in base_path.iterdir():
            if subdir.is_dir() and model_name.lower() in subdir.name.lower():
                test_dir = subdir / "tests"
                if test_dir.exists():
                    return str(test_dir.relative_to(TEST_BASE_DIR))
    
    # Fallback to models/ if nothing specific found
    return "models/"

def run_pytest(args_list: list, description: str) -> int:
    """Run pytest with given arguments."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}\n")

    cmd = ["pytest"] + args_list
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, cwd=TEST_BASE_DIR)
        return result.returncode
    except FileNotFoundError:
        print("ERROR: pytest not found. Install with: pip install pytest")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to run pytest: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="DSI Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Examples:
        python run_tests.py --all              # Run all tests
        python run_tests.py --aerospace        # Run aerospace model tests
        python run_tests.py --cyber --actuarial  # Cyber actuarial tests only
        python run_tests.py --coverage --html  # All tests with HTML coverage report
        """
    )

    # Model selection group
    model_group = parser.add_argument_group('Model Selection')
    model_group.add_argument("--all", action="store_true",
                            help="Run all tests")
    model_group.add_argument("--aerospace", action="store_true",
                            help="Run aerospace model tests only")
    model_group.add_argument("--cyber", action="store_true",
                            help="Run cyber model tests only")
    model_group.add_argument("--do", action="store_true",
                            help="Run D&O model tests only")
    model_group.add_argument("--energy", action="store_true",
                            help="Run energy model tests only")
    model_group.add_argument("--fi", action="store_true",
                            help="Run FI model tests only")
    model_group.add_argument("--marine", action="store_true",
                            help="Run marine model tests only")
    model_group.add_argument("--pi", action="store_true",
                            help="Run PI model tests only")
    model_group.add_argument("--portfolio", action="store_true",
                            help="Run Portfolio model tests only")
    model_group.add_argument("--signal", action="store_true",
                            help="Run Signal Collection model tests only")
    model_group.add_argument("--website", action="store_true",
                            help="Run Website Discovery model tests only")

   
    # Test type selection group
    type_group = parser.add_argument_group('Test Type Selection')
    type_group.add_argument("--structural", action="store_true",
                           help="Run structural tests only")
    type_group.add_argument("--functional", action="store_true",
                           help="Run functional tests only")
    type_group.add_argument("--actuarial", action="store_true",
                           help="Run actuarial validity tests only")
    type_group.add_argument("--edge", action="store_true",
                           help="Run edge case tests only")
    
    # Output options group
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument("--coverage", action="store_true",
                             help="Generate coverage report")
    output_group.add_argument("--html", action="store_true",
                             help="Generate HTML coverage report")
    output_group.add_argument("--verbose", "-v", action="store_true",
                             help="Verbose output")
    output_group.add_argument("--quiet", "-q", action="store_true",
                             help="Quiet output (minimal)")
    output_group.add_argument("--quick", action="store_true",
                             help="Quick smoke tests (structural only)")
    
    # Additional options
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests")
    parser.add_argument("--no-slow", action="store_true",
                       help="Skip slow tests")
    parser.add_argument("--failed-first", "-ff", action="store_true",
                       help="Run previously failed tests first")
    parser.add_argument("--last-failed", "-lf", action="store_true",
                       help="Run only previously failed tests")
    parser.add_argument("--pdb", action="store_true",
                       help="Drop into debugger on failures")
    parser.add_argument("--exitfirst", "-x", action="store_true",
                       help="Exit on first failure")
    
    args = parser.parse_args()

    # Build pytest arguments
    pytest_args = []

    # Verbosity
    if args.quiet:
        pytest_args.append("-q")
    elif args.verbose or not args.quick:
        pytest_args.append("-v")

    # Determine test path based on model selection
    test_path = "models/"  # Default
    description_model = "All Models"
    
    model_flags = {
        "aerospace": args.aerospace,
        "cyber": args.cyber,
        "do": args.do,
        "energy": args.energy,
        "fi": args.fi,
        "marine": args.marine,
        "pi": args.pi,
        "portfolio": args.portfolio,
        "signal": args.signal,
        "website": args.website,
    }
    
    selected_models = [name for name, flag in model_flags.items() if flag]
    
    if len(selected_models) == 1:
        model_name = selected_models[0]
        test_path = find_test_path(model_name)
        description_model = f"{model_name.upper()} Model"
    elif len(selected_models) > 1:
        # Multiple models selected - run each path
        test_paths = [find_test_path(m) for m in selected_models]
        pytest_args.extend(test_paths)
        test_path = None  # Don't add a single path
        description_model = f"Models: {', '.join(m.upper() for m in selected_models)}"
    elif args.all:
        test_path = "models/"
        description_model = "All Models"
    
    if test_path:
        pytest_args.append(test_path)
    
    # Test type filtering
    description_type = "Tests"
    if args.structural or args.quick:
        pytest_args.extend(["-k", "Structure or structure or Structural or structural"])
        description_type = "Structural Tests"
    elif args.functional:
        pytest_args.extend(["-k", "Functional or functional"])
        description_type = "Functional Tests"
    elif args.actuarial:
        pytest_args.extend(["-k", "Actuarial or actuarial"])
        description_type = "Actuarial Tests"
    elif args.edge:
        pytest_args.extend(["-k", "Edge or edge or EdgeCase or edgecase"])
        description_type = "Edge Case Tests"
    
    # Markers
    if args.integration:
        pytest_args.extend(["-m", "integration"])
        description_type = "Integration Tests"
    elif args.no_slow:
        pytest_args.extend(["-m", "not slow"])
    
    # Additional pytest options
    if args.failed_first:
        pytest_args.append("--ff")
    if args.last_failed:
        pytest_args.append("--lf")
    if args.pdb:
        pytest_args.append("--pdb")
    if args.exitfirst:
        pytest_args.append("-x")
    
    # Coverage
    if args.coverage or args.html:
        pytest_args.extend([
            "--cov=models",
            "--cov-report=term-missing",
        ])
        
        if args.html:
            pytest_args.append("--cov-report=html")
            print("HTML coverage report will be in: htmlcov/index.html")
    
    # Build description
    description = f"{description_model} - {description_type}"
    if args.quick:
        description = f"Quick Smoke Tests - {description_model}"
    
    # Run tests
    returncode = run_pytest(pytest_args, description)
    
    # Summary
    print(f"\n{'='*70}")
    if returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print(f"{'='*70}\n")
    
    sys.exit(returncode)


if __name__ == "__main__":
    main()
