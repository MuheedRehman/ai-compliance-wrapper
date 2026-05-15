import os
import importlib
import pytest
from unittest.mock import patch, mock_open

from app.config import get_secret
import app.config


def test_get_secret_from_file():
    with patch("os.path.isfile", return_value=True):
        with patch("builtins.open", mock_open(read_data="secret_value_from_file\n")):
            assert get_secret("ANY_SECRET") == "secret_value_from_file"


def test_get_secret_fallback_to_env():
    with patch("os.path.isfile", return_value=False):
        with patch.dict(os.environ, {"ANY_SECRET": "secret_value_from_env"}):
            assert get_secret("ANY_SECRET") == "secret_value_from_env"


def test_missing_hmac_secret_raises():
    with patch("os.path.isfile", return_value=False):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="EVIDENCE_HMAC_SECRET is missing"):
                importlib.reload(app.config)
    
    # Restore the config so other tests don't fail
    importlib.reload(app.config)


def test_production_config_rejects_mock_and_weak_defaults(monkeypatch):
    monkeypatch.setattr(app.config, "APP_ENV", "production")
    monkeypatch.setattr(app.config, "DATABASE_URL", "sqlite:///./app/data/app.db")
    monkeypatch.setattr(app.config, "EVIDENCE_HMAC_SECRET", "short-secret")
    monkeypatch.setattr(app.config, "STRIPE_API_KEY", "sk_test_mock")
    monkeypatch.setattr(app.config, "STRIPE_WEBHOOK_SECRET", "whsec_mock")
    monkeypatch.setattr(app.config, "FRONTEND_URL", "*")
    monkeypatch.setattr(app.config, "AI_PROVIDER_MODE", "demo")

    with pytest.raises(RuntimeError, match="Production APP_ENV cannot use a SQLite DATABASE_URL"):
        app.config.validate_runtime_config()


def test_production_config_accepts_strong_runtime_settings(monkeypatch):
    monkeypatch.setattr(app.config, "APP_ENV", "production")
    monkeypatch.setattr(app.config, "DATABASE_URL", "postgresql+psycopg2://user:pass@localhost/db")
    monkeypatch.setattr(app.config, "EVIDENCE_HMAC_SECRET", "x" * 32)
    monkeypatch.setattr(app.config, "STRIPE_API_KEY", "sk_live_real")
    monkeypatch.setattr(app.config, "STRIPE_WEBHOOK_SECRET", "whsec_real")
    monkeypatch.setattr(app.config, "FRONTEND_URL", "https://dashboard.example")
    monkeypatch.setattr(app.config, "AI_PROVIDER_MODE", "live")
    monkeypatch.setattr(app.config, "OPENAI_API_KEY", "sk-live-test")

    app.config.validate_runtime_config()


def test_db_sqlite_branch_behavior():
    from app.db import create_app_engine
    from unittest.mock import patch
    
    with patch("app.db.create_engine") as mock_create_engine:
        create_app_engine("sqlite:///./app/data/test.db")
        
        mock_create_engine.assert_called_once_with(
            "sqlite:///./app/data/test.db",
            connect_args={"check_same_thread": False},
            pool_pre_ping=True
        )


def test_db_postgres_pooling_branch_behavior():
    from app.db import create_app_engine
    
    database_url = "postgresql+psycopg2://user:pass@/dbname?host=/cloudsql/project:region:instance"
    engine = create_app_engine(database_url)
        
    assert engine.url.get_backend_name() == "postgresql"
    assert engine.pool.size() == 5
    assert hasattr(engine.pool, "_max_overflow")
    assert engine.pool._max_overflow == 10
    assert engine.pool._timeout == 30
    assert engine.pool._recycle == 1800
