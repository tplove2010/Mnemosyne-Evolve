---
name: mnemosyne-evolve
description: observe recurring work signals and build an experimental self-improvement layer for openclaw without writing directly to memory.md. use when chatgpt needs to summarize success and failure patterns, extract style-fit heuristics, build workflow recommendations, generate recall packs before a task, or propose evolution candidates from feishu conversations, heartbeat summaries, session compaction summaries, execution outcomes, and published mnemosyne memory.
---

# Mnemosyne Evolve 1.1

## Overview

Mnemosyne Evolve is an experimental adaptation layer for OpenClaw.
It does not replace durable memory governance. It reads signals from work, extracts reusable patterns, and writes them into its own sidecar so they can be reviewed, recalled, and selectively promoted later.

Use this skill when the goal is to make the assistant more aligned with the owner's style, better at avoiding repeated failures, and more consistent in applying successful workflows.

## Core design

Treat Mnemosyne Evolve as a separate layer above `mnemosyne-pro`.

- `mnemosyne-pro` governs durable memory correctness.
- `mnemosyne-evolve` governs experimental adaptation.
- Do not write directly into `MEMORY.md` from this skill.
- Write all experimental outputs under `.mnemosyne-evolve/`.
- Promote only after review.

## Operation Modes

### Core Mode (Default)
- **Enabled by default** - no additional configuration needed
- Keyword-based pattern matching
- No embedding dependency
- Full workflow: ingest → synthesize → approve → recall → report

### Enhanced Mode (Optional)
- **Manual activation required**
- Requires embedding service (BGE-M3)
- Features: semantic recall, semantic clustering, semantic classification

**Prerequisites for Enhanced Mode**:
1. OpenClaw must have embedding configuration in `openclaw.json`:
   ```json
   {
     "agents": {
       "defaults": {
         "memorySearch": {
           "model": "BAAI/bge-m3",
           "remote": {
             "baseUrl": "https://api.siliconflow.cn/v1",
             "apiKey": "your-api-key"
           }
         }
       }
     }
   }
   ```
2. Without valid config, Enhanced mode will auto-disable with warning

- To enable, add to `.mnemosyne-evolve/config.jsonc`:
**Enhanced Mode** is for Evolve-specific semantic capabilities (different from Pro):

```jsonc
{
  // Pattern merging based on semantic similarity
  "semantic_pattern_merge": {
    "enabled": true,
    "min_similarity": 0.80
  },
  // Auto-classify event types using embedding
  "semantic_event_classification": {
    "enabled": true
  },
  // Semantic recall (keyword + embedding hybrid)
  "semantic_recall": {
    "enabled": true,
    "top_k": 5,
    "min_similarity": 0.6
  }
}
```

**Verification**: Check `recall-pack.json` for `"semantic_enhanced": true`

## Supported input signals

Version 1.1 observes exactly these signal classes:

1. Feishu conversations
2. heartbeat summaries
3. session compaction summaries
4. execution outcomes, including success, failure, retry, rollback, or refusal
5. durable memory already published by `mnemosyne-pro`

Prefer normalized markdown or json event files over raw transcripts.

## Runtime layout

This skill stores all experimental state here:
- `.mnemosyne-evolve/config.jsonc`
- `.mnemosyne-evolve/inbox/`
- `.mnemosyne-evolve/cache/`
- `.mnemosyne-evolve/review/`
- `.mnemosyne-evolve/patterns/`
- `.mnemosyne-evolve/recall/`
- `.mnemosyne-evolve/audit/`
- `.mnemosyne-evolve/state/`

## Operating workflow

Use this sequence:

1. Run `scripts/evolve/init_runtime.py <workspace>` once.
2. Ingest normalized events with `scripts/evolve/ingest_event.py <workspace> <event-file>`.
3. Run `scripts/evolve/synthesize_patterns.py <workspace>`.
4. Review `.mnemosyne-evolve/review/evolution-candidates.md`.
5. Approve selected candidates with `scripts/evolve/approve_patterns.py <workspace> --ids ... --apply`.
6. Build a task recall pack with `scripts/evolve/build_recall_pack.py <workspace> --query "..."`.
7. Run `scripts/evolve/report_status.py <workspace>`.

## Output classes

This skill can produce only these outputs:
- style-fit candidates
- success and failure patterns
- workflow heuristics
- task recall packs
- promotion suggestions for later human review

Do not directly publish to native memory files.

## Pattern types

Use these pattern types:
- `style_preference`
- `failure_avoidance`
- `workflow_rule`
- `task_tactic`
- `recall_hint`

## Scoring rules

Version 1.1 should favor these priorities:
1. owner style fit
2. repeated success or repeated failure evidence
3. workflow consistency
4. durable usefulness across future tasks
5. recent task relevance

Do not create patterns from a single weak anecdote.
Prefer repeated signals or explicit statements.

## Guardrails

- never overwrite `MEMORY.md`
- never rewrite `mnemosyne-pro` cache or state
- never treat experimental patterns as authoritative durable memory
- never auto-promote a pattern without explicit approval
- keep a clean audit trail for every approved pattern

## Scripts

### `scripts/evolve/init_runtime.py`
Create the `.mnemosyne-evolve/` runtime layout and default config without overwriting existing content.

### `scripts/evolve/ingest_event.py`
Normalize a markdown or json event and store it under `.mnemosyne-evolve/inbox/`.

### `scripts/evolve/synthesize_patterns.py`
Read inbox events and build candidate patterns scored by repetition, explicitness, outcome, and style fit.

### `scripts/evolve/approve_patterns.py`
Move reviewed candidate ids into approved patterns under `.mnemosyne-evolve/patterns/` and write an audit log.

### `scripts/evolve/build_recall_pack.py`
Build a compact recall pack for a task query from approved experimental patterns.

### `scripts/evolve/report_status.py`
Write a status report covering inbox size, candidate counts, approved patterns, and recall artifacts.

## References

Read these when needed:
- `references/operations.md` for the recommended review loop
- `references/schemas.md` for event and pattern shapes

## Output expectations

When using this skill, produce compact operational output:
- what signal was ingested
- what candidate patterns were created
- which patterns need review
- which ids were approved
- what recall guidance should be applied to the current task

Do not describe this skill as autonomous self-training.
Describe it as an experimental adaptation layer with explicit review.
