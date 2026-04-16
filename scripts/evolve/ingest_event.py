#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add parent scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import hash_text, load_config, now_iso, parse_frontmatter, source_allowed, slugify


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    parser.add_argument('event_file')
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    event_path = Path(args.event_file).expanduser().resolve()
    config = load_config(workspace)
    text = event_path.read_text(encoding='utf-8')

    if event_path.suffix.lower() == '.json':
        data = json.loads(text)
        source = data.get('source', 'unknown')
        body = data.get('body', '').strip()
        meta = {k: str(v) for k, v in data.items() if k != 'body'}
    else:
        meta, body = parse_frontmatter(text)
        source = meta.get('source', 'unknown')

    if not source_allowed(config, source):
        print(f'Source disabled: {source}')
        return 1

    topic = meta.get('topic', slugify(body[:40], 'signal'))
    out = {
        'id': hash_text(source + '\n' + topic + '\n' + body),
        'source': source,
        'topic': topic,
        'pattern_type': meta.get('pattern_type', 'recall_hint'),
        'outcome': meta.get('outcome', 'neutral'),
        'explicitness': meta.get('explicitness', 'implied'),
        'confidence': meta.get('confidence', 'medium'),
        'body': body,
        'tags': [t.strip() for t in meta.get('tags', '').split(',') if t.strip()],
        'ingested_at': now_iso(),
        'source_file': str(event_path),
    }
    dst = workspace / '.mnemosyne-evolve' / 'inbox' / f"{out['ingested_at'][:10]}-{out['id']}.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(dst)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
