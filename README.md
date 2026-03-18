# LiteConcat v3.0

Extremely minimalist tool to concatenate project files into a single Markdown file.

## Setup

1. **Permissions**: Make the script executable:
   ```bash
   chmod +x concat.py
   ```

2. **Alias**: Add an alias to your `~/.bashrc` or `~/.zshrc`:
   ```bash
   alias concat='python3 /ABS/PATH/TO/note-concatenator-lite/concat.py'
   ```
   *Note: Use the absolute path to `concat.py`.*

3. **Reload shell**:
   ```bash
   source ~/.bashrc
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
