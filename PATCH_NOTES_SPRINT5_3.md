# Sprint 5.3 — State Transition Fix

## Fixed

### 1. Rejecting current approved version now updates feature pointers

Previously, `reject_feature_version()` checked whether a replacement approved version existed, but did not move:

```python
feature.current_feature_version_id
feature.current_fingerprint
feature.current_prompt_hash
```

to the replacement.

That could leave `AiFeature` pointing at a rejected version.

Now, when rejecting the current approved version and a replacement exists, the feature pointers are updated to the replacement:

```python
feature.current_feature_version_id = replacement.feature_version_id
feature.current_fingerprint = replacement.fingerprint
feature.current_prompt_hash = replacement.prompt_hash
```

### 2. Timestamp semantics made consistent

This patch chooses **current-state timestamp semantics**.

That means:

```text
status = approved    -> approved_at populated
status = superseded  -> superseded_at populated
status = rejected    -> rejected_at populated
```

When an approved version is superseded, this patch now clears:

```python
old_version.approved_at = None
old_version.rejected_at = None
```

When a version is rejected, it clears:

```python
version.approved_at = None
version.superseded_at = None
```

## Note

If you later want full historical lifecycle tracking, add a separate `feature_version_events` table.
