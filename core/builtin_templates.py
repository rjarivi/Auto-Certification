"""
Built-in certificate templates programmatically drawn with Pillow.
No external image files required — every template is generated from scratch.
"""
import io
import math
import os
from PIL import Image, ImageDraw, ImageFont
import config


# ── Helpers ───────────────────────────────────────────────────────────────────

def _font(name, size):
    ttf = os.path.join(config.FONT_FOLDER, name + '.ttf')
    try:
        if os.path.exists(ttf):
            return ImageFont.truetype(ttf, int(size))
    except Exception:
        pass
    try:
        return ImageFont.load_default(size=int(size))
    except Exception:
        return ImageFont.load_default()


def _rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _center(draw, text, font, y, width, color):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw, _ = draw.textsize(text, font=font)
    draw.text(((width - tw) // 2, y), text, font=font, fill=color)


# ── Template 1: Classic Elegance — Horizontal (1200×850) ─────────────────────

def _draw_classic_elegance_h():
    W, H = 1200, 850
    img = Image.new('RGB', (W, H), _rgb('#FFFDF5'))
    d = ImageDraw.Draw(img)
    gold = _rgb('#B8860B')
    lg   = _rgb('#D4AF37')
    dark = _rgb('#2C1810')
    gray = _rgb('#9B8565')

    # Double border
    d.rectangle([18, 18, W-18, H-18], outline=gold, width=3)
    d.rectangle([30, 30, W-30, H-30], outline=lg, width=1)

    # Corner ornaments
    for cx, cy in [(50, 50), (W-50, 50), (50, H-50), (W-50, H-50)]:
        d.ellipse([cx-13, cy-13, cx+13, cy+13], outline=gold, width=2)
        d.ellipse([cx-6, cy-6, cx+6, cy+6], fill=gold)

    # Top ornamental lines
    for offset, w, col in [(110, 1, lg), (114, 2, gold), (118, 1, lg)]:
        d.line([(75, offset), (W-75, offset)], fill=col, width=w)

    # Header
    _center(d, 'CERTIFICATE  OF  ACHIEVEMENT', _font('DejaVuSerif-Bold', 22), 55, W, gold)
    _center(d, '—', _font('DejaVuSerif', 18), 142, W, lg)
    _center(d, 'This is to certify that', _font('DejaVuSerif', 17), 168, W, dark)

    # Bottom ornamental lines
    for offset, w, col in [(H-118, 1, lg), (H-114, 2, gold), (H-110, 1, lg)]:
        d.line([(75, offset), (W-75, offset)], fill=col, width=w)

    # Signature blocks
    for x_c in [W // 4, 3 * W // 4]:
        d.line([(x_c-90, H-74), (x_c+90, H-74)], fill=lg, width=1)
    d.text((W//4-63, H-62), 'Director / Organizer', font=_font('DejaVuSerif', 10), fill=gray)
    d.text((3*W//4-18, H-62), 'Date', font=_font('DejaVuSerif', 10), fill=gray)
    return img


# ── Template 2: Modern Minimal — Horizontal (1200×850) ───────────────────────

def _draw_modern_minimal_h():
    W, H = 1200, 850
    img = Image.new('RGB', (W, H), _rgb('#FFFFFF'))
    d = ImageDraw.Draw(img)
    gold = _rgb('#C8923A')
    pale = _rgb('#FEF3C7')
    gray = _rgb('#6B7280')

    d.rectangle([0, 0, W, 8], fill=gold)
    d.rectangle([0, 8, W, 18], fill=pale)
    d.rectangle([0, H-18, W, H-8], fill=pale)
    d.rectangle([0, H-8, W, H], fill=gold)

    # Left accent stripe
    d.rectangle([66, 88, 71, H-88], fill=_rgb('#F0D9B5'))

    # Corner label
    d.text((90, 34), 'C E R T I F I C A T E', font=_font('DejaVuSans-Bold', 14), fill=gold)
    d.text((90, 58), 'of Achievement', font=_font('DejaVuSans', 11), fill=gray)

    _center(d, 'This is to certify that', _font('DejaVuSans', 16), 158, W, gray)

    # Signature line
    d.line([(755, H-68), (965, H-68)], fill=_rgb('#D1D5DB'), width=1)
    d.text((762, H-55), 'Authorized Signature', font=_font('DejaVuSans', 10), fill=gray)
    return img


# ── Template 3: Corporate Navy — Horizontal (1200×850) ───────────────────────

def _draw_corporate_navy_h():
    W, H = 1200, 850
    img = Image.new('RGB', (W, H), _rgb('#FFFFFF'))
    d = ImageDraw.Draw(img)
    navy   = _rgb('#0A2342')
    gold   = _rgb('#C8923A')
    lbblue = _rgb('#7FB3D3')

    # Sidebar
    sw = 292
    d.rectangle([0, 0, sw, H], fill=navy)
    d.rectangle([sw, 0, sw+5, H], fill=gold)
    d.rectangle([sw+5, 0, W, 6], fill=gold)

    # Sidebar circle ornament
    cx, cy, r = sw // 2, H // 2, 58
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=gold, width=2)
    d.ellipse([cx-r+14, cy-r+14, cx+r-14, cy+r-14], outline=_rgb('#1E3A5F'), width=1)
    _center(d, 'CERTIFIED', _font('DejaVuSans-Bold', 12), cy+70, sw, gold)
    _center(d, 'PROFESSIONAL', _font('DejaVuSans', 9), cy+90, sw, lbblue)

    # Sidebar accent dots
    for dy in [65, 100, H-100, H-65]:
        d.ellipse([cx-3, dy-3, cx+3, dy+3], fill=gold)

    # Main area
    mx = sw + 32
    d.text((mx, 30), 'ORGANIZATION NAME', font=_font('DejaVuSerif', 14), fill=navy)
    d.line([(mx, 66), (W-50, 66)], fill=_rgb('#E2E8F0'), width=1)
    d.text((mx, 86), 'This is to certify that', font=_font('DejaVuSerif', 14), fill=_rgb('#6B7280'))

    # Bottom signature
    d.line([(mx+20, H-84), (mx+240, H-84)], fill=_rgb('#CBD5E1'), width=1)
    d.text((mx+30, H-72), 'Authorized Signature', font=_font('DejaVuSans', 10), fill=_rgb('#94A3B8'))
    return img


# ── Template 4: Emerald Professional — Horizontal (1200×850) ─────────────────

def _draw_emerald_professional_h():
    W, H = 1200, 850
    img = Image.new('RGB', (W, H), _rgb('#F0FDF4'))
    d = ImageDraw.Draw(img)
    em    = _rgb('#065F46')
    em2   = _rgb('#047857')
    gold  = _rgb('#D97706')
    light = _rgb('#D1FAE5')

    # Top green block with diagonal cut
    d.rectangle([0, 0, W, 175], fill=em)
    d.polygon([(0, 145), (W, 120), (W, 175), (0, 175)], fill=em2)

    _center(d, 'CERTIFICATE', _font('DejaVuSerif-Bold', 28), 42, W, _rgb('#FFFFFF'))
    _center(d, 'O F   P R O F E S S I O N A L   A C H I E V E M E N T',
            _font('DejaVuSans', 13), 90, W, light)

    # Gold rule
    d.rectangle([80, 205, W-80, 208], fill=gold)
    _center(d, 'This is to certify that', _font('DejaVuSerif', 16), 225, W, _rgb('#374151'))

    # Side accents
    d.rectangle([40, 200, 44, H-52], fill=light)
    d.rectangle([W-44, 200, W-40, H-52], fill=light)

    # Footer bar
    d.rectangle([0, H-46, W, H], fill=em)
    _center(d, 'Issued with Excellence', _font('DejaVuSans', 11), H-30, W, light)
    return img


# ── Template 5: Appreciation Warm — Horizontal (1200×850) ────────────────────

def _draw_appreciation_warm_h():
    W, H = 1200, 850
    img = Image.new('RGB', (W, H), _rgb('#FEF3E2'))
    d = ImageDraw.Draw(img)
    tc   = _rgb('#C2440C')
    gold = _rgb('#D97706')
    mid  = _rgb('#92400E')
    dim  = _rgb('#A1540F')

    d.rectangle([16, 16, W-16, H-16], outline=tc, width=2)
    d.rectangle([24, 24, W-24, H-24], outline=gold, width=1)

    # Corner rosettes
    for cx, cy in [(44, 44), (W-44, 44), (44, H-44), (W-44, H-44)]:
        for r, col in [(15, tc), (10, gold), (5, tc)]:
            d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=col, width=1)
        d.ellipse([cx-4, cy-4, cx+4, cy+4], fill=tc)

    _center(d, '✦   CERTIFICATE OF APPRECIATION   ✦', _font('DejaVuSerif-Bold', 20), 52, W, tc)
    d.line([(95, 100), (W-95, 100)], fill=gold, width=1)
    _center(d, 'Presented with gratitude and recognition to', _font('DejaVuSerif', 15), 120, W, mid)

    # Bottom
    d.line([(95, H-105), (W-95, H-105)], fill=gold, width=1)
    for x_c in [W // 3, 2 * W // 3]:
        d.line([(x_c-80, H-66), (x_c+80, H-66)], fill=tc, width=1)
    d.text((W//3-56, H-54), 'Program Director', font=_font('DejaVuSerif', 10), fill=dim)
    d.text((2*W//3-18, H-54), 'Date', font=_font('DejaVuSerif', 10), fill=dim)
    return img


# ── Template 6: Classic Elegance — Vertical (850×1200) ───────────────────────

def _draw_classic_elegance_v():
    W, H = 850, 1200
    img = Image.new('RGB', (W, H), _rgb('#FFFDF5'))
    d = ImageDraw.Draw(img)
    gold = _rgb('#B8860B')
    lg   = _rgb('#D4AF37')
    dark = _rgb('#2C1810')
    gray = _rgb('#9B8565')

    d.rectangle([18, 18, W-18, H-18], outline=gold, width=3)
    d.rectangle([30, 30, W-30, H-30], outline=lg, width=1)

    for cx, cy in [(50, 50), (W-50, 50), (50, H-50), (W-50, H-50)]:
        d.ellipse([cx-14, cy-14, cx+14, cy+14], outline=gold, width=2)
        d.ellipse([cx-7, cy-7, cx+7, cy+7], fill=gold)

    for offset, w, col in [(130, 1, lg), (134, 2, gold), (138, 1, lg)]:
        d.line([(68, offset), (W-68, offset)], fill=col, width=w)

    _center(d, 'CERTIFICATE  OF  ACHIEVEMENT', _font('DejaVuSerif-Bold', 20), 66, W, gold)
    _center(d, '✦', _font('DejaVuSerif', 38), 162, W, gold)
    _center(d, 'This is to certify that', _font('DejaVuSerif', 17), 232, W, dark)

    for offset, w, col in [(H-138, 1, lg), (H-134, 2, gold), (H-130, 1, lg)]:
        d.line([(68, offset), (W-68, offset)], fill=col, width=w)

    for x_c in [W // 3, 2 * W // 3]:
        d.line([(x_c-70, H-85), (x_c+70, H-85)], fill=lg, width=1)
    d.text((W//3-54, H-73), 'Authorized Signature', font=_font('DejaVuSerif', 10), fill=gray)
    d.text((2*W//3-18, H-73), 'Date', font=_font('DejaVuSerif', 10), fill=gray)
    return img


# ── Template 7: Bold Contemporary — Vertical (850×1200) ──────────────────────

def _draw_bold_contemporary_v():
    W, H = 850, 1200
    img = Image.new('RGB', (W, H), _rgb('#F8F9FA'))
    d = ImageDraw.Draw(img)
    purple = _rgb('#2D1B69')
    gold   = _rgb('#F59E0B')
    light  = _rgb('#EDE9FE')

    # Top purple block with diagonal cut
    top_h = 310
    d.rectangle([0, 0, W, top_h], fill=purple)
    d.polygon([(0, top_h-28), (W, top_h-54), (W, top_h), (0, top_h)], fill=_rgb('#3D2B79'))

    # Gold triangle corners
    d.polygon([(W-115, 0), (W, 0), (W, 115)], fill=gold)
    d.polygon([(0, top_h-38), (58, top_h), (0, top_h)], fill=gold)

    _center(d, 'CERTIFICATE', _font('DejaVuSans-Bold', 20), 76, W, _rgb('#FFFFFF'))
    _center(d, 'O F   E X C E L L E N C E', _font('DejaVuSans', 12), 114, W, gold)
    d.line([(120, 162), (W-120, 162)], fill=_rgb('#4C3B8A'), width=1)
    _center(d, 'This certificate is proudly presented to',
            _font('DejaVuSans', 13), top_h + 48, W, _rgb('#6B7280'))

    # Bottom bar
    d.rectangle([0, H-75, W, H], fill=purple)
    d.rectangle([0, H-79, W, H-75], fill=gold)
    _center(d, 'Excellence  ·  Achievement  ·  Recognition',
            _font('DejaVuSans', 10), H-52, W, light)
    return img


# ── Template 8: Rose Gold Elegance — Vertical (850×1200) ─────────────────────

def _draw_rose_gold_v():
    W, H = 850, 1200
    img = Image.new('RGB', (W, H), _rgb('#FFF0F3'))
    d = ImageDraw.Draw(img)
    rose   = _rgb('#C2185B')
    rose_l = _rgb('#F48FB1')
    rose_g = _rgb('#C8A0A6')
    dark   = _rgb('#880E4F')

    # Arcs top
    for r, col in [(215, rose_l), (194, rose_g), (170, _rgb('#FCE4EC'))]:
        d.arc([(W//2-r, -r), (W//2+r, r)], 0, 180, fill=col, width=3)
    # Arcs bottom
    for r, col in [(215, rose_l), (194, rose_g), (170, _rgb('#FCE4EC'))]:
        d.arc([(W//2-r, H-r), (W//2+r, H+r)], 180, 360, fill=col, width=3)

    d.rectangle([24, 24, W-24, H-24], outline=rose_g, width=2)

    # Corner flowers
    for cx, cy in [(55, 55), (W-55, 55), (55, H-55), (W-55, H-55)]:
        d.ellipse([cx-17, cy-17, cx+17, cy+17], outline=rose_l, width=2)
        d.ellipse([cx-8, cy-8, cx+8, cy+8], fill=rose_g)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            px = int(cx + 14 * math.cos(rad))
            py = int(cy + 14 * math.sin(rad))
            d.ellipse([px-3, py-3, px+3, py+3], fill=rose_l)

    _center(d, 'Certificate of', _font('DejaVuSerif-Bold', 22), 100, W, rose)
    _center(d, 'Appreciation', _font('DejaVuSerif-Bold', 32), 138, W, dark)
    d.line([(115, 204), (W-115, 204)], fill=rose_g, width=2)
    _center(d, '❧', _font('DejaVuSerif', 22), 220, W, rose_l)
    d.line([(115, 262), (W-115, 262)], fill=rose_g, width=2)
    _center(d, 'With great pleasure, this is awarded to',
            _font('DejaVuSerif', 14), 282, W, _rgb('#6B7280'))

    sig_y = H - 120
    d.line([(W//2-108, sig_y), (W//2+108, sig_y)], fill=rose_g, width=1)
    _center(d, 'Director of Excellence', _font('DejaVuSerif', 11), sig_y+16, W, _rgb('#9E9E9E'))
    return img


# ── Template 9: Tech Achievement — Vertical (850×1200) ───────────────────────

def _draw_tech_achievement_v():
    W, H = 850, 1200
    img = Image.new('RGB', (W, H), _rgb('#0D1117'))
    d = ImageDraw.Draw(img)
    cyan   = _rgb('#00D4FF')
    purple = _rgb('#7C3AED')
    green  = _rgb('#10B981')
    dim    = _rgb('#30363D')

    # Grid lines
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=_rgb('#161B22'), width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=_rgb('#161B22'), width=1)

    # Diagonal accents
    d.line([(0, 0), (W, 280)], fill=_rgb('#21262D'), width=2)
    d.line([(0, 80), (W, 360)], fill=_rgb('#1C2128'), width=1)

    # Corner brackets
    bl = 42
    for bx, by, hd, vd in [(28, 28, 1, 1), (W-28, 28, -1, 1),
                             (28, H-28, 1, -1), (W-28, H-28, -1, -1)]:
        d.line([(bx, by), (bx + hd*bl, by)], fill=cyan, width=3)
        d.line([(bx, by), (bx, by + vd*bl)], fill=cyan, width=3)

    # Top/bottom bars
    d.rectangle([0, 0, W, 5], fill=cyan)
    d.rectangle([0, H-5, W, H], fill=purple)

    _center(d, '[ CERTIFICATE OF ACHIEVEMENT ]', _font('DejaVuSans-Bold', 15), 58, W, cyan)
    _center(d, 'T E C H N O L O G Y   &   I N N O V A T I O N',
            _font('DejaVuSans', 10), 92, W, purple)

    # Hexagon ornament
    hx, hy, hr = W // 2, 220, 58
    hpts = [(int(hx + hr*math.cos(math.radians(a-30))),
             int(hy + hr*math.sin(math.radians(a-30)))) for a in range(0, 360, 60)]
    d.polygon(hpts, outline=cyan, fill=_rgb('#0D1117'))
    ir = 42
    ipts = [(int(hx + ir*math.cos(math.radians(a-30))),
             int(hy + ir*math.sin(math.radians(a-30)))) for a in range(0, 360, 60)]
    d.polygon(ipts, outline=purple, fill=_rgb('#161B22'))
    _center(d, '★', _font('DejaVuSans-Bold', 28), 206, W, green)

    _center(d, 'PRESENTED TO', _font('DejaVuSans', 12), 308, W, _rgb('#8B949E'))

    # Circuit decoration
    pts = [(80, H-188), (W-80, H-188), (W//2, H-218)]
    for i, (px, py) in enumerate(pts):
        d.ellipse([px-7, py-7, px+7, py+7], outline=cyan, width=2)
        d.ellipse([px-2, py-2, px+2, py+2], fill=cyan)
    d.line([pts[0], pts[2]], fill=dim, width=1)
    d.line([pts[1], pts[2]], fill=dim, width=1)

    _center(d, '// ACHIEVEMENT UNLOCKED //', _font('DejaVuSans', 10), H-44, W, dim)
    return img


# ── Template 10 & 11: Custom Excellence (From Upload) ─────────────────────────

def _draw_custom_excellence_h():
    # Load the uploaded image from the workspace backgrounds/ folder
    path = os.path.join(config.BASE_DIR, 'backgrounds', 'media__1776678325207.png')
    img = Image.open(path).convert('RGB')
    
    # We resize it to standard 1200x850 resolution so everything matches
    img = img.resize((1200, 850), Image.LANCZOS)
    return img


def _draw_custom_excellence_v():
    path = os.path.join(config.BASE_DIR, 'backgrounds', 'media__1776678382447.png')
    img = Image.open(path).convert('RGB')
    img = img.resize((850, 1200), Image.LANCZOS)
    return img


# ── Template 12 & 13: Yellow & Purple Custom ──────────────────────────────────

def _draw_yp_excellence_h():
    path = os.path.join(config.BASE_DIR, 'backgrounds', 'Yello_Blue_landscape.png')
    if not os.path.exists(path):
        # fallback just in case
        img = Image.new('RGB', (1200, 850), _rgb('#FFFFFF'))
    else:
        img = Image.open(path).convert('RGB')
        img = img.resize((1200, 850), Image.LANCZOS)
    return img

def _draw_yp_excellence_v():
    path = os.path.join(config.BASE_DIR, 'backgrounds', 'Yello_Blue_landscape.png')
    if not os.path.exists(path):
        img = Image.new('RGB', (850, 1200), _rgb('#FFFFFF'))
    else:
        img = Image.open(path).convert('RGB')
        # Rotate the landscape version to act as portrait
        img = img.rotate(90, expand=True)
        img = img.resize((850, 1200), Image.LANCZOS)
    return img


# ── Text field helper ─────────────────────────────────────────────────────────

def _tf(variable, x_pct, y_pct, font_family, font_size, color_hex,
        align='center', bold=False, italic=False, letterSpacing=0, locked=True, max_width=80):
    var_id = (variable.replace('{', '').replace('}', '')
                       .replace('/', '_').replace(' ', '_').lower())
    return {
        'id':            f'field_{var_id}',
        'variable':      variable,
        'x_percent':     x_pct,
        'y_percent':     y_pct,
        'font_family':   font_family,
        'font_size':     font_size,
        'color_hex':     color_hex,
        'align':         align,
        'bold':          bold,
        'italic':        italic,
        'letterSpacing': letterSpacing,
        'locked':        locked,
        'max_width_percent': max_width,
    }


# ── Template registry ─────────────────────────────────────────────────────────

BUILTIN_TEMPLATES = [
    {
        'template_id':  'builtin_classic_elegance_h',
        'name':         'Classic Elegance',
        'category':     'classic',
        'orientation':  'horizontal',
        'width':        1200,
        'height':       850,
        'background_id': 'builtin_classic_elegance_h.png',
        'thumb_key':    'builtin_thumbs/builtin_classic_elegance_h.png',
        'draw_fn':      _draw_classic_elegance_h,
        'text_fields':  [
            _tf('{{Name}}',         50, 43, 'DejaVuSerif-Bold', 62, '#B8860B'),
            _tf('{{Course/Event}}', 50, 58, 'DejaVuSerif',      34, '#2C1810'),
            _tf('{{Date}}',         75, 83, 'DejaVuSerif',      22, '#9B8565'),
        ],
    },
    {
        'template_id':  'builtin_modern_minimal_h',
        'name':         'Modern Minimal',
        'category':     'modern',
        'orientation':  'horizontal',
        'width':        1200,
        'height':       850,
        'background_id': 'builtin_modern_minimal_h.png',
        'thumb_key':    'builtin_thumbs/builtin_modern_minimal_h.png',
        'draw_fn':      _draw_modern_minimal_h,
        'text_fields':  [
            _tf('{{Name}}',         50, 38, 'DejaVuSerif-Bold', 68, '#111827'),
            _tf('{{Course/Event}}', 50, 54, 'DejaVuSerif',      32, '#374151'),
            _tf('{{Date}}',         50, 65, 'DejaVuSans',       22, '#6B7280'),
        ],
    },
    {
        'template_id':  'builtin_corporate_navy_h',
        'name':         'Corporate Navy',
        'category':     'corporate',
        'orientation':  'horizontal',
        'width':        1200,
        'height':       850,
        'background_id': 'builtin_corporate_navy_h.png',
        'thumb_key':    'builtin_thumbs/builtin_corporate_navy_h.png',
        'draw_fn':      _draw_corporate_navy_h,
        'text_fields':  [
            _tf('{{Name}}',         62, 38, 'DejaVuSerif-Bold', 58, '#0A2342'),
            _tf('{{Course/Event}}', 62, 52, 'DejaVuSerif',      30, '#374151'),
            _tf('{{Date}}',         62, 63, 'DejaVuSans',       21, '#6B7280'),
        ],
    },
    {
        'template_id':  'builtin_emerald_professional_h',
        'name':         'Emerald Professional',
        'category':     'modern',
        'orientation':  'horizontal',
        'width':        1200,
        'height':       850,
        'background_id': 'builtin_emerald_professional_h.png',
        'thumb_key':    'builtin_thumbs/builtin_emerald_professional_h.png',
        'draw_fn':      _draw_emerald_professional_h,
        'text_fields':  [
            _tf('{{Name}}',         50, 42, 'DejaVuSerif-Bold', 62, '#065F46'),
            _tf('{{Course/Event}}', 50, 57, 'DejaVuSerif',      32, '#1F2937'),
            _tf('{{Date}}',         50, 68, 'DejaVuSans',       22, '#374151'),
        ],
    },
    {
        'template_id':  'builtin_appreciation_warm_h',
        'name':         'Appreciation Warm',
        'category':     'appreciation',
        'orientation':  'horizontal',
        'width':        1200,
        'height':       850,
        'background_id': 'builtin_appreciation_warm_h.png',
        'thumb_key':    'builtin_thumbs/builtin_appreciation_warm_h.png',
        'draw_fn':      _draw_appreciation_warm_h,
        'text_fields':  [
            _tf('{{Name}}',         50, 41, 'DejaVuSerif-Bold', 62, '#7C3D12'),
            _tf('{{Course/Event}}', 50, 56, 'DejaVuSerif',      32, '#92400E'),
            _tf('{{Date}}',         67, 83, 'DejaVuSerif',      22, '#A1540F'),
        ],
    },
    {
        'template_id':  'builtin_classic_elegance_v',
        'name':         'Classic Elegance (Portrait)',
        'category':     'classic',
        'orientation':  'vertical',
        'width':        850,
        'height':       1200,
        'background_id': 'builtin_classic_elegance_v.png',
        'thumb_key':    'builtin_thumbs/builtin_classic_elegance_v.png',
        'draw_fn':      _draw_classic_elegance_v,
        'text_fields':  [
            _tf('{{Name}}',         50, 38, 'DejaVuSerif-Bold', 58, '#B8860B'),
            _tf('{{Course/Event}}', 50, 50, 'DejaVuSerif',      30, '#2C1810'),
            _tf('{{Date}}',         67, 62, 'DejaVuSerif',      20, '#9B8565'),
        ],
    },
    {
        'template_id':  'builtin_bold_contemporary_v',
        'name':         'Bold Contemporary',
        'category':     'modern',
        'orientation':  'vertical',
        'width':        850,
        'height':       1200,
        'background_id': 'builtin_bold_contemporary_v.png',
        'thumb_key':    'builtin_thumbs/builtin_bold_contemporary_v.png',
        'draw_fn':      _draw_bold_contemporary_v,
        'text_fields':  [
            _tf('{{Name}}',         50, 43, 'DejaVuSans-Bold', 58, '#2D1B69'),
            _tf('{{Course/Event}}', 50, 55, 'DejaVuSans',      28, '#374151'),
            _tf('{{Date}}',         50, 65, 'DejaVuSans',      20, '#6B7280'),
        ],
    },
    {
        'template_id':  'builtin_rose_gold_v',
        'name':         'Rose Gold Elegance',
        'category':     'appreciation',
        'orientation':  'vertical',
        'width':        850,
        'height':       1200,
        'background_id': 'builtin_rose_gold_v.png',
        'thumb_key':    'builtin_thumbs/builtin_rose_gold_v.png',
        'draw_fn':      _draw_rose_gold_v,
        'text_fields':  [
            _tf('{{Name}}',         50, 38, 'DejaVuSerif-Bold', 54, '#C2185B'),
            _tf('{{Course/Event}}', 50, 50, 'DejaVuSerif',      28, '#880E4F'),
            _tf('{{Date}}',         50, 60, 'DejaVuSerif',      20, '#9E9E9E'),
        ],
    },
    {
        'template_id':  'builtin_tech_achievement_v',
        'name':         'Tech Achievement',
        'category':     'modern',
        'orientation':  'vertical',
        'width':        850,
        'height':       1200,
        'background_id': 'builtin_tech_achievement_v.png',
        'thumb_key':    'builtin_thumbs/builtin_tech_achievement_v.png',
        'draw_fn':      _draw_tech_achievement_v,
        'text_fields':  [
            _tf('{{Name}}',         50, 38, 'DejaVuSans-Bold', 54, '#00D4FF'),
            _tf('{{Course/Event}}', 50, 50, 'DejaVuSans',      28, '#F0F6FC'),
            _tf('{{Date}}',         50, 61, 'DejaVuSans',      20, '#8B949E'),
        ],
    },
    {
        'template_id':  'builtin_custom_excellence_h',
        'name':         'Custom Excellence',
        'category':     'modern',
        'orientation':  'horizontal',
        'width':        1200,
        'height':       850,
        'background_id': 'builtin_custom_excellence_h.png',
        'thumb_key':    'builtin_thumbs/builtin_custom_excellence_h.png',
        'draw_fn':      _draw_custom_excellence_h,
        'text_fields':  [
            _tf('Certificate',      50, 20, 'Italianno',       120, '#D97706'),
            _tf('of excellence',    50, 32, 'Inter',           30,  '#111827'),
            _tf('{{Name}}',         50, 48, 'DejaVuSerif-Bold', 60, '#111827'),
            _tf('{{Course/Event}}', 50, 60, 'Inter',           28,  '#374151'),
            _tf('{{Date}}',         50, 75, 'Inter',           20,  '#6B7280'),
        ],
    },
    {
        'template_id':  'builtin_custom_excellence_v',
        'name':         'Custom Excellence (Portrait)',
        'category':     'modern',
        'orientation':  'vertical',
        'width':        850,
        'height':       1200,
        'background_id': 'builtin_custom_excellence_v.png',
        'thumb_key':    'builtin_thumbs/builtin_custom_excellence_v.png',
        'draw_fn':      _draw_custom_excellence_v,
        'text_fields':  [
            _tf('Certificate',      50, 20, 'Italianno',       110, '#D97706'),
            _tf('of excellence',    50, 29, 'Inter',           26,  '#111827'),
            _tf('{{Name}}',         50, 45, 'DejaVuSerif-Bold', 54, '#111827'),
            _tf('{{Course/Event}}', 50, 56, 'Inter',           24,  '#374151'),
            _tf('{{Date}}',         50, 70, 'Inter',           18,  '#6B7280'),
        ],
    },
    {
        'template_id':  'builtin_yp_excellence_h',
        'name':         'Yellow & Purple Excellence',
        'category':     'modern',
        'orientation':  'horizontal',
        'width':        1200,
        'height':       850,
        'background_id': 'builtin_yp_excellence_h.png',
        'thumb_key':    'builtin_thumbs/builtin_yp_excellence_h.png',
        'draw_fn':      _draw_yp_excellence_h,
        'text_fields':  [
            _tf('Certificate',      50, 24, 'Italianno',       120, '#581C87'),
            _tf('of excellence',    50, 36, 'Inter',           30,  '#111827'),
            _tf('{{Name}}',         50, 56, 'DejaVuSerif-Bold', 60, '#111827'),
            _tf('{{Course/Event}}', 50, 68, 'Inter',           28,  '#374151'),
            _tf('{{Date}}',         50, 78, 'Inter',           20,  '#6B7280'),
        ],
    },
    {
        'template_id':  'builtin_yp_excellence_v',
        'name':         'Yellow & Purple Excellence (Portrait)',
        'category':     'modern',
        'orientation':  'vertical',
        'width':        850,
        'height':       1200,
        'background_id': 'builtin_yp_excellence_v.png',
        'thumb_key':    'builtin_thumbs/builtin_yp_excellence_v.png',
        'draw_fn':      _draw_yp_excellence_v,
        'text_fields':  [
            _tf('Certificate',      50, 24, 'Italianno',       110, '#581C87'),
            _tf('of excellence',    50, 33, 'Inter',           26,  '#111827'),
            _tf('{{Name}}',         50, 54, 'DejaVuSerif-Bold', 54, '#111827'),
            _tf('{{Course/Event}}', 50, 66, 'Inter',           24,  '#374151'),
            _tf('{{Date}}',         50, 78, 'Inter',           18,  '#6B7280'),
        ],
    },
]


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def ensure_builtins_registered():
    """
    Generate background images and thumbnails for all built-in templates and
    upsert their configs into the template store. Idempotent — only generates
    images that are missing from storage.
    """
    from core import storage
    from core.template_manager import save_template

    try:
        existing_bgs    = {f['filename'] for f in storage.list_files('backgrounds/')}
        existing_thumbs = {f['filename'] for f in storage.list_files('builtin_thumbs/')}
    except Exception as exc:
        print(f'WARNING: could not list storage for builtin check: {exc}', flush=True)
        existing_bgs = set()
        existing_thumbs = set()

    for tmpl in BUILTIN_TEMPLATES:
        bg_fn    = tmpl['background_id']
        need_bg  = bg_fn not in existing_bgs
        need_th  = bg_fn not in existing_thumbs  # same filename, different prefix

        img = None
        if need_bg or need_th:
            try:
                img = tmpl['draw_fn']()
            except Exception as exc:
                print(f'WARNING: draw failed for {tmpl["template_id"]}: {exc}', flush=True)
                continue

        if need_bg and img is not None:
            try:
                buf = io.BytesIO()
                img.save(buf, 'PNG')
                storage.upload_bytes(buf.getvalue(), f'backgrounds/{bg_fn}', 'image/png')
            except Exception as exc:
                print(f'WARNING: bg upload failed for {bg_fn}: {exc}', flush=True)

        if need_th and img is not None:
            try:
                w, h = (600, 424) if tmpl['orientation'] == 'horizontal' else (424, 600)
                thumb = img.resize((w, h), Image.LANCZOS)
                buf = io.BytesIO()
                thumb.save(buf, 'PNG')
                storage.upload_bytes(buf.getvalue(), f'builtin_thumbs/{bg_fn}', 'image/png')
            except Exception as exc:
                print(f'WARNING: thumb upload failed for {bg_fn}: {exc}', flush=True)

        # Always upsert template config (cheap — just JSON/DB write)
        cfg = {k: v for k, v in tmpl.items() if k != 'draw_fn'}
        try:
            save_template(cfg)
        except Exception as exc:
            print(f'WARNING: save_template failed for {tmpl["template_id"]}: {exc}', flush=True)

    print(f'[builtin_templates] {len(BUILTIN_TEMPLATES)} templates registered.', flush=True)
