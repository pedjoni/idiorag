# uv Installation and Setup Guide

## Installing uv

### On Linux/WSL/macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### On Windows (PowerShell)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Verify Installation
```bash
uv --version
```

## Quick Start with uv

### 1. Create Virtual Environment
```bash
# Create .venv in project directory
uv venv

# On Linux/WSL/macOS
source .venv/bin/activate

# On Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
# Install all dependencies (creates uv.lock)
uv sync

# Or install from pyproject.toml without lock
uv pip install -e .

# Install with dev dependencies
uv sync --extra dev
```

### 3. Run the Application
```bash
# uv automatically uses the virtual environment
uv run python run.py

# Or activate venv first
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1
python run.py
```

## Common Commands

```bash
# Install a new package
uv add fastapi

# Install a dev dependency
uv add --dev pytest

# Remove a package
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Show outdated packages
uv pip list --outdated

# Run a command in the virtual environment
uv run python test_setup.py
uv run pytest
```

## uv vs pip Comparison

| Task | uv | Traditional pip |
|------|----|-----------------| 
| Create venv | `uv venv` | `python -m venv venv` |
| Activate | Same | Same |
| Install deps | `uv sync` | `pip install -r requirements.txt` |
| Add package | `uv add package` | `pip install package` then update requirements.txt |
| Run script | `uv run python script.py` | `python script.py` |
| Lock deps | `uv lock` (automatic) | Manual with pip-tools |

## Why uv is Better

1. **Speed**: 10-100x faster than pip
2. **Reliability**: Better dependency resolution
3. **Lock file**: `uv.lock` ensures reproducible installs
4. **Simplicity**: One command for most tasks
5. **Modern**: Built in Rust, actively maintained

## Project Structure with uv

```
idiorag/
├── pyproject.toml       # Project config + dependencies
├── uv.lock             # Locked dependency versions (auto-generated)
├── .venv/              # Virtual environment (auto-created)
├── src/idiorag/        # Source code
└── ...
```

## Migration from pip

If you're familiar with pip, here's the mental model:
- `requirements.txt` → `pyproject.toml` [project.dependencies]
- `pip install` → `uv sync` or `uv add`
- `pip freeze` → `uv.lock` (automatic)
- `pip install -e .` → `uv pip install -e .`

## Compatibility

uv is fully compatible with pip:
- Can read requirements.txt
- Can use existing virtualenvs
- Works with all pip packages
- Can be used alongside pip

## Pro Tips

```bash
# Install without creating lock file (faster for testing)
uv pip install -e .

# Install specific Python version
uv venv --python 3.11

# Use system Python
uv venv --python python3.11

# Sync without installing the project itself
uv sync --no-install-project

# Show what would be installed
uv sync --dry-run
```

## Troubleshooting

### uv not found after install
```bash
# Add to PATH (Linux/macOS)
export PATH="$HOME/.cargo/bin:$PATH"

# Add to PATH (Windows PowerShell)
$env:Path += ";$HOME\.cargo\bin"
```

### Virtual environment not activating
```bash
# Make sure you're in project directory
cd ~/workspace/idiorag

# Create fresh venv
uv venv --force
```

### Lock file conflicts
```bash
# Regenerate lock file
rm uv.lock
uv lock
```

## Next Steps

After installing uv:
1. Run `uv venv` to create virtual environment
2. Run `uv sync` to install dependencies
3. Run `uv run python test_setup.py` to verify setup
4. Start developing!

---

**Recommended:** Use `uv sync` for a consistent, fast development experience!
