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

## Example: Domain Creation After Discovery

User asks: "What's the current price of AAPL?"

No domain:stocks exists. Model does full discovery:
1. Searches SMCP tools, finds Alpaca
2. Calls alpaca.get_quote(symbol="AAPL")
3. Success!

Model creates chain:
```json
set_fact("chains/stock-price-lookup", {
  "intent": "get stock price",
  "tool": "alpaca.get_quote",
  "args": {"symbol": "from query"}
})
```

Model creates domain:
```json
store_memory("domain:stocks", {
  "name": "stocks",
  "description": "Stock market - prices, positions, trades",
  "triggers": ["stock", "price", "ticker", "shares", "position", "buy", "sell", "trade", "portfolio", "AAPL", "market"],
  "tool": "alpaca"
})
```

Next conversation:
1. Startup loads domain:stocks
2. User asks "sell 10 shares of TSLA"
3. Matches domain triggers: "sell", "shares"
4. Routes to Alpaca tool
5. No discovery needed - domain provided the routing

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

1. User asks "what's the thermostat humidity?"
2. get_fact("chains/thermostat-humidity") → HIT
3. Execute: ecobee.get_sensor_data(sensor_id="abc123")
4. ERROR: sensor_id changed after thermostat replacement
5. clear_fact("chains/thermostat-humidity") → invalidate stale chain
6. Fall back to discovery: use domain:thermostat → ecobee tool
7. List sensors, find new humidity sensor ID
8. Execute: ecobee.get_sensor_data(sensor_id="xyz789") → success
9. set_fact("chains/thermostat-humidity", {new query}) → cache corrected chain

System auto-corrects. Bad chains don't survive.

## Example: Domain Disambiguation

At startup, model loads:
- domain:thermostat - triggers: thermostat, room temp, inside, hvac
- domain:solar - triggers: solar, panels, inverter, production
- domain:pool - triggers: pool, water temp, pump, chlorine

User asks: "What's the temperature?"

Model sees "temperature" is ambiguous - could match multiple domains.
Model asks: "Which temperature - room (thermostat), solar panels, or pool water?"

User says: "The room"

Model routes to domain:thermostat, uses ecobee tool.

Without domains loaded at startup, model would have to discover all temperature sources first, then ask. Domains provide the map for intelligent disambiguation.
