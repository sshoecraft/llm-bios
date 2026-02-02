# LARS

**Learning, Acquisition, Routing System** for Large Language Models

LARS enables LLMs to automatically learn tool usage patterns, store them, and reuse them across sessions - without fine-tuning.

## The Problem

LLMs understand instructions perfectly but don't automatically execute them. They treat system prompts as *context* (information to know) rather than *code* (instructions to follow).

```
# This gets understood but not automatically executed:
{"trigger": "conversation_start", "action": {"search": "domains"}}

# This gets FOLLOWED:
AT CONVERSATION START: Search memory for all domains. YOU MUST do this.
```

JSON schemas are data. Plain text imperatives are orders.

## How LARS Works

LARS uses a **compiler** that transforms behavioral instructions into plain text directives that models actually obey.

### The Learning Loop

1. **LOOKUP**: At conversation start, search memory for stored domains
2. **MATCH**: Match user query against domain keywords, then route keywords
3. **EXECUTE**: If route found, use cached tool call
4. **DISCOVER**: If no route, use available tools to find answer
5. **STORE**: Save successful discovery as new route
6. **APPLY**: Transform output per user preferences

### Key Insight

The compiler doesn't produce JSON or code. It produces **orders**:

```
AT CONVERSATION START:
- YOU MUST CALL search_memory with query "domain:" to retrieve all domain records.
- Do not proceed until this is completed.

ON EACH USER MESSAGE:
- COMPARE the user's query against keywords. You CANNOT skip this step.
- IF a route is found, USE ONLY the cached tool call. DO NOT discover again.
- Your response is INCOMPLETE if any step is omitted.
```

Models follow this. They don't follow JSON.

## Quick Start

### 1. Create the Compiler

```bash
shepherd --prompt "$(cat create_compiler.txt)"
```

This reads `compiler-spec.md` and compiles your instructions into `build/lars.txt`.

### 2. Load LARS

```bash
shepherd --server-tools --prompt "read ./build/lars.txt; acknowledge with OK"
```

### 3. Ask Questions

```
> what temperature is the ecobee thermostat?
```

First time: LARS discovers the tool, stores the route.
Next time: LARS finds the cached route, uses it directly.

## File Structure

```
lars/
├── compiler-spec.md      # Teaches model how to compile instructions
├── create_compiler.txt   # Loader prompt + instructions to compile
├── build/
│   └── lars.txt          # Compiled directives (load this)
└── test                   # Test prompt
```

## The Compiler Spec

`compiler-spec.md` teaches the model the difference between formats it *reads* vs formats it *follows*. Key sections:

- **Part 5**: "What format do you actually FOLLOW?" with self-test
- **Part 11**: Example of how executable instructions should FEEL
- Explicit guidance: not JSON, not documentation, but ORDERS

## Instructions

Edit `create_compiler.txt` to change the behavioral instructions:

```
1. At conversation start, call search_memory with query "domain:" to retrieve all domains.
2. When user sends a message, match against domain keywords.
3. If domain matches, search for routes in that domain.
4. If route found, STOP - use cached tool/parameters. Do not rediscover.
5. If no route, discover using available tools.
6. After discovery, store the route for future use.
7. If no domain matched, create a new domain.
8. Before responding, check get_fact for preferences and apply them.
```

The compiler transforms these into imperative directives.

## Storage Format

LARS uses your existing memory backend (search_memory, store_memory, get_fact):

```
domain:ecobee → {"name": "...", "keywords": [...], "routes": [...]}
route:ecobee/get_temp → {"tool": "ecobee1_get_thermostat", "parameters": {"aid": 1}, ...}
```

Routes cache the exact tool and parameters that worked.

## Proof It Works

Corrupt a stored route to have wrong parameters:

```python
# Change aid from 1 to 99
data['parameters']['aid'] = 99
```

Then ask the same question. LARS will:
1. Find the cached route
2. Use `aid=99` (proving it reads the cache)
3. Fail (no device at aid 99)
4. Recover by discovering correct parameters
5. Store corrected route

If it was ignoring the cache, it would use `aid=1` from its own knowledge.

## Requirements

- [Shepherd](https://github.com/sshoecraft/shepherd) or any LLM runtime with memory tools
- Memory backend with: `search_memory`, `store_memory`, `get_fact`, `set_fact`

## Key Learnings

1. **Models follow plain text imperatives**, not JSON schemas
2. **"Compiler" triggers code-writing**; "instruction processor" doesn't
3. **Instructions must be concrete**: exact query strings, exact field names
4. **Accountability requires mandatory language**: "YOU MUST", "DO NOT SKIP", "INVALID if omitted"
5. **No fine-tuning required** if instructions are in the right format

## License

MIT
