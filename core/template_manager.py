import os
import json
import uuid
from config import TEMPLATE_FOLDER, SESSION_FOLDER


def save_template(config_dict):
    template_id = config_dict.get('template_id') or str(uuid.uuid4())
    config_dict['template_id'] = template_id
    os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
    path = os.path.join(TEMPLATE_FOLDER, f'{template_id}.json')
    with open(path, 'w') as f:
        json.dump(config_dict, f, indent=2)
    return template_id


def load_template(template_id):
    path = os.path.join(TEMPLATE_FOLDER, f'{template_id}.json')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def list_templates():
    os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
    templates = []
    for fname in os.listdir(TEMPLATE_FOLDER):
        if fname.endswith('.json'):
            with open(os.path.join(TEMPLATE_FOLDER, fname)) as f:
                try:
                    t = json.load(f)
                    templates.append({'template_id': t.get('template_id'), 'name': t.get('name', 'Untitled')})
                except Exception:
                    pass
    return templates


def create_session(excel_path, rows):
    session_id = str(uuid.uuid4())
    os.makedirs(SESSION_FOLDER, exist_ok=True)
    data = {'session_id': session_id, 'excel_path': excel_path, 'rows': rows, 'template_id': None}
    _write_session(session_id, data)
    return session_id


def load_session(session_id):
    path = os.path.join(SESSION_FOLDER, f'{session_id}.json')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def update_session(session_id, key, value):
    data = load_session(session_id) or {}
    data[key] = value
    _write_session(session_id, data)


def _write_session(session_id, data):
    os.makedirs(SESSION_FOLDER, exist_ok=True)
    path = os.path.join(SESSION_FOLDER, f'{session_id}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
