#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIDENCE_RANK = {'low': 1, 'medium': 2, 'high': 3}
EXPLICITNESS_RANK = {'implied': 1, 'explicit': 2}
OUTCOME_SCORE = {'failure': 3, 'success': 2, 'retry': 1, 'rollback': 2, 'neutral': 0}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def ensure_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding='utf-8')


def strip_jsonc_comments(text: str) -> str:
    return re.sub(r'^\s*//.*$', '', text, flags=re.MULTILINE)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_config(workspace: Path) -> dict[str, Any]:
    defaults = {
        'review_mode': True,
        'sources': {
            'feishu': True,
            'heartbeat': True,
            'compaction': True,
            'execution_outcome': True,
            'published_memory': True,
        },
        'thresholds': {
            'min_repeat_count': 2,
            'min_score': 3,
            'prefer_explicit': True,
        },
        'weights': {
            'style_preference': 4,
            'failure_avoidance': 4,
            'workflow_rule': 3,
            'task_tactic': 2,
            'recall_hint': 2,
        },
        'recall': {'default_limit': 8},
    }
    cfg = workspace / '.mnemosyne-evolve' / 'config.jsonc'
    if not cfg.exists():
        return defaults
    loaded = json.loads(strip_jsonc_comments(cfg.read_text(encoding='utf-8')))
    return deep_merge(defaults, loaded)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]


def slugify(text: str, fallback: str = 'item') -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:60] or fallback


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith('---\n'):
        return {}, text.strip()
    parts = text.split('\n---\n', 1)
    if len(parts) != 2:
        return {}, text.strip()
    raw, body = parts
    meta: dict[str, str] = {}
    for line in raw.splitlines()[1:]:
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        meta[key.strip()] = value.strip()
    return meta, body.strip()


def source_allowed(config: dict[str, Any], source: str) -> bool:
    return bool(config.get('sources', {}).get(source, False))


def score_pattern(item: dict, config: dict[str, Any]) -> int:
    thresholds = config.get('thresholds', {})
    weights = config.get('weights', {})
    repeat_count = int(item.get('repeat_count', 1))
    source_count = int(item.get('source_count', 1))
    confidence = CONFIDENCE_RANK.get(item.get('confidence', 'low'), 1)
    explicitness = EXPLICITNESS_RANK.get(item.get('explicitness', 'implied'), 1)
    outcomes = Counter(item.get('outcomes', []))
    outcome_score = sum(OUTCOME_SCORE.get(name, 0) * count for name, count in outcomes.items())
    base = weights.get(item.get('pattern_type', 'recall_hint'), 1)
    score = base + max(0, repeat_count - 1) + min(source_count, 3) + confidence + explicitness + outcome_score
    if thresholds.get('prefer_explicit', True) and explicitness < 2:
        score -= 1
    return score


def tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r'[a-zA-Z0-9_\-]+', text.lower()) if len(t) > 1}
