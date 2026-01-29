#!/usr/bin/env python3
"""
LLM-BIOS Bootstrap Script

Bootstraps a self-compiling BIOS for Large Language Models using the shepherd CLI.
Implements all 6 stages of the bootstrap process.

Usage:
    python3 bootstrap.py
    python3 bootstrap.py --provider anthropic
    python3 bootstrap.py --output-dir ./my-bios
"""

import argparse
import atexit
import json
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"
CLI_SERVER_PORT = 9999

# Prompt files (relative to script location)
PROMPTS_DIR = Path(__file__).parent / "prompts"

# Default template path (relative to script location)
DEFAULT_TEMPLATE = Path(__file__).parent / "template.md"

# Global server process
server_process = None


def load_prompt(name):
    """Load a prompt from the prompts directory."""
    prompt_file = PROMPTS_DIR / f"{name}.txt"
    if not prompt_file.exists():
        raise BootstrapError(f"Prompt file not found: {prompt_file}")
    with open(prompt_file) as f:
        return f.read()


class BootstrapError(Exception):
    """Bootstrap process error."""
    pass


def log(msg, level="INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def start_server(args):
    """Start shepherd CLI server."""
    global server_process

    cmd = ["shepherd", "--cliserver", "--port", str(CLI_SERVER_PORT),
           "--nomcp", "--notools", "--nosched"]

    if args.provider:
        cmd.extend(["--provider", args.provider])
    if args.backend:
        cmd.extend(["--backend", args.backend])
    if args.api_base:
        cmd.extend(["--api-base", args.api_base])

    log(f"Starting shepherd CLI server on port {CLI_SERVER_PORT}...")
    server_process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Give server time to start
    time.sleep(2)

    if server_process.poll() is not None:
        raise BootstrapError("Failed to start shepherd CLI server")

    log("Server started")


def stop_server():
    """Stop shepherd CLI server."""
    global server_process

    if server_process:
        log("Stopping shepherd CLI server...")
        subprocess.run(
            ["shepherd", "ctl", "shutdown", str(CLI_SERVER_PORT)],
            capture_output=True
        )
        server_process = None
        log("Server stopped")


def clear_context():
    """Clear the shepherd context."""
    cmd = f"echo '/clear' | shepherd --backend cli --api-base localhost:{CLI_SERVER_PORT}"
    subprocess.run(cmd, shell=True, capture_output=True)
    log("Context cleared")


def strip_ansi(text):
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def extract_last_response(text):
    """Extract just the last response from conversation history.

    Shepherd CLI returns full history. Format is:
    > prompt1
      response1
    > prompt2
      response2

    We want just the last response.
    """
    # Split on '> ' which marks user prompts
    parts = re.split(r'\n> |\A> ', text)
    if len(parts) > 1:
        # Last part is the last prompt+response, get just the response
        last_exchange = parts[-1]
        # Response starts after the first newline (prompt is first line)
        lines = last_exchange.split('\n', 1)
        if len(lines) > 1:
            return lines[1].strip()
    return text


def call_shepherd(prompt_file):
    """Send prompt to shepherd CLI server and return response."""

    # Read prompt from file
    with open(prompt_file) as f:
        prompt_text = f.read()

    return call_shepherd_text(prompt_text)


def call_shepherd_text(prompt_text):
    """Send text prompt to shepherd CLI server and return response."""

    cmd = [
        "shepherd",
        "--backend", "cli",
        "--api-base", f"localhost:{CLI_SERVER_PORT}",
        "--prompt", prompt_text
    ]

    log("Sending prompt...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            raise BootstrapError(f"Shepherd failed: {result.stderr}")

        output = strip_ansi(result.stdout.strip())
        response = extract_last_response(output)
        return response

    except subprocess.TimeoutExpired:
        raise BootstrapError("Shepherd call timed out")


def extract_json(text):
    """Extract JSON from response text, handling markdown fences."""
    # Remove markdown code fences if present
    text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    # Try to find JSON object
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise BootstrapError(f"Failed to parse JSON: {e}\nText was: {text[:500]}...")


def extract_between_markers(text, begin_marker, end_marker):
    """Extract content between begin and end markers."""
    pattern = re.escape(begin_marker) + r'\s*([\s\S]*?)\s*' + re.escape(end_marker)
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    raise BootstrapError(f"Could not find content between {begin_marker} and {end_marker}")


def save_checkpoint(stage, data, build_dir):
    """Save checkpoint for resume capability."""
    checkpoint_file = build_dir / ".checkpoint.json"

    checkpoint = {}
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            checkpoint = json.load(f)

    checkpoint[f"stage{stage}"] = {
        "completed": True,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

    with open(checkpoint_file, "w") as f:
        json.dump(checkpoint, f, indent=2)

    log(f"Checkpoint saved for stage {stage}")


def load_checkpoint(build_dir):
    """Load checkpoint if exists."""
    checkpoint_file = build_dir / ".checkpoint.json"
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            return json.load(f)
    return {}


def stage1_format_preference(args, checkpoint):
    """Stage 1: Ask model preferred format."""
    log("=" * 60)
    log("STAGE 1: Format Preference")
    log("=" * 60)

    if "stage1" in checkpoint and not args.force:
        log("Stage 1 already complete, skipping (use --force to re-run)")
        return checkpoint["stage1"]["data"]

    prompt_file = PROMPTS_DIR / "stage1-format.txt"
    response = call_shepherd(prompt_file)

    log(f"Model response:\n{response}")

    # Extract format preference from first line
    first_line = response.split('\n')[0].strip().lower()
    format_pref = "json"  # default

    for fmt in ["json", "xml", "yaml", "s-expression", "pseudocode"]:
        if fmt in first_line:
            format_pref = fmt
            break

    log(f"Detected format preference: {format_pref}")

    result = {
        "format": format_pref,
        "reasoning": response
    }

    save_checkpoint(1, result, args.build_dir)
    return result


def stage2_compiler_rules(args, checkpoint):
    """Stage 2: Define compiler rules in natural language."""
    log("=" * 60)
    log("STAGE 2: Compiler Rules (Natural Language)")
    log("=" * 60)

    if "stage2" in checkpoint and not args.force:
        log("Stage 2 already complete, skipping (use --force to re-run)")
        return checkpoint["stage2"]["data"]

    prompt_file = PROMPTS_DIR / "stage2-compiler.txt"
    response = call_shepherd(prompt_file)

    log(f"Compiler spec length: {len(response)} chars")

    # Save natural language spec
    spec_file = args.build_dir / "compiler-spec.md"
    with open(spec_file, "w") as f:
        f.write("# Compiler Specification\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write(response)

    log(f"Saved compiler spec to {spec_file}")

    result = {
        "spec": response,
        "spec_file": str(spec_file)
    }

    save_checkpoint(2, result, args.build_dir)
    return result


def stage3_self_compile(args, checkpoint, stage2_result, format_pref):
    """Stage 3: Self-compile the compiler spec to preferred format."""
    log("=" * 60)
    log("STAGE 3: Self-Compile")
    log("=" * 60)

    if "stage3" in checkpoint and not args.force:
        log("Stage 3 already complete, skipping (use --force to re-run)")
        return checkpoint["stage3"]["data"]

    prompt_file = PROMPTS_DIR / "stage3-selfcompile.txt"
    response = call_shepherd(prompt_file)

    # Extract content between markers
    compiler_data = extract_between_markers(response, "---BEGIN COMPILER---", "---END COMPILER---")

    # Save compiler (format-agnostic)
    compiler_file = args.build_dir / "compiler.txt"
    with open(compiler_file, "w") as f:
        f.write(compiler_data)

    log(f"Saved compiled compiler to {compiler_file}")

    result = {
        "compiler": compiler_data,
        "compiler_file": str(compiler_file),
        "format": format_pref
    }

    save_checkpoint(3, result, args.build_dir)
    return result


def stage4_validate(args, stage3_result):
    """Stage 4: Validate self-compiled output."""
    log("=" * 60)
    log("STAGE 4: Validation")
    log("=" * 60)

    compiler = stage3_result["compiler"]
    format_pref = stage3_result.get("format", "json")

    # For JSON, do structural validation
    if format_pref == "json" and isinstance(compiler, dict):
        errors = []
        if compiler.get("type") != "entity":
            errors.append(f"Expected type 'entity', got '{compiler.get('type')}'")
        content = compiler.get("content", {})
        if not content.get("name"):
            errors.append("Missing content.name")
        if errors:
            for err in errors:
                log(err, "ERROR")
            raise BootstrapError("Validation failed")
        log("Validation passed (JSON structure)")
    else:
        # For other formats, do text-based validation
        required_terms = ["Doc2JSONCompiler", "classificationRules", "extractionRules", "outputSchema"]
        missing = [term for term in required_terms if term not in compiler]
        if missing:
            for term in missing:
                log(f"Missing required term: {term}", "ERROR")
            raise BootstrapError("Validation failed")
        log("Validation passed (text-based)")

    log(f"  - Format: {format_pref}")
    log(f"  - Size: {len(compiler)} chars")

    return True


def stage5_build_bios(args, stage3_result, checkpoint):
    """Stage 5: Build full BIOS."""
    log("=" * 60)
    log("STAGE 5: Build BIOS")
    log("=" * 60)

    if "stage5" in checkpoint and not args.force:
        log("Stage 5 already complete, skipping (use --force to re-run)")
        return checkpoint["stage5"]["data"]

    # Load the prompt and template
    prompt_base = load_prompt("stage5-build-bios")
    template_path = args.template if args.template else DEFAULT_TEMPLATE
    with open(template_path) as f:
        template_content = f.read()

    # Build full prompt: base + template + markers instruction
    full_prompt = (
        prompt_base +
        template_content +
        "\n\nOutput the complete BIOS between these markers:\n"
        "---BEGIN BIOS---\n"
        "(your BIOS here)\n"
        "---END BIOS---\n"
        "Output ONLY the markers and BIOS, no other text."
    )

    response = call_shepherd_text(full_prompt)

    # Extract BIOS between markers
    bios_content = extract_between_markers(response, "---BEGIN BIOS---", "---END BIOS---")

    # Save BIOS
    bios_file = args.build_dir / "bios.txt"
    with open(bios_file, "w") as f:
        f.write(bios_content)

    log(f"Saved BIOS to {bios_file}")

    result = {
        "bios": bios_content,
        "bios_file": str(bios_file)
    }

    save_checkpoint(5, result, args.build_dir)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap LLM-BIOS using shepherd",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--provider", "-p",
                        help="Provider name (optional, uses shepherd default)")
    parser.add_argument("--backend",
                        help="Backend (openai, anthropic, ollama, etc.)")
    parser.add_argument("--api-base",
                        help="API base URL")
    parser.add_argument("--template", "-t", type=Path,
                        help="BIOS template file (default: bios-template.json)")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("."),
                        help="Output directory (default: current)")
    parser.add_argument("--resume", "--continue", action="store_true",
                        help="Resume/continue from last checkpoint")
    parser.add_argument("--force", action="store_true",
                        help="Force re-run all stages")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    args = parser.parse_args()

    # Setup directories
    args.build_dir = args.output_dir / "build"
    args.build_dir.mkdir(parents=True, exist_ok=True)

    log(f"LLM-BIOS Bootstrap v{VERSION}")
    if args.provider:
        log(f"Provider: {args.provider}")
    if args.backend:
        log(f"Backend: {args.backend}")
    log(f"Output directory: {args.output_dir}")

    # Register cleanup
    atexit.register(stop_server)
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    # Load checkpoint if resuming
    checkpoint = {}
    if args.resume:
        checkpoint = load_checkpoint(args.build_dir)
        if checkpoint:
            log(f"Resuming from checkpoint with {len(checkpoint)} completed stages")

    try:
        # Start server
        start_server(args)

        # Only clear context on fresh start, not when resuming
        if not args.resume:
            clear_context()

        # Stage 1: Format preference
        stage1_result = stage1_format_preference(args, checkpoint)
        format_pref = stage1_result["format"]

        # Stage 2: Compiler rules
        stage2_result = stage2_compiler_rules(args, checkpoint)

        # Stage 3: Self-compile
        stage3_result = stage3_self_compile(args, checkpoint, stage2_result, format_pref)

        # Stage 4: Validate
        stage4_validate(args, stage3_result)

        # Stage 5: Build BIOS
        bios_result = stage5_build_bios(args, stage3_result, checkpoint)

        log("=" * 60)
        log("BOOTSTRAP COMPLETE")
        log("=" * 60)
        log(f"Format: {format_pref}")
        log(f"Compiler: {args.build_dir}/compiler.txt")
        log(f"BIOS: {args.build_dir}/bios.txt")
        log(f"Spec: {args.build_dir}/compiler-spec.md")

    except BootstrapError as e:
        log(f"Bootstrap failed: {e}", "ERROR")
        sys.exit(1)
    except KeyboardInterrupt:
        log("Interrupted by user", "WARN")
        sys.exit(130)
    finally:
        stop_server()


if __name__ == "__main__":
    main()
