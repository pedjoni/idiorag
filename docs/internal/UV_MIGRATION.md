# IdioRAG - Now with uv! 🚀

## What Changed?

Your IdioRAG project is now configured to use **uv** for dependency management!

### Before (pip)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # slow 😴
```

### After (uv)
```bash
uv venv
source .venv/bin/activate
uv sync  # 10-100x faster! ⚡
```

## Quick Setup

### 1. Install uv (if not already installed)

**On Windows PowerShell:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**On Linux/WSL:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:
```bash
uv --version
```

### 2. Set Up Your Environment

```bash
# In your IdioRAG project directory
cd ~/workspace/idiorag

# Create virtual environment
uv venv

# Activate it
source .venv/bin/activate  # Linux/WSL
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install all dependencies (this creates uv.lock)
uv sync

# Done! Much faster than pip 🎉
```

### 3. Verify Setup

```bash
# Run the verification script
uv run python tests/test_setup.py

# Or if venv is activated
python tests/test_setup.py
```

## Key Differences

| Feature | Old (pip) | New (uv) |
|---------|-----------|----------|
| Venv location | `venv/` | `.venv/` |
| Install command | `pip install -r requirements.txt` | `uv sync` |
| Add package | Edit requirements.txt + pip install | `uv add package` |
| Lock file | None | `uv.lock` (auto-generated) |
| Speed | Baseline | 10-100x faster |

## Common Commands

```bash
# Install dependencies
uv sync

# Add a new package
uv add httpx

# Add a dev dependency
uv add --dev pytest

# Remove a package
uv remove package-name

# Update dependencies
uv sync --upgrade

# Run a script (auto-activates venv)
uv run python run.py

# Run tests
uv run pytest
```

## Files Changed

1. **pyproject.toml** - Now includes all dependencies (pip-compatible)
2. **.gitignore** - Added `.venv/` and `uv.lock`
3. **UV_GUIDE.md** - Comprehensive uv documentation
4. **All docs** - Updated with uv commands as primary option

## Backward Compatibility

Good news! The project **still works with pip**:
- `requirements.txt` still exists
- You can use `pip install -r requirements.txt` if needed
- uv and pip can coexist

But we recommend uv for the speed and reliability benefits!

## Next Steps

1. **Install uv** (see commands above)
2. Run `uv venv` to create virtual environment
3. Run `uv sync` to install dependencies
4. Continue with [VERIFICATION.md](VERIFICATION.md)

## Need Help?

See [UV_GUIDE.md](UV_GUIDE.md) for:
- Installation instructions
- Troubleshooting
- Advanced usage
- Comparison with pip

---

**TL;DR:** Run these three commands:
```bash
uv venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
uv sync
```

Then continue with your Phase 1 verification! 🎉
