#!/usr/bin/env python3
"""Run the test suite."""

import subprocess
import sys
from pathlib import Path

def main():
    """Run pytest with coverage."""
    project_root = Path(__file__).parent.parent
    
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=src/wardrobe",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "tests/"
    ]
    
    try:
        subprocess.run(cmd, cwd=project_root, check=True)
        print("\n✅ All tests passed!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()