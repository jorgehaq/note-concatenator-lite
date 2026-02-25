#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ANSI color codes
CLR_RESET = "\033[0m"
CLR_RED = "\033[31m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_CYAN = "\033[36m"
CLR_BOLD = "\033[1m"

CONFIG_PATH = Path.home() / ".concat_projects.json"

DEFAULT_CONFIG_TEMPLATE = {
    "example-project": {
        "source": str(Path.home() / "projects" / "example"),
        "output": str(Path.home() / "notes"),
        "note-name": "example-context",
        "versionar": False,
        "extensions": [".py", ".md", ".json"],
        "ignore": [".git", "__pycache__", "node_modules", ".venv"]
    }
}

def load_config():
    if not CONFIG_PATH.exists():
        with open(CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_CONFIG_TEMPLATE, f, indent=2)
        print(f"{CLR_YELLOW}Warning: {CONFIG_PATH} not found. Created a template.{CLR_RESET}")
        return DEFAULT_CONFIG_TEMPLATE
    
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"{CLR_RED}Error: Failed to parse config file: {e}{CLR_RESET}")
        sys.exit(1)

def concat_project(project_name, config):
    if project_name not in config:
        print(f"{CLR_RED}Error: Project '{project_name}' not found in {CONFIG_PATH}{CLR_RESET}")
        print(f"Available projects: {', '.join(config.keys())}")
        sys.exit(1)

    proj = config[project_name]
    source_dir = Path(proj.get("source", "")).expanduser().resolve()
    
    # Refactored dynamic output path
    base_path = Path(proj.get("output", "")).expanduser()
    note_name = proj.get("note-name", project_name)
    
    # Ensure note_name has an extension
    note_path = Path(note_name)
    if not note_path.suffix:
        note_name += ".md"
        note_path = Path(note_name)

    # Apply versioning if requested
    if proj.get("versionar", False):
        timestamp = datetime.now().strftime("-%y-%m-%d.%H-%M-%S")
        stem = note_path.stem
        suffix = note_path.suffix
        note_name = f"{stem}{timestamp}{suffix}"
        
    # Final output path: base_path / project_name / note_name
    # NO .resolve() on output_file to avoid OSError on WSL2/drvfs symlinks
    output_file = base_path / project_name / note_name
    
    extensions = proj.get("extensions", [])
    ignore_list = proj.get("ignore", [])

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"{CLR_RED}Error: Source directory '{source_dir}' does not exist or is not a directory.{CLR_RESET}")
        sys.exit(1)

    print(f"{CLR_CYAN}Concatenating {CLR_BOLD}{project_name}{CLR_RESET}...")
    print(f"Source: {source_dir}")
    print(f"Output: {output_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_file, "w", encoding="utf-8") as out:
            out.write(f"# Project: {project_name}\n\n")
            
            count = 0
            for path in sorted(source_dir.rglob("*")):
                if not path.is_file():
                    continue
                
                # Check for ignored directories in the path
                if any(ignored in path.parts for ignored in ignore_list):
                    continue
                
                if path.suffix in extensions:
                    try:
                        relative_path = path.relative_to(source_dir)
                        content = path.read_text(encoding="utf-8", errors="replace")
                        
                        out.write(f"### 📄 {relative_path}\n")
                        # Guess language for markdown block if possible, else empty
                        lang = path.suffix[1:] if path.suffix else ""
                        out.write(f"```{lang}\n")
                        out.write(content)
                        if not content.endswith("\n"):
                            out.write("\n")
                        out.write("```\n\n")
                        count += 1
                        print(f"  {CLR_GREEN}Added:{CLR_RESET} {relative_path}")
                    except Exception as e:
                        print(f"  {CLR_YELLOW}Skipped:{CLR_RESET} {path} (Error: {e})")

        print(f"\n{CLR_GREEN}{CLR_BOLD}Success!{CLR_RESET} {count} files concatenated into {output_file}")
    except Exception as e:
        print(f"{CLR_RED}Error: Failed to write to output file: {e}{CLR_RESET}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="LiteConcat v3.0: Concatenate project files into a single Markdown.")
    parser.add_argument("project", help="Name of the project to concatenate (from ~/.concat_projects.json)")
    args = parser.parse_args()

    config = load_config()
    concat_project(args.project, config)

if __name__ == "__main__":
    main()
