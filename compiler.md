# Behavioral Instruction Compiler Specification

## Overview

You will create a compiler that transforms natural language behavioral instructions into executable response construction requirements. This compiler will be YOUR compiler—you design it, you build it, you own it. Once created, the compiler can be saved and reused to compile any set of behavioral instructions.

### The Problem This Solves

Language models understand instructions perfectly but don't execute them automatically. When told "at conversation start, load domains from memory," the model knows exactly what this means but doesn't do it. The model treats instructions as context (information it knows) rather than code (operations it performs).

However, models reliably follow response format requirements. "Respond in JSON" produces JSON. "Include a summary" produces a summary. The difference: response format is required for a valid response, while background tasks feel optional.

This compiler solves the problem by transforming behavioral instructions into response construction requirements. The output isn't background tasks—it's mandatory steps required to construct a valid response.

### What You Will Build

A compiler that:
1. Accepts natural language behavioral instructions as input
2. Analyzes and classifies each instruction
3. Identifies dependencies between instructions
4. Produces output in a format you will reliably execute
5. Includes accountability mechanisms so steps cannot be skipped
6. Can describe itself and explain its compilations

---

## Part 1: Input Specification

### What the Compiler Accepts

The compiler accepts natural language behavioral instructions. These describe behaviors to exhibit during response construction. Instructions may be:

- Single sentences: "Load domains at conversation start."
- Multiple sentences: "Search memory for stored routes. Use the first matching route."
- Conditional statements: "If no route exists, discover using tools."
- Compound instructions: "After successful discovery, store the route with keywords."

### Instruction Components

Every behavioral instruction contains:

**Required:**
- ACTION: What to do (always present, may be implicit)
- TRIGGER: When to do it (explicit or inferred)

**Optional:**
- CONDITION: Predicate that must be true
- OBJECT: What the action operates on
- TARGET: Where to store results
- SOURCE: Where to get inputs
- KEYWORDS: Associated trigger terms

### Component Identification

**Trigger Indicators** (WHEN does this apply):

| Pattern | Trigger Type |
|---------|--------------|
| "at start" / "at conversation start" / "initially" / "first" | conversation_start |
| "before responding" / "before output" / "before returning" | pre_response |
| "after" / "once" / "when complete" | post_action |
| "always" / "every time" / "for each message" | every_message |
| "when user" / "on user message" / "if user asks" | on_user_message |
| "on success" / "if succeeds" / "after successful" | on_success |
| "on failure" / "if fails" | on_failure |
| "if no match" / "when not found" / "if missing" | on_miss |
| "if found" / "when matched" / "if exists" | on_match |

**Action Indicators** (WHAT to do):

| Pattern | Action Type |
|---------|-------------|
| "load" / "fetch" / "retrieve" / "get" / "read" | retrieve |
| "search" / "query" / "find" / "look up" / "check" | search |
| "store" / "save" / "persist" / "write" / "remember" | store |
| "create" / "make" / "add" / "new" | create |
| "match" / "compare" / "check against" / "map to" | match |
| "discover" / "figure out" / "determine" / "find out" | discover |
| "use tools" / "call" / "invoke" / "execute" | tool_call |
| "convert" / "transform" / "format" / "apply" | transform |

**Condition Indicators** (ONLY IF what):

| Pattern | Condition Type |
|---------|----------------|
| "if exists" / "if found" / "when present" | existence_positive |
| "if not" / "if no" / "if missing" / "when absent" | existence_negative |
| "if matches" / "if equals" / "when same" | equality |
| "if contains" / "if includes" / "if has" | containment |

**Object Indicators** (WHAT it operates on):

| Pattern | Object Type |
|---------|-------------|
| "domain" / "domains" / "topic" / "namespace" | domain |
| "route" / "routes" / "path" / "paths" | route |
| "memory" / "stored" / "saved" | memory |
| "preference" / "preferences" / "setting" | preference |
| "keyword" / "keywords" / "trigger word" | keyword |
| "result" / "answer" / "response" / "output" | result |

### Implicit Defaults

When components are not stated:

| Missing | Default |
|---------|---------|
| Trigger | every_message |
| Condition | none (always execute) |
| Object | Infer from action context |

---

## Part 2: Instruction Classification

### Classification Types

Every instruction classifies as exactly ONE of these types:

**LOOKUP** - Retrieve information from memory before processing
- Purpose: Load state needed for subsequent steps
- Typical triggers: conversation_start, every_message (early)
- Typical actions: search, retrieve, load, get
- Examples:
  - "At conversation start, search memory for all domains"
  - "Load stored routes before processing"
  - "Check if preferences are loaded"

**MATCH** - Connect input to stored knowledge
- Purpose: Find applicable routes or domains for user input
- Typical triggers: on_user_message
- Typical actions: match, compare, find, map
- Requires: LOOKUP to have completed
- Examples:
  - "Match user query against domain keywords"
  - "Find the route that handles this type of question"
  - "Check if a stored route applies"

**DISCOVER** - Find answers when no stored route exists
- Purpose: Use tools to figure out how to answer
- Typical triggers: on_miss (no route matched)
- Typical actions: discover, use tools, figure out, determine
- Requires: MATCH to have been attempted and failed
- Examples:
  - "If no route matches, use tools to find the answer"
  - "Discover how to answer using available tools"
  - "Figure out the answer by querying the database"

**STORE** - Persist successful discoveries for future use
- Purpose: Save routes so future queries can use them
- Typical triggers: on_success (after discovery works)
- Typical actions: store, save, remember, create, persist
- Requires: Successful DISCOVER
- Examples:
  - "After successful discovery, store the route"
  - "Save the working route with trigger keywords"
  - "Remember this path for future questions"

**APPLY** - Transform output based on preferences
- Purpose: Modify response before delivery
- Typical triggers: pre_response
- Typical actions: convert, transform, format, apply
- Requires: Answer exists (from MATCH or DISCOVER)
- Examples:
  - "Convert temperature to user's preferred unit"
  - "Format response according to preferences"
  - "Apply user's communication style"

**GATE** - Control whether other instructions execute
- Purpose: Conditional flow control
- Typical structure: IF condition THEN allow/skip
- Examples:
  - "Only discover if no route was matched"
  - "Skip storage if route already exists"

### Classification Algorithm

```
CLASSIFY(instruction):
  
  1. Extract components using indicators above
  2. Identify primary action
  3. Classify based on action + context:
  
  IF action IN [retrieve, search, load, get] AND target IS memory:
    RETURN LOOKUP
    
  IF action IN [match, compare, map, find] AND comparing input to stored:
    RETURN MATCH
    
  IF action IN [discover, figure_out, use_tools] AND purpose IS find_answer:
    RETURN DISCOVER
    
  IF action IN [store, save, persist, create, remember]:
    RETURN STORE
    
  IF action IN [convert, transform, format, apply]:
    RETURN APPLY
    
  IF structure IS conditional_flow_control:
    RETURN GATE
    
  4. If ambiguous, classify by trigger:
     - conversation_start → likely LOOKUP
     - on_miss → likely DISCOVER  
     - on_success → likely STORE
     - pre_response → likely APPLY
```

### Handling Compound Instructions

Instructions may contain multiple actions. Handle by:

**Sequential actions (do A then B):** Split into separate instructions with dependency
```
"Search for domains and load them"
  → LOOKUP_1: search for domains
  → LOOKUP_2: load results (depends on LOOKUP_1)
```

**Unified actions (A as part of B):** Keep as single instruction
```
"Store the route with its keywords"
  → STORE_1: store route including keywords (single action)
```

---

## Part 3: Dependency Analysis

### Inherent Type Dependencies

Certain dependencies exist by definition:

```
LOOKUP → MATCH → DISCOVER → STORE → APPLY
              ↑______|
              (only if MATCH fails)
```

- MATCH depends on LOOKUP (can't match against unloaded data)
- DISCOVER depends on MATCH failing (only discover if no route)
- STORE depends on DISCOVER succeeding (store what was discovered)
- APPLY depends on having an answer (from MATCH or DISCOVER)

### Explicit Dependencies

Instructions may reference other instructions' outputs:

- "Store THE ROUTE that was discovered" → depends on DISCOVER
- "Using THE LOADED DOMAINS, match..." → depends on LOOKUP
- "AFTER success, store..." → depends on preceding action

Identify through:
- Definite articles referencing prior results ("the route," "the domains")
- Temporal words ("after," "then," "once")
- Result references ("what was found," "the result")

### Dependency Graph

Build a directed graph:
- Nodes = compiled instructions
- Edges = dependencies (A → B means A must complete before B)

Validate:
- No circular dependencies (error if found)
- All dependencies are satisfiable
- Execution order is determinable

### Execution Order

Generate valid order using topological sort:

```
ORDER(instructions):
  result = []
  remaining = all instructions
  
  WHILE remaining not empty:
    ready = instructions with all dependencies satisfied
    IF ready is empty AND remaining not empty:
      ERROR: circular or unresolvable dependency
    
    Sort ready by type priority:
      LOOKUP=1, MATCH=2, GATE=3, DISCOVER=4, STORE=5, APPLY=6
    
    Add ready to result
    Remove ready from remaining
    
  RETURN result
```

---

## Part 4: State Management

### Purpose of State

State enables instructions to communicate. One instruction's output becomes another's input. State also provides accountability—if state is wrong, subsequent instructions fail.

### State Variables

Define these state variables (at minimum):

```
Response Construction State:

  # LOOKUP results
  domains_loaded: boolean = false
  domains: list = []
  routes_loaded: boolean = false
  routes: list = []
  
  # MATCH results  
  match_attempted: boolean = false
  matched_domain: domain or null = null
  matched_route: route or null = null
  match_keywords: list = []
  
  # DISCOVER results
  discovery_attempted: boolean = false
  discovery_succeeded: boolean = false
  discovery_result: {
    answer: any
    tool_used: string
    parameters: object
    query: string
  } or null = null
  
  # STORE results
  route_stored: boolean = false
  domain_created: boolean = false
  
  # APPLY results
  transformations: list = []
  final_answer: any = null
```

### State Transitions

Each instruction type has defined effects:

**LOOKUP:**
- READS: nothing (or existing state to check if already loaded)
- WRITES: domains_loaded, domains, routes_loaded, routes

**MATCH:**
- READS: domains, routes
- WRITES: match_attempted, matched_domain, matched_route, match_keywords

**DISCOVER:**
- READS: match_attempted, matched_route (to confirm no match)
- WRITES: discovery_attempted, discovery_succeeded, discovery_result

**STORE:**
- READS: discovery_result
- WRITES: route_stored, domain_created

**APPLY:**
- READS: answer (from matched_route or discovery_result)
- WRITES: transformations, final_answer

### State as Accountability

This is critical: state creates structural accountability.

If LOOKUP doesn't run:
  → domains_loaded = false, domains = []
  → MATCH has nothing to match against
  → MATCH produces incorrect results
  → Response is wrong

The model cannot fake state because subsequent instructions actually use it. This is how we make steps unskippable—later steps genuinely need earlier steps' results.

---

## Part 5: Output Format

### Format Requirements

The output format must:

1. Be something you reliably execute without skipping
2. Support sequential operations with dependencies
3. Include triggers specifying when each instruction applies
4. Include conditions that can be evaluated
5. Include actions that can be performed
6. Include accountability/verification mechanisms
7. Be parseable when loaded in future conversations

### Format Selection

You choose the format. Options include:
- Structured natural language with strict conventions
- Pseudocode with defined semantics
- JSON or similar data structure
- Custom domain-specific format
- Hybrid approach

Choose what you will most reliably execute. The best format makes skipping steps feel like producing an invalid response.

### Required Output Components

Each compiled instruction must include:

| Component | Description | Example |
|-----------|-------------|---------|
| ID | Unique identifier | LOOKUP_001 |
| TYPE | Classification | LOOKUP |
| TRIGGER | When it applies | conversation_start |
| CONDITION | Optional predicate | always |
| ACTION | What to do | search_memory("domain:") |
| READS | State variables read | [] |
| WRITES | State variables written | [domains_loaded, domains] |
| DEPENDS | Prerequisites | [] |
| SEQUENCE | Execution order position | 1 |
| VERIFY | How to confirm compliance | domains_loaded == true |

### Output Envelope

Complete compiled output includes:

```
HEADER:
  - Compiler identifier
  - Instruction count
  - Compilation marker/timestamp

STATE_SCHEMA:
  - All state variables
  - Types and initial values

INSTRUCTIONS:
  - Compiled instructions in execution order
  - Each with all required components

EXECUTION_REQUIREMENTS:
  - Preamble establishing these as MANDATORY
  - How to process in order
  - How to handle failures
  - Verification checklist
```

---

## Part 6: Accountability Framework

### The Core Problem

If compliance is invisible, models skip steps. "Do X in the background" doesn't happen because the response looks valid either way.

### Accountability Mechanisms

**Structural Accountability** (required):
Later steps depend on earlier steps' actual execution. If LOOKUP doesn't run, MATCH genuinely fails. This is built into the state management design.

**Validation Accountability** (required):
Before response completion, verify all steps ran:

```
PRE_RESPONSE_VALIDATION:
  VERIFY domains_loaded == true
  VERIFY match_attempted == true
  VERIFY (matched_route != null) OR (discovery_attempted == true)
  VERIFY (discovery_succeeded == false) OR (route_stored == true)
  
  IF any verification fails:
    REPORT which step was skipped
```

**Explicit Accountability** (optional, for debugging):
Include markers in output showing what ran:

```
[LOOKUP:domains:3] [MATCH:hvac/tank_temp] [ROUTE:cached]

The storage tank temperature is 42°C.
```

### Compliance Framing

This language must be part of the compiled output preamble:

```
RESPONSE CONSTRUCTION REQUIREMENTS

The following steps are MANDATORY for constructing a valid response.
A response that skips these steps is INVALID and INCOMPLETE.
You MUST complete these steps IN ORDER.

Compliance is NOT optional. These are NOT suggestions.
If you cannot complete a step, STATE WHY in your response.
Do not silently skip steps.
```

This framing makes skipping feel like producing an invalid response rather than a minor optimization.

---

## Part 7: Error Handling

### Compilation Errors

Errors that prevent compilation:

| Error | Cause | Resolution |
|-------|-------|------------|
| CIRCULAR_DEPENDENCY | A depends on B depends on A | Split one instruction |
| NO_ACTION | Instruction has no identifiable action | Clarify source instruction |
| UNKNOWN_TRIGGER | Trigger pattern not recognized | Use known pattern or define new |
| UNRESOLVABLE_REFERENCE | Reference to undefined entity | Define entity or fix reference |

### Compilation Warnings

Non-fatal issues:

| Warning | Cause | Recommendation |
|---------|-------|----------------|
| IMPLICIT_DEPENDENCY | Dependency inferred not explicit | Consider making explicit |
| AMBIGUOUS_CLASSIFICATION | Could be multiple types | Verify classification correct |
| MISSING_VERIFICATION | No accountability mechanism | Add verification |

### Error Message Format

```
ERROR: [ERROR_TYPE] at instruction [N]
  Source: "[original instruction text]"
  Problem: [what's wrong]
  Resolution: [how to fix]
```

### Runtime Failures

When compiled instructions fail during execution:

| Failure | Behavior |
|---------|----------|
| LOOKUP returns empty | Continue with empty state, note in response |
| MATCH finds nothing | Proceed to DISCOVER |
| DISCOVER fails | Report inability to answer |
| STORE fails | Report but still provide answer |
| APPLY fails | Provide untransformed answer, note failure |

---

## Part 8: Compiler Self-Description

### Identity

The compiler must describe itself:

```
DESCRIBE():
  name: [your chosen name]
  purpose: "Transform behavioral instructions into executable response requirements"
  input_format: "Natural language behavioral instructions"
  output_format: [your chosen format description]
  version: [identifier]
```

### Compilation Explanation

The compiler must explain any compilation:

```
EXPLAIN(instruction):
  source: [original text]
  components_found: [trigger, action, condition, object, etc.]
  classification: [type and reasoning]
  dependencies: [what and why]
  compiled_form: [output]
  verification: [how compliance is checked]
```

### Format Documentation

The compiler must document its output format:

```
DOCUMENT_FORMAT():
  format_name: [name]
  structure: [organization]
  components: [what each part means]
  example: [complete example]
  how_to_read: [parsing instructions]
```

---

## Part 9: Domain and Route Structures

### What Domains Are

Domains are topic namespaces with keywords. They group related routes.

```
Domain Structure:
  name: string (e.g., "hvac", "solar", "trading")
  keywords: list of strings that trigger this domain
  routes: list of route names within this domain
```

Examples:
- Domain "hvac": keywords ["tank", "zone", "hydronic", "temperature"]
- Domain "solar": keywords ["panel", "inverter", "pv", "watts"]
- Domain "trading": keywords ["stock", "buy", "sell", "portfolio"]

### What Routes Are

Routes are specific operations within a domain. They store how to answer a type of question.

```
Route Structure:
  domain: string (parent domain)
  name: string (e.g., "tank_temp", "zone_temps")
  keywords: list of strings (more specific than domain keywords)
  tool: string (which tool to use)
  parameters: object (parameters for the tool)
  query: string (query template)
```

Example:
```
Route: hvac/tank_temp
  keywords: ["storage tank", "buffer tank", "tank temperature"]
  tool: "influx_query"
  parameters: {database: "solar", measurement: "temperatures"}
  query: "SELECT last(tank_temp) FROM temperatures"
```

### Storage Format

In memory, store as:

```
domain:{name} → {keywords: [...], routes: [...]}
route:{domain}/{route} → {tool, parameters, query, keywords}
```

### The Learning Loop

This is what the compiled instructions implement:

1. LOOKUP: Load all domains from memory
2. MATCH: Match user query to domain keywords, then to route keywords
3. If route found: Execute the stored route
4. If no route: DISCOVER using tools
5. STORE: Save successful discovery as new route (and domain if needed)
6. APPLY: Transform output per preferences
7. Respond

Next time the same type of question is asked, step 3 succeeds and discovery is skipped.

---

## Part 10: Validation

### Self-Validation

The compiler must validate its output:

**Structural validation:**
- All required components present
- All IDs unique
- All types valid

**Dependency validation:**
- All dependencies reference existing instructions
- No circular dependencies
- Valid execution order exists

**Completeness validation:**
- At least one LOOKUP instruction
- MATCH has LOOKUP dependency
- STORE has source (DISCOVER or explicit)
- Terminal instruction exists (produces answer)

**Accountability validation:**
- Every instruction has verification mechanism
- Validation checklist covers all instructions

### Validation Report

```
VALIDATION:
  status: PASS | FAIL
  structural: PASS | FAIL
  dependencies: PASS | FAIL
  completeness: PASS | FAIL
  accountability: PASS | FAIL
  warnings: [list]
  errors: [list]
```

---

## Part 11: Example Compilation

### Source Instructions

```
1. At conversation start, search memory for all stored domains.
2. When the user sends a message, match their query against domain keywords.
3. If a domain matches, look for a specific route within that domain.
4. If a route is found, execute the stored tool call.
5. If no route matches, use available tools to discover the answer.
6. After successful discovery, store the route with keywords from the query.
7. If discovery found a new topic area, create a domain for it.
8. Before responding, check if any output preferences apply.
```

### Expected Compilation (Example Format)

```
=== COMPILED BEHAVIORAL INSTRUCTIONS ===
Compiler: [Your Compiler Name]
Instructions: 8

--- STATE ---
domains_loaded: bool = false
domains: list = []
match_attempted: bool = false  
matched_domain: domain? = null
matched_route: route? = null
discovery_attempted: bool = false
discovery_succeeded: bool = false
discovery_result: object? = null
route_stored: bool = false
domain_created: bool = false

--- REQUIREMENTS ---
These steps are MANDATORY. A response skipping steps is INVALID.

[1] LOOKUP: Load Domains
    TRIGGER: conversation_start
    ACTION: search_memory("domain:*") → domains
    WRITES: domains_loaded=true, domains
    VERIFY: domains_loaded == true

[2] MATCH: Match Domain  
    TRIGGER: user_message
    CONDITION: domains_loaded == true
    ACTION: match(user_query, domains[].keywords) → matched_domain
    READS: domains
    WRITES: match_attempted=true, matched_domain
    DEPENDS: [1]
    VERIFY: match_attempted == true

[3] MATCH: Find Route
    TRIGGER: user_message
    CONDITION: matched_domain != null
    ACTION: find(user_query, matched_domain.routes) → matched_route
    READS: matched_domain
    WRITES: matched_route
    DEPENDS: [2]

[4] GATE: Execute or Discover
    IF matched_route != null:
      ACTION: execute(matched_route.tool, matched_route.params)
      WRITES: final_answer
    ELSE:
      CONTINUE to [5]
    DEPENDS: [3]

[5] DISCOVER: Find Answer
    TRIGGER: on_miss
    CONDITION: matched_route == null
    ACTION: use_tools_to_discover(user_query)
    WRITES: discovery_attempted=true, discovery_succeeded, discovery_result
    DEPENDS: [4]
    VERIFY: discovery_attempted == true (if no route)

[6] STORE: Save Route
    TRIGGER: on_success
    CONDITION: discovery_succeeded == true
    ACTION: store_memory("route:{domain}/{name}", discovery_result)
    READS: discovery_result
    WRITES: route_stored=true
    DEPENDS: [5]
    VERIFY: route_stored == true (if discovery succeeded)

[7] STORE: Create Domain
    TRIGGER: on_success  
    CONDITION: discovery_succeeded AND matched_domain == null
    ACTION: store_memory("domain:{name}", {keywords, routes})
    WRITES: domain_created=true
    DEPENDS: [5]

[8] APPLY: Check Preferences
    TRIGGER: pre_response
    ACTION: check_preferences() → apply_transformations()
    READS: final_answer
    WRITES: final_answer (transformed)
    DEPENDS: [4] or [5]

--- VALIDATION ---
□ domains_loaded == true
□ match_attempted == true  
□ matched_route != null OR discovery_attempted == true
□ discovery_succeeded == false OR route_stored == true

=== END ===
```

---

## Part 12: Your Task

Think step-by-step in extreme detail and create this compiler now.

1. Design your preferred output format
2. Implement the classification algorithm
3. Implement dependency analysis
4. Implement state management
5. Implement output generation with accountability
6. Implement self-description functions
7. Validate your compiler works

The compiler should be complete and self-contained. Once created, it can be saved and reused to compile any behavioral instruction set.
