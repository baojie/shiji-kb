# Workspace

## Quick Start

1. **Read `spec.md`** — what to build
2. **Use `mapping.md`** — navigate SKUs by feature
3. **Check `eureka.md`** — creative ideas and cross-cutting insights

## Structure

```
workspace/
├── spec.md                      # App specification
├── mapping.md                   # SKU router — find the right knowledge
├── eureka.md                    # Creative insights and feature ideas
├── workspace_manifest.json      # Assembly metadata
├── chat_log.json                # Chatbot conversation log
└── skus/
    ├── factual/                 # Facts, definitions, data (header.md + content)
    ├── procedural/              # Skills and workflows (header.md + SKILL.md)
    ├── relational/              # Label tree + glossary
    ├── postprocessing/          # Bucketing, dedup, confidence reports
    └── skus_index.json          # Master index of all SKUs
```

## SKU Types

| Type | Description | Files |
|------|-------------|-------|
| **Factual** | Facts, definitions, data points, statistics | `header.md` + `content.md` or `content.json` |
| **Procedural** | Workflows, skills, step-by-step processes | `header.md` + `SKILL.md` |
| **Relational** | Category hierarchy and glossary | `label_tree.json` + `glossary.json` |

## Stats

- **Factual SKUs**: 434
- **Procedural SKUs**: 241
- **Relational knowledge**: Yes
- **Total files copied**: 1359

## How to Use

1. Start with `spec.md` to understand what the app should do
2. Use `mapping.md` to find relevant SKUs for each feature
3. Read SKU `header.md` files for quick summaries before loading full content
4. Reference `eureka.md` for creative ideas that connect multiple knowledge areas
