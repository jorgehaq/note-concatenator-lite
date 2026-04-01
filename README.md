# LiteConcat v3.0

Extremely minimalist tool to concatenate project files into a single Markdown file.

## Setup

Choose your preferred Python environment manager:

### Option A: Modern Way (Using `uv` - Isolated & Blazing Fast)
Requires `uv` installed. Keeps your system Python completely untouched.

1. **Initialize the environment**:
   ```bash
   cd /ABS/PATH/TO/note-concatenator-lite
   uv venv --python 3.12
   # uv pip install -r requirements.txt (If you have dependencies)
   ```

2. **Create the Alias**: Add this to your `~/.bashrc` or `~/.zshrc`. Notice it points directly to the isolated binary:
   ```bash
   alias concat='/ABS/PATH/TO/note-concatenator-lite/.venv/bin/python /ABS/PATH/TO/note-concatenator-lite/concat.py'
   ```

### Option B: Classic Way (System Python & `venv`)
Uses your OS-provided Python runtime.

1. **Initialize the environment**:
   ```bash
   cd /ABS/PATH/TO/note-concatenator-lite
   python3 -m venv .venv
   # source .venv/bin/activate && pip install -r requirements.txt (If you have dependencies)
   ```

2. **Create the Alias**: Add this to your `~/.bashrc` or `~/.zshrc`:
   ```bash
   alias concat='/ABS/PATH/TO/note-concatenator-lite/.venv/bin/python /ABS/PATH/TO/note-concatenator-lite/concat.py'
   ```

---

### Finalize Setup

Make the script executable and reload your shell configuration:

```bash
chmod +x /ABS/PATH/TO/note-concatenator-lite/concat.py
source ~/.bashrc  # or source ~/.zshrc
```

## Configuration

Define your projects in `.concat_projects.json` (recommended, in the project folder).  
Fallback: `~/.concat_projects.json`.

```json
{
  "my_project": {
    "command": "concat my_project",
    "note": "my_project.md",
    "source": "/path/to/source",
    "output": "/path/to/",
    "extensions": [".py", ".md"],
    "ignore": [".git", ".venv"]
  }
}
```

## Usage

```bash
concat my_project
```

List available projects:

```bash
concat list
```

At the end of the generated note, LiteConcat appends an extra section with the
folder/file structure of all concatenated files (a tree skeleton of what was
actually included).
```