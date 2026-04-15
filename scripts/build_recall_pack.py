#!/usr/bin/env python3
from __future__ import annotations

import argparse

from pathlib import Path

from common import dump_json, load_config, load_json, now_iso, tokenize


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    parser.add_argument('--query', default='')
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    config = load_config(workspace)
    approved = load_json(workspace / '.mnemosyne-evolve' / 'state' / 'approved-patterns.json', {'patterns': []}).get('patterns', [])
    q = tokenize(args.query)
    limit = args.limit or int(config.get('recall', {}).get('default_limit', 8))

    ranked = []
    for item in approved:
        hay = tokenize(item.get('topic', '') + '\n' + item.get('statement', '') + '\n' + ' '.join(item.get('reasons', [])))
        overlap = len(q & hay)
        if q and overlap == 0:
            continue
        ranked.append((overlap, item.get('score', 0), item))
    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    chosen = [item for _, _, item in ranked[:limit]] if q else [item for _, _, item in sorted(ranked, key=lambda x: x[1], reverse=True)[:limit]]

    payload = {'generated_at': now_iso(), 'query': args.query, 'items': chosen}
    dump_json(workspace / '.mnemosyne-evolve' / 'recall' / 'recall-pack.json', payload)
    lines = ['# Recall pack', '', f"Generated: {payload['generated_at']}", f"Query: {args.query or '(none)'}", '']
    if not chosen:
        lines += ['No approved patterns matched.', '']
    for item in chosen:
        lines += [
            f"## {item['pattern_type']} · {item['topic']}",
            f"- score: {item['score']}",
            f"- reasons: {', '.join(item.get('reasons', [])) if item.get('reasons') else 'none'}",
            '',
            item['statement'],
            '',
        ]
    (workspace / '.mnemosyne-evolve' / 'recall' / 'recall-pack.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Recall items: {len(chosen)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
