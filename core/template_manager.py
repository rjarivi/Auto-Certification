import os
import json
import uuid
import config

# ── DB helpers ────────────────────────────────────────────────────────────────

def _db_exec(sql, params=(), fetch=None):
    """Run a single SQL statement. fetch='one'|'all'|None."""
    from core.db import get_conn
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch == 'one':
                return cur.fetchone()
            if fetch == 'all':
                return cur.fetchall()
        conn.commit()


# ── Templates ─────────────────────────────────────────────────────────────────

def save_template(config_dict):
    template_id = config_dict.get('template_id') or str(uuid.uuid4())
    config_dict['template_id'] = template_id

    if config.USE_DB:
        _db_exec(
            """
            INSERT INTO templates (template_id, name, config_json)
            VALUES (%s, %s, %s)
            ON CONFLICT (template_id) DO UPDATE
                SET name = EXCLUDED.name,
                    config_json = EXCLUDED.config_json
            """,
            (template_id, config_dict.get('name', 'Untitled'), json.dumps(config_dict)),
        )
        return template_id

    # Local file fallback
    os.makedirs(config.TEMPLATE_FOLDER, exist_ok=True)
    path = os.path.join(config.TEMPLATE_FOLDER, f'{template_id}.json')
    with open(path, 'w') as f:
        json.dump(config_dict, f, indent=2)
    return template_id


def load_template(template_id):
    if config.USE_DB:
        row = _db_exec(
            'SELECT config_json FROM templates WHERE template_id = %s',
            (template_id,), fetch='one',
        )
        return json.loads(row[0]) if row else None

    path = os.path.join(config.TEMPLATE_FOLDER, f'{template_id}.json')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def list_templates():
    if config.USE_DB:
        rows = _db_exec(
            'SELECT template_id, name FROM templates ORDER BY created_at DESC',
            fetch='all',
        ) or []
        return [{'template_id': r[0], 'name': r[1]} for r in rows]

    os.makedirs(config.TEMPLATE_FOLDER, exist_ok=True)
    templates = []
    for fname in os.listdir(config.TEMPLATE_FOLDER):
        if fname.endswith('.json'):
            with open(os.path.join(config.TEMPLATE_FOLDER, fname)) as f:
                try:
                    t = json.load(f)
                    templates.append({'template_id': t.get('template_id'), 'name': t.get('name', 'Untitled')})
                except Exception:
                    pass
    return templates


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session(excel_key, rows):
    session_id = str(uuid.uuid4())

    if config.USE_DB:
        _db_exec(
            'INSERT INTO sessions (session_id, excel_key, rows_json) VALUES (%s, %s, %s)',
            (session_id, excel_key, json.dumps(rows)),
        )
        return session_id

    os.makedirs(config.SESSION_FOLDER, exist_ok=True)
    data = {'session_id': session_id, 'excel_path': excel_key, 'rows': rows, 'template_id': None}
    _write_session(session_id, data)
    return session_id


def load_session(session_id):
    if config.USE_DB:
        row = _db_exec(
            'SELECT session_id, excel_key, rows_json, template_id FROM sessions WHERE session_id = %s',
            (session_id,), fetch='one',
        )
        if not row:
            return None
        return {
            'session_id': row[0],
            'excel_path': row[1],
            'rows': json.loads(row[2]),
            'template_id': row[3],
        }

    path = os.path.join(config.SESSION_FOLDER, f'{session_id}.json')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def update_session(session_id, key, value):
    if config.USE_DB:
        if key == 'template_id':
            _db_exec(
                'UPDATE sessions SET template_id = %s WHERE session_id = %s',
                (value, session_id),
            )
        else:
            # Generic: load, patch in-memory, re-save rows_json
            session = load_session(session_id) or {}
            session[key] = value
            _db_exec(
                'UPDATE sessions SET rows_json = %s WHERE session_id = %s',
                (json.dumps(session.get('rows', [])), session_id),
            )
        return

    data = load_session(session_id) or {}
    data[key] = value
    _write_session(session_id, data)


def _write_session(session_id, data):
    os.makedirs(config.SESSION_FOLDER, exist_ok=True)
    path = os.path.join(config.SESSION_FOLDER, f'{session_id}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
