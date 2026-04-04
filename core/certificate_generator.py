import os
import re
from PIL import Image, ImageDraw, ImageFont
from config import BACKGROUND_FOLDER, FONT_FOLDER, OUTPUT_FOLDER


def _resolve_font(font_family, font_size):
    """Load a TrueType font from FONT_FOLDER or fall back to default."""
    ttf_path = os.path.join(FONT_FOLDER, font_family + '.ttf')
    try:
        if os.path.exists(ttf_path):
            return ImageFont.truetype(ttf_path, int(font_size))
    except Exception:
        pass
    try:
        return ImageFont.load_default(size=int(font_size))
    except Exception:
        return ImageFont.load_default()


def _substitute(text, row):
    """Replace {{Variable}} placeholders with row values."""
    def replacer(match):
        key = match.group(1).strip()
        return row.get(key, match.group(0))
    return re.sub(r'\{\{([^}]+)\}\}', replacer, text)


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c*2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def render_one(template_config, row, output_path):
    """
    Render a single certificate image.
    template_config: dict with background_id, width, height, text_fields
    row: dict with Name, Email, Course/Event, Date
    output_path: full path where PNG will be saved
    """
    bg_filename = template_config.get('background_id', '')
    bg_path = os.path.join(BACKGROUND_FOLDER, bg_filename)

    if bg_filename and os.path.exists(bg_path):
        img = Image.open(bg_path).convert('RGBA')
        img = img.resize((template_config['width'], template_config['height']), Image.LANCZOS)
    else:
        # Default blank white certificate
        img = Image.new('RGBA', (template_config['width'], template_config['height']), (255, 255, 255, 255))

    draw = ImageDraw.Draw(img)
    img_w, img_h = img.size

    for field in template_config.get('text_fields', []):
        text = _substitute(field.get('variable', ''), row)
        if not text:
            continue

        font = _resolve_font(field.get('font_family', 'DejaVuSerif'), field.get('font_size', 36))
        color = _hex_to_rgb(field.get('color_hex', '#000000'))

        x = int(field['x_percent'] / 100.0 * img_w)
        y = int(field['y_percent'] / 100.0 * img_h)

        align = field.get('align', 'center')
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            text_w, text_h = draw.textsize(text, font=font)

        if align == 'center':
            x -= text_w // 2
        elif align == 'right':
            x -= text_w

        # Optional max width: wrap text
        max_width_px = int(field.get('max_width_percent', 80) / 100.0 * img_w)
        if text_w > max_width_px:
            # Simple word wrap
            words = text.split()
            lines = []
            line = ''
            for word in words:
                test = (line + ' ' + word).strip()
                try:
                    tw = draw.textbbox((0, 0), test, font=font)[2]
                except Exception:
                    tw, _ = draw.textsize(test, font=font)
                if tw <= max_width_px:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)

            for i, ln in enumerate(lines):
                try:
                    lw = draw.textbbox((0, 0), ln, font=font)[2]
                except Exception:
                    lw, _ = draw.textsize(ln, font=font)
                lx = x if align != 'center' else (img_w // 2 - lw // 2)
                draw.text((lx, y + i * (text_h + 4)), ln, font=font, fill=color)
        else:
            draw.text((x, y), text, font=font, fill=color)

    # Convert to RGB for PNG saving (strip alpha if background was opaque)
    final = img.convert('RGB')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final.save(output_path, 'PNG')
    return output_path


def render_all(session_id, template_config, rows):
    """
    Render certificates for all rows. Yields (row, output_path, error) tuples.
    """
    session_out = os.path.join(OUTPUT_FOLDER, session_id)
    os.makedirs(session_out, exist_ok=True)

    for row in rows:
        safe_name = re.sub(r'[^\w\s-]', '', row.get('Name', 'Unknown')).strip().replace(' ', '_')
        filename = f"{safe_name}.png"
        output_path = os.path.join(session_out, filename)
        try:
            render_one(template_config, row, output_path)
            yield row, output_path, None
        except Exception as e:
            yield row, None, str(e)
