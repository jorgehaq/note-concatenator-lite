#!/usr/bin/env python3
import argparse
import json
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

HOME_CONFIG_PATH = Path.home() / ".concat_projects.json"
LOCAL_CONFIG_BASENAME = ".concat_projects.json"

DEFAULT_CONFIG_TEMPLATE = {
    "example-project": {
        "source": str(Path.home() / "projects" / "example"),
        "output": str(Path.home() / "notes"),
        "note-name": "example-context",
        "versionar": False,
        "extensions": [".py", ".md", ".json"],
        "ignore": [".git", "__pycache__", "node_modules", ".venv"],
    }
}


def _find_git_root(start_dir: Path) -> Path | None:
    cur = start_dir.resolve()
    for parent in (cur, *cur.parents):
        if (parent / ".git").exists():
            return parent
    return None


def _find_local_config(start_dir: Path) -> Path | None:
    cur = start_dir.resolve()
    for parent in (cur, *cur.parents):
        candidate = parent / LOCAL_CONFIG_BASENAME
        if candidate.exists():
            return candidate
        if (parent / ".git").exists():
            break
    return None


def get_config_path() -> Path:
    local = _find_local_config(Path.cwd())
    if local is not None:
        return local
    return HOME_CONFIG_PATH


def load_config(config_path: Path):
    if not config_path.exists():
        git_root = _find_git_root(Path.cwd())
        if git_root is not None and config_path == HOME_CONFIG_PATH:
            config_path = git_root / LOCAL_CONFIG_BASENAME

    if not config_path.exists():
        with open(config_path, "w") as f:
            json.dump(DEFAULT_CONFIG_TEMPLATE, f, indent=2)
        print(
            f"{CLR_YELLOW}Warning: {config_path} not found. Created a template."
            f"{CLR_RESET}"
        )
        return DEFAULT_CONFIG_TEMPLATE

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"{CLR_RED}Error: Failed to parse config file: {e}{CLR_RESET}")
        sys.exit(1)


def list_projects(config: dict, config_path: Path) -> None:
    names = sorted([k for k in config.keys() if isinstance(k, str)])
    if not names:
        print(f"{CLR_YELLOW}No projects found in {config_path}{CLR_RESET}")
        return

    for i, name in enumerate(names, start=1):
        print(f"{i}. concat {name}")

    try:
        selection = input(f"\n{CLR_CYAN}Select a project number to run (or press Enter to exit): {CLR_RESET}").strip()
        if selection:
            idx = int(selection) - 1
            if 0 <= idx < len(names):
                concat_project(names[idx], config, config_path)
            else:
                print(f"{CLR_RED}Invalid selection index.{CLR_RESET}")
    except ValueError:
        print(f"{CLR_RED}Invalid input. Please enter a number.{CLR_RESET}")
    except EOFError:
        pass
    except KeyboardInterrupt:
        print("\nExiting...")


def _paths_to_tree(relative_paths: list[Path]) -> dict:
    tree: dict = {}
    for rel in relative_paths:
        node = tree
        parts = rel.parts
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault("__files__", []).append(parts[-1])
    return tree


def _render_tree(tree: dict, prefix: str = "") -> list[str]:
    lines: list[str] = []
    
    # Se elimina 'sorted' para conservar el orden cronológico de inserción
    dir_entries = [k for k in tree.keys() if k != "__files__"]
    files = tree.get("__files__", [])
    
    entries: list[tuple[str, str]] = [(d, "dir") for d in dir_entries] + [
        (f, "file") for f in files
    ]

    for idx, (name, kind) in enumerate(entries):
        last = idx == len(entries) - 1
        branch = " \\-- " if last else " |-- "
        if kind == "file":
            lines.append(f"{prefix}{branch}{name}")
            continue

        lines.append(f"{prefix}{branch}{name}/")
        child_prefix = f"{prefix}{'    ' if last else ' |  '}"
        lines.extend(_render_tree(tree[name], prefix=child_prefix))

    return lines


def concat_project(project_name, config, config_path: Path):
    if project_name not in config:
        print(f"{CLR_RED}Error: Project '{project_name}' not found in {config_path}{CLR_RESET}")
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

    # Always apply versioning with timestamp
    timestamp = datetime.now().strftime("-%y-%m-%d.%H-%M-%S")
    stem = note_path.stem
    suffix = note_path.suffix
    note_name = f"{stem}{timestamp}{suffix}"

    # Final output path: base_path / project_name / note_name
    # NO .resolve() on output_file to avoid OSError on WSL2/drvfs symlinks
    output_file = base_path / project_name / note_name

    extensions = [ext if ext.startswith(".") else f".{ext}" for ext in proj.get("extensions", [])]
    ignore_list = proj.get("ignore", [])

    try:
        if not source_dir.exists() or not source_dir.is_dir():
            print(
                f"{CLR_RED}Error: Source directory '{source_dir}' does not exist or is "
                f"not a directory.{CLR_RESET}"
            )
            sys.exit(1)

        print(f"{CLR_CYAN}Concatenating {CLR_BOLD}{project_name}{CLR_RESET}...")
        print(f"Source: {source_dir}")
        print(f"Output: {output_file}")

        output_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        import errno
        if e.errno == errno.ENODEV:
            failed_path = e.filename if e.filename else "one of the configured paths"
            print(
                f"{CLR_RED}Error: Connection lost to device (OSError 19) while accessing: "
                f"{failed_path}{CLR_RESET}"
            )
            print(f"Check if your Windows drive (often G: or external) is mounted and functional in WSL.")
        else:
            print(f"{CLR_RED}FileSystem Error: {e}{CLR_RESET}")
        sys.exit(1)

    try:
        with open(output_file, "w", encoding="utf-8") as out:
            out.write(f"# Project: {project_name}\n\n")

            # First pass: gather valid paths and build tree
            valid_paths = []
            
            for path in source_dir.rglob("*"):
                if not path.is_file():
                    continue

                # Check for ignored directories in the path
                if any(ignored in path.parts for ignored in ignore_list):
                    continue

                if path.suffix in extensions:
                    valid_paths.append(path)

            # Ordenar los archivos cronológicamente por fecha de modificación (de más antiguo a más reciente)
            valid_paths.sort(key=lambda p: p.stat().st_mtime)

            included_paths = [p.relative_to(source_dir) for p in valid_paths]
            count = len(valid_paths)

            # Write the file structure (tree) at the beginning
            out.write("## Tabla de Contenido (Estructura de archivos)\n\n")
            out.write("```text\n")
            out.write(f"{project_name}/\n")
            tree = _paths_to_tree(included_paths)
            for line in _render_tree(tree):
                out.write(f"{line}\n")
            out.write("```\n\n")

            # Second pass: read and write file contents
            for path in valid_paths:
                try:
                    relative_path = path.relative_to(source_dir)
                    content = path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                    
                    stat = path.stat()
                    # Use creation/metadata change time and modification time
                    created_at = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    modified_at = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                    out.write("---\n\n")
                    out.write(f"### 📄 {relative_path}\n")
                    out.write(f"**Creación:** {created_at} | **Modificación:** {modified_at}\n\n")
                    
                    # Guess language for markdown block if possible, else empty
                    lang = path.suffix[1:] if path.suffix else ""
                    out.write(f"```{lang}\n")
                    out.write(content)
                    if not content.endswith("\n"):
                        out.write("\n")
                    out.write("```\n\n")
                    print(f"  {CLR_GREEN}Added:{CLR_RESET} {relative_path}")
                except Exception as e:
                    print(
                        f"  {CLR_YELLOW}Skipped:{CLR_RESET} {path} "
                        f"(Error: {e})"
                    )

        print(
            f"\n{CLR_GREEN}{CLR_BOLD}Success!{CLR_RESET} {count} files "
            f"concatenated into {output_file}"
        )
    except Exception as e:
        print(f"{CLR_RED}Error: Failed to write to output file: {e}{CLR_RESET}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="LiteConcat v3.0: Concatenate project files into a single Markdown."
    )
    parser.add_argument(
        "project",
        help="Project name, or 'list' to show available projects",
    )
    args = parser.parse_args()

    config_path = get_config_path()
    config = load_config(config_path)
    if args.project == "list":
        list_projects(config, config_path)
        return

    concat_project(args.project, config, config_path)


if __name__ == "__main__":
    main()
