# Sprint 6A SQLite Lock Fix

## Error fixed

```text
sqlite3.OperationalError: database is locked
```

## Why it happened

The provider-failure path writes evidence using an independent DB session so provider-error evidence survives rollback.

That is correct for audit durability, but in SQLite local tests, the main request session may still hold a write lock after flushing auth/feature state. When the independent session tries to insert provider-error evidence, SQLite raises:

```text
database is locked
```

## Fix

In the provider exception branch of `app/services/pipeline.py`, the main request transaction now rolls back before writing provider-error evidence independently:

```python
db.rollback()
event = write_failure_evidence_independently(event_data)
```

## Why this is acceptable

Provider failure semantics are:

```text
Partial request state is discarded.
Provider-error evidence survives.
```

That is the intended governance behavior.

## Files changed

```text
backend/app/services/pipeline.py
```
