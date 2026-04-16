#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import load_json, now_iso


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    root = workspace / '.mnemosyne-evolve'
    candidates = load_json(root / 'cache' / 'candidates.json', [])
    approved = load_json(root / 'state' / 'approved-patterns.json', {'patterns': []}).get('patterns', [])
    inbox_count = sum(1 for _ in (root / 'inbox').glob('*.json')) if (root / 'inbox').exists() else 0
    recall_md = root / 'recall' / 'recall-pack.md'

    lines = [
        '# Mnemosyne Evolve status',
        '',
        f'Generated: {now_iso()}',
        f'Workspace: {workspace}',
        '',
        '## Counts',
        f'- inbox events: {inbox_count}',
        f'- candidate patterns: {len(candidates)}',
        f'- approved patterns: {len(approved)}',
        f"- recall pack present: {'yes' if recall_md.exists() else 'no'}",
        '',
    ]
    report = root / 'audit' / 'runtime-status.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
