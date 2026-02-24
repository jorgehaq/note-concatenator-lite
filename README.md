# LiteConcat v3.0

Extremely minimalist tool to concatenate project files into a single Markdown file.

## Setup

1. **Permissions**: Make the script executable:
   ```bash
   chmod +x concat.py
   ```

2. **Alias**: Add an alias to your `~/.bashrc` or `~/.zshrc`:
   ```bash
   alias concat='python3 /home/jorgehaq_wsl/projects/note-concatenator-lite/concat.py'
   ```
   *Note: Use the absolute path to `concat.py`.*

3. **Reload shell**:
   ```bash
   source ~/.bashrc
   ```

## Configuration

Edit `~/.concat_projects.json` to define your projects:

```json
{
  "my_project": {
    "source": "/path/to/source",
    "output": "/path/to/output.md",
    "extensions": [".py", ".md"],
    "ignore": [".git", ".venv"]
  }
}
```

## Usage

```bash
concat my_project
```
