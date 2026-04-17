#!/usr/bin/env python3
"""
build_recall_pack.py - 含嵌入增强版
新增功能:
- 语义相似度检索
- 综合排序 (exact match + key match + semantic similarity)
- 保持 pattern priority 优先级
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import dump_json, load_config, load_json, now_iso, tokenize
from embedding_client import check_embedding_available, find_similar
from semantic_utils import PATTERN_PRIORITY, rank_recall_results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    parser.add_argument('--query', default='')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--keyword-only', action='store_true', help='仅使用关键词匹配')
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    config = load_config(workspace)
    approved = load_json(workspace / '.mnemosyne-evolve' / 'state' / 'approved-patterns.json', {'patterns': []}).get('patterns', [])
    q = tokenize(args.query)
    limit = args.limit or int(config.get('recall', {}).get('default_limit', 8))
    
    # 加载语义配置
    sem_config = config.get('semantic_recall', {})
    semantic_enabled = not args.keyword_only and sem_config.get('enabled', False)
    
    # Preflight check: 验证 embedding 服务可用性
    if semantic_enabled:
        available, reason = check_embedding_available()
        if not available:
            print(f"[WARN] Semantic recall disabled: {reason}")
            print(f"[INFO] Falling back to keyword-only mode. Use --keyword-only to suppress this warning.")
            semantic_enabled = False
    
    sem_top_k = sem_config.get('top_k', 5)
    sem_min_sim = sem_config.get('min_similarity', 0.6)

    ranked = []
    for item in approved:
        hay = tokenize(item.get('topic', '') + '\n' + item.get('statement', '') + '\n' + ' '.join(item.get('reasons', [])))
        overlap = len(q & hay)
        if q and overlap == 0:
            continue
        
        # 基础分数 = exact match + score
        base_score = (overlap, item.get('score', 0))
        ranked.append({
            'topic': item.get('topic', ''),
            'statement': item.get('statement', ''),
            'score': item.get('score', 0),
            'pattern_type': item.get('pattern_type', 'recall_hint'),
            'explicitness': item.get('explicitness', 'implied'),
            'base_overlap': overlap,
            'original_item': item
        })

    # === 语义增强 ===
    if semantic_enabled and args.query:
        # 构建 corpus
        corpus = {item['topic']: item['statement'] for item in approved}
        
        cache_dir = workspace / '.mnemosyne-evolve' / 'cache' / 'embeddings'
        
        # 语义检索
        semantic_results = find_similar(
            args.query,
            corpus,
            cache_dir=cache_dir,
            top_k=sem_top_k * 2,  # 多取一些用于排序
            min_similarity=sem_min_sim
        )
        
        # 为 ranked 结果添加 similarity_score
        sem_lookup = {r['id']: r for r in semantic_results}
        
        for r in ranked:
            topic = r['topic']
            if topic in sem_lookup:
                r['similarity_score'] = sem_lookup[topic]['similarity_score']
            else:
                r['similarity_score'] = 0.0
        
        # 综合排序
        ranked = rank_recall_results(
            ranked,
            pattern_priority=PATTERN_PRIORITY,
            explicit_weight=0.3,
            similarity_weight=0.7
        )
        
        # 标记使用了语义增强
        for r in ranked:
            r['recall_method'] = 'keyword + semantic'
    else:
        # 纯关键词模式
        ranked.sort(key=lambda x: (x['base_overlap'], x['score']), reverse=True)
        for r in ranked:
            r['recall_method'] = 'keyword'

    # 取前 limit 个
    chosen = ranked[:limit]

    payload = {
        'generated_at': now_iso(), 
        'query': args.query, 
        'items': [r['original_item'] for r in chosen],
        'recall_method': chosen[0].get('recall_method', 'keyword') if chosen else 'none',
        'metadata': {
            'semantic_enhanced': semantic_enabled and bool(args.query),
            'total_candidates': len(ranked)
        }
    }
    
    dump_json(workspace / '.mnemosyne-evolve' / 'recall' / 'recall-pack.json', payload)
    
    lines = ['# Recall pack', '', f"Generated: {payload['generated_at']}", f"Query: {args.query or '(none)'}", f"Method: {payload['recall_method']}", '']
    if not chosen:
        lines += ['No approved patterns matched.', '']
    for item in chosen:
        lines += [
            f"## {item['pattern_type']} · {item['topic']}",
            f"- score: {item['score']}",
        ]
        
        # 显示语义相似度（如果有）
        if semantic_enabled and 'similarity_score' in item:
            lines.append(f"- similarity_score: {item['similarity_score']:.2%}")
        
        lines.append(f"- reasons: {', '.join(item.get('reasons', [])) if item.get('reasons') else 'none'}")
        
        # 标记 recall method
        if 'recall_method' in item:
            lines.append(f"- recall_method: {item['recall_method']}")
        
        lines += ['', item.get('statement', ''), '']
    
    (workspace / '.mnemosyne-evolve' / 'recall' / 'recall-pack.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Recall items: {len(chosen)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())