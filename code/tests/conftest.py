"""Pytest configuration."""

import sys
from pathlib import Path

# Ensure the code/ directory is on the path for imports.
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
