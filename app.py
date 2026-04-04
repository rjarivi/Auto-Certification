import os
import re
import uuid
import tempfile
from flask import (Flask, render_template, request, jsonify,
                   send_from_directory, Response, stream_with_context)
from werkzeug.utils import secure_filename

import config
from core.excel_parser import parse_excel
from core.certificate_generator import render_one, render_to_bytes
from core.email_sender import send_all_sse
from core.template_manager import (save_template, load_template, list_templates,
                                    create_session, load_session, update_session)
from core import storage
from core.font_manager import list_fonts, download_google_font, register_uploaded_font

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# ── Startup ───────────────────────────────────────────────────────────────────

if config.USE_DB:
    from core.db import db_init
    try:
        db_init()
    except Exception as e:
        print(f'WARNING: db_init() failed: {e}', flush=True)

try:
    from core.builtin_templates import ensure_builtins_registered
    ensure_builtins_registered()
except Exception as e:
    import traceback
    print(f'WARNING: ensure_builtins_registered() failed: {traceback.format_exc()}', flush=True)

# In local dev mode ensure writable directories exist
if not config.USE_S3:
    for d in [config.UPLOAD_FOLDER, config.BACKGROUND_FOLDER,
              config.OUTPUT_FOLDER, config.FONT_FOLDER]:
        os.makedirs(d, exist_ok=True)

if not config.USE_DB:
    for d in [config.TEMPLATE_FOLDER, config.SESSION_FOLDER]:
        os.makedirs(d, exist_ok=True)


def _allowed(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


@app.errorhandler(500)
def internal_error(e):
    import traceback
    tb = traceback.format_exc()
    print(tb, flush=True)
    if request.path.startswith('/api/'):
        return jsonify({'error': str(e), 'detail': tb}), 500
    return f'<pre>500 Error:\n{tb}</pre>', 500


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
    try:
        session   = load_session(session_id) if session_id else None
        templates = list_templates()
    except Exception as e:
        import traceback
        return f'<pre>Designer error:\n{traceback.format_exc()}</pre>', 500
    fonts = list_fonts()
    return render_template('designer.html', session_id=session_id, session=session,
                           fonts=fonts, templates=templates)


@app.route('/preview')
def preview_page():
    session_id = request.args.get('session_id', '')
    session    = load_session(session_id) if session_id else None
    return render_template('preview.html', session_id=session_id, session=session)


@app.route('/templates')
def gallery_page():
    session_id = request.args.get('session_id', '')
    return render_template('gallery.html', session_id=session_id, show_steps=False)


@app.route('/send')
def send_page():
    session_id = request.args.get('session_id', '')
    session    = load_session(session_id) if session_id else None
    ses_configured = bool(config.SES_FROM_EMAIL)
    return render_template('send.html', session_id=session_id, session=session,
                           ses_configured=ses_configured)


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

    try:
        if config.USE_S3:
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                f.save(tmp.name)
                tmp_path = tmp.name
            result   = parse_excel(tmp_path)
            s3_key   = f'uploads/{uuid.uuid4()}_{filename}'
            storage.upload_file(tmp_path, s3_key)
            os.unlink(tmp_path)
            excel_key = s3_key
        else:
            filepath  = os.path.join(config.UPLOAD_FOLDER, f'{uuid.uuid4()}_{filename}')
            f.save(filepath)
            result    = parse_excel(filepath)
            excel_key = filepath
    except Exception as e:
        return jsonify({'error': f'Server error during upload: {str(e)}'}), 500

    if not result['rows'] and result['errors']:
        return jsonify({'errors': result['errors']}), 422

    try:
        session_id = create_session(excel_key, result['rows'])
    except Exception as e:
        return jsonify({'error': f'Failed to create session: {str(e)}'}), 500

    return jsonify({
        'session_id':   session_id,
        'row_count':    len(result['rows']),
        'columns':      result['columns'],
        'preview_rows': result['rows'][:10],
        'errors':       result['errors'],
    })


@app.route('/api/session/<session_id>')
def api_session(session_id):
    session = load_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session)


@app.route('/api/backgrounds')
def api_backgrounds():
    return jsonify(storage.list_files('backgrounds/'))


@app.route('/api/upload-background', methods=['POST'])
def api_upload_background():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f = request.files['file']
    if not _allowed(f.filename, config.ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({'error': 'Only PNG/JPG allowed'}), 400
    filename = secure_filename(f.filename)
    s3_key   = f'backgrounds/{filename}'
    url      = storage.upload_bytes(f.read(), s3_key, content_type=f.content_type or 'image/png')
    return jsonify({'filename': filename, 'url': url})


@app.route('/api/fonts')
def api_fonts():
    return jsonify(list_fonts())


@app.route('/api/add-google-font', methods=['POST'])
def api_add_google_font():
    data = request.get_json() or {}
    family_input = data.get('family', '').strip()
    if not family_input:
        return jsonify({'error': 'Font family name or URL required'}), 400
    try:
        font_id, display_name, filename = download_google_font(family_input)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {e}'}), 500
    return jsonify({'font_id': font_id, 'display_name': display_name, 'filename': filename})


@app.route('/api/upload-font', methods=['POST'])
def api_upload_font():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'No filename'}), 400
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
    if ext not in {'ttf', 'otf', 'woff', 'woff2'}:
        return jsonify({'error': 'Only TTF, OTF, WOFF, or WOFF2 files allowed'}), 400
    filename  = secure_filename(f.filename)
    dest_path = os.path.join(config.FONT_FOLDER, filename)
    os.makedirs(config.FONT_FOLDER, exist_ok=True)
    f.save(dest_path)
    display_name = request.form.get('display_name', '').strip()
    try:
        font_id, display_name = register_uploaded_font(filename, display_name)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'font_id': font_id, 'display_name': display_name, 'filename': filename})


@app.route('/api/health')
def api_health():
    """Diagnostic endpoint — tests storage and DB connections."""
    result = {
        'USE_S3': config.USE_S3,
        'USE_DB': config.USE_DB,
        'storage_endpoint': config.STORAGE_ENDPOINT_URL or 'AWS S3',
        'bucket': config.S3_BUCKET_NAME,
    }
    if config.USE_S3:
        try:
            storage.list_files('backgrounds/')
            result['storage'] = 'OK'
        except Exception as e:
            result['storage'] = f'ERROR: {str(e)}'
    if config.USE_DB:
        try:
            from core.db import get_conn
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
            result['database'] = 'OK'
        except Exception as e:
            result['database'] = f'ERROR: {str(e)}'
    return jsonify(result)


@app.route('/api/save-template', methods=['POST'])
def api_save_template():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    template_id = save_template(data)
    session_id  = data.get('session_id')
    if session_id:
        update_session(session_id, 'template_id', template_id)
    return jsonify({'template_id': template_id})


@app.route('/api/templates')
def api_templates():
    return jsonify(list_templates())


@app.route('/api/builtin-templates')
def api_builtin_templates():
    from core.builtin_templates import BUILTIN_TEMPLATES
    result = []
    for tmpl in BUILTIN_TEMPLATES:
        result.append({
            'template_id': tmpl['template_id'],
            'name':        tmpl['name'],
            'category':    tmpl['category'],
            'orientation': tmpl['orientation'],
            'width':       tmpl['width'],
            'height':      tmpl['height'],
            'thumb_url':   storage.get_url(tmpl['thumb_key']),
        })
    return jsonify(result)


@app.route('/api/template/<template_id>')
def api_get_template(template_id):
    template = load_template(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    bg_id = template.get('background_id', '')
    if bg_id:
        template['background_url'] = storage.get_url(f'backgrounds/{bg_id}')
    return jsonify(template)


@app.route('/api/preview-certificate')
def api_preview_certificate():
    session_id = request.args.get('session_id')
    row_index  = int(request.args.get('row_index', 0))

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

    row       = rows[min(row_index, len(rows) - 1)]
    safe_name = re.sub(r'[^\w\s-]', '', row.get('Name', 'preview')).strip().replace(' ', '_')

    try:
        if config.USE_S3:
            png_bytes = render_to_bytes(template, row)
            s3_key    = f'outputs/{session_id}/preview_{row_index}_{safe_name}.png'
            image_url = storage.upload_bytes(png_bytes, s3_key, 'image/png')
        else:
            out_path  = os.path.join(config.OUTPUT_FOLDER, session_id,
                                     f'preview_{row_index}_{safe_name}.png')
            render_one(template, row, out_path)
            rel = os.path.relpath(out_path, config.OUTPUT_FOLDER)
            image_url = f'/output/{rel.replace(os.sep, "/")}'
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'image_url':      image_url,
        'recipient_name': row.get('Name', ''),
        'row_index':      row_index,
        'total':          len(rows),
    })


@app.route('/api/send-certificates', methods=['POST'])
def api_send_certificates():
    data        = request.get_json()
    session_id  = data.get('session_id')
    smtp_config = data.get('smtp', {})

    # If SES mode, inject server-side sender email
    if smtp_config.get('mode') == 'ses':
        smtp_config['sender_email'] = config.SES_FROM_EMAIL

    session = load_session(session_id)
    if not session:
        return Response('data: {"type":"error","message":"Session not found"}\n\n',
                        mimetype='text/event-stream')

    template_id = session.get('template_id')
    template    = load_template(template_id) if template_id else None
    if not template:
        return Response('data: {"type":"error","message":"No template configured"}\n\n',
                        mimetype='text/event-stream')

    rows = session.get('rows', [])

    if not config.USE_S3:
        out_dir = os.path.join(config.OUTPUT_FOLDER, session_id)
        os.makedirs(out_dir, exist_ok=True)

    def render_fn(row):
        safe = re.sub(r'[^\w\s-]', '', row.get('Name', 'cert')).strip().replace(' ', '_')
        if config.USE_S3:
            try:
                png_bytes = render_to_bytes(template, row)
                s3_key    = f'outputs/{session_id}/{safe}.png'
                storage.upload_bytes(png_bytes, s3_key, 'image/png')
                return png_bytes, None   # return bytes so email_sender attaches in-memory
            except Exception as e:
                return None, str(e)
        else:
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


# ─── Static file serving (local dev only) ────────────────────────────────────

if not config.USE_S3:
    @app.route('/builtin_thumbs/<filename>')
    def serve_builtin_thumb(filename):
        thumb_dir = os.path.join(config.BASE_DIR, 'builtin_thumbs')
        return send_from_directory(thumb_dir, filename)

    @app.route('/backgrounds/<filename>')
    def serve_background_local(filename):
        return send_from_directory(config.BACKGROUND_FOLDER, filename)

    @app.route('/output/<path:filename>')
    def serve_output_local(filename):
        return send_from_directory(config.OUTPUT_FOLDER, filename)

    # Keep legacy /assets/backgrounds/ URL working for local dev
    @app.route('/assets/backgrounds/<filename>')
    def serve_background_legacy(filename):
        return send_from_directory(config.BACKGROUND_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=5000)
