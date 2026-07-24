# Contributing

Thanks for your interest in improving the Adaptive Test-Time Compute Controller.

## Development setup

```bash
python3 -m venv venv
source venv/bin/activate
make install
```

`make install` pulls the runtime dependencies from `requirements.txt` plus the
dev extras (`pytest`, `pytest-asyncio`, `ruff`) declared in `pyproject.toml`.

## Before opening a pull request

Run the same checks CI runs:

```bash
make check      # == ruff check + pytest
```

Or individually:

```bash
make lint       # ruff check backend tests
make test       # pytest
make fmt        # auto-fix lint issues (ruff --fix)
```

The test suite does **not** call the OpenAI API — `generate_samples` is mocked
in the controller tests and the client is constructed lazily, so tests run
offline without an API key.

## Style

- Formatting and linting are enforced by [ruff](https://docs.astral.sh/ruff/);
  the config lives in `pyproject.toml`. Line length is 100.
- Keep the deterministic core (`evaluator.py`, `controller.py`) covered by a
  test whenever you change its behavior.
- Prefer small, self-contained commits with
  [conventional](https://www.conventionalcommits.org/) messages
  (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `ci:`).

## Reporting issues

Please include the strategy used, the config overrides (if any), and — where
relevant — the extracted vs. expected answer, so extraction edge cases can be
reproduced quickly.
