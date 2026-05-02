# Windows Implementation Steps — Sprint 5

## 1. Unzip

```powershell
cd $env:USERPROFILE\Downloads
Expand-Archive Sprint5_Tenancy_Version_Integrity.zip -DestinationPath Sprint5_Tenancy_Version_Integrity
cd Sprint5_Tenancy_Version_Integrity\backend
```

## 2. Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

Generate secret:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Set `.env`:

```env
OPENAI_API_KEY=your_openai_key_here
DEFAULT_MODEL=gpt-4.1-nano
DATABASE_URL=sqlite:///./app/data/app.db
APP_ENV=development
FEATURE_ID_ENFORCEMENT=warn
CANDIDATE_VERSION_POLICY=allow_with_warning
EVIDENCE_CHAIN_MODE=best_effort_tenant_chain
EVIDENCE_HMAC_SECRET=paste_generated_secret_here
```

## 3. Initialize DB

```powershell
python scripts\init_db.py
python scripts\seed_dev.py
```

## 4. Run

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## 5. Test keys

App key:

```text
aigw_dev_app_key_123
```

Admin key:

```text
aigw_dev_admin_key_123
```

## 6. Recommended tests

1. Send normal request using `customer_support_bot`.
2. Change prompt and verify candidate version behavior.
3. Set `CANDIDATE_VERSION_POLICY=quarantine` and verify provider is not called.
4. Set `FEATURE_ID_ENFORCEMENT=block` and send missing `feature_id`; verify evidence is written.
5. Re-send same unknown feature multiple times; verify one review task increments `occurrence_count`.
6. Try rejecting current approved version; verify it is blocked unless another version is current.
