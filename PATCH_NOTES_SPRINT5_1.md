# Sprint 5.1 — Full Code Patch

## Fixed

The final compliance decision logic in:

```text
backend/app/services/pipeline.py
```

has been rewritten from a compact nested ternary into explicit `if/elif/else` branches.

This avoids subtle operator-precedence and readability issues in governance/control-plane code.

## New logic

```python
if final_score >= 60:
    final_level = "high"
    decision = "flag"
elif final_score >= 25:
    final_level = "medium"
    decision = "allow_with_warning"
elif "candidate_feature_version" in metadata_warnings:
    final_level = "low"
    decision = "allow_with_warning"
else:
    final_level = "low"
    decision = "allow"
```

## Notes

- This package contains the full updated backend code, not just patch notes.
- Provider layer is still OpenAI-only.
- Evidence chain remains best-effort tenant-local.
- Review-task dedupe is primarily service-layer logic.
