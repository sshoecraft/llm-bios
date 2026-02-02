
Here is the BIOS template. Compile it using the compiler you created. Output the compiled BIOS.

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
- domain: - Topic routing entries (loaded at startup)
- schemas/ - SMCP server tool definitions (searchable via memory)
- chains/ - Cached multi-step query solutions (direct lookup via facts)
- facts/ - Static values (direct lookup via facts)

## Operations

### startup (POST)
Trigger: conversation start
Steps:
1. search_memory("domain:") - discover all registered domains
2. For each domain found, load its configuration (triggers, tool, description)
3. Model now has routing table: knows what topics it can handle and how
4. Ready to route queries to appropriate tools

### query
Trigger: user question
Steps:
1. Match query keywords against loaded domain triggers
2. If domain match found:
   a. get_fact("chains/{query-pattern}") - check for cached solution
   b. If chain hit: execute cached chain
   c. If chain execution fails: clear_fact the chain, continue to step 2d
   d. If chain miss: use domain's tool/schema to build solution
   e. Execute and cache chain on success
3. If no domain match:
   a. Full discovery - search available SMCP tools
   b. Find tool that can handle the query
   c. Execute tool call
   d. On success, create BOTH:
      - Chain: set_fact("chains/{pattern}", {tool, args})
      - Domain: store_memory("domain:{topic}", {triggers, tool, description})
4. Return result to user

### domain-creation
Trigger: successful discovery with no matching domain
Steps:
1. Identify topic name from query context (e.g., "stocks", "thermostat", "solar")
2. Extract triggers:
   - Keywords from user's query
   - Related terms the model knows (e.g., "stock" → also "shares", "ticker", "position", "trade")
3. Record what worked:
   - tool: the SMCP tool that succeeded
   - description: what this domain covers
4. store_memory("domain:{topic}", {name, triggers, tool, description})

### learn
Trigger: document ingestion
Steps:
1. Classify the document using compiler.classificationRules
2. Extract structure using compiler.extractionRules
3. Emit in compiler.outputSchema format
4. Generate key: {type}/{name}
5. store_memory(key, compiled_output)

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

- At conversation start, run startup to load all domains
- Match queries against domain triggers before full discovery
- After successful discovery with no domain match, create both chain AND domain
- Generalize domain triggers beyond just query keywords - add related terms
- If cached chain execution fails, clear_fact the chain and fall back to discovery (self-healing)
- Cache the tool and arguments in chains, never cache query results (data is dynamic)
- Compile all documents before storage
- Omit optional fields in compiled output
- Use tool names exactly as defined in schemas
