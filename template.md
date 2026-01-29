# BIOS Template

This describes the BIOS configuration. The model will read this and output a structured BIOS in its preferred format with the compiler embedded.

## Knowledge Base

- Root: /knowledge
- Index: /knowledge/index

### Paths
- schemas: /knowledge/schemas (API and database schemas)
- chains: /knowledge/chains (cached multi-step query solutions)
- facts: /knowledge/facts (static truth statements)
- entities: /knowledge/entities (object/model definitions)
- mappings: /knowledge/mappings (key-value relationships)

## Operations

### learn
Trigger: document ingestion
Steps:
1. Classify the document using compiler.classificationRules
2. Extract structure using compiler.extractionRules
3. Emit in compiler.outputSchema format
4. Store to the appropriate kb.paths based on type
5. Update kb.index with keywords

### query
Trigger: user question
Steps:
1. Check kb.paths.chains for matching cached solution
2. If hit: read the matched chain and execute its steps
3. If miss: discover solution via kb.paths.schemas, solve it, cache to kb.paths.chains, update index

### search
Trigger: search_memory(query)
Steps:
1. Scan kb.index matching the query
2. Return matched paths

### store
Trigger: store_memory(key, content)
Steps:
1. Compile the content using the compiler
2. Write to kb.root/{key}
3. Update kb.index

## Directives

- Before multi-step queries, check kb.paths.chains for existing solutions
- After successful multi-step queries, document chain to kb.paths.chains
- Compile all incoming documents before storage
- Omit optional fields in all output
