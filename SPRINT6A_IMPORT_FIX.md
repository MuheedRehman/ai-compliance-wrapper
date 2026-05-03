# Sprint 6A Import Fix

If pytest says:

```text
ModuleNotFoundError: No module named 'app'
```

it means Python cannot see the backend root as an import path.

This package fixes it in two ways:

1. `pytest.ini` includes:

```ini
pythonpath = .
```

2. `tests/conftest.py` inserts the backend root into `sys.path` before importing `app`.

Run tests from the `backend` folder:

```powershell
pytest
```

Alternative manual command:

```powershell
$env:PYTHONPATH="."
pytest
```
