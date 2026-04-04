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
      ctx.font = `${f.font_family.includes('Bold') ? 'bold' : 'normal'} ${size}px serif`;
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
      ctx.font = `${fields[i].font_family.includes('Bold') ? 'bold' : 'normal'} ${size}px serif`;
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

  // Default starter fields
  addField({ variable: '{{Name}}',         y_percent: 52, font_size: 54 });
  addField({ variable: '{{Course/Event}}', y_percent: 62, font_size: 36 });
  addField({ variable: '{{Date}}',         y_percent: 71, font_size: 28, color_hex: '#64748B' });
  selectField(0);
})();
