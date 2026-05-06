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

