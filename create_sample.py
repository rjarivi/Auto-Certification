"""Helper script to create sample Excel and copy system fonts."""
import os
import shutil
import openpyxl

BASE = os.path.dirname(os.path.abspath(__file__))

# Create sample Excel
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Recipients"
ws.append(["Name", "Email", "Course/Event", "Date"])
ws.append(["Alice Johnson", "alice@example.com", "Python Fundamentals", "2026-04-04"])
ws.append(["Bob Smith", "bob@example.com", "Data Science Bootcamp", "2026-04-04"])
ws.append(["Carol White", "carol@example.com", "Web Development", "2026-04-04"])
ws.append(["David Lee", "david@example.com", "Machine Learning", "2026-04-04"])
ws.append(["Eva Martinez", "eva@example.com", "Cloud Computing", "2026-04-04"])
wb.save(os.path.join(BASE, 'static', 'sample_data.xlsx'))
print("Created sample_data.xlsx")

# Copy DejaVu fonts from system if available
font_dir = os.path.join(BASE, 'static', 'fonts')
os.makedirs(font_dir, exist_ok=True)

font_search_paths = [
    '/usr/share/fonts/truetype/dejavu',
    '/usr/share/fonts/dejavu',
    '/usr/share/fonts/TTF',
    '/usr/local/share/fonts',
]

needed = {
    'DejaVuSerif.ttf':      'DejaVuSerif.ttf',
    'DejaVuSerif-Bold.ttf': 'DejaVuSerif-Bold.ttf',
    'DejaVuSans.ttf':       'DejaVuSans.ttf',
    'DejaVuSans-Bold.ttf':  'DejaVuSans-Bold.ttf',
}

for src_name, dst_name in needed.items():
    dst = os.path.join(font_dir, dst_name)
    if os.path.exists(dst):
        print(f"Font already present: {dst_name}")
        continue
    for search in font_search_paths:
        src = os.path.join(search, src_name)
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"Copied {src_name}")
            break
    else:
        print(f"WARNING: {src_name} not found in system font paths. Fallback font will be used.")

print("Done.")
