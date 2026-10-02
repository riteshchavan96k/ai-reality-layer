# ai-reality-layer
AI Reality Layer — infrastructure for giving autonomous AI systems continuously verified information about the world before they reason, decide, or act.

## Development validation

Install the production and test dependencies through the development requirements file, then run the complete backend regression suite from the repository root:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest
```

GitHub Actions runs the same backend test suite automatically on pushes and pull requests to `main`.

