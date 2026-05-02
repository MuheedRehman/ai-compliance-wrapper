# Sprint 6A SQLAlchemy Metadata Fix

## Error fixed

```text
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

## Why it happened

SQLAlchemy declarative models reserve the attribute name:

```python
metadata
```

because `Base.metadata` is used internally to represent schema metadata.

The `EvidenceLog` model had:

```python
metadata = Column(JSON, nullable=False, default=dict)
```

which conflicts with SQLAlchemy internals.

## Fix

The Python ORM attribute is now:

```python
request_metadata = Column("metadata", JSON, nullable=False, default=dict)
```

This keeps the database column named `metadata`, but avoids using the reserved Python attribute name.

## Files changed

```text
backend/app/models.py
backend/app/services/evidence_service.py
```

Run:

```powershell
pytest
```
