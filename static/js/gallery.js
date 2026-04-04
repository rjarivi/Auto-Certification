(function () {
  const sessionId = document.getElementById('sessionId').value;
  let templates = [];
  let activeCategory    = 'all';
  let activeOrientation = 'all';

  // ── Load templates ───────────────────────────────────────────────────────────
  fetch('/api/builtin-templates')
    .then(r => r.json())
    .then(data => {
      templates = data;
      render();
    })
    .catch(() => {
      document.getElementById('galleryGrid').innerHTML =
        '<p class="text-muted gallery-empty">Failed to load templates — please refresh.</p>';
    });

  // ── Filter chips ─────────────────────────────────────────────────────────────
  document.querySelectorAll('.chip[data-filter]').forEach(chip => {
    chip.addEventListener('click', () => {
      const type  = chip.dataset.filter;
      const value = chip.dataset.value;
      document.querySelectorAll(`.chip[data-filter="${type}"]`).forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      if (type === 'category')    activeCategory    = value;
      if (type === 'orientation') activeOrientation = value;
      render();
    });
  });

  // ── Render ───────────────────────────────────────────────────────────────────
  function filtered() {
    return templates.filter(t => {
      if (activeCategory    !== 'all' && t.category    !== activeCategory)    return false;
      if (activeOrientation !== 'all' && t.orientation !== activeOrientation) return false;
      return true;
    });
  }

  function render() {
    const grid  = document.getElementById('galleryGrid');
    const items = filtered();
    if (!items.length) {
      grid.innerHTML = '<p class="text-muted gallery-empty">No templates match your filters.</p>';
      return;
    }
    grid.innerHTML = items.map(card).join('');
    grid.querySelectorAll('.gallery-use-btn').forEach(btn => {
      btn.addEventListener('click', () => useTemplate(btn.dataset.id));
    });
  }

  function card(t) {
    const catLabel = t.category.charAt(0).toUpperCase() + t.category.slice(1);
    const orientLabel = t.orientation === 'vertical' ? '↕ Portrait' : '↔ Landscape';
    return `
      <div class="gallery-card gallery-card--${t.orientation}">
        <div class="gallery-thumb-wrap">
          <img src="${t.thumb_url}" alt="${t.name}" class="gallery-thumb" loading="lazy" />
        </div>
        <div class="gallery-card-body">
          <div class="gallery-card-meta">
            <span class="chip chip-cat chip-cat--${t.category}">${catLabel}</span>
            <span class="gallery-orient-label">${orientLabel}</span>
          </div>
          <h3 class="gallery-card-title">${t.name}</h3>
          <button class="btn btn-primary btn-sm gallery-use-btn" data-id="${t.template_id}">
            Use this template →
          </button>
        </div>
      </div>`;
  }

  // ── Use template ─────────────────────────────────────────────────────────────
  function useTemplate(templateId) {
    if (sessionId) {
      window.location.href = `/designer?session_id=${sessionId}&load_template=${templateId}`;
    } else {
      // Store hint so upload page can redirect to designer with the template pre-loaded
      localStorage.setItem('pendingTemplate', templateId);
      window.location.href = '/upload';
    }
  }
})();
