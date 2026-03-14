# Agentic Ontology 101: A Guide to Building Your First Knowledge Graph with AI

**Jie Bao, with Claude (Anthropic)**

*Based on the Shiji Knowledge Base project: 130 chapters, 570,000 characters, 18 entity types, 98,000+ annotations, built in 6 weeks by one person + AI agents.*

> This document parallels and updates Noy & McGuinness's classic *"Ontology Development 101: A Guide to Creating Your First Ontology"* (Stanford, 2001) for the age of AI agents. Where Ontology 101 taught humans to design ontologies top-down using Protege, this guide teaches humans to *grow* ontologies bottom-up with AI, using a real 570,000-character classical Chinese text as running example.

---

## 1. Why Build an Ontology with AI Agents?

Noy & McGuinness (2001) listed five reasons to develop an ontology:

1. To share common understanding of information structure
2. To enable reuse of domain knowledge
3. To make domain assumptions explicit
4. To separate domain knowledge from operational knowledge
5. To analyze domain knowledge

All five remain valid. But the landscape has changed fundamentally:

**What's different in 2026:**

| | Ontology 101 (2001) | Agentic Ontology 101 (2026) |
|--|---------------------|---------------------------|
| Who designs | Human expert with Protege | Human + AI agent collaboration |
| Starting point | Blank schema, top-down | Raw text, bottom-up extraction |
| Scale | Dozens of classes, hundreds of instances | Thousands of classes, tens of thousands of instances |
| Iteration speed | Weeks per revision | Hours per revision |
| Error rate | Low (human-curated) | High initial (AI-generated), converging through reflection |
| Primary bottleneck | Expert time for design | Quality control of AI output |

**The core shift:** In 2001, the hard part was *designing* the ontology. In 2026, the hard part is *curating* the AI-extracted ontology. The design emerges from the data.

### About This Guide

We build on our experience creating a knowledge base from Sima Qian's *Records of the Grand Historian* (《史记》, c. 94 BCE) -- 130 chapters, 570,000 characters of classical Chinese. The project produced:

- 18 entity types with ~98,000 annotations
- 3,185 historical events with BCE dating
- 7,637 event relations (4 auto-computed + 5 LLM-inferred types)
- 3,600+ person entities with alias resolution (586 alias groups)
- All built by one person + Claude in approximately 120 hours + ~3 billion tokens

We use this project as our running example, the way Ontology 101 used wine and food.

---

## 2. What Is in an Agentic Ontology?

Ontology 101 defined an ontology as **classes**, **slots** (properties), **facets** (constraints), and **instances**. This remains true, but in practice an agentic ontology has a different emphasis:

| Component | Ontology 101 | Agentic Ontology |
|-----------|-------------|-----------------|
| **Classes** | Designed first, stable | Emerge from data, evolve (11 → 18 types over 6 weeks) |
| **Instances** | Filled in last | Extracted first (by AI), drive class refinement |
| **Properties** | Defined as slots with facets | Discovered through relation extraction |
| **Constraints** | Formal axioms in OWL/DL | Operational rules enforced by validation scripts |
| **Knowledge base** | Separate from ontology | Inseparable -- the annotated text *is* the knowledge base |

### The Annotation-as-Ontology Pattern

In our project, the ontology is not a separate `.owl` file -- it is *embedded in the source text* as inline annotations:

```
〖@刘邦〗起〖=沛〗，〖;丞相〗〖@萧何〗佐之。
(person)  (place)  (official)(person)
```

Each annotation marker (`〖@〗` for person, `〖=〗` for place, etc.) is effectively a class declaration. The annotated word is an instance. The text itself provides context that serves as implicit properties and relations.

This is radically different from Ontology 101's approach of defining classes in a GUI tool, then manually creating instances. Here, the instances come first (extracted by AI from text), and the class system grows to accommodate them.

---

## 3. A New Knowledge-Engineering Methodology

Ontology 101 proposed a 7-step process:

1. Determine the domain and scope
2. Consider reusing existing ontologies
3. Enumerate important terms
4. Define the classes and class hierarchy
5. Define the properties of classes (slots)
6. Define the facets of the slots
7. Create instances

We propose a different 7-step process for agentic ontology development:

### Step 1. Start with Raw Text and a Rough Type System

**Ontology 101 said:** "Determine the domain and scope" by listing competency questions.

**Agentic approach:** Start with the actual text corpus and a minimal, imperfect type system. Don't try to get the types right -- you will refine them later.

*Shiji example:* We started with 11 entity types borrowed from standard NER categories (person, place, time, official, dynasty, institution, tribe, artifact, astronomy, mythical, flora-fauna). This was deliberately rough. We knew "dynasty" was too broad (it conflated Qin-the-state with Qin-the-dynasty with Liu-the-clan), but we started anyway.

**Rule 1:** *Don't design -- extract. Let the AI annotate first, then see what categories emerge from the data.*

**Rule 2 (from Ontology 101, still valid):** *There is no one correct way to model a domain. The best solution depends on what you plan to do with it.*

### Step 2. AI Bulk Extraction (The "90% Pass")

**Ontology 101 said:** "Enumerate important terms" by hand.

**Agentic approach:** Have the AI annotate the entire corpus in one pass. Accept ~90% accuracy. The remaining 10% is where the real ontology design happens.

*Shiji example:* Claude annotated all 130 chapters in batches of 5-10, producing ~80,000 annotations. Each chapter took about 2-3 minutes of AI time. The prompt specified the 11 entity types with examples. We used `temperature=0` for consistency.

```python
SYSTEM_PROMPT = """You are a 《史记》 annotation expert.
Use 18 entity types: 〖@person〗 〖=place〗 〖;official〗 ...
Tag noun usages only. Skip verbs/adjectives/metaphors.
Output Markdown directly, no explanations."""
```

**Rule 3:** *AI annotation at 90% accuracy is more valuable than human annotation at 99% accuracy, because you get it 100x faster and can iterate.*

### Step 3. Validate and Discover Type Boundaries

**Ontology 101 said:** "Define the classes and class hierarchy."

**Agentic approach:** Don't define classes from theory. Instead, validate the AI output and discover where your type boundaries are wrong.

*Shiji example:* After bulk annotation, we ran `validate_tagging.py` (text integrity: does removing all tags recover the original text?) and `lint_markdown.py` (structural: unclosed tags, empty annotations). The results revealed:

- "Dynasty" (`〖&〗`) was being used for three different things: political entities (Han dynasty), feudal states (State of Qi), and blood clans (Liu clan)
- "Official" (`〖;〗`) mixed formal appointments (丞相 Chancellor) with social roles (天子 Son of Heaven)
- Many person names were actually titles (齐桓公 Duke Huan of Qi = specific person, not a title)

Each discovery led to a type split or merge:

```
v1.0  dynasty (朝代)           → v2.1  feudal-state (邦国) + clan (氏族)
v1.0  official (官职)          → v2.3  official + identity (身份)
v1.0  flora-fauna (动植物)     → v2.4  biology (生物, renamed + new marker)
v2.5  (new)                    → v2.5  quantity (数量)
```

**Rule 4:** *Type boundaries are discovered, not designed. If annotators (human or AI) consistently confuse two categories, the categories are wrong.*

### Step 4. Iterative Reflection (The Agent Loop)

**Ontology 101 said:** "Ontology development is necessarily an iterative process."

**Agentic approach:** Formalize iteration as an *agent reflection loop*: extract → review → correct → re-extract.

This is the most important methodological innovation. In Ontology 101, iteration was informal ("revise and refine"). In agentic ontology engineering, it is a structured pipeline:

```
┌─────────────────────────────────────────────┐
│  Phase 1: Auto-Replace                      │
│  High-confidence items from wordlist         │
│  (e.g., 天子 is ALWAYS identity, not official) │
├─────────────────────────────────────────────┤
│  Phase 2: Context Review                    │
│  Ambiguous items → TSV report with context   │
│  Human/LLM fills decision column            │
├─────────────────────────────────────────────┤
│  Phase 3: New Term Scan                     │
│  Search untagged text for missing instances  │
│  Expand the wordlist                         │
└─────────────────────────────────────────────┘
         ↓ repeat for each type ↓
```

*Shiji example:* We ran this loop for every major type migration:
- Official → Identity: 2,235 corrections
- Dynasty → Feudal-state + Clan: ~6,100 corrections
- Broken tag repair: 18,302 nested tags + 134 cross-sentence tags
- Cumulative: ~12,200 corrections across all rounds

Each round converges. Event date reflection showed this clearly:

| Round | Corrections | Chapters affected |
|-------|-------------|-------------------|
| 1     | 1,010       | 118/130           |
| 2     | 431         | 105/130           |
| 3     | 465         | 70/130            |
| 4     | 167         | 68/130            |
| 5     | 46          | 28/130            |

**Rule 5:** *Quality converges through repeated reflection. Each round finds fewer errors. Stop when the marginal return is too low.*

### Step 5. Classify Instances, Not Classes

**Ontology 101 said:** "Define the properties of classes (slots)." For example, Wine has slots for `color`, `body`, `flavor`.

**Agentic approach:** Instead of defining abstract slot schemas, focus on *classification principles* that resolve ambiguous instances.

*Shiji example:* Rather than defining slots like `ruler.reign_start` in a schema editor, we discovered classification rules from edge cases:

| Principle | Rule | Example |
|-----------|------|---------|
| Specific person → person name | State + posthumous name + title = one specific person | `〖@齐桓公〗` (Duke Huan of Qi) |
| Generic role → official | State + title (no posthumous name) = can refer to multiple people | `〖;吴王〗` (King of Wu) |
| Formal appointment → official | Court-appointed positions | `〖;丞相〗` (Chancellor) |
| Social role → identity | Non-appointed social status | `〖#天子〗` (Son of Heaven) |
| Tag integrity | One tag = one entity, no crossing punctuation | ✓ `〖*驷马〗`  ✗ `〖*驷〗马〖*，迎...〗` |

These principles emerged from debugging misclassifications -- they were not designed in advance.

**Rule 6:** *Classification principles are discovered from edge cases, not designed from definitions. The hard cases teach you what your ontology really means.*

### Step 6. Separate Source from Interpretation

**Ontology 101 said:** "Define the facets of the slots" (cardinality, value type, etc.)

**Agentic approach:** Strictly separate the source text (annotated original) from interpretive metadata (disambiguation, dating, relations). Never modify the source to add interpretation.

*Shiji example:* We enforce this with the "metadata overlay" architecture:

```
Source layer (immutable):     chapter_md/*.tagged.md
                                ↓ read-only ↓
Metadata layer (mutable):    entity_aliases.json      (刘邦 = 沛公 = 汉王)
                             disambiguation_map.json   (武王 → 周武王 in ch.4)
                             year_ce_map.json          (元光六年 → 129 BCE)
                             event_relations.json      (7,637 cross-references)
```

The rendering engine merges these layers at display time. The source text never changes to accommodate disambiguation or dating -- those are overlays.

**Rule 7 (the iron rule):** *Annotation may only add markup characters. It must never add, delete, or change any character of the original text. Validation: stripping all markup from the annotated file must yield the original file byte-for-byte.*

### Step 7. Build Downstream Knowledge Structures

**Ontology 101 said:** "Create instances."

**Agentic approach:** Once the type system stabilizes and annotations are clean, build higher-order structures: event extraction, relation inference, genealogies, timelines.

*Shiji example:* From the annotated text we built:

| Structure | Method | Scale |
|-----------|--------|-------|
| Entity index | Regex extraction + alias merging | 11,680 entities |
| Event index | LLM extraction per chapter | 3,185 events |
| Event relations | Auto (co-person, co-location, concurrent, cross-ref) + LLM (causal, sequel, part_of, opposition) | 7,637 relations |
| Person genealogy | LLM extraction from 本纪/世家 | 868 rulers, 254 family relations |
| Chronology | Table parsing + reign period database | 3,051 BCE-dated events |

Each downstream structure depends on the annotation quality from Steps 2-6. This is why the reflection loop (Step 4) matters so much -- errors in entity annotation propagate to event extraction, relation inference, and everything downstream.

---

## 4. Three Fundamental Rules (Revisited)

Ontology 101 stated three fundamental rules:

> *1) There is no one correct way to model a domain.*
> *2) Ontology development is necessarily an iterative process.*
> *3) Concepts should be close to objects in your domain of interest.*

All three still hold. We add four more:

**4) Extract first, design later.** Let AI produce a rough pass, then discover your ontology from the errors.

**5) Quality converges through reflection.** Each round of review finds fewer problems. The ontology stabilizes.

**6) Classification principles emerge from edge cases.** The hard instances teach you what your categories mean.

**7) Never modify the source.** Interpretation belongs in a metadata overlay, not in the annotated text.

---

## 5. Toolchain: From Protege to Scripts + LLM

Ontology 101 used Protege-2000 as the primary tool. The agentic approach uses a different stack:

| Function | Ontology 101 (2001) | Agentic (2026) |
|----------|--------------------|-----------------|
| Schema design | Protege GUI | Evolves in code (Python regex patterns + JSON wordlists) |
| Instance creation | Protege forms | LLM bulk annotation (Claude, temperature=0) |
| Validation | Chimaera | Custom scripts (`lint_markdown.py`, `validate_tagging.py`) |
| Querying | SPARQL / DL reasoner | Python scripts + JSON indexes |
| Visualization | Protege class browser | HTML rendering + metro map |
| Collaboration | Shared `.owl` files | Git (text-based annotation is diff-friendly) |

**Key advantage of text-based annotation:** Because our ontology is embedded as lightweight markers in plain text (not stored in a binary `.owl` database), every change is visible in `git diff`. This makes collaboration, review, and rollback trivial.

---

## 6. Common Pitfalls

### Pitfalls from Ontology 101 (still relevant)

- **Overcommitting to a hierarchy too early.** In an agentic workflow, this manifests as designing 30 entity types before seeing any data. Start with 10, let the data show you what's missing.
- **Confusing classes with instances.** "齐桓公 (Duke Huan of Qi)" is an instance of Person, not a subclass.

### New pitfalls in agentic ontology engineering

- **Trusting AI output without validation.** AI annotation at 90% accuracy means ~10,000 errors in a 100,000-annotation corpus. You *must* have automated quality checks.
- **Migrating formats without testing.** Our v2.0 symbol migration introduced 18,302 nested tag errors (`〖〖=X〗...〖〗Y〗`) that persisted for weeks until discovered. Always run `validate_tagging.py` after any batch transformation.
- **Tag boundary violations.** AI sometimes swallows adjacent text into a tag: `〖;陶青为〗` should be `〖@陶青〗为`. Automated scanning for tags containing sentence punctuation catches these.
- **Losing original text.** Our AI initially dropped the character "唯" from "唯禹之功为大" during annotation. The iron rule (Step 6, Rule 7) and byte-level validation prevent this.

---

## 7. Comparison: Wine Ontology vs. Shiji Knowledge Base

| Dimension | Wine Ontology (2001) | Shiji KB (2026) |
|-----------|---------------------|-----------------|
| Domain | Wine and food pairing | Chinese historical text (2,100 years of history) |
| Source | Expert knowledge | Raw classical Chinese text (570K characters) |
| Classes | ~20 (Wine, Winery, Region, Grape...) | 18 entity types + 11 event types + 9 relation types |
| Instances | ~100 wines | 11,680 entities, 3,185 events |
| Relations | ~5 (produces, hasColor, locatedIn...) | 7,637 event relations, 4,500+ person relations |
| Build time | Days (by expert) | 6 weeks (1 person + AI) |
| Build method | Top-down in Protege | Bottom-up: AI extract → human reflect → converge |
| Representation | OWL/RDF | Annotated Markdown + JSON metadata |
| Iteration | Informal | Formalized 3-phase migration pipeline |
| Validation | Manual review | Automated: lint + text integrity + cross-validation |

---

## 8. Lessons Learned

### What worked

1. **"先粗后细" (rough first, refine later).** AI-annotating all 130 chapters before perfecting the type system was the right call. We could see the whole landscape before deciding where the boundaries should be.

2. **Content-style separation.** Lightweight text markers (`〖@X〗`) kept the annotated text human-readable and git-diffable. This was vastly superior to our v1 attempt with HTML `<span>` tags.

3. **Metadata overlay architecture.** Disambiguation, dating, and alias resolution as external JSON files meant we never corrupted the source annotations.

4. **Three-phase migration.** Every type change followed the same protocol (auto-replace → context review → new scan), making large-scale restructuring safe and repeatable.

### What we'd do differently

1. **Run `validate_tagging.py` from day one.** We discovered the "唯" character loss months after it happened. Byte-level validation should be part of every annotation batch.

2. **Freeze the symbol system earlier.** Our v2.0 migration (changing markup symbols) introduced 18,302 bugs. If we'd chosen the right symbols initially, we'd have saved a week of cleanup.

3. **Start with more types.** 11 was too few. Starting with 15-18 would have avoided the painful dynasty → feudal-state + clan split.

---

## 9. Future Directions

- **Agentic reflection at scale.** Our 3-phase pipeline could be fully automated with LLM judges reviewing each phase's output, potentially eliminating the human review step for high-confidence cases.

- **Cross-corpus ontology transfer.** Can the 18-type system developed for *Records of the Grand Historian* be reused for other Chinese historical texts (*Book of Han*, *Zuo Zhuan*, *Zizhi Tongjian*)? Our token-based annotation system is designed to be portable.

- **Formal ontology grounding.** Our current system uses JSON and regex. A future step would be generating OWL/RDF representations from the annotation data, enabling SPARQL queries and formal reasoning.

- **Continuous learning.** As new annotations are added, the type system should continue to evolve. The reflection pipeline could run continuously, proposing type splits/merges based on annotation statistics.

---

## References

- Noy, N.F. and McGuinness, D.L. (2001). *Ontology Development 101: A Guide to Creating Your First Ontology.* Stanford Knowledge Systems Laboratory Technical Report KSL-01-05.
- Gruber, T.R. (1993). A translation approach to portable ontology specifications. *Knowledge Acquisition*, 5(2), 199-220.
- The Shiji Knowledge Base project: source code and data at `github.com/baojie/shiji-kb` (forthcoming).

---

*This document was co-authored by a human ontologist and Claude (Anthropic) based on 6 weeks of collaborative ontology engineering on the Records of the Grand Historian. The original Ontology 101 taught a generation of knowledge engineers to think in classes and slots. We hope this update teaches a new generation to think in extraction, reflection, and convergence.*
