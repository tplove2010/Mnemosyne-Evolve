#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import ensure_text

# Try multiple possible config locations
SCRIPT_DIR = Path(__file__).resolve().parents[0]
WORKSPACE_DIR = Path(__file__).resolve().parents[1]

DEFAULT_CONFIG_LOCATIONS = [
    SCRIPT_DIR / 'mnemosyne-evolve.config.jsonc',  # In scripts/ folder
    WORKSPACE_DIR / '.mnemosyne-evolve' / 'config.jsonc',  # In workspace .mnemosyne-evolve/
    SCRIPT_DIR.parent / 'assets' / 'mnemosyne-evolve.config.jsonc',  # Original source path
]

DEFAULT_CONFIG = None
for loc in DEFAULT_CONFIG_LOCATIONS:
    if loc.exists():
        DEFAULT_CONFIG = loc
        break

if DEFAULT_CONFIG is None:
    DEFAULT_CONFIG = DEFAULT_CONFIG_LOCATIONS[0]  # Fallback
DIRS = [
    '.mnemosyne-evolve',
    '.mnemosyne-evolve/inbox',
    '.mnemosyne-evolve/cache',
    '.mnemosyne-evolve/review',
    '.mnemosyne-evolve/patterns',
    '.mnemosyne-evolve/recall',
    '.mnemosyne-evolve/audit',
    '.mnemosyne-evolve/state',
]
STATE_FILES = {
    '.mnemosyne-evolve/state/ingest-state.json': '{"files": {}}\n',
    '.mnemosyne-evolve/state/approved-patterns.json': '{"patterns": []}\n',
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    for rel in DIRS:
        (workspace / rel).mkdir(parents=True, exist_ok=True)
    ensure_text(workspace / '.mnemosyne-evolve' / 'config.jsonc', DEFAULT_CONFIG.read_text(encoding='utf-8'))
    for rel, content in STATE_FILES.items():
        ensure_text(workspace / rel, content)
    print(f'Initialized Mnemosyne Evolve runtime at: {workspace}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
