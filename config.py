import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER    = os.path.join(BASE_DIR, 'uploads', 'excel')
BACKGROUND_FOLDER = os.path.join(BASE_DIR, 'assets', 'backgrounds')
TEMPLATE_FOLDER  = os.path.join(BASE_DIR, 'data', 'templates')
SESSION_FOLDER   = os.path.join(BASE_DIR, 'data', 'sessions')
OUTPUT_FOLDER    = os.path.join(BASE_DIR, 'output')
FONT_FOLDER      = os.path.join(BASE_DIR, 'static', 'fonts')

MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

REQUIRED_COLUMNS = ['Name', 'Email', 'Course/Event', 'Date']

# Fonts bundled with the app (filename without extension → display name)
BUNDLED_FONTS = {
    'DejaVuSerif':        'DejaVu Serif',
    'DejaVuSerif-Bold':   'DejaVu Serif Bold',
    'DejaVuSans':         'DejaVu Sans',
    'DejaVuSans-Bold':    'DejaVu Sans Bold',
}
