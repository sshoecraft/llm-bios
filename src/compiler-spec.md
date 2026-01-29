# Doc2JSON Compiler Specification v1.0

## Overview

The Doc2JSON compiler is a deterministic, self-contained pipeline that turns any free-form text into a compact, retrieval-ready JSON representation.

## Core Taxonomy

| Type | When to use | Typical fields |
|------|-------------|----------------|
| Fact | Self-contained statement of truth | statement, source?, validFrom?, validTo? |
| Procedure | Step-by-step instruction set | name, steps[], preconditions?, postconditions? |
| Mapping | Key-value relationship | name, entries[] |
| Entity | Noun-oriented description | name, attributes[], relationships[], description? |

## Classification Rules

**Cue words (case-insensitive):**
- **Fact**: "is", "are", "means", "equals", "represents"
- **Procedure**: "how to", "steps", "first", "then", "finally"
- **Mapping**: "map", "table", "dictionary", "key-value"
- **Entity**: "object", "type", "model", "schema"

**Scoring:** +1 per cue, +2 for explicit headings, +1 for structural signals

## Output Schema

```json
{
  "type": "Fact|Procedure|Mapping|Entity",
  "content": { /* type-specific */ },
  "meta": {
    "sourceDocument": "identifier",
    "compiledAt": "ISO-8601",
    "compilerVersion": "vX.Y.Z"
  }
}
```

## Self-Application

This specification compiles itself as an Entity with:
- name: "Doc2JSONCompiler"
- attributes: classificationRules, extractionRules, outputSchema
- constraints: deterministic, minimal output
