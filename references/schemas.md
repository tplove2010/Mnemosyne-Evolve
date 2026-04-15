# Event and pattern schemas

## event markdown frontmatter
- source: feishu | heartbeat | compaction | execution_outcome | published_memory
- topic: short topic slug
- pattern_type: optional hint such as style_preference or workflow_rule
- outcome: success | failure | retry | rollback | neutral
- explicitness: explicit | implied
- confidence: low | medium | high
- tags: comma-separated optional tags

Body should contain the factual signal text.

## candidate pattern
- id
- pattern_type
- topic
- statement
- score
- repeat_count
- source_count
- outcomes
- evidence_files
- reasons

## approved pattern
Same as candidate pattern plus:
- approved_at
- status: active
