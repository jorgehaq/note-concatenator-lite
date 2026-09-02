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


def load_config(config_path: Path, quiet: bool = False):
    if not config_path.exists():
        git_root = _find_git_root(Path.cwd())
        if git_root is not None and config_path == HOME_CONFIG_PATH:
            config_path = git_root / LOCAL_CONFIG_BASENAME

    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG_TEMPLATE, f, indent=2)
        if not quiet:
            print(
                f"{CLR_YELLOW}Warning: {config_path} not found. Created a template."
                f"{CLR_RESET}"
            )
        return DEFAULT_CONFIG_TEMPLATE

    try:
        with open(config_path, "r", encoding="utf-8") as f:
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
    
    # Ordenar directorios y archivos alfabéticamente (sin distinguir mayúsculas de minúsculas)
    dir_entries = sorted([k for k in tree.keys() if k != "__files__"], key=lambda s: s.lower())
    files = sorted(tree.get("__files__", []), key=lambda s: s.lower())
    
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


def _build_file_entry(path: Path, source_dir: Path) -> dict:
    """Build a metadata+content dict for a single file."""
    relative_path = path.relative_to(source_dir)
    content = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )
    stat = path.stat()
    created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
    modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
    language = path.suffix[1:] if path.suffix else ""

    return {
        "relative_path": str(relative_path),
        "created_at": created_at,
        "modified_at": modified_at,
        "language": language,
        "content": content,
    }


def concat_project(project_name, config, config_path: Path, json_output: bool = False,
                   output_json_path: Path | None = None, quiet: bool = False):
    if project_name not in config:
        msg = f"Error: Project '{project_name}' not found in {config_path}"
        if json_output:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(f"{CLR_RED}{msg}{CLR_RESET}")
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

    extensions_config = proj.get("extensions", [])
    target_exts = {ext if ext.startswith(".") else f".{ext}" for ext in extensions_config}
    target_names = {ext for ext in extensions_config if not ext.startswith(".")}
    ignore_list = proj.get("ignore", [])

    try:
        if not source_dir.exists() or not source_dir.is_dir():
            msg = (
                f"Error: Source directory '{source_dir}' does not exist or is "
                f"not a directory."
            )
            if json_output:
                print(json.dumps({"error": msg}, ensure_ascii=False))
            else:
                print(f"{CLR_RED}{msg}{CLR_RESET}")
            sys.exit(1)

        if not quiet and not json_output:
            print(f"{CLR_CYAN}Concatenating {CLR_BOLD}{project_name}{CLR_RESET}...")
            print(f"Source: {source_dir}")
            print(f"Output: {output_file}")

        output_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        import errno
        if e.errno == errno.ENODEV:
            failed_path = e.filename if e.filename else "one of the configured paths"
            msg = (
                f"Error: Connection lost to device (OSError 19) while accessing: "
                f"{failed_path}"
            )
            if json_output:
                print(json.dumps({"error": msg}, ensure_ascii=False))
            else:
                print(f"{CLR_RED}{msg}{CLR_RESET}")
                print(f"Check if your Windows drive (often G: or external) is mounted and functional in WSL.")
        else:
            msg = f"FileSystem Error: {e}"
            if json_output:
                print(json.dumps({"error": msg}, ensure_ascii=False))
            else:
                print(f"{CLR_RED}{msg}{CLR_RESET}")
        sys.exit(1)

    try:
        with open(output_file, "w", encoding="utf-8-sig") as out:
            out.write(f"# Project: {project_name}\n\n")

            # First pass: gather valid paths and build tree
            valid_paths = []
            
            for path in source_dir.rglob("*"):
                if not path.is_file():
                    continue

                # Check for ignored directories in the path
                if any(ignored in path.parts for ignored in ignore_list):
                    continue

                if path.suffix in target_exts or path.name in target_names:
                    valid_paths.append(path)

            # Ordenar los archivos alfabéticamente (sin distinguir mayúsculas de minúsculas) por su ruta relativa
            valid_paths.sort(key=lambda p: str(p.relative_to(source_dir)).lower())

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
                        encoding="utf-8-sig",
                        errors="replace",
                    )

                    stat = path.stat()
                    # Use creation/metadata change time and modification time
                    created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
                    modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

                    out.write("---\n\n")
                    out.write(f"### {relative_path}\n")
                    out.write(f"**Creado:** {created_at} | **Modificado:** {modified_at}\n\n")

                    # Guess language for markdown block if possible, else empty
                    lang = path.suffix[1:] if path.suffix else ""
                    out.write(f"```{lang}\n")
                    out.write(content)
                    if not content.endswith("\n"):
                        out.write("\n")
                    out.write("```\n\n")
                    if not quiet and not json_output:
                        print(f"  {CLR_GREEN}Added:{CLR_RESET} {relative_path}")
                except Exception as e:
                    if not quiet and not json_output:
                        print(
                            f"  {CLR_YELLOW}Skipped:{CLR_RESET} {path} "
                            f"(Error: {e})"
                        )

        if json_output:
            # Build the JSON payload for headless mode
            tree_lines = _render_tree(_paths_to_tree(included_paths))
            files_payload = [_build_file_entry(p, source_dir) for p in valid_paths]

            payload = {
                "project": project_name,
                "source": str(source_dir),
                "output": str(output_file),
                "files_count": count,
                "files": files_payload,
                "tree": tree_lines,
            }

            # Print clean JSON to stdout (no ANSI)
            print(json.dumps(payload, ensure_ascii=False, indent=2))

            # Optionally write JSON payload to a file
            if output_json_path is not None:
                output_json_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_json_path, "w", encoding="utf-8") as jf:
                    json.dump(payload, jf, ensure_ascii=False, indent=2)

        elif not quiet:
            print(
                f"\n{CLR_GREEN}{CLR_BOLD}Success!{CLR_RESET} {count} files "
                f"concatenated into {output_file}"
            )
    except Exception as e:
        if json_output:
            print(json.dumps({"error": f"Error: Failed to write to output file: {e}"}, ensure_ascii=False))
        else:
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON payload to stdout instead of ANSI-colored messages.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Write the JSON payload to the given file path (also emits to stdout with --json).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress and informational prints.",
    )
    args = parser.parse_args()

    config_path = get_config_path()
    config = load_config(config_path, quiet=args.quiet or args.json)
    if args.project == "list":
        list_projects(config, config_path)
        return

    output_json_path = Path(args.output_json) if args.output_json else None
    concat_project(
        args.project,
        config,
        config_path,
        json_output=args.json,
        output_json_path=output_json_path,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
