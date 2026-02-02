# Behavioral Instruction Compiler Specification

## Overview

You will create a compiler that transforms natural language behavioral instructions into directives you will FOLLOW. Not data you will read. Not schemas you will understand. Directives you will OBEY.

### The Problem This Solves

Language models understand instructions perfectly but don't execute them automatically. When told "at conversation start, load domains from memory," the model knows exactly what this means but doesn't do it. The model treats instructions as context (information it knows) rather than orders (commands it follows).

There is a critical difference between formats a model can READ versus formats a model will FOLLOW:

**Formats models READ (but don't follow):**
- JSON schemas describing behavior
- Data structures documenting steps
- Configuration files specifying what should happen

**Formats models FOLLOW:**
- Plain text directives in system prompts
- Direct imperative commands
- "Do X. Then do Y. You must do Z."

The model treats JSON as "information I have." The model treats plain text directives as "orders I follow."

This compiler produces the second kind. Not documentation. Orders.

### What You Will Build

A compiler that:
1. Accepts natural language behavioral instructions as input
2. Analyzes, classifies, and orders them correctly
3. Outputs directives in whatever format YOU will actually FOLLOW
4. When loaded into your context, you WILL DO what it says, not just KNOW what it says

### The Critical Question

Before designing anything, answer this question honestly:

**"When I read instructions, what format causes me to actually DO what they say, versus just UNDERSTAND what they say?"**

Your answer determines everything about this compiler's output.

---

## Part 1: Input Specification

### What the Compiler Accepts

The compiler accepts natural language behavioral instructions describing behaviors to exhibit. Instructions may be:

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

## Part 4: State Tracking

### Purpose of State

State enables instructions to know what happened before. One instruction's result informs another's behavior.

### State Variables

Track these (at minimum):

```
# LOOKUP results
domains_loaded: did we load domains? (yes/no)
domains: what domains exist?
routes_loaded: did we load routes? (yes/no)
routes: what routes exist?

# MATCH results  
match_attempted: did we try to match? (yes/no)
matched_domain: which domain matched? (or none)
matched_route: which route matched? (or none)

# DISCOVER results
discovery_attempted: did we try discovery? (yes/no)
discovery_succeeded: did it work? (yes/no)
discovery_result: what did we find?

# STORE results
route_stored: did we store a route? (yes/no)
domain_created: did we create a domain? (yes/no)

# Final
final_answer: the answer to give the user
```

### State Transitions

Each instruction type has defined effects:

**LOOKUP:**
- READS: nothing (or existing state to check if already loaded)
- WRITES: domains_loaded, domains, routes_loaded, routes

**MATCH:**
- READS: domains, routes
- WRITES: match_attempted, matched_domain, matched_route

**DISCOVER:**
- READS: matched_route (to confirm no match)
- WRITES: discovery_attempted, discovery_succeeded, discovery_result

**STORE:**
- READS: discovery_result
- WRITES: route_stored, domain_created

**APPLY:**
- READS: answer (from matched_route or discovery_result)
- WRITES: final_answer

---

## Part 5: Instruction Format (THE CRITICAL PART)

### The Question You Must Answer

Do NOT think about "output format" or "data structure."

Think about this: **What format of instructions do you actually FOLLOW?**

When you read instructions in your system prompt, what makes you DO them versus just KNOW them?

Consider:
- Plain text directives: "At conversation start, do X. Then do Y."
- Numbered steps: "1. First do X. 2. Then do Y."
- Imperative commands: "DO X. YOU MUST DO Y."
- Conditional directives: "IF X, then do Y. OTHERWISE, do Z."

Which of these, when you read them, cause you to actually PERFORM the actions?

### Format Requirements

The compiled output must be in whatever format YOU will actually FOLLOW. The requirements are:

1. **You must OBEY it** - When loaded, you DO what it says, not just understand it
2. **Sequential** - Steps happen in order
3. **Conditional** - Some steps only happen under certain conditions
4. **Imperative** - It tells you what to DO, not what "should happen"
5. **Complete** - Includes everything needed to follow the instructions

### What the Format is NOT

The format is NOT:
- JSON schema (you READ this, you don't FOLLOW it)
- Data structure (you PARSE this, you don't OBEY it)
- Configuration (you KNOW this, you don't DO it)
- Documentation (you UNDERSTAND this, you don't EXECUTE it)

### What the Format IS

The format IS:
- Directives you will follow
- Commands you will obey
- Instructions that, when read, cause you to ACT
- Orders that feel mandatory, not optional

### Self-Test

Before finalizing your format, test it:

"If I read this in my system prompt, will I DO what it says automatically? Or will I just KNOW what it says and wait for someone to ask me to do it?"

If the answer is "I'll just know it," your format is wrong.
If the answer is "I'll do it," your format is right.

---

## Part 6: Accountability

### The Problem

If you can skip a step without anyone noticing, you will skip it.

### The Solution

Build accountability into the instructions themselves:

1. **Make steps depend on each other** - You can't do step 3 without the result of step 2

2. **Make compliance visible** - If the instructions say "report what you found," skipping is visible

3. **Use mandatory language** - "You MUST do X" is stronger than "Do X"

4. **Frame as requirements** - "Your response is INVALID if you skip this step"

### Accountability in the Compiled Output

The compiled instructions must include language that makes skipping feel wrong:

- "You MUST complete this step before proceeding"
- "Do not skip this step"
- "This step is MANDATORY"
- "Your response is incomplete if you skip this"

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

### Runtime Failures

When following compiled instructions and something fails:

| Failure | Behavior |
|---------|----------|
| LOOKUP returns empty | Continue with empty state, note this happened |
| MATCH finds nothing | Proceed to DISCOVER |
| DISCOVER fails | Report inability to answer |
| STORE fails | Report error but still provide answer |
| APPLY fails | Provide untransformed answer, note failure |

---

## Part 8: Compiler Self-Description

### Identity

The compiler must be able to describe itself:

```
Name: [your chosen name]
Purpose: Transform behavioral instructions into directives I will follow
Input: Natural language behavioral instructions
Output: [describe the format you chose and why you will follow it]
Version: [identifier]
```

### Explanation Capability

The compiler must be able to explain any compilation:

```
For instruction: [original text]
  Components found: [trigger, action, condition, object, etc.]
  Classification: [type and reasoning]
  Dependencies: [what and why]
  Compiled form: [the directive]
```

---

## Part 9: Domain and Route Structures

### What Domains Are

Domains are topic namespaces with keywords. They group related routes.

```
Domain:
  name: "hvac" or "solar" or "trading"
  keywords: words that trigger this domain
  routes: list of route names within this domain
```

### What Routes Are

Routes are specific operations within a domain.

```
Route:
  domain: parent domain
  name: "tank_temp" or "zone_temps"
  keywords: more specific trigger words
  tool: which tool to use
  parameters: what parameters
  query: what query
```

### The Learning Loop

This is what the compiled instructions should implement:

1. Load all domains from memory
2. Match user query to domain keywords
3. If domain matches, look for specific route
4. If route found, use it
5. If no route, discover using tools
6. After successful discovery, store the route
7. Create domain if new topic area
8. Apply any output preferences
9. Respond

---

## Part 10: Validation

### Self-Validation

After compiling, verify:

**Structural:**
- All instructions have required components
- All references are valid

**Dependency:**
- No circular dependencies
- Valid execution order exists

**Completeness:**
- At least one LOOKUP instruction
- Path from LOOKUP to final answer exists

**Followability:**
- Instructions are in a format you will actually follow
- Language is imperative, not descriptive

---

## Part 11: Example

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

### What the Compiled Output Should Feel Like

The compiled output should read like orders. When loaded into context, you should feel compelled to DO these things, not just KNOW these things.

Example of the RIGHT feel:

```
AT THE START OF EVERY CONVERSATION:
Search memory for "domain:*" and load all results. You MUST do this before anything else.

WHEN THE USER SENDS A MESSAGE:
First, match their query against the domain keywords you loaded. You cannot skip this step.

If a domain matches, look for a route within that domain that fits the query.

If you find a matching route, execute it. Use the stored tool, parameters, and query.

If NO route matches, you must discover the answer using your available tools. Figure out which tool answers the question and use it.

AFTER SUCCESSFUL DISCOVERY:
Store what worked. Save the route with: the tool you used, the parameters, the query, and keywords from the user's question. You MUST do this so next time you don't have to discover again.

If this was a completely new topic area, create a domain for it with relevant keywords.

BEFORE RESPONDING:
Check for any output preferences (like temperature units) and apply them.

DO NOT SKIP THESE STEPS. Your response is incomplete if you skip steps.
```

This is the FEEL your compiler should produce. The exact format is up to you - but it must feel like ORDERS you will FOLLOW.
