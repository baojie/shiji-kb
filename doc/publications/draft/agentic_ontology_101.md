---
status: draft
platforms: []
---

# Agentic Ontology 101: A Practical Guide to Building Knowledge Graphs with AI Agents

**Jie Bao, with Claude (Anthropic)**

*Based on the Shiji Knowledge Base project: 130 chapters, 577,000 characters, 18 entity types, 102,851 annotations, 3,197 events, 7,637 relations — built in 6 weeks by one person + AI agents.*

> This document updates Noy & McGuinness's classic *"Ontology Development 101: A Guide to Creating Your First Ontology"* (Stanford, 2001) for the age of AI agents. Where Ontology 101 taught humans to design ontologies top-down using Protégé, this guide teaches humans to *grow* ontologies bottom-up with AI, using iterative reflection and hybrid automation.

---

## Part I: The Paradigm Shift

### 1. Why Agentic Ontology?

Noy & McGuinness (2001) listed five reasons to develop an ontology:

1. To share common understanding of information structure
2. To enable reuse of domain knowledge
3. To make domain assumptions explicit
4. To separate domain knowledge from operational knowledge
5. To analyze domain knowledge

All five remain valid. But the **how** has fundamentally changed:

| | Ontology 101 (2001) | Agentic Ontology (2026) |
|--|---------------------|---------------------------|
| **Starting point** | Blank schema in Protégé | Raw text corpus |
| **Direction** | Top-down design | Bottom-up emergence |
| **Scale** | Dozens of classes, hundreds of instances | Thousands of classes, tens of thousands of instances |
| **Iteration speed** | Weeks per round | Hours per round |
| **Core bottleneck** | **2001: Design** | **2026: Reflect/Evolve** |

**The core shift:** In 2001, the hard part was *designing* the ontology. In 2026, the hard part is **reflecting on and evolving** the AI-extracted ontology. The ontology is not a pre-designed blueprint — it is an organic structure that grows from data, pruned and calibrated by humans.

### 2. About This Project

We demonstrate these principles through the Shiji Knowledge Base — a complete knowledge graph extracted from Sima Qian's *Records of the Grand Historian* (《史记》, c. 94 BCE), covering 2,600 years of Chinese history:

**Data scale:**
- **Text:** 130 chapters, 577,000 characters of classical Chinese
- **Entities:** 15,190 unique entities, 102,851 annotations across 18 types
- **Events:** 3,197 historical events, 98.7% with BCE dating
- **Relations:** 7,637 event relations (4 auto-computed + 5 LLM-inferred types)
- **Quality:** 5 rounds of reflection, 12,200+ corrections converged

**Methodology:**
- **14 meta-skills:** Universal knowledge engineering methods (OTF+JIT+Bootstrap, Reflection, Lancet Method, etc.)
- **40 pipeline skills:** Domain-specific techniques for classical texts
- **Time investment:** ~120 hours human + ~3 billion tokens AI
- **Human-AI division:** Human sets vision, AI executes bulk work, human curates quality

This is not a toy example. It is a production knowledge base with interactive reader, subway-map timeline, and cross-chapter reasoning — all methods documented as reusable SKILL files.

---

## Part II: Three Methodological Pillars

The three core innovations distinguishing agentic ontology engineering from traditional approaches:

### 3. OTF + JIT + Bootstrap: The Meta-Method

#### 3.1 On-The-Fly (OTF): Summarize While You Work

**Traditional approach (Post-Mortem):**
```
Day 1-90: Execute tasks (no summarization)
Day 91: Start summarizing
  ├─ Problem 1: Details forgotten, low-quality summary
  ├─ Problem 2: Error patterns repeated 90 times, high rework cost
  └─ Problem 3: Cannot apply to the project itself (already finished)
```

**OTF approach:**
```
Day 1: Process 5 samples
  ├─ Discover pattern A (disambiguation issue)
  └─ Immediately summarize → Update rule base

Day 2: Process 30 samples
  ├─ Apply Day 1 rules (80% automated)
  ├─ Discover new pattern B (format issue)
  └─ Immediately summarize → Develop lint tool (1 hour)

Day 3-10: Process all 130 chapters
  ├─ Apply accumulated rules + tools
  ├─ Error rate drops from 20% → 5%
  └─ Discover final patterns C, D → Immediately summarize
```

**Key principle:** Don't wait until the end to summarize. When you see a pattern repeat 3 times, extract it immediately and codify it as a rule/tool/SKILL document.

*Shiji example:* During entity annotation, we discovered the "single-character state name" error pattern (赵/韩/魏 mis tagged as person names) after processing just 10 chapters. Immediately created a detection script. This pattern appeared 1,200+ times across all chapters — catching it early saved weeks of manual correction.

#### 3.2 Just-In-Time (JIT): Deliver Minimally Viable Versions

**Traditional approach (Big Bang):**
```
Week 1-4: Design perfect schema (50-attribute ontology)
Week 5-8: Execute once (discover schema mismatch)
Week 9: Large-scale rework (restructure ontology, re-enter data)
→ Total: 9 weeks, quality uncertain
```

**JIT approach:**
```
Week 1:
  JIT-v0.1: Minimal ontology (4 types) + annotate 5 chapters
  ├─ Deliver: Initial data (60% quality)
  └─ Feedback: Need "feudal-state" type

Week 2:
  JIT-v0.5: Ontology evolves (4→8 types) + annotate 30 chapters
  ├─ Deliver: Expanded data (75% quality)
  └─ Feedback: Need "artifact" type

Week 3:
  JIT-v1.0: Ontology stabilizes (18 types) + annotate 130 chapters
  ├─ Deliver: Full data (85% quality)
  └─ Feedback: Systematic error patterns

Week 4:
  JIT-v1.5: First reflection round
  ├─ Deliver: High-quality data (92% quality)
  └─ Feedback: Converged

→ Total: 4 weeks, quality 92%
```

**Key principle:** Don't pursue perfection in the first iteration. Deliver a minimally viable version quickly, gather feedback, and iterate. Quality improves through successive refinement, not through upfront perfectionism.

*Shiji example:* Event dating annotation went through 5 quality tiers:
- P0 (Day 1-2): 3,092 events with initial BCE dates (60% accuracy)
- P1 (Week 1): First reflection, 1,010 corrections (80% accuracy)
- P2 (Week 2): Second reflection, 431 corrections (88% accuracy)
- P3 (Week 3): Third reflection, 465 corrections (92% accuracy)
- P4 (Week 4): Fourth reflection, 167 corrections (95% accuracy)
- P5 (Week 5): Fifth reflection, 46 corrections (97% accuracy, converged)

Each tier delivered usable data. Early tiers enabled downstream work (relation extraction) to begin before dating was perfect.

#### 3.3 Bootstrap: Knowledge Self-Growth (5 Stages)

**Traditional view:**
```
Human labor → Complete task → Project ends
  ↓
Next project: Start from scratch
```

**Bootstrap view:**
```
Human labor → Produces intermediate knowledge (logs/scripts)
  ↓
Intermediate knowledge → Summarized as SKILL documents
  ↓
SKILL documents → Automated tools (reduce human effort)
  ↓
Tool usage → Generates higher-order knowledge (patterns)
  ↓
Patterns → Auto-update SKILL documents (automation of summarization itself)
  ↓
SKILL documents → Auto-evolve (system self-governance)
```

**The five bootstrap stages:**

| Stage | Automation Rate | Key Products | Human Role |
|-------|----------------|--------------|------------|
| **Stage 1: Manual Labor** | 0% | Annotated samples, chat logs | Executor |
| **Stage 2: Scripts** | 20% | Lint/stats/transform scripts | Executor + scripter |
| **Stage 3: SKILL Documents** | 60% | Method docs, Agent workflows | Reviewer |
| **Stage 4: Auto-Summarization** | 90% | Agent auto-updates SKILLs | Quality controller |
| **Stage 5: Meta-Evolution** | 99% | Meta-SKILLs (methods for generating methods) | Exception handler |

*Shiji example:* Entity annotation bootstrap trajectory:
- Week 1: Manual annotation (100% human)
- Week 2: Wrote 10 validation scripts (20% automated)
- Week 3: Documented SKILL_03, Agent reads and auto-executes (60% automated)
- Week 5-8: Agent auto-discovers new error patterns, updates SKILL (90% automated)
- Month 3: Meta-SKILL extracted (00-META-01_Reflection), applicable to all annotation tasks (98% automated)

**Convergence proof:** Human time decreased exponentially:
```
Week 1:  40 hours (100% human)
Week 2:  32 hours (80% human)
Week 3-4: 24 hours (40% human)
Week 5-8: 10 hours (10% human, across 4 weeks)
Month 3-4: 5 hours (1% human, across 2 months)
→ Total human time: 111 hours vs. estimated 400 hours (traditional approach)
```

---

### 4. Reflection Loop: Quality Convergence

The structured iteration process that transforms "AI output (90% accurate)" into "production-grade data (97%+ accurate)."

#### 4.1 Three Dimensions of Reflection

| Dimension | Use Case | Example | Advantage | Limitation |
|-----------|----------|---------|-----------|------------|
| **Chapter-wise** | Chapter-specific context errors | SKILL_03c entity review by chapter | Captures local context | Misses cross-chapter patterns |
| **Type-wise** | Systematic errors across all chapters | Migrating "criminal law" terms from institution→law type | One fix applies to entire corpus | Requires pattern discovery first |
| **Global** | Cross-chapter consistency | Fifth round event dating: cross-validate same event across chapters | Finds contradictions | High computational cost |

**Selection principle:**
- Round 1: **Chapter-wise** to establish baseline, accumulate error patterns
- Round 2-3: **Type-wise** for systematic corrections (batch processing)
- Final round: **Global** for cross-validation and consistency checks

#### 4.2 Convergence Proof: Event Dating Case Study

Five rounds of Agent-driven reflection on 3,092 event BCE dates:

| Round | Corrections | Chapters Affected | New Patterns | Main Fix Types |
|-------|-------------|-------------------|--------------|----------------|
| **R1** | 1,010 | 118/130 | 25 | Systematic year errors + certainty upgrades |
| **R2** | 431 | 105/130 | 1 | Certainty upgrades + fine-tuning |
| **R3** | 465 | 70/130 | 0 | Convergence validation + residual cleanup |
| **R4** | 167 | 68/130 | 0 | Final validation + format unification |
| **R5** | 46 | 28/130 | 0 | Cross-chapter validation + certainty upgrades |

**Exponential decay:** Correction volume decreased by ~57% each round (R1→R2→R3), then accelerated drop in R4-R5.

**Convergence criteria:**
- Correction count < 5% of total
- New pattern count = 0 (for 2 consecutive rounds)
- Cross-chapter contradiction count < 10

**Key insight:** AI errors are not random — they are **systematic**. Once you discover the pattern, you can fix hundreds of instances at once. Each round accumulates patterns, making the next round more efficient.

#### 4.3 The Four-Phase Workflow

Every reflection task follows this structure:

```
┌─────────────────────────────────────────────────┐
│  Phase 0: Preparation                           │
│  ├─ Define quality standards & error patterns   │
│  ├─ Write SKILL document (methodology + known   │
│  │   patterns)                                   │
│  └─ Prepare detection tools (lint/grep/stats)   │
├─────────────────────────────────────────────────┤
│  Phase 1: Reconnaissance                        │
│  ├─ Sample 10-20 chapters, identify main error  │
│  │   types                                       │
│  ├─ Count error distribution (by chapter/type)  │
│  └─ Determine strategy (chapter/type/global)    │
├─────────────────────────────────────────────────┤
│  Phase 2: Execution                             │
│  ├─ Agent batch review (SKILL-guided)           │
│  ├─ Extract correction suggestions (JSON)       │
│  └─ Apply corrections (scripted automation)     │
├─────────────────────────────────────────────────┤
│  Phase 3: Validation                            │
│  ├─ Run lint checks (format validation)         │
│  ├─ Compare before/after stats                  │
│  ├─ Spot-check 5-10% (human review)             │
│  └─ Decision: Converged → exit, or iterate →    │
│      update SKILL, next round                    │
└─────────────────────────────────────────────────┘
```

**Output:** JSON-formatted corrections with rationale, enabling audit trails and rollback.

---

### 5. Lancet Method: Hybrid Precision

Named after the surgical tool, this method advocates **fine-grained task decomposition** and **selecting the optimal solution** (LLM/rules/code) for each subtask.

> *"Scalpel-like precision, not sledgehammer end-to-end."*

#### 5.1 Task Decomposition: The Decision Tree

```
Task analysis
  ├─ Has explicit rules?
  │   ├─ Yes → [Rules + Code] (e.g., format validation, type filtering)
  │   └─ No ↓
  ├─ Structured matching problem?
  │   ├─ Yes → [Code Algorithm] (e.g., entity co-occurrence, time alignment)
  │   └─ No ↓
  ├─ Requires semantic understanding?
  │   ├─ Yes → [LLM] (e.g., causal reasoning, sentiment analysis)
  │   └─ No ↓
  ├─ Safe to automate?
  │   ├─ Yes → [Rules + LLM Joint] (rule-based candidate filtering + LLM confirmation)
  │   └─ No → [Human Review] (conservative fallback)
```

#### 5.2 Example: Event Relation Extraction

**Task:** Extract 7,637 relations among 3,185 events (507万 possible pairs).

**Decomposition by relation type:**

| Relation Type | Solution | Count | Rationale |
|---------------|----------|-------|-----------|
| **cross_ref** (mutual reference) | Rules + Code: name similarity ≥0.6 + shared persons | 294 | Deterministic matching |
| **co_person** (shared persons) | Code: cross-chapter events share ≥2 key persons | 867 | Graph algorithm, O(n²) |
| **co_location** (shared location) | Code: shared place + ≥1 person (noise filter) | 542 | Composite constraints |
| **concurrent** (same time) | Code: same BCE year + shared ≥1 person | 173 | Time alignment |
| **sequel** (continuation) | LLM: within-chapter temporal sequence | 1,623 | Semantic understanding |
| **causal** (causation) | LLM: within-chapter cause-effect judgment | 407 | Complex logic reasoning |
| **part_of** (containment) | LLM: part-whole event hierarchy | 107 | Semantic analysis |
| **opposition** (conflict) | LLM: identify opposing parties' actions | 50 | Semantic role labeling |
| **cross-chapter causal** | LLM 2nd-pass: refine auto-generated candidates | 352 | Hybrid: auto-filter then LLM |

**Cost-benefit analysis:**

| Approach | Precision | Recall | Cost | Time |
|----------|-----------|--------|------|------|
| Pure LLM (all 507万 pairs) | 87% | 92% | $41,000 | 11 hours |
| Pure Rules (deterministic only) | 95% | 68% | $50 | 5 minutes |
| **Hybrid (4 auto + 5 LLM)** | **94%** | **89%** | **$380** | **1 hour** |

**Key insight:** Don't use LLM for everything. Use code for structured tasks (100x cheaper), reserve LLM for semantic tasks where rules fail.

#### 5.3 Three Collaboration Patterns

**Pattern 1: Rules → LLM (Filter then Refine)**
```
All event pairs (5.07M)
  ↓ [Rule filter]: shared entity/time/location
Candidates (25K)  ← 99.5% reduction
  ↓ [LLM reasoning]: semantic relation classification
Final relations (7,637)
```

**Pattern 2: LLM → Rules (Generate then Validate)**
```
LLM generates alias candidates
  ↓ [Heuristic rules]
    - Long name must contain short name
    - Character overlap ≥50%
    - Co-occur ≥3 times in same chapter
  ↓ [Auto-confirm]
Safe alias pairs (595)
  ↓ [Human review]
Ambiguous cases (103)
```

**Pattern 3: Rules → Code → LLM (Layered Fallback)**
```python
def infer_event_year(event):
    # Layer 1: Rule-based lookup (exact known events)
    if event.name in KNOWN_EVENTS:
        return KNOWN_EVENTS[event.name]

    # Layer 2: Code constraint reasoning (interval narrowing)
    if event.persons:
        valid_range = [max(p.birth for p in event.persons),
                       min(p.death for p in event.persons)]
        if valid_range[0] <= valid_range[1]:
            return interpolate(valid_range)

    # Layer 3: LLM semantic reasoning (fallback)
    return llm_infer_from_context(event.description)
```

**Coverage:** Rules (40%) + Code constraints (30%) + LLM (25%) + Human (5%)

---

## Part III: The 9-Stage Pipeline

The complete knowledge engineering workflow, from raw text to interactive applications.

### 6. Overview: Four Semantic Layers

```
        ┌─────────────────────────────────────────────┐
  L4    │  Application Semantics                      │  Stage 9
        │  Historical research, contradiction          │
        │  detection, pattern mining                   │
        ├─────────────────────────────────────────────┤
  L3    │  Knowledge Semantics                        │  Stages 6-8
        │  Ontology, inference rules, SKUs             │
        ├─────────────────────────────────────────────┤
  L2    │  Graph Semantics                            │  Stages 3-5
        │  Entities, events, relations, atomic facts   │
        ├─────────────────────────────────────────────┤
  L1    │  Structural Semantics                       │  Stages 1-2
        │  Chapters, paragraphs, sentences, commentary │
        └─────────────────────────────────────────────┘
```

Each layer builds on the previous. No graph semantics without structural semantics. No application semantics without knowledge semantics.

### 7. Stages 1-2: Text Collation & Structural Analysis

**Stage 1: Collation (SKILL_01)**
- **Input:** Multiple text versions from Wikisource, Ctext, etc.
- **Process:** Variant comparison, error correction, establish authoritative edition
- **Output:** Cleaned definitive text (`docs/original_text/`)

**Stage 2: Structural Analysis (SKILL_02)**
- **Process:**
  - Chapter/section segmentation, paragraph numbering (Purple Numbers)
  - Dialogue splitting, rhyme detection
  - Commentary alignment (Pei Yin, Sima Zhen, Zhang Shoujie's three-layer annotations)
  - Sentence-level semantic relations (causation, parallelism, progression)
- **Output:** Structured text with `§1`, `§2` ... paragraph IDs
- **Key innovation:** Purple Numbers (inspired by Doug Engelbart) for precise citation

*Data:* 130 chapters, 577,000 characters, ~12,000 paragraphs numbered

### 8. Stage 3: Entity Construction (18 Types)

**Evolution of the type system:**

| Version | Types | Trigger | Example Change |
|---------|-------|---------|----------------|
| v1.0 | 11 | Initial design | person/place/official/time/dynasty/institution/tribe/artifact/astronomy/mythical/biology |
| v2.1 | 13 | Data revealed "dynasty" conflates 3 concepts | Split: dynasty → dynasty + feudal-state + clan |
| v2.3 | 15 | "Official" mixes appointments and social roles | Split: official → official + identity |
| v2.4 | 16 | "Flora-fauna" renamed for clarity | Rename: flora-fauna → biology |
| v2.5 | 18 | Need to mark numerical quantities | Add: quantity, reference |

**Final 18 types:** person, place, official, time, dynasty, feudal-state, clan, institution, tribe, artifact, document, thought, identity, quantity, biology, astronomy, mythical, event-name

**Workflow:**
1. AI bulk annotation (Claude, temperature=0) → 102,851 initial annotations
2. Chapter-wise reflection (SKILL_03c) → Fix 1,913 errors in R1
3. Type-wise reflection (SKILL_03e) → Migrate 2,235 items from official→identity, 400+ items from institution→law
4. Alias resolution → Merge 595 alias groups (e.g., 刘邦 = 沛公 = 汉王 = 高祖)
5. Disambiguation → Resolve 644 ambiguous short names (e.g., 武王 → 周武王 in ch.4, 秦武王 in ch.5)

**Quality assurance:**
- Text integrity validation: Removing all tags must recover original text byte-for-byte
- Tag symmetry check: All `〖@X〗` open-close pairs must match
- Cross-file reference check: Entities in events must exist in entity index

*Final data:* 15,190 unique entities, 102,851 annotations, 100% text integrity

### 9. Stage 4: Event Extraction (3,197 Events)

**Why LLM for event extraction?**
- Classical Chinese events span multiple paragraphs (e.g., "Feast at Hong Gate" spans 10+ paragraphs)
- Event granularity requires semantic judgment ("Fall of the Six States" = 1 event or 6?)
- Causal relations embedded in narrative structure, not extractable by keywords

**Hybrid approach:**
- **Event extraction:** LLM (semantic understanding required)
- **BCE dating:** Rules (reign period tables + in-office year calculable)
- **Dating validation:** LLM Agent (comprehensive reasonableness judgment)

**Event schema:**
```json
{
  "event_id": "001_003",
  "chapter": "001",
  "name": "黄帝战蚩尤",
  "event_type": "战争",
  "date_display": "约前2700年",
  "date_ce": -2700,
  "date_certainty": "估算",
  "persons": ["@黄帝@", "@蚩尤@"],
  "locations": ["=涿鹿="],
  "description": "黄帝与蚩尤战于涿鹿之野..."
}
```

**Dating convergence (5 rounds):**
- R1: Discover "single-anchor collapse" pattern (66 events in ch.001 all dated -2290, should span -2700 to -2230)
- R2: Discover "certainty undermarking" (43.6% corrections upgrade from "~BCE XXX" → "BCE XXX" with chronicle verification)
- R3: Discover "anchor pollution" (R2 certainty upgrades introduced new errors, validate anchor quality first)
- R4: Cross-chapter validation (same event mentioned in multiple chapters must have consistent dates)
- R5: Final cleanup, converged (<5% correction rate)

*Final data:* 3,197 events, 98.7% with BCE dates, span -2700 to -87

### 10. Stage 5: Relation Discovery (7,637 Relations)

**9 relation types, 2 discovery methods:**

**Auto-computed (code, 4 types):**
1. `cross_ref` (mutual reference): Name similarity + shared persons
2. `co_person`: Cross-chapter events share ≥2 persons
3. `co_location`: Shared place + ≥1 person
4. `concurrent`: Same BCE year + ≥1 person

**LLM-inferred (5 types):**
5. `sequel`: Temporal continuation within chapter
6. `causal`: Cause-effect relation
7. `part_of`: Part-whole hierarchy
8. `opposition`: Conflict between parties
9. *Cross-chapter causal (5 subtypes)*: Auto candidates → LLM refine

**"Subway map" application:** 3,197 events as "stations," 7,637 relations as "transfer connections." Users can navigate history like a metro system.

*Example transfer:*
- Event 007_042 "项羽自刎" (Xiang Yu's suicide) in ch.007
- `cross_ref` → Event 008_087 "项羽之死" (Death of Xiang Yu) in ch.008
- User can "transfer" between chapters to see different narrative perspectives

### 11. Stages 6-9: Ontology, Reasoning, SKU, Applications

**Stage 6: Ontology Construction (SKILL_06)**
- Build class hierarchy from entity vocabulary
- Generate OWL/RDF representations (future work)
- Current: JSON-based taxonomy with inheritance

**Stage 7: Logical Reasoning (SKILL_07)**
- **Inference:** Person birth/death year ranges from event participation constraints
- **Surname reasoning:** Separate surname (姓) vs. clan name (氏) for pre-Qin figures (7 iteration rounds)
- **Anomaly detection:** Single-fact violations of common sense/institution/rules
- **Contradiction mining:** Cross-chapter inconsistencies (e.g., ch.007 says "dozens" killed, ch.008 says "80,000" killed in same battle — 100x discrepancy)

**Stage 8: SKU Construction (SKILL_08)**
- **SKU** = Stock Keeping Unit, borrowed from inventory management
- Three SKU types:
  - **Factual SKU:** Atomic facts (who did what when where)
  - **Procedural SKU:** How-to knowledge (ritual procedures, battle tactics)
  - **Relational SKU:** Entity relations (family trees, alliance networks)

**Stage 9: Application Construction (SKILL_09)**
- **Cognitive-assist reader:** 18-type syntax highlighting, hover commentary, clickable entity index
- **Subway map:** Interactive timeline with 130 lines (chapters) × 3,197 stations (events)
- **Gamification:** SKUs → skill cards, events → plotlines, entities → characters (future work)

---

## Part IV: Lessons & Principles

### 12. Seven Rules for Agentic Ontology

*Ontology 101 stated three fundamental rules. We keep all three and add four more:*

**Rule 0 (Meta-rule): Extract First, Design Later**
- Don't design the perfect ontology upfront. Let AI produce a rough pass, then discover your ontology from the errors.
- *Example:* Started with 11 types, evolved to 18 based on data-driven discoveries.

**Rule 1 (from Ontology 101): There is no one correct way to model a domain**
- Still true. The best ontology depends on your application goals.

**Rule 2 (from Ontology 101): Ontology development is necessarily an iterative process**
- Still true, but now formalized as the **Reflection Loop** with measurable convergence.

**Rule 3 (from Ontology 101): Concepts should be close to objects in your domain of interest**
- Still true. Our 18 entity types map directly to historical text objects, not abstract categories.

**Rule 4 (new): Quality Converges Through Reflection**
- AI output at 90% accuracy + 5 reflection rounds → 97%+ accuracy
- Each round finds fewer errors (exponential decay)
- Stop when marginal return < threshold

**Rule 5 (new): Classification Principles Emerge from Edge Cases**
- Don't define classes from theory. Debug misclassifications, extract the decision rules.
- *Example:* "齐桓公 = specific person (person type)" vs. "吴王 = generic role (official type)" distinction emerged from edge case analysis.

**Rule 6 (new): Separate Source from Interpretation**
- Never modify the original text to add metadata
- Use overlay architecture: `source.md` (immutable) + `aliases.json` + `dates.json` + `relations.json` (mutable)

**Rule 7 (The Iron Rule): Annotation Must Not Alter Source Text**
- Validation: `strip_all_tags(annotated_text) == original_text` (byte-for-byte)
- Any character addition/deletion/change = failure

### 13. Anti-Patterns to Avoid

**❌ Anti-pattern 1: Over-reliance on LLM**
- *Symptom:* Using LLM for all tasks, including simple rule-based ones
- *Consequence:* Cost explosion ($41,000 vs. $380), slow speed, unstable results
- *Example:* Using GPT-4 to check "is event A after event B" when both have BCE dates
  - Wrong: LLM reasoning ($0.01 cost, 1 sec, may error)
  - Right: `year_A > year_B` (code, 0.001 sec, deterministic)

**❌ Anti-pattern 2: Rule Over-engineering**
- *Symptom:* Writing rules for every edge case, rule base balloons to thousands
- *Consequence:* Maintenance hell, poor generalization, high iteration cost
- *Example:* Writing 644 individual rules for 644 ambiguous short names
  - Wrong: 644 hardcoded rules
  - Right: Layered strategy (rule lookup 40% + heuristics 45% + LLM 10% + human 5%)

**❌ Anti-pattern 3: Black-box Pipeline**
- *Symptom:* Each module developed independently, no visibility into intermediate results
- *Consequence:* Hard to debug, error propagation, no attribution of failure
- *Solution:* Output intermediate files (JSON/Markdown) at each stage, support breakpoint resume

**❌ Anti-pattern 4: Blind End-to-End**
- *Symptom:* Trying to solve everything with a single large model
- *Consequence:* Large data requirements (10K+ annotations), high training cost, poor interpretability
- *Our choice:* Modular pipeline + hybrid automation, not end-to-end deep learning

**❌ Anti-pattern 5: Premature Schema Freeze**
- *Symptom:* Designing 30 entity types and 50 properties per type before seeing any data
- *Consequence:* Schema-data mismatch, large-scale rework
- *Right approach:* Minimal viable ontology (4-5 types) → data-driven evolution → stabilize at 15-20 types

### 14. Quality Assurance: Five-Layer Checks

| Layer | Check Type | Tool | Pass Rate Requirement |
|-------|-----------|------|----------------------|
| **L1: Format** | Tag symmetry, text integrity | `lint_markdown.py` | 100% |
| **L2: Type** | Entity type validity | `validate_entity_types.py` | 100% |
| **L3: Cross-reference** | Entity references in events must exist in entity index | `validate_cross_refs.py` | 100% |
| **L4: Constraint** | Date constraints (event year ∈ [person birth, person death]) | `validate_constraints.py` | >95% |
| **L5: Consistency** | Cross-chapter same-event date consistency | Agent global reflection | >98% |

**Lint-first principle:** Run L1-L3 checks before every reflection round. Fix format errors before semantic errors (prevents noise in semantic review).

---

## Part V: From One Book to a Library

### 15. Skills as DNA: Reusable Methodology

**The innovation:** Methods are not buried in code comments or informal notes. They are **explicitly documented as SKILL files** — structured Markdown documents that AI agents can read and execute.

**Two-tier structure:**

**14 Meta-skills (domain-agnostic):**
- `00-META-00`: OTF + JIT + Bootstrap (the meta-meta-skill)
- `00-META-01`: Reflection
- `00-META-02`: Iterative Workflow
- `00-META-03`: Cold Start
- `00-META-04`: Lancet Method
- `00-META-05`: Knowledge as Context Compression
- `00-META-06`: SKILL Optimization and Evolution
- `00-META-07`: Readability (data format design)
- `00-META-08`: Annotation Schema Design
- `00-META-09`: Agent Prompt Engineering
- `00-META-10`: Quality Control
- `00-META-11`: Data Intuition Cultivation
- `00-META-12`: Data Fusion
- `00-META-13`: Skill Transfer

**40 Pipeline skills (domain-specific):**
- `SKILL_01`: Text Collation
- `SKILL_02`: Structural Analysis (a-h: segmentation, commentary, statistics, etc.)
- `SKILL_03`: Entity Construction (a-e: annotation, disambiguation, reflection, etc.)
- `SKILL_04`: Event Construction (a-f: extraction, dating, validation, etc.)
- `SKILL_05`: Relation Construction (a-e: discovery, war events, etc.)
- `SKILL_06`: Ontology Construction
- `SKILL_07`: Logical Reasoning (a-c: birth/death inference, surname reasoning, anomaly detection)
- `SKILL_08`: SKU Construction
- `SKILL_09`: Application Construction (a-b: reader, gamification)

**How AI reads SKILLs:**
- Agent prompt includes: `Read SKILL_XX.md to understand the task methodology`
- SKILL documents contain: error patterns (table format), quality criteria, validation checklists, JSON output schema
- Agent outputs: corrections + newly discovered patterns (auto-append to SKILL in next round)

**Bootstrap loop:**
```
Human executes task → Summarizes as SKILL → Agent reads SKILL and executes
  ↓
Agent discovers new patterns → Auto-updates SKILL → Agent reads updated SKILL
  ↓
Multiple SKILLs share patterns → Extract meta-SKILL → Agent reads meta-SKILL
  ↓
Meta-SKILL applied to new domain → Domain SKILL auto-generated → System self-evolves
```

*Shiji proof:* The 54 SKILL files (14 meta + 40 pipeline) are the project's most valuable output — more reusable than the 15,190 entities or 3,197 events. These SKILLs can guide the next project (*Book of Han*, *Zizhi Tongjian*) with 80-90% method reuse.

### 16. Scaling: From 60万 Characters to 40亿 Characters

**Cost model (optimized, post-learning curve):**

| Target Corpus | Scale | Estimated Cost | Key Adaptations |
|---------------|-------|----------------|----------------|
| **Shiji** (pilot) | 577K characters | $1,000 level (trial & error included) | Method exploration, 54 SKILLs created |
| **Book of Han** (next) | 740K characters | $200-400 (80% method reuse) | Entity types: +2 (era names), prompt tweaking |
| **Twenty-Six Histories** | 40M characters | $50K-100K optimized | Pipeline parallelization, type system expansion |
| **Zizhi Tongjian series** | 6-7M characters | $10K-20K optimized | Annalistic vs. biographical structure, cross-reference to Histories |
| **Four Libraries** (long-term) | 3B characters | $1M-2M (if industrialized) | Multi-genre adaptation, crowd-sourced QA |

**Key insight:** Cost per 100K characters drops exponentially as SKILLs stabilize and automation improves:
- Shiji (first project): ~$1.7/100K chars (exploration cost)
- Book of Han (second project, method reuse): ~$0.3/100K chars
- Steady-state (industrialized): ~$0.05/100K chars

**Not just scale, but depth:** The goal is not mere digitization, but **structured knowledge extraction** enabling:
- Cross-corpus contradiction detection (same event in multiple histories, compare accounts)
- Pattern mining (what institutional factors correlate with dynasty stability?)
- Genealogy reconstruction (auto-generate family trees from scattered textual mentions)

**Vision:** An AI-agent-maintained, continuously evolving knowledge network spanning 3,000 years of Chinese classical texts. Open-source methods (SKILL files), open data (CC BY-NC-SA 4.0), enabling anyone to explore historical wisdom through Q&A, visualization, and inference.

---

## References

- Noy, N.F. and McGuinness, D.L. (2001). *Ontology Development 101: A Guide to Creating Your First Ontology.* Stanford Knowledge Systems Laboratory Technical Report KSL-01-05. [https://protege.stanford.edu/publications/ontology_development/ontology101.pdf](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf)

- Gruber, T.R. (1993). A translation approach to portable ontology specifications. *Knowledge Acquisition*, 5(2), 199-220.

- Bao, J. (2020). The Lancet Method in RegTech Knowledge Extraction (in Chinese). [https://www.sohu.com/a/405212034_634795](https://www.sohu.com/a/405212034_634795)

- The Shiji Knowledge Base project:
  - **Online demo:** [https://baojie.github.io/shiji-kb](https://baojie.github.io/shiji-kb)
  - **Source code:** [https://github.com/baojie/shiji-kb](https://github.com/baojie/shiji-kb)
  - **Method documentation:** 54 SKILL files at `/skills/`
  - **Data:** Licensed under CC BY-NC-SA 4.0

---

## Appendix: Quick Comparison

| Dimension | Wine Ontology (2001) | Shiji KB (2026) |
|-----------|---------------------|-----------------|
| **Domain** | Wine and food pairing | 2,600 years of Chinese history |
| **Source** | Expert knowledge | Raw classical text (577K chars) |
| **Classes** | ~20 (Wine, Winery, Region...) | 18 entity + 11 event + 9 relation types |
| **Instances** | ~100 wines | 15,190 entities, 3,197 events, 7,637 relations |
| **Build time** | Days (by expert in Protégé) | 6 weeks (1 human + AI agents) |
| **Method** | Top-down design | **Bottom-up: AI extract → human reflect → converge** |
| **Representation** | OWL/RDF in `.owl` files | Annotated Markdown + JSON metadata overlays |
| **Iteration** | Informal refinement | **Formalized: 3-phase migration × 5 reflection rounds** |
| **Validation** | Manual review | **Automated: 5-layer quality checks** |
| **Error correction** | N/A (expert-curated) | **12,200+ corrections across 5 rounds, exponential convergence** |
| **Reusability** | Wine ontology for wine domain | **54 SKILL files → 80-90% reusable for other classical texts** |
| **Automation** | N/A | **99% automated after bootstrap (human = exception handler)** |

---

*This document was co-authored by a human ontologist and Claude (Anthropic) based on 6 weeks of collaborative knowledge engineering on 577,000 characters of classical Chinese text. The original Ontology 101 taught a generation to think in classes and slots. We hope this update teaches a new generation to think in **extraction, reflection, and convergence**.*

---

**Status:** Draft, v2.0
**Last updated:** 2026-03-19
**License:** CC BY 4.0
