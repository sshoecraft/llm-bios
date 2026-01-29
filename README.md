# LLM-BIOS

A self-compiling BIOS system for Large Language Models that enables models to define and compile their own knowledge representation format.

## Concept

Traditional RAG systems impose external structure on knowledge. LLM-BIOS inverts this: the model itself defines how it wants information represented, then compiles that specification into a format it can execute.

Like a computer BIOS, LLM-BIOS lives in the system prompt (ROM) and provides:

- **Compiler**: Transforms any document into model-native JSON
- **Knowledge Base Operations**: Store, retrieve, search compiled knowledge
- **Self-Applicability**: The compiler can compile its own specification

## Bootstrap Process

1. **Stage 1**: Ask model its preferred format (usually JSON)
2. **Stage 2**: Define compiler rules in natural language
3. **Stage 3**: Model outputs compiler rules
4. **Stage 4**: Model compiles rules into JSON specification
5. **Stage 5**: Validate - compiler compiles itself
6. **Stage 6**: Embed compiled compiler into BIOS

## Content Types

The compiler classifies documents into four types:

| Type | Purpose | Example |
|------|---------|---------|
| **Fact** | Static truth statement | "The solar array is 18kW" |
| **Procedure** | Step-by-step process | "How to query InfluxDB" |
| **Mapping** | Key-value relationships | "HTTP status codes" |
| **Entity** | Object with attributes | "Ecobee API schema" |

## Key Innovation

1. Model designs its own representation format
2. Self-compiling compiler specification
3. BIOS analogy executed literally
4. Model-native knowledge compilation

Existing RAG systems impose structure. LLM-BIOS lets the model define structure.

## License

MIT
