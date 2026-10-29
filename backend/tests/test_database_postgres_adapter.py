"""
Unit tests for the Database Persistence Layer and PostgreSQL Adapter.
Verifies PostgreSQL connection string resolution, URL standardization,
CursorWrapper parameter placeholder translation (? -> %s),
fallback to /tmp when filesystem is read-only, and PostgreSQL execution paths.
"""
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from services.db import (
    _get_db_url,
    _is_postgres_active,
    _get_sqlite_path,
    CursorWrapper,
    init_db,
    save_prediction,
    save_draft,
    get_connection
)


def test_get_db_url_standardization():
    """Ensures postgres:// URLs are converted to postgresql:// for driver compatibility."""
    with patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"}):
        url = _get_db_url()
        assert url == "postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"

    with patch.dict(os.environ, {"POSTGRES_URL": "postgresql://user:pass@ep-xyz.neon.tech/neondb"}):
        url = _get_db_url()
        assert url == "postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"


def test_is_postgres_active_behavior():
    """Ensures test runs stay on SQLite, while production environment activates Postgres."""
    # When target_db is passed, postgres is never active
    assert not _is_postgres_active(target_db="/tmp/test.db")

    # When TEST_DB_PATH is set in environment, postgres is never active
    with patch.dict(os.environ, {"TEST_DB_PATH": "/tmp/test.db", "DATABASE_URL": "postgres://user:pass@host/db"}):
        assert not _is_postgres_active()

    # When no test markers exist and DATABASE_URL is set, postgres is active
    with patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pass@host/db"}, clear=True):
        assert _is_postgres_active()


def test_cursor_wrapper_placeholder_translation():
    """Verifies that ? placeholders are correctly rewritten to %s in PostgreSQL mode."""
    mock_cursor = MagicMock()
    wrapper = CursorWrapper(mock_cursor, is_postgres=True)

    query = "SELECT * FROM users WHERE email = ? AND role = ?"
    params = ("analyst@security.org", "SecOps Analyst")
    wrapper.execute(query, params)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM users WHERE email = %s AND role = %s",
        params
    )


def test_cursor_wrapper_sqlite_passthrough():
    """Verifies that SQLite execution preserves ? placeholders without rewriting."""
    mock_cursor = MagicMock()
    wrapper = CursorWrapper(mock_cursor, is_postgres=False)

    query = "SELECT * FROM users WHERE email = ? AND role = ?"
    params = ("analyst@security.org", "SecOps Analyst")
    wrapper.execute(query, params)

    mock_cursor.execute.assert_called_once_with(query, params)


def test_sqlite_fallback_on_readonly_filesystem(tmp_path):
    """Ensures /tmp path is returned if the configured DB directory is read-only."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("services.db.DB_PATH", tmp_path / "readonly_dir" / "probmail.db"):
            with patch.object(Path, "mkdir", side_effect=OSError("Read-only file system")):
                resolved_path = _get_sqlite_path()
                assert resolved_path == Path("/tmp/probmail.db")


def test_postgres_init_db_ddl_and_migrations():
    """Verifies that init_db() in PostgreSQL mode executes PostgreSQL DDL and column migrations."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with patch("services.db._is_postgres_active", return_value=True):
        with patch("services.db._create_raw_connection", return_value=(mock_conn, True)):
            init_db()

    # Verify DDL executed contains SERIAL PRIMARY KEY and PostgreSQL table statements
    calls = [c[0][0] for c in mock_cur.execute.call_args_list]
    joined_ddl = " ".join(calls)
    assert "SERIAL PRIMARY KEY" in joined_ddl
    assert "predictions" in joined_ddl
    assert "mailbox_messages" in joined_ddl
    assert "drafts" in joined_ddl
    assert "training_history" in joined_ddl
    assert "ADD COLUMN IF NOT EXISTS" in joined_ddl


def test_postgres_save_prediction_returning_id():
    """Verifies that save_prediction in PostgreSQL mode uses RETURNING id and returns row id."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {"id": 142}
    mock_conn.cursor.return_value = mock_cur

    with patch("services.db._is_postgres_active", return_value=True):
        with patch("services.db._create_raw_connection", return_value=(mock_conn, True)):
            pred_id = save_prediction(
                subject="Test Suspicious Email",
                snippet="Claim prize now",
                predicted_class="spam",
                confidence=98.5,
                owner_id="usr_test_1"
            )

    assert pred_id == 142
    # Verify SQL query used %s and RETURNING id
    call_args = mock_cur.execute.call_args
    sql_query = call_args[0][0]
    assert "RETURNING id" in sql_query
    assert "%s" in sql_query


def test_postgres_save_draft_on_conflict():
    """Verifies that save_draft in PostgreSQL mode uses ON CONFLICT DO UPDATE."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with patch("services.db._is_postgres_active", return_value=True):
        with patch("services.db._create_raw_connection", return_value=(mock_conn, True)):
            draft = save_draft(
                draft_id="drf_123",
                user_id="usr_test_1",
                recipient_email="partner@company.com",
                recipient_name="Partner",
                subject="Draft Subject",
                body="Draft Body"
            )

    assert draft["id"] == "drf_123"
    sql_query = mock_cur.execute.call_args[0][0]
    assert "ON CONFLICT(id) DO UPDATE SET" in sql_query
    assert "EXCLUDED.recipient_email" in sql_query


def test_get_db_url_component_variables():
    """Verifies that discrete POSTGRES_HOST / POSTGRES_USER variables are assembled into a valid URL."""
    env = {
        "POSTGRES_HOST": "ep-cool-db.us-east-2.aws.neon.tech",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "secret_password",
        "POSTGRES_DATABASE": "mailguard_db",
        "POSTGRES_PORT": "5432"
    }
    with patch.dict(os.environ, env, clear=True):
        url = _get_db_url()
        assert url is not None
        assert "postgresql://test_user:secret_password@ep-cool-db.us-east-2.aws.neon.tech:5432/mailguard_db" in url
        assert "sslmode=require" in url


def test_get_db_url_value_scan_and_quotes():
    """Verifies that URLs wrapped in quotes or stored in custom variable names are found."""
    env = {
        "CUSTOM_APP_NEON_URI": "  \"postgres://usr:pwd@neon.tech/appdb\"  "
    }
    with patch.dict(os.environ, env, clear=True):
        url = _get_db_url()
        assert url is not None
        assert url.startswith("postgresql://usr:pwd@neon.tech/appdb")
        assert "sslmode=require" in url


def test_serverless_sqlite_tmp_resolution():
    """Verifies that when running on Vercel, SQLite always resolves to /tmp/probmail.db."""
    with patch.dict(os.environ, {"VERCEL": "1"}, clear=True):
        path = _get_sqlite_path()
        assert path == Path("/tmp/probmail.db")


def test_row_dict_compatibility():
    """Verifies that RowDict supports integer indexing, named access, and dict conversion."""
    from services.db import RowDict
    row = RowDict(["id", "subject", "score"], [101, "Suspicious Invoice", 92.5])
    assert row[0] == 101
    assert row["subject"] == "Suspicious Invoice"
    assert row["score"] == 92.5
    d = dict(row)
    assert d == {"id": 101, "subject": "Suspicious Invoice", "score": 92.5}
    assert set(row.keys()) == {"id", "subject", "score"}

