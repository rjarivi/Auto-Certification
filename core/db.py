import psycopg2
import config


def get_conn():
    """Open and return a new psycopg2 connection."""
    return psycopg2.connect(config.DATABASE_URL)


def db_init():
    """Create tables if they don't exist. Safe to call on every startup."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id  TEXT PRIMARY KEY,
                    excel_key   TEXT,
                    rows_json   TEXT NOT NULL,
                    template_id TEXT,
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    template_id TEXT PRIMARY KEY,
                    name        TEXT NOT NULL DEFAULT 'Untitled',
                    config_json TEXT NOT NULL,
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()
