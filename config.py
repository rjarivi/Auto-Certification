import os
from dotenv import load_dotenv

load_dotenv()  # no-op in production where env vars are already set

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# ── Object storage (AWS S3 or Cloudflare R2) ──────────────────────────────────
# Works for both — R2 is S3-compatible.
# For AWS S3:  set AWS_REGION + S3_BUCKET_NAME, leave STORAGE_ENDPOINT_URL blank.
# For R2:      set STORAGE_ENDPOINT_URL, STORAGE_PUBLIC_URL, S3_BUCKET_NAME,
#              and use R2 API credentials for AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY.
AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_REGION            = os.environ.get('AWS_REGION', 'auto')
S3_BUCKET_NAME        = os.environ.get('S3_BUCKET_NAME', '')

# R2-specific: endpoint and public URL (leave blank when using plain AWS S3)
STORAGE_ENDPOINT_URL = os.environ.get('STORAGE_ENDPOINT_URL', '')   # e.g. https://<id>.r2.cloudflarestorage.com
STORAGE_PUBLIC_URL   = os.environ.get('STORAGE_PUBLIC_URL', '')     # e.g. https://pub-xxx.r2.dev  (no trailing slash)

# ── AWS SES ───────────────────────────────────────────────────────────────────
SES_REGION     = os.environ.get('SES_REGION', AWS_REGION)
SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', '')

# ── Feature flags ─────────────────────────────────────────────────────────────
USE_S3 = bool(S3_BUCKET_NAME)
USE_DB = bool(DATABASE_URL)

# ── Local-dev fallback paths (used only when USE_S3 / USE_DB are False) ───────
UPLOAD_FOLDER     = os.path.join(BASE_DIR, 'uploads', 'excel')
BACKGROUND_FOLDER = os.path.join(BASE_DIR, 'backgrounds')
TEMPLATE_FOLDER   = os.path.join(BASE_DIR, 'data', 'templates')
SESSION_FOLDER    = os.path.join(BASE_DIR, 'data', 'sessions')
OUTPUT_FOLDER     = os.path.join(BASE_DIR, 'output')
FONT_FOLDER       = os.path.join(BASE_DIR, 'static', 'fonts')

# ── Upload limits & allowed types ─────────────────────────────────────────────
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

REQUIRED_COLUMNS = ['Name', 'Email', 'Course/Event', 'Date']

# ── Bundled fonts (filename without extension → display name) ─────────────────
BUNDLED_FONTS = {
    'DejaVuSerif':        'DejaVu Serif',
    'DejaVuSerif-Bold':   'DejaVu Serif Bold',
    'DejaVuSans':         'DejaVu Sans',
    'DejaVuSans-Bold':    'DejaVu Sans Bold',
}
