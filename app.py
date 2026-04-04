import os
import re
import uuid
from flask import (Flask, render_template, request, jsonify,
                   send_from_directory, Response, stream_with_context)
from werkzeug.utils import secure_filename

import config
from core.excel_parser import parse_excel
from core.certificate_generator import render_one, render_all
from core.email_sender import send_all_sse
from core.template_manager import (save_template, load_template, list_templates,
                                    create_session, load_session, update_session)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Ensure required directories exist
for d in [config.UPLOAD_FOLDER, config.BACKGROUND_FOLDER, config.TEMPLATE_FOLDER,
          config.SESSION_FOLDER, config.OUTPUT_FOLDER, config.FONT_FOLDER]:
    os.makedirs(d, exist_ok=True)


def _allowed(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


# ─── Page routes ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload')
def upload_page():
    return render_template('upload.html')


@app.route('/designer')
def designer_page():
    session_id = request.args.get('session_id', '')
    session = load_session(session_id) if session_id else None
    fonts = list(config.BUNDLED_FONTS.items())  # [(filename, display_name), ...]
    templates = list_templates()
    return render_template('designer.html', session_id=session_id, session=session,
                           fonts=fonts, templates=templates)


@app.route('/preview')
def preview_page():
    session_id = request.args.get('session_id', '')
    session = load_session(session_id) if session_id else None
    return render_template('preview.html', session_id=session_id, session=session)


@app.route('/send')
def send_page():
    session_id = request.args.get('session_id', '')
    session = load_session(session_id) if session_id else None
    return render_template('send.html', session_id=session_id, session=session)


# ─── API routes ─────────────────────────────────────────────────────────────────

@app.route('/api/upload-excel', methods=['POST'])
def api_upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'No file selected'}), 400
    if not _allowed(f.filename, config.ALLOWED_EXCEL_EXTENSIONS):
        return jsonify({'error': 'Only .xlsx / .xls files allowed'}), 400

    filename = secure_filename(f.filename)
    filepath = os.path.join(config.UPLOAD_FOLDER, f'{uuid.uuid4()}_{filename}')
    f.save(filepath)

    result = parse_excel(filepath)
    if not result['rows'] and result['errors']:
        return jsonify({'errors': result['errors']}), 422

    session_id = create_session(filepath, result['rows'])
    return jsonify({
        'session_id': session_id,
        'row_count': len(result['rows']),
        'columns': result['columns'],
        'preview_rows': result['rows'][:10],
        'errors': result['errors'],
    })


@app.route('/api/session/<session_id>')
def api_session(session_id):
    session = load_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session)


@app.route('/api/backgrounds')
def api_backgrounds():
    items = []
    for fname in os.listdir(config.BACKGROUND_FOLDER):
        if fname.rsplit('.', 1)[-1].lower() in config.ALLOWED_IMAGE_EXTENSIONS:
            items.append({'filename': fname, 'url': f'/assets/backgrounds/{fname}'})
    return jsonify(items)


@app.route('/api/upload-background', methods=['POST'])
def api_upload_background():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f = request.files['file']
    if not _allowed(f.filename, config.ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({'error': 'Only PNG/JPG allowed'}), 400
    filename = secure_filename(f.filename)
    save_path = os.path.join(config.BACKGROUND_FOLDER, filename)
    f.save(save_path)
    return jsonify({'filename': filename, 'url': f'/assets/backgrounds/{filename}'})


@app.route('/api/save-template', methods=['POST'])
def api_save_template():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    template_id = save_template(data)
    session_id = data.get('session_id')
    if session_id:
        update_session(session_id, 'template_id', template_id)
    return jsonify({'template_id': template_id})


@app.route('/api/templates')
def api_templates():
    return jsonify(list_templates())


@app.route('/api/preview-certificate')
def api_preview_certificate():
    session_id = request.args.get('session_id')
    row_index = int(request.args.get('row_index', 0))

    session = load_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    template_id = session.get('template_id')
    if not template_id:
        return jsonify({'error': 'No template selected'}), 400

    template = load_template(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404

    rows = session.get('rows', [])
    if not rows:
        return jsonify({'error': 'No data rows'}), 400

    row = rows[min(row_index, len(rows) - 1)]
    safe_name = re.sub(r'[^\w\s-]', '', row.get('Name', 'preview')).strip().replace(' ', '_')
    out_path = os.path.join(config.OUTPUT_FOLDER, session_id, f'preview_{row_index}_{safe_name}.png')

    try:
        render_one(template, row, out_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    rel_path = os.path.relpath(out_path, config.OUTPUT_FOLDER)
    return jsonify({
        'image_url': f'/output/{rel_path.replace(os.sep, "/")}',
        'recipient_name': row.get('Name', ''),
        'row_index': row_index,
        'total': len(rows),
    })


@app.route('/api/send-certificates', methods=['POST'])
def api_send_certificates():
    data = request.get_json()
    session_id = data.get('session_id')
    smtp_config = data.get('smtp', {})

    session = load_session(session_id)
    if not session:
        return Response('data: {"type":"error","message":"Session not found"}\n\n',
                        mimetype='text/event-stream')

    template_id = session.get('template_id')
    template = load_template(template_id) if template_id else None
    if not template:
        return Response('data: {"type":"error","message":"No template configured"}\n\n',
                        mimetype='text/event-stream')

    rows = session.get('rows', [])
    out_dir = os.path.join(config.OUTPUT_FOLDER, session_id)
    os.makedirs(out_dir, exist_ok=True)

    def render_fn(row):
        safe = re.sub(r'[^\w\s-]', '', row.get('Name', 'cert')).strip().replace(' ', '_')
        path = os.path.join(out_dir, f'{safe}.png')
        try:
            render_one(template, row, path)
            return path, None
        except Exception as e:
            return None, str(e)

    def generate():
        yield ': keep-alive\n\n'
        for chunk in send_all_sse(rows, template, smtp_config, session_id, render_fn):
            yield chunk

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


# ─── Static file serving ────────────────────────────────────────────────────────

@app.route('/output/<path:filename>')
def serve_output(filename):
    return send_from_directory(config.OUTPUT_FOLDER, filename)


@app.route('/assets/backgrounds/<filename>')
def serve_background(filename):
    return send_from_directory(config.BACKGROUND_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=5000)
