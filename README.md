# Mnemosyne Evolve 1.1

> English below | 中文说明见下方

---

## 定位说明 | Positioning

**Mnemosyne Evolve 就像是 OpenClaw 的「复盘教练 + 经验笔记员」。**

它会把你和 AI 日常互动里那些做得对的方式、做错的坑、你反复强调的风格要求整理出来，慢慢让 AI 更懂你、少犯老错误、越来越贴近你的做事方式。

**Mnemosyne Evolve is like OpenClaw's "Review Coach + Experience Note-taker".**

It organizes how you interact with the AI daily — what works well, what mistakes to avoid, your repeated style preferences — gradually making the AI understand you better, avoid recurring mistakes, and align more closely with your working style.

---

## English

### Overview

Mnemosyne Evolve is an **experimental adaptation layer** for OpenClaw. It is built on top of Mnemosyne Pro and helps the AI continuously learn and adapt to the owner's behavior patterns without directly writing to native memory.

### Core Design

- **Not replace** durable memory governance (Mnemosyne Pro)
- **Separate layer** that reads signals from work and builds reusable patterns
- **Human review required** before any pattern is approved
- All outputs stored in `.mnemosyne-evolve/`

### What It Does

Observes these signal types:
1. Feishu conversations
2. Heartbeat summaries
3. Session compaction summaries  
4. Execution outcomes (success/failure/retry)
5. Published memory from Mnemosyne Pro

Generates these pattern types:
- `style_preference` - User's communication style
- `failure_avoidance` - Patterns to avoid repeated failures
- `workflow_rule` - Reusable workflow heuristics
- `task_tactic` - Task-specific tactics
- `recall_hint` - Memory hints for future tasks

### Installation

#### Windows
```powershell
# Copy all scripts (evolve/* + common utilities)
New-Item -ItemType Directory -Path "$env:USERPROFILE\.openclaw\workspace\scripts\evolve" -Force
Copy-Item -Path ".\scripts\evolve\*" -Destination "$env:USERPROFILE\.openclaw\workspace\scripts\evolve\"
Copy-Item -Path ".\scripts\common.py" -Destination "$env:USERPROFILE\.openclaw\workspace\scripts\"
Copy-Item -Path ".\scripts\embedding_client.py" -Destination "$env:USERPROFILE\.openclaw\workspace\scripts\"
Copy-Item -Path ".\scripts\semantic_utils.py" -Destination "$env:USERPROFILE\.openclaw\workspace\scripts\"

# Copy assets (default config)
New-Item -ItemType Directory -Path "$env:USERPROFILE\.openclaw\workspace\assets" -Force
Copy-Item -Path ".\assets\mnemosyne-evolve.config.jsonc" -Destination "$env:USERPROFILE\.openclaw\workspace\assets\"

# Initialize runtime
python "$env:USERPROFILE\.openclaw\workspace\scripts\evolve\init_runtime.py" "$env:USERPROFILE\.openclaw\workspace"
```

#### macOS / Linux
```bash
# Copy all scripts (evolve/* + common utilities)
mkdir -p ~/.openclaw/workspace/scripts/evolve
cp -r ./scripts/evolve/* ~/.openclaw/workspace/scripts/evolve/
cp ./scripts/common.py ~/.openclaw/workspace/scripts/
cp ./scripts/embedding_client.py ~/.openclaw/workspace/scripts/
cp ./scripts/semantic_utils.py ~/.openclaw/workspace/scripts/

# Copy assets (default config)
mkdir -p ~/.openclaw/workspace/assets
cp ./assets/mnemosyne-evolve.config.jsonc ~/.openclaw/workspace/assets/

# Initialize runtime
python ~/.openclaw/workspace/scripts/evolve/init_runtime.py ~/.openclaw/workspace
```

### Operating Workflow

```bash
# 1. Initialize (once)
python scripts/evolve/init_runtime.py <workspace>

# 2. Ingest events
python scripts/evolve/ingest_event.py <workspace> <event-file>

# 3. Synthesize patterns
python scripts/evolve/synthesize_patterns.py <workspace>

# 4. Review candidates (see .mnemosyne-evolve/review/evolution-candidates.md)

# 5. Approve patterns
python scripts/evolve/approve_patterns.py <workspace> --ids <pattern-id> --apply

# 6. Build recall pack for next task
python scripts/evolve/build_recall_pack.py <workspace> --query "your task"

# 7. Check status
python scripts/evolve/report_status.py <workspace>
```

### Relationship with Mnemosyne Pro

| Layer | Writes To | Purpose |
|-------|-----------|---------|
| Mnemosyne Pro 1.3 | `memory/*.md` | Durable memory correctness |
| Mnemosyne Evolve 1.1 | `.mnemosyne-evolve/` | Experimental adaptation |

---

## 中文

### 概述

Mnemosyne Evolve 是 OpenClaw 的**实验性自适应层**。它构建在 Mnemosyne Pro 之上，帮助 AI 持续学习和适应主人的行为模式，而不直接写入原生记忆。

### 核心设计

- **不替换**持久记忆治理（Mnemosyne Pro）
- **独立层**读取工作信号并构建可复用模式
- **需要人工审核**后才能批准模式
- 所有输出存储在 `.mnemosyne-evolve/`

### 功能说明

观测以下信号类型：
1. Feishu 对话
2. Heartbeat 摘要
3. Session 压缩摘要
4. 执行结果（成功/失败/重试）
5. Mnemosyne Pro 已发布的记忆

生成以下模式类型：
- `style_preference` - 用户的沟通风格
- `failure_avoidance` - 规避重复失败的模式
- `workflow_rule` - 可复用工作流规则
- `task_tactic` - 任务特定策略
- `recall_hint` - 未来任务的记忆提示

### 安装

#### Windows
```powershell
# 复制所有脚本（evolve/* + 公共工具）
New-Item -ItemType Directory -Path "$env:USERPROFILE\.openclaw\workspace\scripts\evolve" -Force
Copy-Item -Path ".\scripts\evolve\*" -Destination "$env:USERPROFILE\.openclaw\workspace\scripts\evolve\"
Copy-Item -Path ".\scripts\common.py" -Destination "$env:USERPROFILE\.openclaw\workspace\scripts\"
Copy-Item -Path ".\scripts\embedding_client.py" -Destination "$env:USERPROFILE\.openclaw\workspace\scripts\"
Copy-Item -Path ".\scripts\semantic_utils.py" -Destination "$env:USERPROFILE\.openclaw\workspace\scripts\"

# 复制 assets（默认配置）
New-Item -ItemType Directory -Path "$env:USERPROFILE\.openclaw\workspace\assets" -Force
Copy-Item -Path ".\assets\mnemosyne-evolve.config.jsonc" -Destination "$env:USERPROFILE\.openclaw\workspace\assets\"

# 初始化运行时
python "$env:USERPROFILE\.openclaw\workspace\scripts\evolve\init_runtime.py" "$env:USERPROFILE\.openclaw\workspace"
```

#### macOS / Linux
```bash
# 复制所有脚本（evolve/* + 公共工具）
mkdir -p ~/.openclaw/workspace/scripts/evolve
cp -r ./scripts/evolve/* ~/.openclaw/workspace/scripts/evolve/
cp ./scripts/common.py ~/.openclaw/workspace/scripts/
cp ./scripts/embedding_client.py ~/.openclaw/workspace/scripts/
cp ./scripts/semantic_utils.py ~/.openclaw/workspace/scripts/

# 复制 assets（默认配置）
mkdir -p ~/.openclaw/workspace/assets
cp ./assets/mnemosyne-evolve.config.jsonc ~/.openclaw/workspace/assets/

# 初始化运行时
python ~/.openclaw/workspace/scripts/evolve/init_runtime.py ~/.openclaw/workspace
```

### 操作流程

```bash
# 1. 初始化（仅一次）
python scripts/evolve/init_runtime.py <workspace>

# 2. 摄入事件
python scripts/evolve/ingest_event.py <workspace> <event-file>

# 3. 合成模式
python scripts/evolve/synthesize_patterns.py <workspace>

# 4. 审核候选（查看 .mnemosyne-evolve/review/evolution-candidates.md）

# 5. 批准模式
python scripts/evolve/approve_patterns.py <workspace> --ids <pattern-id> --apply

# 6. 为下一任务构建记忆包
python scripts/evolve/build_recall_pack.py <workspace> --query "你的任务"

# 7. 查看状态
python scripts/evolve/report_status.py <workspace>
```

### 与 Mnemosyne Pro 的关系

| 层级 | 写入位置 | 用途 |
|------|----------|------|
| Mnemosyne Pro 1.3 | `memory/*.md` | 持久记忆治理 |
| Mnemosyne Evolve 1.1 | `.mnemosyne-evolve/` | 实验性自适应 |

---

## 文件结构 / File Structure

```
mnemosyne-evolve/
├── scripts/
│   ├── init_runtime.py          # 初始化运行时
│   ├── ingest_event.py          # 摄入事件
│   ├── synthesize_patterns.py   # 合成候选模式
│   ├── approve_patterns.py      # 批准模式
│   ├── build_recall_pack.py     # 构建记忆包
│   ├── report_status.py         # 状态报告
│   └── common.py                # 公共函数
├── .mnemosyne-evolve/           # 配置模板
├── references/
│   ├── operations.md            # 操作指南
│   └── schemas.md               # 数据模式
├── agents/
│   └── openai.yaml              # Agent 配置
├── SKILL.md                     # 技能定义
└── README.md                    # 本文件
```

---

## 更新日志 / Changelog

### 1.1 (2026-04-17) - 嵌入增强版

#### 新增特性：语义嵌入增强

1. **语义 Pattern 聚类 (semantic_pattern_merge)**
   - 基于 embedding 相似度自动合并相似事件
   - 配置: `min_similarity: 0.80`
   - 输出: `semantic_cluster_hint` 建议

2. **语义 Recall 检索 (semantic_recall)**
   - 使用 BGE-M3 embedding 进行语义搜索
   - 配置: `top_k: 5`, `min_similarity: 0.6`
   - fallback: keyword 搜索

3. **事件语义分类 (semantic_event_classification)**
   - 对无明确 keyword 的事件使用 embedding 分类
   - 支持 5 种类型: style_preference, failure_avoidance, workflow_rule, task_tactic, recall_hint
   - method: keyword → embedding fallback

#### 验证结果
- Success/Failure 聚类相似度: 89.15% / 85.71%
- 分类测试: 7/7 通过
- Keyword 占比: 71%, Embedding 占比: 29%

---

### 1.0 (2026-04-16)
- 初始版本 / Initial release
- 实验性自适应层 / Experimental adaptation layer
- 模式合成与审核 / Pattern synthesis and approval
- 记忆包构建 / Recall pack generation

---

MIT License | 开源协议: MIT

Built for OpenClaw + William's Memory Evolution 🌷