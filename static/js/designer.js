/* ═══════════════════════════════════════════════════════════════════════════
   CertifyAuto Designer — Certifier.io-style editor
═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ── State ─────────────────────────────────────────────────────────────── */
  const canvas    = document.getElementById('certCanvas');
  const ctx       = canvas.getContext('2d');
  const sessionId = document.getElementById('sessionId').value;

  let bgImage    = null;
  let bgFilename = '';
  let fields     = [];
  let selectedIdx = -1;

  // Zoom
  let zoom = 1.0;
  const ZOOM_MIN = 0.15, ZOOM_MAX = 3.0, ZOOM_STEP = 0.15;

  // Undo/Redo
  let history = [], historyIdx = -1;

  // Drag state (HTML overlay drag)
  let dragging = false;
  let dragField = null, dragOffX = 0, dragOffY = 0;

  // Already-loaded font set
  const _loadedFonts = new Set();

  /* ── Placeholder definitions ────────────────────────────────────────────── */
  const PLACEHOLDER_INFO = {
    '{{Name}}':         { label: 'John Doe',              desc: '{{Name}} is a required dynamic attribute — will be replaced with each recipient\'s name.' },
    '{{Email}}':        { label: 'john@example.com',       desc: '{{Email}} shows each recipient\'s email address.' },
    '{{Course/Event}}': { label: 'Web Development Bootcamp', desc: '{{Course/Event}} is the course or event name.' },
    '{{Date}}':         { label: new Date().toLocaleDateString(), desc: '{{Date}} is the certificate issue date.' },
    '{{CertID}}':       { label: 'CERT-00001',             desc: '{{CertID}} is the unique certificate identifier. This attribute is mandatory.' },
  };

  function variableLabel(v) {
    return PLACEHOLDER_INFO[v] ? PLACEHOLDER_INFO[v].label : v;
  }

  /* ── Font helpers ──────────────────────────────────────────────────────── */
  function _fontInfo(id) { return (typeof FONT_CSS_MAP !== 'undefined' && FONT_CSS_MAP[id]) || null; }

  function buildCtxFont(fontId, scaledSize, bold, italic) {
    const info = _fontInfo(fontId);
    const isBold = bold || (info ? info.bold : fontId.includes('Bold'));
    let family;
    if (info && info.source !== 'bundled' && info.display_name) {
      family = `"${info.display_name}"`;
    } else if (info && info.css_family) {
      family = info.css_family;
    } else {
      family = fontId.includes('Sans') ? 'Helvetica,Arial,sans-serif' : 'Georgia,serif';
    }
    return `${italic ? 'italic ' : ''}${isBold ? 'bold ' : ''}${scaledSize}px ${family}`;
  }

  function ensureFontFaceLoaded(fontId) {
    if (_loadedFonts.has(fontId)) return;
    const info = _fontInfo(fontId);
    if (!info || info.source === 'bundled' || !info.filename) return;
    const displayName = info.display_name || fontId;
    const style = document.createElement('style');
    style.textContent = `@font-face { font-family: "${displayName}"; src: url("/static/fonts/${info.filename}"); }`;
    document.head.appendChild(style);
    document.fonts.load(`16px "${displayName}"`).then(() => redraw()).catch(() => {});
    _loadedFonts.add(fontId);
  }

  function preloadCustomFonts() {
    if (typeof FONT_CSS_MAP === 'undefined') return;
    Object.keys(FONT_CSS_MAP).forEach(id => {
      if (FONT_CSS_MAP[id] && FONT_CSS_MAP[id].source !== 'bundled') ensureFontFaceLoaded(id);
    });
  }
  preloadCustomFonts();

  /* ── Undo / Redo ───────────────────────────────────────────────────────── */
  function pushHistory() {
    const snap = JSON.stringify({ fields, bgFilename, w: canvas.width, h: canvas.height });
    history = history.slice(0, historyIdx + 1);
    history.push(snap);
    if (history.length > 60) history.shift();
    historyIdx = history.length - 1;
    updateUndoRedoBtns();
  }

  function undo() {
    if (historyIdx <= 0) return;
    historyIdx--;
    applySnap(JSON.parse(history[historyIdx]));
    updateUndoRedoBtns();
  }
  function redo() {
    if (historyIdx >= history.length - 1) return;
    historyIdx++;
    applySnap(JSON.parse(history[historyIdx]));
    updateUndoRedoBtns();
  }
  function applySnap(snap) {
    fields = snap.fields;
    selectedIdx = -1;
    canvas.width = snap.w;
    canvas.height = snap.h;
    redraw();
    rebuildOverlay();
    renderLayersList();
    hideProps();
    hideFloatToolbar();
  }
  function updateUndoRedoBtns() {
    document.getElementById('undoBtn').disabled = historyIdx <= 0;
    document.getElementById('redoBtn').disabled = historyIdx >= history.length - 1;
  }

  document.getElementById('undoBtn').addEventListener('click', undo);
  document.getElementById('redoBtn').addEventListener('click', redo);
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) { e.preventDefault(); undo(); }
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) { e.preventDefault(); redo(); }
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedIdx >= 0 && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA' && document.activeElement.tagName !== 'SELECT') {
      deleteSelectedField();
    }
  });

  /* ── Coordinate helpers ────────────────────────────────────────────────── */
  function canvasToPct(cx, cy) {
    return { x: (cx / canvas.width) * 100, y: (cy / canvas.height) * 100 };
  }
  function pctToCanvas(xp, yp) {
    return { x: (xp / 100) * canvas.width, y: (yp / 100) * canvas.height };
  }

  /* ── Canvas drawing ────────────────────────────────────────────────────── */
  function redraw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (bgImage) {
      ctx.drawImage(bgImage, 0, 0, canvas.width, canvas.height);
    } else {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    // Draw text fields on canvas
    fields.forEach((f) => {
      const pos  = pctToCanvas(f.x_percent, f.y_percent);
      const label = variableLabel(f.variable);
      const size  = Math.round(f.font_size * (canvas.width / 1200));
      ctx.save();
      ensureFontFaceLoaded(f.font_family);
      ctx.font      = buildCtxFont(f.font_family, size, f.bold, f.italic);
      ctx.fillStyle  = f.color_hex;
      ctx.globalAlpha = (f.opacity ?? 100) / 100;
      ctx.textAlign  = f.align || 'left';
      ctx.textBaseline = 'middle';
      ctx.letterSpacing = (f.letterSpacing || 0) + 'px';
      ctx.fillText(label, pos.x, pos.y);
      if (f.underline) {
        const w = ctx.measureText(label).width;
        const lx = f.align === 'center' ? pos.x - w / 2 : f.align === 'right' ? pos.x - w : pos.x;
        ctx.strokeStyle = f.color_hex;
        ctx.lineWidth = Math.max(1, size / 18);
        ctx.globalAlpha = (f.opacity ?? 100) / 100;
        ctx.beginPath();
        ctx.moveTo(lx, pos.y + 3);
        ctx.lineTo(lx + w, pos.y + 3);
        ctx.stroke();
      }
      ctx.restore();
    });
  }

  /* ── HTML Overlay for interactive field handles ─────────────────────────── */
  const overlay = document.getElementById('fieldsOverlay');

  function rebuildOverlay() {
    overlay.innerHTML = '';
    fields.forEach((f, i) => {
      const handle = buildHandle(f, i);
      overlay.appendChild(handle);
    });
    positionOverlayHandles();
  }

  function positionOverlayHandles() {
    // Canvas might be scaled; we need CSS pixel size of canvas element
    const canvasRect = canvas.getBoundingClientRect();
    const scaleX = canvas.width  / canvasRect.width;
    const scaleY = canvas.height / canvasRect.height;

    fields.forEach((f, i) => {
      const el = overlay.querySelector(`[data-idx="${i}"]`);
      if (!el) return;
      const pos = pctToCanvas(f.x_percent, f.y_percent);
      const size = Math.round(f.font_size * (canvas.width / 1200));
      ctx.save();
      ctx.font = buildCtxFont(f.font_family, size, f.bold, f.italic);
      ctx.textBaseline = 'middle';
      const label = variableLabel(f.variable);
      const metrics = ctx.measureText(label);
      ctx.restore();

      const w = metrics.width + 16;
      const h = size + 16;
      // Convert canvas px → overlay px (they are identical because overlay lives inside the scaled shadow div)
      const cx = pos.x;
      const cy = pos.y;
      let lx = cx;
      if (f.align === 'center') lx = cx - w / 2;
      else if (f.align === 'right') lx = cx - w;

      el.style.left   = lx + 'px';
      el.style.top    = (cy - h/2) + 'px';
      el.style.width  = w + 'px';
      el.style.height = h + 'px';
    });
  }

  function buildHandle(f, i) {
    const div = document.createElement('div');
    div.className = 'ds-field-handle' + (i === selectedIdx ? ' selected' : '');
    div.dataset.idx = i;
    // Resize corner handles (shown only when selected)
    ['tl','tr','bl','br'].forEach(pos => {
      const rh = document.createElement('div');
      rh.className = `ds-resize-handle ds-resize-handle--${pos}`;
      div.appendChild(rh);
    });

    // Drag logic
    div.addEventListener('mousedown', e => {
      e.stopPropagation();
      if (e.target.classList.contains('ds-resize-handle')) return; // TODO: resize
      selectField(i);

      if (fields[i].locked) {
        div.style.borderColor = '#ef4444';
        setTimeout(() => { div.style.borderColor = ''; }, 300);
        return; 
      }

      dragging = true;
      dragField = i;
      const canvasEl = canvas;
      const rect = canvasEl.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const canvasX = (e.clientX - rect.left) * scaleX;
      const canvasY = (e.clientY - rect.top)  * scaleY;
      const fpos = pctToCanvas(fields[i].x_percent, fields[i].y_percent);
      dragOffX = canvasX - fpos.x;
      dragOffY = canvasY - fpos.y;
      div.style.cursor = 'grabbing';
    });

    // Click to select + show tooltip on placeholder fields
    div.addEventListener('click', e => {
      e.stopPropagation();
      selectField(i);
      if (PLACEHOLDER_INFO[f.variable]) {
        showPlaceholderTip(i, e.clientX, e.clientY);
      }
    });

    div.addEventListener('dblclick', e => {
      e.stopPropagation();
      // Open text panel for quick editing
      openPanel('text');
    });

    return div;
  }

  // Deselect when clicking on canvas background
  document.getElementById('canvasOuter').addEventListener('mousedown', e => {
    if (e.target === canvas || e.target === document.getElementById('canvasOuter') || e.target === document.getElementById('dsWorkspace')) {
      selectField(-1);
    }
  });

  window.addEventListener('mousemove', e => {
    if (!dragging || dragField < 0) return;
    if (fields[dragField].locked) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const canvasX = (e.clientX - rect.left) * scaleX;
    const canvasY = (e.clientY - rect.top)  * scaleY;
    const nx = canvasX - dragOffX;
    const ny = canvasY - dragOffY;
    const pct = canvasToPct(nx, ny);
    fields[dragField].x_percent = Math.max(0, Math.min(100, pct.x));
    fields[dragField].y_percent = Math.max(0, Math.min(100, pct.y));
    redraw();
    positionOverlayHandles();
    positionFloatToolbar();
    syncPropsFromField(dragField);
  });

  window.addEventListener('mouseup', () => {
    if (dragging) {
      dragging = false;
      const handle = overlay.querySelector(`[data-idx="${dragField}"]`);
      if (handle) handle.style.cursor = 'grab';
      dragField = -1;
      pushHistory();
    }
  });

  /* ── Placeholder tooltip ────────────────────────────────────────────────── */
  const tip = document.getElementById('placeholderTip');
  const tipContent = document.getElementById('tipContent');
  let tipTimeout;

  function showPlaceholderTip(i, mx, my) {
    clearTimeout(tipTimeout);
    const f = fields[i];
    const info = PLACEHOLDER_INFO[f.variable];
    if (!info) { hideTip(); return; }
    const tagHtml = `<span class="ds-attr-pill-tag">${f.variable}</span>`;
    tipContent.innerHTML = `${tagHtml} ${info.desc} <a href="#" style="color:var(--accent)">Learn more</a>`;
    tip.style.display = 'block';
    // Position
    const tW = 260, tH = 90;
    let tx = mx + 12, ty = my + 12;
    if (tx + tW > window.innerWidth) tx = mx - tW - 12;
    if (ty + tH > window.innerHeight) ty = my - tH - 12;
    tip.style.left = tx + 'px';
    tip.style.top  = ty + 'px';
    tipTimeout = setTimeout(hideTip, 5000);
  }
  function hideTip() { tip.style.display = 'none'; }
  document.addEventListener('click', hideTip);

  /* ── Floating toolbar ───────────────────────────────────────────────────── */
  const floatToolbar = document.getElementById('floatToolbar');

  function positionFloatToolbar() {
    if (selectedIdx < 0) { hideFloatToolbar(); return; }
    const handle = overlay.querySelector(`[data-idx="${selectedIdx}"]`);
    if (!handle) { hideFloatToolbar(); return; }
    const rect = handle.getBoundingClientRect();
    const overlayRect = canvas.getBoundingClientRect();
    floatToolbar.style.display = 'flex';
    const ftW = 140;
    let fx = rect.left + rect.width / 2 - ftW / 2;
    let fy = rect.top - 44;
    if (fy < overlayRect.top) fy = rect.bottom + 4;
    fx = Math.max(8, Math.min(fx, window.innerWidth - ftW - 8));
    floatToolbar.style.left = fx + 'px';
    floatToolbar.style.top  = fy + 'px';
  }
  function hideFloatToolbar() { floatToolbar.style.display = 'none'; }

  document.getElementById('ftDuplicate').addEventListener('click', () => {
    if (selectedIdx < 0) return;
    const orig = { ...fields[selectedIdx], id: 'field_' + Date.now(), x_percent: fields[selectedIdx].x_percent + 2, y_percent: fields[selectedIdx].y_percent + 2 };
    fields.push(orig);
    selectField(fields.length - 1);
    redraw(); rebuildOverlay(); renderLayersList(); pushHistory();
  });
  document.getElementById('ftBringFront').addEventListener('click', () => {
    if (selectedIdx < 0) return;
    const [f] = fields.splice(selectedIdx, 1);
    fields.push(f);
    selectedIdx = fields.length - 1;
    redraw(); rebuildOverlay(); renderLayersList(); pushHistory();
  });
  document.getElementById('ftDelete').addEventListener('click', deleteSelectedField);

  /* ── Field operations ───────────────────────────────────────────────────── */
  function selectField(i) {
    selectedIdx = i;
    // Update handle classes
    overlay.querySelectorAll('.ds-field-handle').forEach((h, idx) => {
      h.classList.toggle('selected', idx === i);
    });
    redraw();
    if (i >= 0 && i < fields.length) {
      showProps();
      syncPropsFromField(i);
      positionFloatToolbar();
    } else {
      hideProps();
      hideFloatToolbar();
    }
    renderLayersList(); // highlight active layer
  }

  function addField(opts = {}) {
    const f = {
      id:           'field_' + Date.now(),
      variable:     opts.variable     || '{{Name}}',
      font_family:  opts.font_family  || (FONTS.length ? FONTS[0].id : 'DejaVuSerif'),
      font_size:    opts.font_size    || 48,
      color_hex:    opts.color_hex    || '#1a1a2e',
      align:        opts.align        || 'left',
      bold:         opts.bold         || false,
      italic:       opts.italic       || false,
      underline:    opts.underline    || false,
      letterSpacing: opts.letterSpacing || 0,
      lineHeight:   opts.lineHeight   || 1.2,
      opacity:      opts.opacity      ?? 100,
      x_percent:    opts.x_percent    ?? 50,
      y_percent:    opts.y_percent    ?? 50,
      locked:       opts.locked       || false
    };
    fields.push(f);
    redraw();
    rebuildOverlay();
    renderLayersList();
    selectField(fields.length - 1);
    pushHistory();
  }

  function deleteSelectedField() {
    if (selectedIdx < 0) return;
    fields.splice(selectedIdx, 1);
    selectedIdx = -1;
    redraw(); rebuildOverlay(); renderLayersList(); hideProps(); hideFloatToolbar(); pushHistory();
  }

  document.getElementById('deleteFieldBtn').addEventListener('click', deleteSelectedField);

  /* ── Properties panel sync ──────────────────────────────────────────────── */
  function showProps() {
    document.getElementById('dsProps').style.display = 'flex';
    document.getElementById('dsProps').style.flexDirection = 'column';
  }
  function hideProps() {
    document.getElementById('dsProps').style.display = 'none';
  }

  document.getElementById('propsCloseBtn').addEventListener('click', () => {
    selectField(-1);
  });

  function syncPropsFromField(i) {
    if (i < 0 || i >= fields.length) return;
    const f = fields[i];
    const varSel = document.getElementById('fVariable');
    const known = Object.keys(PLACEHOLDER_INFO);
    varSel.value = known.includes(f.variable) ? f.variable : 'Custom';
    document.getElementById('customTextRow').style.display = varSel.value === 'Custom' ? 'block' : 'none';
    if (varSel.value === 'Custom') document.getElementById('fCustomText').value = f.variable;
    document.getElementById('fFont').value   = f.font_family;
    document.getElementById('fSize').value   = f.font_size;
    document.getElementById('fColor').value  = f.color_hex;
    document.getElementById('fColorHex').value = f.color_hex;
    document.getElementById('fPosX').value   = f.x_percent.toFixed(1);
    document.getElementById('fPosY').value   = f.y_percent.toFixed(1);

    // Alignment
    document.querySelectorAll('.ds-align-btn').forEach(b => b.classList.toggle('active', b.dataset.align === f.align));

    // Bold / italic / underline
    document.getElementById('fBold').classList.toggle('active', !!f.bold);
    document.getElementById('fItalic').classList.toggle('active', !!f.italic);
    document.getElementById('fUnderline').classList.toggle('active', !!f.underline);

    // Sliders
    const ls = f.letterSpacing || 0;
    document.getElementById('fLetterSpacing').value = ls;
    document.getElementById('fLetterSpacingVal').textContent = ls;
    const lh = f.lineHeight || 1.2;
    document.getElementById('fLineHeight').value = lh;
    document.getElementById('fLineHeightVal').textContent = lh;
    const op = f.opacity ?? 100;
    document.getElementById('fOpacity').value = op;
    document.getElementById('fOpacityVal').textContent = op + '%';
  }

  function syncFieldFromProps() {
    if (selectedIdx < 0) return;
    const f = fields[selectedIdx];
    const varVal = document.getElementById('fVariable').value;
    f.variable    = varVal === 'Custom' ? document.getElementById('fCustomText').value : varVal;
    f.font_family = document.getElementById('fFont').value;
    f.font_size   = parseInt(document.getElementById('fSize').value) || 36;
    f.color_hex   = document.getElementById('fColor').value;

    const activeAlign = document.querySelector('.ds-align-btn.active');
    f.align = activeAlign ? activeAlign.dataset.align : 'left';

    f.bold      = document.getElementById('fBold').classList.contains('active');
    f.italic    = document.getElementById('fItalic').classList.contains('active');
    f.underline = document.getElementById('fUnderline').classList.contains('active');
    f.letterSpacing = parseFloat(document.getElementById('fLetterSpacing').value) || 0;
    f.lineHeight    = parseFloat(document.getElementById('fLineHeight').value) || 1.2;
    f.opacity       = parseInt(document.getElementById('fOpacity').value) ?? 100;
    f.x_percent     = parseFloat(document.getElementById('fPosX').value) || f.x_percent;
    f.y_percent     = parseFloat(document.getElementById('fPosY').value) || f.y_percent;

    redraw(); rebuildOverlay(); renderLayersList();
  }

  // Wire up all prop controls
  ['fVariable','fFont','fSize','fColor','fPosX','fPosY','fCustomText'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', () => { syncFieldFromProps(); pushHistory(); });
  });

  document.getElementById('fVariable').addEventListener('change', () => {
    document.getElementById('customTextRow').style.display =
      document.getElementById('fVariable').value === 'Custom' ? 'block' : 'none';
  });

  // Color hex input sync
  document.getElementById('fColor').addEventListener('input', e => {
    document.getElementById('fColorHex').value = e.target.value;
    syncFieldFromProps(); pushHistory();
  });
  document.getElementById('fColorHex').addEventListener('input', e => {
    const v = e.target.value.trim();
    if (/^#[0-9a-fA-F]{6}$/.test(v)) {
      document.getElementById('fColor').value = v;
      syncFieldFromProps(); pushHistory();
    }
  });

  // Alignment buttons
  document.querySelectorAll('.ds-align-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ds-align-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      syncFieldFromProps(); pushHistory();
    });
  });

  // Bold/Italic/Underline toggle
  ['fBold','fItalic','fUnderline'].forEach(id => {
    document.getElementById(id).addEventListener('click', () => {
      document.getElementById(id).classList.toggle('active');
      syncFieldFromProps(); pushHistory();
    });
  });

  // Range sliders
  [['fLetterSpacing','fLetterSpacingVal',''], ['fLineHeight','fLineHeightVal',''], ['fOpacity','fOpacityVal','%']].forEach(([sId, vId, suffix]) => {
    document.getElementById(sId).addEventListener('input', e => {
      document.getElementById(vId).textContent = e.target.value + suffix;
      syncFieldFromProps();
    });
    document.getElementById(sId).addEventListener('change', () => pushHistory());
  });

  /* ── Panel navigation (icon sidebar) ──────────────────────────────────── */
  const panel = document.getElementById('dsPanel');
  let currentPanel = null;

  function openPanel(name) {
    // Show new panel content
    document.querySelectorAll('.ds-panel-content').forEach(p => {
      p.classList.toggle('active', p.id === `panel-${name}`);
    });
    document.querySelectorAll('.ds-icon-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.panel === name);
    });
    if (currentPanel === name) {
      // Toggle close
      panel.classList.remove('open');
      currentPanel = null;
    } else {
      panel.classList.add('open');
      currentPanel = name;
    }
  }

  document.querySelectorAll('.ds-icon-btn').forEach(btn => {
    btn.addEventListener('click', () => openPanel(btn.dataset.panel));
  });

  // Close buttons inside panels
  document.querySelectorAll('.ds-panel-close').forEach(btn => {
    btn.addEventListener('click', () => {
      panel.classList.remove('open');
      document.querySelectorAll('.ds-icon-btn').forEach(b => b.classList.remove('active'));
      currentPanel = null;
    });
  });

  // Open templates panel by default
  setTimeout(() => openPanel('templates'), 100);

  /* ── Zoom controls ──────────────────────────────────────────────────────── */
  const scaler = document.getElementById('canvasScaler');
  const zoomVal = document.getElementById('zoomVal');

  function applyZoom(z) {
    zoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, z));
    scaler.style.transform = `scale(${zoom})`;
    zoomVal.textContent = Math.round(zoom * 100) + '%';
    positionOverlayHandles();
    positionFloatToolbar();
  }

  document.getElementById('zoomInBtn').addEventListener('click', () => applyZoom(zoom + ZOOM_STEP));
  document.getElementById('zoomOutBtn').addEventListener('click', () => applyZoom(zoom - ZOOM_STEP));
  document.getElementById('zoomFitBtn').addEventListener('click', () => {
    const outer = document.getElementById('canvasOuter');
    const fitW = (outer.clientWidth - 80) / canvas.width;
    const fitH = (outer.clientHeight - 80) / canvas.height;
    applyZoom(Math.min(fitW, fitH));
  });

  // Ctrl+wheel zoom
  document.getElementById('canvasOuter').addEventListener('wheel', e => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      applyZoom(zoom - e.deltaY * 0.001);
    }
  }, { passive: false });

  /* ── Paper size buttons ─────────────────────────────────────────────────── */
  document.querySelectorAll('.ds-paper-btn[data-w]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ds-paper-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      canvas.width  = parseInt(btn.dataset.w);
      canvas.height = parseInt(btn.dataset.h);
      redraw(); rebuildOverlay(); pushHistory();
    });
  });

  /* ── Background upload ──────────────────────────────────────────────────── */
  const bgInput = document.getElementById('bgInput');
  bgInput.addEventListener('change', function () {
    if (!this.files.length) return;
    Array.from(this.files).forEach(file => {
      const fd = new FormData();
      fd.append('file', file);
      fetch('/api/upload-background', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(d => {
          if (d.filename) { bgFilename = d.filename; loadBackground(d.url); addBgThumb(d.url, d.filename); pushHistory(); }
        });
    });
    this.value = '';
  });

  const bgDropZone = document.getElementById('bgDropZone');
  if (bgDropZone) {
    bgDropZone.addEventListener('dragover', e => { e.preventDefault(); bgDropZone.classList.add('dragover'); });
    bgDropZone.addEventListener('dragleave', () => bgDropZone.classList.remove('dragover'));
    bgDropZone.addEventListener('drop', e => {
      e.preventDefault(); bgDropZone.classList.remove('dragover');
      const files = e.dataTransfer.files;
      if (files.length) { bgInput.files = files; bgInput.dispatchEvent(new Event('change')); }
    });
  }

  function loadBackground(url) {
    const img = new Image();
    img.onload = () => { 
      bgImage = img; 
      analyzeBackgroundForColors(bgImage);
      redraw(); 
      pushHistory(); 
    };
    img.src = url;
  }

  function addBgThumb(url, filename) {
    const grid = document.getElementById('bgList');
    const wrap = document.createElement('div');
    wrap.className = 'ds-bg-thumb';
    wrap.title = filename;
    const img = document.createElement('img');
    img.src = url;
    const useBtn = document.createElement('div');
    useBtn.className = 'ds-bg-thumb-use';
    useBtn.textContent = 'Use';
    wrap.appendChild(img);
    wrap.appendChild(useBtn);
    wrap.addEventListener('click', () => {
      document.querySelectorAll('.ds-bg-thumb').forEach(t => t.classList.remove('selected'));
      wrap.classList.add('selected');
      bgFilename = filename;
      loadBackground(url);
    });
    grid.appendChild(wrap);
    wrap.classList.add('selected');
  }

  fetch('/api/backgrounds')
    .then(r => r.json())
    .then(list => list.forEach(b => addBgThumb(b.url, b.filename)));

  /* ── Add text via panel buttons ─────────────────────────────────────────── */
  document.getElementById('addTextboxBtn').addEventListener('click', () => addField({ variable: 'Custom', font_size: 36 }));
  document.getElementById('addHeadingBtn').addEventListener('click', () => addField({ variable: 'Custom', font_size: 64, bold: true }));
  document.getElementById('addSubheadingBtn').addEventListener('click', () => addField({ variable: 'Custom', font_size: 40, bold: true }));
  document.getElementById('addBodyBtn').addEventListener('click', () => addField({ variable: 'Custom', font_size: 28 }));

  // Text combinations
  document.querySelectorAll('.ds-combo-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const combo = btn.dataset.combo;
      if (combo === 'cert-title') {
        addField({ variable: 'CERTIFICATE', font_size: 64, bold: true, letterSpacing: 6, align: 'center', y_percent: 25 });
        addField({ variable: 'OF ACHIEVEMENT', font_size: 24, align: 'center', letterSpacing: 2, y_percent: 32 });
      } else if (combo === 'cert-name') {
        addField({ variable: 'CERTIFICATE OF COMPLETION', font_size: 26, bold: true, letterSpacing: 2, align: 'center', y_percent: 42 });
        addField({ variable: '{{Name}}', font_size: 60, bold: true, align: 'center', y_percent: 54 });
      } else if (combo === 'signature') {
        addField({ variable: 'Signature', font_family: 'Italianno', font_size: 60, align: 'center', y_percent: 75 });
        addField({ variable: 'Name Surname', font_size: 22, bold: true, align: 'center', y_percent: 82 });
        addField({ variable: 'Program Mentor', font_size: 16, align: 'center', y_percent: 87 });
      } else if (combo === 'issue-date') {
        addField({ variable: '{{Date}}', font_size: 30, bold: true, align: 'center', y_percent: 75 });
        addField({ variable: 'Issue Date', font_size: 18, align: 'center', y_percent: 82 });
      }
    });
  });

  /* ── Attributes panel: click to add placeholder ─────────────────────────── */
  document.querySelectorAll('.ds-attr-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const v = pill.dataset.var;
      addField({ variable: v, font_size: 48, align: 'center' });
      // Switch to canvas focus
    });
  });

  // Custom attribute
  document.getElementById('addCustomAttrBtn').addEventListener('click', () => {
    const input = document.getElementById('customAttrInput');
    const name = input.value.trim();
    if (!name) return;
    const varName = `{{${name}}}`;
    // Add pill to list
    const pill = document.createElement('button');
    pill.className = 'ds-attr-pill';
    pill.dataset.var = varName;
    pill.innerHTML = `<span class="ds-attr-pill-tag">${varName}</span><span class="ds-attr-pill-label">${name}</span><span class="ds-attr-pill-icon">+</span>`;
    pill.addEventListener('click', () => addField({ variable: varName, font_size: 36, align: 'center' }));
    document.getElementById('attrList').appendChild(pill);
    input.value = '';
  });

  /* ── Layers list ────────────────────────────────────────────────────────── */
  function renderLayersList() {
    const list = document.getElementById('layersList');
    list.innerHTML = '';
    [...fields].reverse().forEach((f, ri) => {
      const i = fields.length - 1 - ri;
      const row = document.createElement('div');
      row.className = 'ds-layer-row' + (i === selectedIdx ? ' selected' : '');
      row.innerHTML = `
        <span class="ds-layer-icon">T</span>
        <span style="flex:1;font-size:0.78rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${variableLabel(f.variable)}</span>
        <span class="ds-layer-handle" title="Drag to reorder">⠿</span>
      `;
      row.addEventListener('click', () => selectField(i));
      list.appendChild(row);
    });
  }

  /* ── Elements (shapes) ──────────────────────────────────────────────────── */
  document.querySelectorAll('.ds-elem-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      // For now, add a text label representing the element (canvas shapes would need a shape system)
      const elem = btn.dataset.elem;
      addField({ variable: `[${elem}]`, font_size: 32, align: 'center' });
    });
  });

  /* ── Template gallery ───────────────────────────────────────────────────── */
  function loadTemplateGallery() {
    fetch('/api/builtin-templates')
      .then(r => r.json())
      .then(list => {
        const grid = document.getElementById('tmplGrid');
        grid.innerHTML = '';
        if (!list.length) {
          grid.innerHTML = '<p style="font-size:0.8rem;color:var(--text-3);padding:0.5rem 0;grid-column:1/-1">No templates yet.</p>';
          return;
        }
        list.forEach(tmpl => {
          const card = document.createElement('div');
          card.className = 'ds-tmpl-card';
          card.innerHTML = `<img src="${tmpl.thumb_url || ''}" alt="${tmpl.name}" onerror="this.style.display='none'"><div class="ds-tmpl-card-name">${tmpl.name}</div>`;
          card.addEventListener('click', () => applyBuiltinTemplate(tmpl.template_id));
          grid.appendChild(card);
        });
      })
      .catch(() => {
        document.getElementById('tmplGrid').innerHTML = '<p style="font-size:0.8rem;color:var(--text-3);padding:0.5rem 0;grid-column:1/-1">Could not load templates.</p>';
      });
  }
  loadTemplateGallery();

  // Filter chips
  document.querySelectorAll('.ds-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.ds-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
    });
  });

  function applyBuiltinTemplate(templateId) {
    fetch(`/api/template/${templateId}`)
      .then(r => r.ok ? r.json() : Promise.reject('not found'))
      .then(tmpl => {
        canvas.width  = tmpl.width  || 1200;
        canvas.height = tmpl.height || 850;
        if (tmpl.background_url) { bgFilename = tmpl.background_id || ''; loadBackground(tmpl.background_url); }
        fields = []; selectedIdx = -1;
        (tmpl.text_fields || []).forEach(f => {
          fields.push({
            id: f.id || ('field_' + Date.now() + '_' + Math.random().toString(36).slice(2)),
            variable: f.variable || '{{Name}}',
            font_family: f.font_family || (FONTS.length ? FONTS[0].id : 'DejaVuSerif'),
            font_size: f.font_size || 36,
            color_hex: f.color_hex || '#000000',
            align: f.align || 'left',
            bold: false, italic: false, underline: false,
            letterSpacing: 0, lineHeight: 1.2, opacity: 100,
            x_percent: f.x_percent ?? 50,
            y_percent: f.y_percent ?? 50,
          });
        });
        redraw(); rebuildOverlay(); renderLayersList(); hideProps(); hideFloatToolbar(); pushHistory();
        // Close template panel
        panel.classList.remove('open');
        currentPanel = null;
        document.querySelectorAll('.ds-icon-btn').forEach(b => b.classList.remove('active'));
      })
      .catch(() => {});
  }

  /* ── Google Fonts ───────────────────────────────────────────────────────── */
  function _fontStatusMsg(msg, isError) {
    const el = document.getElementById('fontStatus');
    if (!el) return;
    el.style.display = 'block';
    el.style.background = isError ? 'var(--danger-dim)' : 'var(--success-dim)';
    el.style.color = isError ? 'var(--danger)' : 'var(--success)';
    el.textContent = msg;
    if (!isError) setTimeout(() => { el.style.display = 'none'; }, 4000);
  }

  function _registerFontInUI(fontId, displayName, fontInfo) {
    FONT_CSS_MAP[fontId] = fontInfo;
    const sel = document.getElementById('fFont');
    if (sel && !Array.from(sel.options).some(o => o.value === fontId)) {
      const opt = document.createElement('option');
      opt.value = fontId; opt.textContent = displayName;
      sel.appendChild(opt);
    }
    // Also add to font list display
    const fl = document.getElementById('fontList');
    if (fl) {
      const row = document.createElement('div');
      row.className = 'ds-font-row';
      row.textContent = displayName;
      fl.appendChild(row);
    }
    ensureFontFaceLoaded(fontId);
  }

  document.getElementById('addGoogleFontBtn').addEventListener('click', () => {
    const input = document.getElementById('googleFontInput');
    const family = (input.value || '').trim();
    if (!family) { _fontStatusMsg('Enter a font family name first.', true); return; }
    const btn = document.getElementById('addGoogleFontBtn');
    btn.disabled = true; btn.textContent = '…';
    _fontStatusMsg('Downloading from Google Fonts…', false);
    fetch('/api/add-google-font', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ family }) })
      .then(r => r.json())
      .then(d => {
        if (d.error) { _fontStatusMsg(d.error, true); return; }
        _registerFontInUI(d.font_id, d.display_name, { display_name: d.display_name, css_family: `"${d.display_name}",serif`, bold: false, source: 'google', filename: d.filename });
        input.value = '';
        _fontStatusMsg(`"${d.display_name}" added!`, false);
      })
      .catch(e => _fontStatusMsg('Network error: ' + e.message, true))
      .finally(() => { btn.disabled = false; btn.textContent = 'Add'; });
  });

  document.getElementById('googleFontInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('addGoogleFontBtn').click();
  });

  document.getElementById('fontFileInput').addEventListener('change', function () {
    const file = this.files[0]; if (!file) return;
    const fd = new FormData(); fd.append('file', file);
    _fontStatusMsg('Uploading font…', false);
    fetch('/api/upload-font', { method: 'POST', body: fd })
      .then(r => r.json())
      .then(d => {
        if (d.error) { _fontStatusMsg(d.error, true); return; }
        _registerFontInUI(d.font_id, d.display_name, { display_name: d.display_name, css_family: `"${d.display_name}",serif`, bold: false, source: 'upload', filename: d.filename });
        _fontStatusMsg(`"${d.display_name}" uploaded!`, false);
      })
      .catch(e => _fontStatusMsg('Upload error: ' + e.message, true));
    this.value = '';
  });

  /* ── Save template ──────────────────────────────────────────────────────── */
  document.getElementById('saveTemplateBtn').addEventListener('click', () => {
    const name = document.getElementById('designName').value.trim() || 'My Certificate';
    if (!fields.length) { alert('Add at least one text field before saving.'); return; }
    const payload = { name, session_id: sessionId, background_id: bgFilename, width: canvas.width, height: canvas.height, text_fields: fields };
    fetch('/api/save-template', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      .then(r => r.json())
      .then(d => {
        if (d.template_id) {
          if (sessionId) {
            window.location.href = `/preview?session_id=${sessionId}`;
          } else {
            alert('Template saved successfully in your gallery!');
            window.location.href = '/';
          }
        }
        else alert('Save failed: ' + (d.error || 'Unknown error'));
      });
  });

  document.getElementById('previewTopBtn').addEventListener('click', () => {
    if (!sessionId) {
      alert("You need to upload recipient data before you can preview the generated certificates.");
      return;
    }
    window.open(`/preview?session_id=${sessionId}`, '_blank');
  });

  /* ── Background Auto-Color & Palette Gen ────────────────────────────────── */
  function analyzeBackgroundForColors(imgObj) {
    const oc = document.createElement('canvas');
    const octx = oc.getContext('2d');
    oc.width = 100;
    oc.height = 100;
    octx.drawImage(imgObj, 0, 0, 100, 100);
    const data = octx.getImageData(0, 0, 100, 100).data;
    
    let r = 0, g = 0, b = 0;
    for (let i = 0; i < data.length; i += 16) {
      r += data[i]; g += data[i+1]; b += data[i+2];
    }
    const px = data.length / 16;
    const brightness = (r/px * 299 + g/px * 587 + b/px * 114) / 1000;
    
    // Auto-contrast color for fields that are not locked
    const newColor = brightness < 128 ? '#ffffff' : '#111827';
    fields.forEach(f => {
      if (!f.locked) f.color_hex = newColor;
    });

    // Extract quick palette (5 unique colors)
    const colors = [];
    // sample 25 discrete pixels out of the 100x100
    for(let y = 10; y < 100; y+=20) {
      for(let x = 10; x < 100; x+=20) {
        const idx = (y * 100 + x) * 4;
        const hex = "#" + (1 << 24 | data[idx] << 16 | data[idx+1] << 8 | data[idx+2]).toString(16).slice(1);
        if (!colors.includes(hex)) colors.push(hex);
      }
    }
    renderColorPresets(colors.slice(0, 6));
  }

  function renderColorPresets(palette) {
    let presetDiv = document.getElementById('dsColorPresets');
    if (!presetDiv) {
      const colorInput = document.getElementById('fColor');
      presetDiv = document.createElement('div');
      presetDiv.id = 'dsColorPresets';
      presetDiv.style.display = 'flex';
      presetDiv.style.flexWrap = 'wrap';
      presetDiv.style.gap = '6px';
      presetDiv.style.marginTop = '10px';
      colorInput.parentNode.appendChild(presetDiv);
    }
    presetDiv.innerHTML = '';
    
    // Ensure we provide basic black/white too
    const finalPalette = ['#ffffff', '#000000', ...palette].slice(0, 8);
    finalPalette.forEach(hex => {
      if (!hex) return;
      const dot = document.createElement('div');
      dot.style.width = '24px'; dot.style.height = '24px';
      dot.style.borderRadius = '50%'; dot.style.backgroundColor = hex;
      dot.style.cursor = 'pointer'; dot.style.border = '1px solid rgba(255,255,255,0.2)';
      dot.style.boxShadow = '0 1px 3px rgba(0,0,0,0.3)';
      dot.addEventListener('click', () => {
        document.getElementById('fColor').value = hex;
        if (selectedIdx >= 0) { 
          fields[selectedIdx].color_hex = hex; 
          document.getElementById('fColorHex').value = hex;
          redraw(); 
          pushHistory();
        }
      });
      presetDiv.appendChild(dot);
    });
  }

  /* ── Init ───────────────────────────────────────────────────────────────── */
  const _loadTemplateId = new URLSearchParams(window.location.search).get('load_template');

  if (_loadTemplateId) {
    fetch(`/api/template/${_loadTemplateId}`)
      .then(r => r.ok ? r.json() : Promise.reject('not found'))
      .then(tmpl => {
        canvas.width  = tmpl.width  || 1200;
        canvas.height = tmpl.height || 850;
        if (tmpl.background_url) { bgFilename = tmpl.background_id || ''; loadBackground(tmpl.background_url); }
        fields = [];
        (tmpl.text_fields || []).forEach(f => {
          fields.push({ id: f.id || ('field_' + Date.now()), variable: f.variable || '{{Name}}', font_family: f.font_family || (FONTS.length ? FONTS[0].id : 'DejaVuSerif'), font_size: f.font_size || 36, color_hex: f.color_hex || '#000', align: f.align || 'left', bold: false, italic: false, underline: false, letterSpacing: 0, lineHeight: 1.2, opacity: 100, x_percent: f.x_percent ?? 50, y_percent: f.y_percent ?? 50 });
        });
        redraw(); rebuildOverlay(); renderLayersList(); pushHistory();
      })
      .catch(() => _addDefaultFields());
  } else {
    _addDefaultFields();
  }

  function _addDefaultFields() {
    addField({ variable: '{{Name}}',         y_percent: 52, font_size: 54, align: 'center', bold: true });
    addField({ variable: '{{Course/Event}}', y_percent: 63, font_size: 36, align: 'center' });
    addField({ variable: '{{Date}}',         y_percent: 73, font_size: 28, align: 'center', color_hex: '#64748B' });
    selectField(0);
    pushHistory();
  }

  // Initial zoom fit
  setTimeout(() => {
    const outer = document.getElementById('canvasOuter');
    const fitW = (outer.clientWidth - 80) / canvas.width;
    const fitH = (outer.clientHeight - 80) / canvas.height;
    applyZoom(Math.min(fitW, fitH, 0.9));
  }, 200);

})();
