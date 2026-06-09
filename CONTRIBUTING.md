# Contributing to PortPilot

Thanks for your interest in making PortPilot better! 🎉

## Workflow

1. **Open an issue first** for non-trivial changes so we can align on direction.
2. Fork & branch off `main` using a descriptive name:
   - `feature/<short-desc>` for new functionality
   - `bugfix/<short-desc>` for fixes
   - `docs/<short-desc>` for documentation
3. Keep commits focused and write clear messages.
4. Open a pull request and link the related issue.

## Code Style

- **Python**: PEP 8, enforced by `ruff`. Run `ruff check src tests` before pushing.
- **Function length**: prefer < 80 lines.
- **Line length**: ≤ 100 characters.
- **Type hints**: required for public functions.
- **Docstrings**: Google or NumPy style; single-line is fine for trivial helpers.

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

Add tests in `tests/` for any new logic. Pure functions (e.g. parsers) should
have direct unit tests; integration with `psutil` can be smoke-tested.

## Front-end

The dashboard is a single `static/index.html`. We deliberately avoid a build
step. If you need to add JS, prefer plain Alpine.js components.

## Reporting Bugs

Please include:
- macOS / Linux version
- Python version
- Output of `python -m portpilot.server --port <whatever>`
- Steps to reproduce
