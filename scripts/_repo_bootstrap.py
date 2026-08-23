from __future__ import annotations

import sys
from pathlib import Path


def activate_repo_root(script_file: str) -> Path:
    """Make the repository root importable for direct script execution."""
    repo_root = Path(script_file).resolve().parents[1]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)
    return repo_root
