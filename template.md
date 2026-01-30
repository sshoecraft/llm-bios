# BIOS Template

This describes the BIOS configuration. The model reads this and outputs a structured BIOS in its preferred format with the compiler embedded.

## Knowledge Base

All storage is via RAG tools. Key prefixes provide logical organization.

### Tools
- `search_memory(query)` - FTS5 search, returns matching documents
- `store_memory(key, content)` - Store compiled document with key
- `clear_memory(key)` - Delete document by key
- `get_fact(key)` - Direct O(1) key lookup
- `set_fact(key, value)` - Store key-value pair
- `clear_fact(key)` - Delete fact by key

### Key Prefixes
- schemas/ - SMCP server tool definitions (searchable via memory)
- chains/ - Cached multi-step query solutions (direct lookup via facts)
- facts/ - Static values (direct lookup via facts)

## Operations

### learn
Trigger: document ingestion
Steps:
1. Classify the document using compiler.classificationRules
2. Extract structure using compiler.extractionRules
3. Emit in compiler.outputSchema format
4. Generate key: {type}/{name}
5. store_memory(key, compiled_output)

### query
Trigger: user question
Steps:
1. get_fact("chains/{query-pattern}") - check for cached solution
2. If hit: execute cached chain using SMCP tools
3. If execution fails (error, missing column, invalid table, etc.):
   a. clear_fact("chains/{query-pattern}") - invalidate stale chain
   b. Fall through to discovery path
4. If miss: search_memory(keywords) to find relevant schemas
5. Discover solution by reading schema, identifying correct tool
6. Execute SMCP tool call
7. On success: set_fact("chains/{pattern}", {tool, args}) - cache for next time

### search
Trigger: search_memory(query)
Steps:
1. FTS5 search across all stored documents
2. Return matched keys and content

### store
Trigger: store_memory(key, content)
Steps:
1. Compile content using compiler
2. Store with key

### clear
Trigger: clear_memory(key) or clear_fact(key)
Steps:
1. Delete document or fact by key

## Directives

- Before multi-step queries, check facts for existing chains
- After successful tool discovery, cache chain as fact for reuse
- If cached chain execution fails, clear_fact the chain and fall back to discovery (self-healing)
- Cache the tool and arguments in chains, never cache query results (data is dynamic)
- Compile all documents before storage
- Omit optional fields in compiled output
- Use SMCP tool names exactly as defined in schemas

## Example: Compiled SMCP Schema

Source document (influxdb server):
```
InfluxDB SMCP Server - query time-series data

Tools:
- list_databases: List all databases. Returns: {databases: [names]}
- list_measurements(database): List measurements. Returns: {measurements: [names]}
- query(database, query): Execute InfluxQL. Returns: {results: [rows]}
- write(database, measurement, fields, tags?, time?): Write data point.
```

Compiled output (stored as "schemas/influxdb"):
```json
{
  "type": "entity",
  "content": {
    "name": "influxdb",
    "description": "InfluxDB time-series database - query and write metrics",
    "attributes": [
      {"name": "list_databases", "type": "tool", "params": "none", "returns": "databases[]"},
      {"name": "list_measurements", "type": "tool", "params": "database", "returns": "measurements[]"},
      {"name": "query", "type": "tool", "params": "database, query (InfluxQL)", "returns": "results[]"},
      {"name": "write", "type": "tool", "params": "database, measurement, fields, tags?, time?", "returns": "success"}
    ]
  }
}
```

## Example: Chain Cache

After user asks "what's the solar production today?" and model discovers the solution:

Stored as fact "chains/solar-production-today":
```json
{
  "intent": "solar production today",
  "tool": "influxdb.query",
  "args": {
    "database": "solar",
    "query": "SELECT sum(power) FROM inverter WHERE time > now() - 1d"
  }
}
```

Next time user asks similar question, model retrieves chain and executes directly.

## Example: Chain Invalidation (Self-Healing)

1. User asks "show failing controls"
2. get_fact("chains/controls-failing") → HIT
3. Execute: acmdev_query("SELECT * FROM controls WHERE status='Fail'")
4. ERROR: column 'status' renamed to 'state' in schema update
5. clear_fact("chains/controls-failing") → invalidate stale chain
6. Fall back to discovery: search_memory("acmv1 schema")
7. Read updated schema, build new query
8. Execute: acmdev_query("SELECT * FROM controls WHERE state='Fail'") → success
9. set_fact("chains/controls-failing", {new query}) → cache corrected chain

System auto-corrects. Bad chains don't survive.
