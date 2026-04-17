#!/usr/bin/env python3
"""
synthesize_patterns.py - 含嵌入增强版
新增功能:
- pattern 语义聚类 (semantic_pattern_merge)
- 与已批准 patterns 的相似度比较
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

# Add parent scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import dump_json, load_config, load_json, now_iso, score_pattern, slugify
from embedding_client import check_embedding_available
from semantic_utils import (
    PATTERN_PRIORITY,
    classify_event_type,
    load_patterns,
    merge_similar_patterns,
    rank_recall_results,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    parser.add_argument('--skip-semantic', action='store_true', help='跳过嵌入增强')
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    config = load_config(workspace)
    inbox = workspace / '.mnemosyne-evolve' / 'inbox'
    
    # 加载嵌入配置
    sem_config = config.get('semantic_pattern_merge', {})
    semantic_enabled = not args.skip_semantic and sem_config.get('enabled', False)
    
    # Preflight check: 验证 embedding 服务可用性
    if semantic_enabled:
        available, reason = check_embedding_available()
        if not available:
            print(f"[WARN] Semantic pattern merge disabled: {reason}")
            print(f"[INFO] Falling back to keyword-only mode. Set --skip-semantic to suppress this warning.")
            semantic_enabled = False
    
    min_similarity = sem_config.get('min_similarity', 0.8)
    
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)

    # 读取 inbox 事件
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
        
        # 事件语义分类 (如果启用)
        if semantic_enabled and config.get('semantic_event_classification', {}).get('enabled', False):
            type_hint = classify_event_type(statement)
            if type_hint['predicted_type'] != pattern_type:
                # 添加类型建议，但不替代主规则
                candidates.append({
                    '_type_suggestion': type_hint,
                    '_hint_only': True
                })
        
        # 获取主要 outcome
        main_outcome = 'neutral'
        if outcomes:
            # 优先使用 success/failure
            if 'success' in outcomes:
                main_outcome = 'success'
            elif 'failure' in outcomes:
                main_outcome = 'failure'
        
        candidate = {
            'id': slugify(f'{pattern_type}-{topic}-{items[-1].get("id", topic)}'),
            'pattern_type': pattern_type,
            'topic': topic,
            'statement': statement,
            'repeat_count': len(items),
            'source_count': len({i.get('source', 'unknown') for i in items}),
            'explicitness': max((i.get('explicitness', 'implied') for i in items), key=lambda x: 2 if x == 'explicit' else 1),
            'confidence': max((i.get('confidence', 'low') for i in items), key=lambda x: {'low': 1, 'medium': 2, 'high': 3}.get(x, 1)),
            'outcome': main_outcome,  # 添加 outcome 字段用于聚类
            'outcomes': outcomes,
            'evidence_files': [i['_path'] for i in items],
            'reasons': [],
            'generated_at': now_iso(),
        }
        
        # Success/Failure 归并提示
        if semantic_enabled:
            if 'failure' in outcomes:
                candidate['reasons'].append('failure_avoidance_semantic_check')
            if 'success' in outcomes:
                candidate['reasons'].append('success_pattern_semantic_check')
        
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

    # === 语义聚类增强 ===
    if semantic_enabled:
        # 加载已批准的 patterns
        patterns_dir = workspace / '.mnemosyne-evolve' / 'patterns'
        existing_patterns = load_patterns(patterns_dir)
        
        # 创建缓存目录
        cache_dir = workspace / '.mnemosyne-evolve' / 'cache' / 'embeddings'
        
        # 语义聚类
        candidates = merge_similar_patterns(
            candidates,
            existing_patterns,
            cache_dir=cache_dir,
            min_similarity=min_similarity
        )

    # 过滤掉非候选条目（如类型建议）
    candidates = [c for c in candidates if 'id' in c and 'score' in c]
    candidates.sort(key=lambda x: (x.get('score', 0), x.get('repeat_count', 1)), reverse=True)
    
    # 生成输出
    dump_json(workspace / '.mnemosyne-evolve' / 'cache' / 'candidates.json', candidates)

    lines = ['# Evolution candidates', '', f'Generated: {now_iso()}', '']
    if not candidates:
        lines += ['No candidates.', '']
    for c in candidates:
        # 跳过类型建议条目
        if c.get('_type_suggestion'):
            continue
            
        lines += [
            f"## {c['pattern_type']} · {c['topic']}",
            f"- id: {c['id']}",
            f"- score: {c['score']}",
            f"- repeat_count: {c.get('repeat_count', 1)}",
            f"- source_count: {c.get('source_count', 1)}",
            f"- confidence: {c['confidence']}",
            f"- explicitness: {c['explicitness']}",
            f"- reasons: {', '.join(c['reasons']) if c['reasons'] else 'none'}",
        ]
        
        # 添加语义聚类提示
        if semantic_enabled:
            if 'semantic_merge_hint' in c:
                hint = c['semantic_merge_hint']
                lines.append(f"- **semantic_merge_hint**: similar to {len(hint['similar_to'])} existing pattern(s)")
                lines.append(f"  - action: {hint['action']}")
                for s in hint['similar_to']:
                    lines.append(f"  - `{s['id']}`: similarity {s['similarity']:.2%}")
            if 'semantic_cluster_hint' in c:
                hint = c['semantic_cluster_hint']
                lines.append(f"- **semantic_cluster_hint**: {len(hint.get('similar_candidates', []))} similar candidate(s)")
                lines.append(f"  - action: {hint.get('action', 'consider_merge')}")
                for s in hint.get('similar_candidates', []):
                    lines.append(f"  - `{s['id']}`: similarity {s['similarity']:.2%} (outcome={s.get('outcome', 'N/A')})")
        
        lines += ['', c.get('statement', ''), '']
    
    (workspace / '.mnemosyne-evolve' / 'review' / 'evolution-candidates.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Candidates: {len(candidates)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())