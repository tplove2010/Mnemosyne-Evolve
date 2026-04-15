#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from common import dump_json, load_config, load_json, now_iso, score_pattern, slugify


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    config = load_config(workspace)
    inbox = workspace / '.mnemosyne-evolve' / 'inbox'
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for path in sorted(inbox.glob('*.json')):
        event = load_json(path, {})
        if not event:
            continue
        key = (event.get('pattern_type', 'recall_hint'), event.get('topic', slugify(path.stem)))
        event['_path'] = str(path.relative_to(workspace))
        grouped[key].append(event)

    candidates = []
    for (pattern_type, topic), items in grouped.items():
        items.sort(key=lambda x: x.get('ingested_at', ''))
        statement = items[-1].get('body', '').strip()
        outcomes = [i.get('outcome', 'neutral') for i in items]
        candidate = {
            'id': slugify(f'{pattern_type}-{topic}-{items[-1].get("id", topic)}'),
            'pattern_type': pattern_type,
            'topic': topic,
            'statement': statement,
            'repeat_count': len(items),
            'source_count': len({i.get('source', 'unknown') for i in items}),
            'explicitness': max((i.get('explicitness', 'implied') for i in items), key=lambda x: 2 if x == 'explicit' else 1),
            'confidence': max((i.get('confidence', 'low') for i in items), key=lambda x: {'low': 1, 'medium': 2, 'high': 3}.get(x, 1)),
            'outcomes': outcomes,
            'evidence_files': [i['_path'] for i in items],
            'reasons': [],
            'generated_at': now_iso(),
        }
        if candidate['repeat_count'] > 1:
            candidate['reasons'].append('repeated signal')
        if candidate['explicitness'] == 'explicit':
            candidate['reasons'].append('explicit wording observed')
        if 'failure' in outcomes:
            candidate['reasons'].append('failure avoidance opportunity')
        if 'success' in outcomes:
            candidate['reasons'].append('successful pattern observed')
        candidate['score'] = score_pattern(candidate, config)
        candidates.append(candidate)

    candidates.sort(key=lambda x: (x['score'], x['repeat_count']), reverse=True)
    dump_json(workspace / '.mnemosyne-evolve' / 'cache' / 'candidates.json', candidates)

    lines = ['# Evolution candidates', '', f'Generated: {now_iso()}', '']
    if not candidates:
        lines += ['No candidates.', '']
    for c in candidates:
        lines += [
            f"## {c['pattern_type']} · {c['topic']}",
            f"- id: {c['id']}",
            f"- score: {c['score']}",
            f"- repeat_count: {c['repeat_count']}",
            f"- source_count: {c['source_count']}",
            f"- confidence: {c['confidence']}",
            f"- explicitness: {c['explicitness']}",
            f"- reasons: {', '.join(c['reasons']) if c['reasons'] else 'none'}",
            '',
            c['statement'],
            '',
        ]
    (workspace / '.mnemosyne-evolve' / 'review' / 'evolution-candidates.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Candidates: {len(candidates)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
