Write-Host "Running Sprint 6B release gate..."

pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

alembic downgrade -1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Release gate passed."
