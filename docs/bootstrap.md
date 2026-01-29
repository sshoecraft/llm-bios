# Bootstrap Process

## Stage 1: Ask Model Preferred Format

Most models choose JSON due to massive training exposure.

## Stage 2: Define Compiler (Natural Language)

Have model describe rules for classifying and extracting structure from documents.

## Stage 3: Self-Compile

Model writes its own rules as JSON it can interpret.

## Stage 4: Validate

Compiler compiles itself as an Entity - proves self-applicability.

## Stage 5: Build BIOS

Wrap compiler with knowledge base operations.

## Cross-Compilation

Different models may prefer different formats. Maintain per-model builds:

```
targets/gpt-4.yaml -> build/gpt-4-bios.json
targets/llama3.yaml -> build/llama3-bios.json
```
