#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import dump_json, load_json, now_iso


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    parser.add_argument('--ids', nargs='+', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    candidates = load_json(workspace / '.mnemosyne-evolve' / 'cache' / 'candidates.json', [])
    approved_store = load_json(workspace / '.mnemosyne-evolve' / 'state' / 'approved-patterns.json', {'patterns': []})
    selected = [c for c in candidates if c.get('id') in set(args.ids)]
    if not args.apply:
        print('Dry run approvals:')
        for item in selected:
            print(f"- {item['id']} ({item['pattern_type']} · {item['topic']})")
        return 0

    existing = {p['id']: p for p in approved_store.get('patterns', [])}
    for item in selected:
        item = dict(item)
        item['approved_at'] = now_iso()
        item['status'] = 'active'
        existing[item['id']] = item
    approved_store['patterns'] = sorted(existing.values(), key=lambda x: x.get('approved_at', ''), reverse=True)
    dump_json(workspace / '.mnemosyne-evolve' / 'state' / 'approved-patterns.json', approved_store)
    audit = workspace / '.mnemosyne-evolve' / 'audit' / f"approve-log-{now_iso().replace(':','').replace('+','_')}.md"
    audit.write_text('# Approved patterns\n\n' + '\n'.join(f"- {item['id']}" for item in selected) + '\n', encoding='utf-8')
    print(f'Approved: {len(selected)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
