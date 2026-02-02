# Behavioral Instruction Compiler
# Implements the specification in compiler-spec.md
# Generates imperative directives that the model will follow.

import re
from collections import defaultdict
from typing import List, Dict, Set

# ---------------------------------------------------------------------------
# Patterns from spec (simplified)
TRIGGER_PATTERNS = {
    r"\b(at start|conversation start|initially|first)\b": "conversation_start",
    r"\b(before responding|before output|before returning)\b": "pre_response",
    r"\b(after|once|when complete)\b": "post_action",
    r"\b(always|every time|for each message)\b": "every_message",
    r"\b(on user message|when user|if user asks)\b": "on_user_message",
    r"\b(on success|if succeeds|after successful)\b": "on_success",
    r"\b(on failure|if fails)\b": "on_failure",
    r"\b(if no match|when not found|if missing)\b": "on_miss",
    r"\b(if found|when matched|if exists)\b": "on_match"
}

ACTION_PATTERNS = {
    r"\\b(load|fetch|retrieve|get|read)\\b": "retrieve",
    r"\\b(search|query|find|look up|check)\\b": "search",
    r"\\b(store|save|persist|write|remember)\\b": "store",
    r"\\b(create|make|add|new)\\b": "create",
    r"\\b(match|compare|check against|map to)\\b": "match",
    r"\\b(discover|figure out|get out?|determine)\\b": "discover",
    r"\\b(use tools|call|invoke|execute)\\b": "tool_call",
    r"\\b(convert|transform|format|apply)\\b": "transform"
}

CONDITION_PATTERNS = {
    r"\bif exists\b|\bwhen present\b": "existence_positive",
    r"\bif not\b|\bif no\b|\bif missing\b|\bwhen absent\b": "existence_negative",
    r"\bif matches?\b|equals?": "equality",
    r"\bcontains?|includes?|has\b": "containment"
}

OBJECT_PATTERNS = {
    r"\bdomain|topic|namespace\b": "domain",
    r"\broute|path|paths\b": "route",
    r"\bmemory|stored|saved\b": "memory",
    r"\bpreference|settings?\b": "preference",
    r"\bkeyword|trigger word\b": "keyword",
    r"\bresult|answer|response|output\b": "result"
}

# ---------------------------------------------------------------------------
def find_first_match(patterns: Dict[str, str], text: str) -> str:
    for pat, typ in patterns.items():
        if re.search(pat, text, re.IGNORECASE):
            return typ
    return ""

def extract_components(instruction: str) -> Dict[str, str]:
    comp = {
        "trigger": find_first_match(TRIGGER_PATTERNS, instruction),
        "action":  find_first_match(ACTION_PATTERNS, instruction),
        "condition": find_first_match(CONDITION_PATTERNS, instruction),
        "object":   find_first_match(OBJECT_PATTERNS, instruction)
    }
    if not comp["trigger"]:
        comp["trigger"] = "every_message"
    return comp

# ---------------------------------------------------------------------------
def classify_instruction(comp: Dict[str, str]) -> str:
    action = comp["action"]
    obj = comp["object"]
    trigger = comp["trigger"]
    if action in ["retrieve", "search", "load", "get"] and obj == "memory":
        return "LOOKUP"
    if action == "match" or (action in ["compare", "map"] and obj in ["domain", "route"]):
        return "MATCH"
    if action in ["discover", "tool_call"]:
        return "DISCOVER"
    if action in ["store", "create"]:
        return "STORE"
    if action == "transform":
        return "APPLY"
    if comp["condition"]:
        return "GATE"
    # fallback based on trigger
    mapping = {
        "conversation_start": "LOOKUP",
        "on_miss": "DISCOVER",
        "on_success": "STORE",
        "pre_response": "APPLY"
    }
    return mapping.get(trigger, "UNKNOWN")

# ---------------------------------------------------------------------------
def split_compound(text: str) -> List[str]:
    parts = re.split(r"[;,.]\s*", text)
    return [p.strip() for p in parts if p.strip()]

TYPE_DEPENDENCIES = {
    "LOOKUP": [],
    "MATCH": ["LOOKUP"],
    "DISCOVER": ["MATCH"],
    "STORE": ["DISCOVER"],
    "APPLY": ["MATCH", "DISCOVER"],
    "GATE": []
}

PRIORITY = {"LOOKUP":1, "MATCH":2, "GATE":3, "DISCOVER":4, "STORE":5, "APPLY":6, "UNKNOWN":7}

class BehavioralCompiler:
    def __init__(self, raw_text: str):
        self.raw_instructions = split_compound(raw_text)
        self.parsed: List[Dict] = []  # each dict holds id, original, components, type
        self.graph: Dict[int, Set[int]] = defaultdict(set)
        self.id_counter = 0

    def parse(self):
        for instr in self.raw_instructions:
            comp = extract_components(instr)
            typ = classify_instruction(comp)
            entry = {
                "id": self.id_counter,
                "original": instr,
                "components": comp,
                "type": typ
            }
            self.parsed.append(entry)
            self.id_counter += 1

    def build_dependency_graph(self):
        # map type -> ids (preserve order)
        type_to_ids = defaultdict(list)
        for e in self.parsed:
            type_to_ids[e["type"]].append(e["id"])
        # explicit type dependencies (only earlier nodes considered)
        for e in self.parsed:
            cur = e["id"]
            needed = TYPE_DEPENDENCIES.get(e["type"], [])
            for dep_type in needed:
                for dep_id in type_to_ids.get(dep_type, []):
                    if dep_id < cur:
                        self.graph[cur].add(dep_id)
        # sequential order to keep original flow
        for i in range(1, len(self.parsed)):
            self.graph[i].add(i-1)

    def topological_sort(self) -> List[int]:
        indeg = {i:0 for i in range(len(self.parsed))}
        for node, deps in self.graph.items():
            indeg[node] += len(deps)
        ready = [i for i,d in indeg.items() if d==0]
        order = []
        while ready:
            # sort by priority then original index
            ready.sort(key=lambda x: (PRIORITY.get(self.parsed[x]["type"], 99), x))
            n = ready.pop(0)
            order.append(n)
            for nxt in range(len(self.parsed)):
                if n in self.graph[nxt]:
                    indeg[nxt] -= 1
                    self.graph[nxt].remove(n)
                    if indeg[nxt]==0:
                        ready.append(nxt)
        if len(order)!=len(self.parsed):
            raise ValueError("Circular dependency detected")
        return order

    def generate_directive(self, entry: Dict) -> str:
        typ = entry["type"]
        comp = entry["components"]
        obj = comp.get('object','') or 'data'
        if typ == "LOOKUP":
            return ("AT THE START OF EVERY CONVERSATION:\n"
                    f"Search memory for \"{obj}:*\" and load all results. YOU MUST do this before anything else.")
        if typ == "MATCH":
            return ("WHEN THE USER SENDS A MESSAGE:\n"
                    f"First, match their query against the loaded {obj} keywords. DO NOT SKIP THIS STEP.")
        if typ == "DISCOVER":
            return ("IF NO MATCH IS FOUND:\n"
                    "You MUST DISCOVER the answer using available tools. Determine which tool fits and invoke it.")
        if typ == "STORE":
            return ("AFTER SUCCESSFUL DISCOVERY:\n"
                    "Store what worked. Save the route with its tool, parameters, query, and keywords from the user's question. THIS STEP IS MANDATORY.")
        if typ == "APPLY":
            return ("BEFORE RESPONDING:\n"
                    "Check for any output preferences (e.g., units) and apply them to the answer. DO NOT SKIP.")
        if typ == "GATE":
            cond = comp.get('condition','some condition')
            return f"IF {cond.upper()}:\nProceed with next step. OTHERWISE, skip."
        return f"# UNKNOWN INSTRUCTION: {entry['original']}"

    def compile(self) -> str:
        self.parse()
        self.build_dependency_graph()
        order = self.topological_sort()
        directives = [self.generate_directive(self.parsed[i]) for i in order]
        return "\n\n".join(directives)

# ---------------------------------------------------------------------------
SELF_DESCRIPTION = {
    "Name": "BehavioralInstructionCompiler",
    "Purpose": "Transform behavioral instructions into imperative directives that the model will follow.",
    "Input": "Natural language behavioral instructions (plain text).",
    "Output": "Plain‑text ordered imperative steps using mandatory language. The format is a series of commands the model must execute, not merely data it knows.",
    "Version": "1.0.0"
}

def describe_self() -> str:
    return "\n".join([f"{k}: {v}" for k,v in SELF_DESCRIPTION.items()])

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    example = """
    At conversation start, search memory for all stored domains.
    When the user sends a message, match their query against domain keywords.
    If a domain matches, look for a specific route within that domain.
    If a route is found, execute the stored tool call.
    If no route matches, use available tools to discover the answer.
    After successful discovery, store the route with keywords from the query.
    If discovery found a new topic area, create a domain for it.
    Before responding, check if any output preferences apply.
    """
    compiler = BehavioralCompiler(example)
    print(describe_self())
    print("\n--- Compiled Directives ---\n")
    print(compiler.compile())
