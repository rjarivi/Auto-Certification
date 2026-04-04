import smtplib
import re
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


def _substitute(text, row):
    def replacer(match):
        key = match.group(1).strip()
        return row.get(key, match.group(0))
    return re.sub(r'\{\{([^}]+)\}\}', replacer, text)


def _build_message(smtp_config, row, cert_path):
    msg = MIMEMultipart('mixed')
    sender_name = smtp_config.get('sender_name', '')
    sender_email = smtp_config['sender_email']
    msg['From'] = f'{sender_name} <{sender_email}>' if sender_name else sender_email
    msg['To'] = row['Email']
    msg['Subject'] = _substitute(smtp_config.get('subject', 'Your Certificate'), row)

    body = _substitute(smtp_config.get('body_text', 'Please find your certificate attached.'), row)
    msg.attach(MIMEText(body, 'plain'))

    if cert_path:
        with open(cert_path, 'rb') as f:
            img_data = f.read()
        img_part = MIMEImage(img_data, name='certificate.png')
        img_part.add_header('Content-Disposition', 'attachment', filename='certificate.png')
        msg.attach(img_part)

    return msg


def _get_smtp_connection(smtp_config):
    mode = smtp_config.get('mode', 'gmail')
    if mode == 'gmail':
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(smtp_config['sender_email'], smtp_config['app_password'])
    else:
        host = smtp_config.get('host', 'localhost')
        port = int(smtp_config.get('port', 587))
        use_tls = smtp_config.get('use_tls', True)
        if use_tls:
            server = smtplib.SMTP(host, port)
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP(host, port)
        username = smtp_config.get('username', '')
        password = smtp_config.get('password', '')
        if username and password:
            server.login(username, password)
    return server


def send_all_sse(rows, template_config, smtp_config, session_id, render_fn):
    """
    Generator that yields SSE-formatted strings.
    render_fn(row) -> (output_path, error)
    """
    total = len(rows)

    def sse(data):
        return f'data: {json.dumps(data)}\n\n'

    # Try connecting first
    try:
        server = _get_smtp_connection(smtp_config)
    except Exception as e:
        yield sse({'type': 'error', 'message': f'SMTP connection failed: {str(e)}'})
        return

    sent = 0
    failed = 0

    try:
        for i, row in enumerate(rows):
            yield sse({'type': 'generating', 'index': i, 'total': total, 'name': row.get('Name', '')})

            cert_path, gen_error = render_fn(row)

            if gen_error:
                failed += 1
                yield sse({'type': 'progress', 'index': i, 'total': total,
                           'name': row.get('Name', ''), 'email': row.get('Email', ''),
                           'status': 'failed', 'error': f'Certificate generation failed: {gen_error}'})
                continue

            try:
                msg = _build_message(smtp_config, row, cert_path)
                server.sendmail(smtp_config['sender_email'], row['Email'], msg.as_string())
                sent += 1
                yield sse({'type': 'progress', 'index': i, 'total': total,
                           'name': row.get('Name', ''), 'email': row.get('Email', ''),
                           'status': 'sent'})
            except smtplib.SMTPAuthenticationError:
                failed += 1
                yield sse({'type': 'error', 'message': 'Authentication failed. Check your credentials or App Password.'})
                break
            except Exception as e:
                failed += 1
                yield sse({'type': 'progress', 'index': i, 'total': total,
                           'name': row.get('Name', ''), 'email': row.get('Email', ''),
                           'status': 'failed', 'error': str(e)})
    finally:
        try:
            server.quit()
        except Exception:
            pass

    yield sse({'type': 'done', 'sent': sent, 'failed': failed, 'total': total})
