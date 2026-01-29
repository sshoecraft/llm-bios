# LLM-BIOS

A self-compiling BIOS system for Large Language Models. The model defines its own knowledge representation format, compiles that specification, and uses it to process all future documents.

## The Problem with Traditional RAG

Current RAG (Retrieval-Augmented Generation) systems work like this:

1. User asks about thermostat
2. Model searches RAG for ecobee API docs
3. Model retrieves schema
4. Model identifies temperature endpoint
5. Model queries the API
6. Model formats response

This has issues:
- **Two-hop latency**: Model fetches schema, then acts
- **Redundant retrieval**: Model may re-fetch schema it already has in context
- **No caching**: Successful query chains aren't remembered
- **Unreliable tool use**: Model decides whether to use tools

## How LLM-BIOS Solves This

LLM-BIOS inverts the RAG approach:

- **BIOS in system prompt** tells model HOW to process queries (never evicted from context)
- **Knowledge base** stores compiled documents in model-native format
- **Chains directory** caches successful multi-step query solutions
- Model checks chains first, only discovers if no cached solution
- After successful discovery, model writes new chain for next time

The key insight: like a computer BIOS lives in ROM, LLM-BIOS lives in the system prompt. It's always there, defining how the model operates.

## Self-Compilation: Why It Matters

The bootstrap process asks the model to:

1. **Choose its preferred format** - Usually JSON, but could be XML, YAML, etc.
2. **Define compiler rules** - Classification, extraction, output schema
3. **Compile its own specification** - The compiler compiles itself

This self-compilation proves the compiler works. If it can compile its own specification correctly, it can compile any document.

The model isn't just following rules we wrote - it's following rules IT wrote, in a format IT chose. This means:
- Optimized for how that specific model processes information
- No impedance mismatch between external structure and model understanding
- The model "owns" its knowledge representation

## Knowledge Base Architecture

```
/knowledge
├── index                # Keyword → path mapping (format per model preference)
├── schemas/             # API and database schemas (compiled)
├── chains/              # Cached multi-step query solutions
├── facts/               # Static truth statements
├── entities/            # Object/model definitions
└── mappings/            # Key-value relationships
```

### Chain Caching

When the model successfully solves a multi-step query:

1. It documents the solution as a "chain"
2. Stores it in `/knowledge/chains/`
3. Next time a similar query comes in, it checks chains first
4. If found, executes the cached solution instead of re-discovering

This turns O(n) discovery into O(1) lookup for repeated query patterns.

## Content Type Taxonomy

The compiler classifies documents into four types:

| Type | Purpose | Cue Words | Example |
|------|---------|-----------|---------|
| **FACT** | Static truth statement | is, are, means, equals | "The solar array is 18kW" |
| **PROCEDURE** | Step-by-step instructions | how to, steps, first, then | "How to query InfluxDB" |
| **MAPPING** | Key-value relationships | map, table, dictionary | "HTTP status codes" |
| **ENTITY** | Object with attributes | object, type, schema, model | "Ecobee API schema" |

Each type has specific extraction rules and output schema optimized for that content structure.

## Bootstrap Process

```bash
# Basic usage (uses shepherd defaults)
./bootstrap.py

# With specific provider
./bootstrap.py --provider anthropic

# Resume interrupted bootstrap
./bootstrap.py --continue

# Force fresh start
./bootstrap.py --force
```

The bootstrap runs 5 stages:

1. **Format Preference** - Ask model what format it prefers
2. **Compiler Rules** - Define classification, extraction, output rules
3. **Self-Compile** - Model outputs compiler spec in its preferred format
4. **Validation** - Verify the spec contains required components
5. **Build BIOS** - Create full BIOS from template with compiler embedded

Output (all in `build/`):
- `compiler.txt` - The self-compiled compiler specification
- `compiler-spec.md` - Human-readable compiler rules
- `bios.txt` - Full BIOS ready for system prompt injection

## Template

The `template.md` file defines your BIOS configuration in plain markdown:
- Knowledge base paths
- Operations (learn, query, search, store)
- Directives

Edit this file to customize paths, add operations, or modify directives. The model reads your description and outputs the structured BIOS in its preferred format.

## Format Agnostic

The bootstrap asks the model its preferred format. Most choose JSON, but if a model prefers XML or YAML, the entire pipeline adapts:

- Compiler spec output in preferred format
- BIOS output in preferred format
- All using marker-based extraction (`---BEGIN BIOS---` / `---END BIOS---`)

We don't impose JSON. We ask the model what works best for it.

## Using the BIOS

Once bootstrapped, inject `build/bios.txt` into your system prompt. The model will:

1. Use the compiler to classify and extract structure from new documents
2. Store compiled documents in the knowledge base
3. Check chains before multi-step queries
4. Cache successful query solutions for reuse

## Key Innovations

1. **Model designs its own format** - Not imposed by developers
2. **Self-compiling specification** - Proves the compiler works
3. **BIOS analogy executed literally** - Lives in system prompt, never evicted
4. **Chain caching** - Successful multi-step queries cached for O(1) reuse
5. **Format agnostic** - Works with whatever format the model prefers

No existing project combines all of these. Traditional RAG imposes structure; LLM-BIOS lets the model define it.

## Requirements

- Python 3.8+
- [Shepherd](https://github.com/sshoecraft/shepherd) CLI for LLM interaction

## License

MIT
