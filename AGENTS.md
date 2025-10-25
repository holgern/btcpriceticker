# AGENTS.md - Guidelines for BTC Price Ticker

## Commands

- **Run tests:** `pytest`
- **Run single test:** `pytest tests/test_file.py::TestClass::test_method`
- Tests with Coverage: `pytest --cov=btcpriceticker`
- **Ruff**: `ruff check --fix --exit-non-zero-on-fix --config=.ruff.toml`
- **pre-commit**: `pre-commit run --show-diff-on-failure --color=always --all-files`
- **git**: Never use git, never pull, push or commit

## Code Style

- **Formatting:** Use ruff for auto-formatting, line length 88 characters
- **Imports:** Organized in sections: future, standard-library, third-party,
  first-party, local-folder
- **Types:** Python 3.9+ type hints encouraged
- **Error handling:** Use appropriate try/except blocks, return boolean success flags
- **Naming:**
  - snake_case for functions/variables
  - CamelCase for classes
  - Service-specific implementations in dedicated modules
- **Testing:** unittest framework with mocking, patch decorators for external services

## Repository Structure

- Core functionality in `/btcpriceticker/`
- Tests in `/tests/` mirroring main module structure
- Command-line interface in `cli.py`
