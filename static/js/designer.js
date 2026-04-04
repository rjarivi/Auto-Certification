(function () {
  const canvas    = document.getElementById('certCanvas');
  const ctx       = canvas.getContext('2d');
  const sessionId = document.getElementById('sessionId').value;

  let bgImage     = null;
  let bgFilename  = '';
  let fields      = [];
  let selectedIdx = -1;
  let dragging    = false;
  let dragOffX    = 0;
  let dragOffY    = 0;

  // Tracks which custom fonts have already been injected into the page
  const _loadedFonts = new Set();

  // ── Font helpers ─────────────────────────────────────────────────────────────
  function _fontInfo(fontId) {
    return (typeof FONT_CSS_MAP !== 'undefined' && FONT_CSS_MAP[fontId]) || null;
  }

  /**
   * Build a CSS font string for ctx.font.
   * Bundled fonts map to generic CSS families; custom/google fonts use their
   * actual family name (loaded via @font-face below).
   */
  function buildCtxFont(fontId, scaledSize) {
    const info = _fontInfo(fontId);
    const bold = info ? info.bold : fontId.includes('Bold');
    let family;
    if (info && info.source !== 'bundled' && info.display_name) {
      family = `"${info.display_name}"`;
    } else if (info && info.css_family) {
      family = info.css_family;
    } else {
      family = fontId.includes('Sans') ? 'Helvetica, Arial, sans-serif' : 'Georgia, serif';
    }
    return `${bold ? 'bold ' : ''}${scaledSize}px ${family}`;
  }

  /**
   * Inject an @font-face rule so the canvas can use a custom / google font.
   * No-ops if the font was already injected.
   */
  function ensureFontFaceLoaded(fontId) {
    if (_loadedFonts.has(fontId)) return;
    const info = _fontInfo(fontId);
    if (!info || info.source === 'bundled' || !info.filename) return;
    const displayName = info.display_name || fontId;
    const style = document.createElement('style');
    style.textContent =
      `@font-face { font-family: "${displayName}"; src: url("/static/fonts/${info.filename}"); }`;
    document.head.appendChild(style);
    // Kick off async load (canvas will look correct after the next redraw)
    document.fonts.load(`16px "${displayName}"`).then(() => redraw()).catch(() => {});
    _loadedFonts.add(fontId);
  }

  /** Pre-load @font-face rules for all non-bundled fonts in the registry. */
  function preloadCustomFonts() {
    if (typeof FONT_CSS_MAP === 'undefined') return;
    Object.keys(FONT_CSS_MAP).forEach(id => {
      const info = FONT_CSS_MAP[id];
      if (info && info.source !== 'bundled') ensureFontFaceLoaded(id);
    });
  }
  preloadCustomFonts();

  // ── Utility ──────────────────────────────────────────────────────────────────
  function canvasToPercent(cx, cy) {
    return { x: (cx / canvas.width) * 100, y: (cy / canvas.height) * 100 };
  }
  function percentToCanvas(xp, yp) {
    return { x: (xp / 100) * canvas.width, y: (yp / 100) * canvas.height };
  }

  // ── Drawing ──────────────────────────────────────────────────────────────────
  function redraw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (bgImage) {
      ctx.drawImage(bgImage, 0, 0, canvas.width, canvas.height);
    } else {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = '#e2e8f0';
      ctx.strokeRect(0, 0, canvas.width, canvas.height);
    }

    fields.forEach((f, i) => {
      const pos = percentToCanvas(f.x_percent, f.y_percent);
      const label = variableLabel(f.variable);
      ctx.save();

      const size = Math.round(f.font_size * (canvas.width / 1200));
      ensureFontFaceLoaded(f.font_family);
      ctx.font = buildCtxFont(f.font_family, size);
      ctx.fillStyle = f.color_hex;
      ctx.textAlign = f.align || 'center';
      ctx.fillText(label, pos.x, pos.y);

      // Selection indicator
      if (i === selectedIdx) {
        const metrics = ctx.measureText(label);
        const w = metrics.width + 16;
        const h = size + 12;
        let rx = pos.x;
        if (f.align === 'center') rx -= w / 2;
        else if (f.align === 'right') rx -= w;
        ctx.strokeStyle = '#4F46E5';
        ctx.lineWidth = 2;
        ctx.strokeRect(rx - 4, pos.y - h + 4, w, h);
        ctx.setLineDash([]);
      }

      ctx.restore();
    });
  }

  function variableLabel(variable) {
    const map = {
      '{{Name}}': 'John Doe',
      '{{Email}}': 'john@example.com',
      '{{Course/Event}}': 'Web Development Bootcamp',
      '{{Date}}': new Date().toLocaleDateString(),
    };
    return map[variable] || variable;
  }

  // ── Canvas size ──────────────────────────────────────────────────────────────
  document.getElementById('applySize').addEventListener('click', () => {
    canvas.width  = parseInt(document.getElementById('canvasW').value) || 1200;
    canvas.height = parseInt(document.getElementById('canvasH').value) || 850;
    redraw();
  });

  // ── Background upload ────────────────────────────────────────────────────────
  document.getElementById('bgInput').addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    fetch('/api/upload-background', { method: 'POST', body: fd })
      .then(r => r.json())
      .then(d => {
        if (d.filename) {
          bgFilename = d.filename;
          loadBackground(d.url);
          addBgThumb(d.url, d.filename);
        }
      });
  });

  function loadBackground(url) {
    const img = new Image();
    img.onload = () => { bgImage = img; redraw(); };
    img.src = url;
  }

  function addBgThumb(url, filename) {
    const list = document.getElementById('bgList');
    const img  = document.createElement('img');
    img.src = url;
    img.className = 'bg-thumb';
    img.title = filename;
    img.addEventListener('click', () => {
      document.querySelectorAll('.bg-thumb').forEach(t => t.classList.remove('selected'));
      img.classList.add('selected');
      bgFilename = filename;
      loadBackground(url);
    });
    list.appendChild(img);
    img.classList.add('selected');
  }

  // Load existing backgrounds
  fetch('/api/backgrounds')
    .then(r => r.json())
    .then(list => list.forEach(b => addBgThumb(b.url, b.filename)));

  // ── Fields ───────────────────────────────────────────────────────────────────
  function addField(opts = {}) {
    const f = {
      id:         'field_' + Date.now(),
      variable:   opts.variable   || '{{Name}}',
      font_family: opts.font_family || (FONTS.length ? FONTS[0][0] : 'DejaVuSerif'),
      font_size:  opts.font_size   || 48,
      color_hex:  opts.color_hex  || '#1a1a2e',
      align:      opts.align      || 'center',
      x_percent:  opts.x_percent  ?? 50,
      y_percent:  opts.y_percent  ?? 50,
    };
    fields.push(f);
    renderFieldList();
    selectField(fields.length - 1);
    redraw();
  }

  document.getElementById('addFieldBtn').addEventListener('click', () => addField());

  function renderFieldList() {
    const list = document.getElementById('fieldList');
    list.innerHTML = '';
    fields.forEach((f, i) => {
      const div = document.createElement('div');
      div.className = 'field-item' + (i === selectedIdx ? ' selected' : '');
      div.textContent = variableLabel(f.variable);
      div.addEventListener('click', () => selectField(i));
      list.appendChild(div);
    });
  }

  function selectField(i) {
    selectedIdx = i;
    renderFieldList();
    redraw();
    const editor = document.getElementById('fieldEditor');
    if (i < 0 || i >= fields.length) {
      editor.style.display = 'none';
      return;
    }
    const f = fields[i];
    editor.style.display = 'block';

    // Populate editor
    const varSel = document.getElementById('fVariable');
    const knownVars = ['{{Name}}', '{{Email}}', '{{Course/Event}}', '{{Date}}'];
    varSel.value = knownVars.includes(f.variable) ? f.variable : 'Custom';
    document.getElementById('customTextRow').style.display = varSel.value === 'Custom' ? 'block' : 'none';
    document.getElementById('fCustomText').value = varSel.value === 'Custom' ? f.variable : '';
    document.getElementById('fFont').value  = f.font_family;
    document.getElementById('fSize').value  = f.font_size;
    document.getElementById('fColor').value = f.color_hex;
    document.getElementById('fAlign').value = f.align;
  }

  // Editor change handlers
  ['fVariable', 'fFont', 'fSize', 'fColor', 'fAlign', 'fCustomText'].forEach(id => {
    document.getElementById(id).addEventListener('input', syncFieldFromEditor);
  });

  document.getElementById('fVariable').addEventListener('change', () => {
    const v = document.getElementById('fVariable').value;
    document.getElementById('customTextRow').style.display = v === 'Custom' ? 'block' : 'none';
    syncFieldFromEditor();
  });

  function syncFieldFromEditor() {
    if (selectedIdx < 0) return;
    const f = fields[selectedIdx];
    const varSel = document.getElementById('fVariable').value;
    f.variable   = varSel === 'Custom' ? document.getElementById('fCustomText').value : varSel;
    f.font_family = document.getElementById('fFont').value;
    f.font_size  = parseInt(document.getElementById('fSize').value) || 36;
    f.color_hex  = document.getElementById('fColor').value;
    f.align      = document.getElementById('fAlign').value;
    renderFieldList();
    redraw();
  }

  document.getElementById('deleteFieldBtn').addEventListener('click', () => {
    if (selectedIdx >= 0) {
      fields.splice(selectedIdx, 1);
      selectedIdx = -1;
      document.getElementById('fieldEditor').style.display = 'none';
      renderFieldList();
      redraw();
    }
  });

  // ── Drag ─────────────────────────────────────────────────────────────────────
  function getCanvasPos(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width  / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top)  * scaleY,
    };
  }

  function hitTest(cx, cy) {
    for (let i = fields.length - 1; i >= 0; i--) {
      const pos  = percentToCanvas(fields[i].x_percent, fields[i].y_percent);
      const size = Math.round(fields[i].font_size * (canvas.width / 1200));
      ctx.font = buildCtxFont(fields[i].font_family, size);
      const w = ctx.measureText(variableLabel(fields[i].variable)).width + 24;
      const h = size + 16;
      let lx = pos.x;
      if (fields[i].align === 'center') lx -= w / 2;
      else if (fields[i].align === 'right') lx -= w;
      if (cx >= lx - 4 && cx <= lx + w && cy >= pos.y - h + 4 && cy <= pos.y + 4) {
        return i;
      }
    }
    return -1;
  }

  canvas.addEventListener('mousedown', e => {
    const pos = getCanvasPos(e);
    const hit = hitTest(pos.x, pos.y);
    if (hit >= 0) {
      selectField(hit);
      dragging = true;
      const fpos = percentToCanvas(fields[hit].x_percent, fields[hit].y_percent);
      dragOffX = pos.x - fpos.x;
      dragOffY = pos.y - fpos.y;
      canvas.style.cursor = 'grabbing';
    }
  });

  canvas.addEventListener('mousemove', e => {
    const pos = getCanvasPos(e);
    if (dragging && selectedIdx >= 0) {
      const nx = pos.x - dragOffX;
      const ny = pos.y - dragOffY;
      const pct = canvasToPercent(nx, ny);
      fields[selectedIdx].x_percent = Math.max(0, Math.min(100, pct.x));
      fields[selectedIdx].y_percent = Math.max(0, Math.min(100, pct.y));
      redraw();
    } else {
      canvas.style.cursor = hitTest(pos.x, pos.y) >= 0 ? 'grab' : 'default';
    }
  });

  canvas.addEventListener('mouseup', () => { dragging = false; canvas.style.cursor = 'default'; });
  canvas.addEventListener('mouseleave', () => { dragging = false; });

  // ── Google Fonts + custom font upload ────────────────────────────────────────

  function _fontStatusMsg(msg, isError) {
    const el = document.getElementById('fontStatus');
    if (!el) return;
    el.style.display = 'block';
    el.style.color = isError ? 'var(--danger)' : 'var(--success)';
    el.textContent = msg;
    if (!isError) setTimeout(() => { el.style.display = 'none'; }, 4000);
  }

  /** Append a new font to the #fFont <select> and update FONT_CSS_MAP. */
  function _registerFontInUI(fontId, displayName, fontInfo) {
    FONT_CSS_MAP[fontId] = fontInfo;
    // Append option to font selector (only if not already there)
    const sel = document.getElementById('fFont');
    if (sel && !Array.from(sel.options).some(o => o.value === fontId)) {
      const opt = document.createElement('option');
      opt.value = fontId;
      opt.textContent = displayName;
      sel.appendChild(opt);
    }
    ensureFontFaceLoaded(fontId);
  }

  document.getElementById('addGoogleFontBtn').addEventListener('click', () => {
    const input = document.getElementById('googleFontInput');
    const family = (input.value || '').trim();
    if (!family) { _fontStatusMsg('Enter a font family name first.', true); return; }

    const btn = document.getElementById('addGoogleFontBtn');
    btn.disabled = true;
    btn.textContent = '…';
    _fontStatusMsg('Downloading from Google Fonts…', false);

    fetch('/api/add-google-font', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ family }),
    })
      .then(r => r.json())
      .then(d => {
        if (d.error) { _fontStatusMsg(d.error, true); return; }
        _registerFontInUI(d.font_id, d.display_name, {
          display_name: d.display_name,
          css_family:   `"${d.display_name}", serif`,
          bold: false, source: 'google', filename: d.filename,
        });
        input.value = '';
        _fontStatusMsg(`"${d.display_name}" added!`, false);
      })
      .catch(e => _fontStatusMsg('Network error: ' + e.message, true))
      .finally(() => { btn.disabled = false; btn.textContent = 'Add'; });
  });

  // Also trigger on Enter key in the input
  document.getElementById('googleFontInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('addGoogleFontBtn').click();
  });

  document.getElementById('fontFileInput').addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    _fontStatusMsg('Uploading font…', false);
    fetch('/api/upload-font', { method: 'POST', body: fd })
      .then(r => r.json())
      .then(d => {
        if (d.error) { _fontStatusMsg(d.error, true); return; }
        _registerFontInUI(d.font_id, d.display_name, {
          display_name: d.display_name,
          css_family:   `"${d.display_name}", serif`,
          bold: false, source: 'upload', filename: d.filename,
        });
        _fontStatusMsg(`"${d.display_name}" uploaded!`, false);
      })
      .catch(e => _fontStatusMsg('Upload error: ' + e.message, true));
    this.value = '';
  });

  // ── Load built-in template ───────────────────────────────────────────────────
  function applyBuiltinTemplate(tmpl) {
    // Canvas dimensions
    const w = tmpl.width  || 1200;
    const h = tmpl.height || 850;
    canvas.width  = w;
    canvas.height = h;
    document.getElementById('canvasW').value = w;
    document.getElementById('canvasH').value = h;

    // Template name
    if (tmpl.name) {
      document.getElementById('templateName').value = tmpl.name;
    }

    // Background
    if (tmpl.background_url) {
      bgFilename = tmpl.background_id || '';
      loadBackground(tmpl.background_url);
    }

    // Text fields
    fields = [];
    selectedIdx = -1;
    if (tmpl.text_fields && tmpl.text_fields.length) {
      tmpl.text_fields.forEach(f => {
        fields.push({
          id:          f.id || ('field_' + Date.now() + '_' + Math.random().toString(36).slice(2)),
          variable:    f.variable    || '{{Name}}',
          font_family: f.font_family || (FONTS.length ? FONTS[0][0] : 'DejaVuSerif'),
          font_size:   f.font_size   || 36,
          color_hex:   f.color_hex   || '#000000',
          align:       f.align       || 'center',
          x_percent:   f.x_percent   ?? 50,
          y_percent:   f.y_percent   ?? 50,
        });
      });
    }
    renderFieldList();
    redraw();
  }

  // ── Save Template ─────────────────────────────────────────────────────────────
  document.getElementById('saveTemplateBtn').addEventListener('click', () => {
    const name = document.getElementById('templateName').value.trim() || 'My Certificate';
    if (!fields.length) {
      alert('Add at least one text field before saving.');
      return;
    }
    const payload = {
      name,
      session_id:    sessionId,
      background_id: bgFilename,
      width:         canvas.width,
      height:        canvas.height,
      text_fields:   fields,
    };

    fetch('/api/save-template', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    })
      .then(r => r.json())
      .then(d => {
        if (d.template_id) {
          window.location.href = `/preview?session_id=${sessionId}`;
        } else {
          alert('Save failed: ' + (d.error || 'Unknown error'));
        }
      });
  });

  // ── Initialise fields (default or from ?load_template=) ─────────────────────
  const _loadTemplateId = new URLSearchParams(window.location.search).get('load_template');

  if (_loadTemplateId) {
    fetch(`/api/template/${_loadTemplateId}`)
      .then(r => {
        if (!r.ok) throw new Error('not found');
        return r.json();
      })
      .then(tmpl => applyBuiltinTemplate(tmpl))
      .catch(() => {
        // Fall back to defaults if template fetch fails
        _addDefaultFields();
      });
  } else {
    _addDefaultFields();
  }

  function _addDefaultFields() {
    addField({ variable: '{{Name}}',         y_percent: 52, font_size: 54 });
    addField({ variable: '{{Course/Event}}', y_percent: 62, font_size: 36 });
    addField({ variable: '{{Date}}',         y_percent: 71, font_size: 28, color_hex: '#64748B' });
    selectField(0);
  }
})();
