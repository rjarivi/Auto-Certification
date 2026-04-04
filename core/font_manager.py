"""
Font registry + helpers for downloading Google Fonts and registering custom
uploaded TTF/OTF files.

Font IDs (e.g. "PlayfairDisplay") map to a filesystem file
  FONT_FOLDER/<id>.ttf  (or .otf / .woff2)
and a metadata entry in  data/fonts.json.

Both Pillow (backend rendering) and the browser canvas (designer preview)
use the same downloaded file — Pillow reads the TTF from disk, the browser
loads it via an injected @font-face rule pointing to /static/fonts/<filename>.
"""
import os, re, json, urllib.request, urllib.parse, urllib.error
import config

_DATA_DIR = os.path.join(config.BASE_DIR, 'data')
_REGISTRY  = os.path.join(_DATA_DIR, 'fonts.json')

# ── Bundled fonts (always present, not written to fonts.json) ─────────────────
BUNDLED = {
    'DejaVuSerif': {
        'display_name': 'DejaVu Serif',
        'css_family':   'Georgia, "Times New Roman", serif',
        'bold': False, 'source': 'bundled', 'filename': 'DejaVuSerif.ttf',
    },
    'DejaVuSerif-Bold': {
        'display_name': 'DejaVu Serif Bold',
        'css_family':   'Georgia, "Times New Roman", serif',
        'bold': True,  'source': 'bundled', 'filename': 'DejaVuSerif-Bold.ttf',
    },
    'DejaVuSans': {
        'display_name': 'DejaVu Sans',
        'css_family':   'Helvetica, Arial, sans-serif',
        'bold': False, 'source': 'bundled', 'filename': 'DejaVuSans.ttf',
    },
    'DejaVuSans-Bold': {
        'display_name': 'DejaVu Sans Bold',
        'css_family':   'Helvetica, Arial, sans-serif',
        'bold': True,  'source': 'bundled', 'filename': 'DejaVuSans-Bold.ttf',
    },
}


def load_registry() -> dict:
    """Bundled fonts + custom/google fonts from data/fonts.json."""
    reg = dict(BUNDLED)
    if os.path.exists(_REGISTRY):
        try:
            with open(_REGISTRY) as f:
                reg.update(json.load(f))
        except Exception:
            pass
    return reg


def list_fonts() -> list:
    """Return a list of font dicts for use in templates and JS."""
    reg = load_registry()
    return [{'id': k, **v} for k, v in reg.items()]


def _save_entry(font_id: str, entry: dict):
    os.makedirs(_DATA_DIR, exist_ok=True)
    custom = {}
    if os.path.exists(_REGISTRY):
        try:
            with open(_REGISTRY) as f:
                custom = json.load(f)
        except Exception:
            pass
    custom[font_id] = entry
    with open(_REGISTRY, 'w') as f:
        json.dump(custom, f, indent=2)


# ── Google Fonts download ─────────────────────────────────────────────────────

# Old Safari UA → Google Fonts returns TTF instead of WOFF2
_UA_TTF = (
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; de-at) '
    'AppleWebKit/533.21.1 (KHTML, like Gecko) Version/5.0.5 Safari/533.21.1'
)


def download_google_font(family_input: str) -> tuple:
    """
    Download a Google Font TTF to FONT_FOLDER and register it.

    family_input may be:
      - A font family name:  "Playfair Display"
      - A Google Fonts URL:  "https://fonts.google.com/specimen/Playfair+Display"

    Returns (font_id, display_name, filename).
    """
    family_name = family_input.strip()

    # Extract name from Google Fonts page URL
    if 'fonts.google.com' in family_name:
        m = re.search(r'/specimen/([^?#/]+)', family_name)
        if m:
            family_name = m.group(1).replace('+', ' ').replace('_', ' ')
        else:
            raise ValueError('Could not extract font name from that URL')

    if not family_name:
        raise ValueError('Font family name is empty')

    # CSS API v1 with old UA → TTF format
    api_url = ('https://fonts.googleapis.com/css?family='
               + urllib.parse.quote(family_name)
               + '&subset=latin')
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': _UA_TTF})
        with urllib.request.urlopen(req, timeout=15) as resp:
            css = resp.read().decode('utf-8')
    except urllib.error.HTTPError as exc:
        raise ValueError(
            f'Google Fonts returned HTTP {exc.code} — is "{family_name}" spelled correctly?')
    except Exception as exc:
        raise ValueError(f'Could not reach Google Fonts: {exc}')

    # Pull first font URL from the CSS (prefer TTF/OTF)
    ttf_urls = re.findall(
        r'url\((https://fonts\.gstatic\.com/[^)]+\.(?:ttf|otf))\)', css)
    any_urls = re.findall(
        r'url\((https://fonts\.gstatic\.com/[^)]+)\)', css)

    if ttf_urls:
        font_url, ext = ttf_urls[0], ttf_urls[0].rsplit('.', 1)[-1]
    elif any_urls:
        font_url = any_urls[0]
        raw_ext = font_url.rsplit('.', 1)[-1].split('?')[0]
        ext = raw_ext if raw_ext in {'ttf', 'otf', 'woff', 'woff2'} else 'ttf'
    else:
        raise ValueError(
            f'No downloadable font URL found for "{family_name}". '
            'Try uploading a TTF file manually.')

    # Derive a safe font ID (filename stem)
    font_id = re.sub(r'[^A-Za-z0-9]', '', family_name)   # "PlayfairDisplay"
    filename = f'{font_id}.{ext}'
    dest = os.path.join(config.FONT_FOLDER, filename)
    os.makedirs(config.FONT_FOLDER, exist_ok=True)

    # Download
    try:
        dl_req = urllib.request.Request(font_url, headers={'User-Agent': _UA_TTF})
        with urllib.request.urlopen(dl_req, timeout=20) as resp:
            data = resp.read()
        with open(dest, 'wb') as f:
            f.write(data)
    except Exception as exc:
        raise ValueError(f'Failed to download font file: {exc}')

    entry = {
        'display_name':   family_name,
        'css_family':     f'"{family_name}", serif',
        'bold':           False,
        'source':         'google',
        'filename':       filename,
        'google_family':  family_name,
    }
    _save_entry(font_id, entry)
    return font_id, family_name, filename


# ── Uploaded font registration ────────────────────────────────────────────────

def register_uploaded_font(filename: str, display_name: str = '') -> tuple:
    """
    Register a font file already saved to FONT_FOLDER.
    Returns (font_id, display_name).
    """
    stem = filename.rsplit('.', 1)[0]
    font_id = re.sub(r'[^A-Za-z0-9_-]', '', stem)
    if not font_id:
        raise ValueError('Invalid font filename')

    if not display_name:
        # "PlayfairDisplay" → "Playfair Display"
        display_name = re.sub(r'([A-Z])', r' \1', font_id).strip()
        display_name = re.sub(r'[-_]+', ' ', display_name)

    entry = {
        'display_name': display_name,
        'css_family':   f'"{display_name}", serif',
        'bold':         False,
        'source':       'upload',
        'filename':     filename,
    }
    _save_entry(font_id, entry)
    return font_id, display_name
