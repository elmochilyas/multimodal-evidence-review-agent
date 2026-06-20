"""Thin CLI entry point for the evaluation workflow.

This wrapper delegates to evaluation/evaluate.py so that the evaluator can run:

    python evaluation/main.py --sample ../dataset/sample_claims.csv ...

from the code/ directory.
"""

import sys
from pathlib import Path

# Load local environment variables from .env if present. Secrets must never be
# committed; .env is excluded from code.zip via .gitignore.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # Environment variables can still be supplied directly.

# Ensure code/ is importable when running from evaluation/ directory.
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from evaluation.evaluate import main

if __name__ == "__main__":
    sys.exit(main())
