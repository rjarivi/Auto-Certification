(function () {
  const dropZone   = document.getElementById('dropZone');
  const fileInput  = document.getElementById('fileInput');
  const errorsDiv  = document.getElementById('errors');
  const loader     = document.getElementById('loader');
  const resultSec  = document.getElementById('resultSection');
  const rowCount   = document.getElementById('rowCount');
  const warnCount  = document.getElementById('warnCount');
  const tableHead  = document.getElementById('tableHead');
  const tableBody  = document.getElementById('tableBody');
  const proceedBtn = document.getElementById('proceedBtn');

  let sessionId = null;

  // Drag & drop
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });
  dropZone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => { if (fileInput.files[0]) uploadFile(fileInput.files[0]); });

  function uploadFile(file) {
    errorsDiv.style.display = 'none';
    resultSec.style.display = 'none';
    loader.style.display    = 'flex';

    const fd = new FormData();
    fd.append('file', file);

    fetch('/api/upload-excel', { method: 'POST', body: fd })
      .then(r => {
        const ct = r.headers.get('content-type') || '';
        if (!ct.includes('application/json')) {
          throw new Error(`Server error (HTTP ${r.status}) — check Railway logs for details.`);
        }
        return r.json();
      })
      .then(data => {
        loader.style.display = 'none';

        if (data.error) {
          showError(data.error);
          return;
        }
        if (data.errors && data.errors.length && !data.row_count) {
          showError(data.errors.join('\n'));
          return;
        }

        sessionId = data.session_id;
        renderResult(data);
      })
      .catch(err => {
        loader.style.display = 'none';
        showError('Upload failed: ' + err.message);
      });
  }

  function showError(msg) {
    errorsDiv.textContent = msg;
    errorsDiv.style.display = 'block';
  }

  function renderResult(data) {
    rowCount.textContent = `${data.row_count} recipients loaded`;
    if (data.errors && data.errors.length) {
      warnCount.textContent = `${data.errors.length} warning(s)`;
      warnCount.style.display = 'inline-block';
    }

    // Build table header
    tableHead.innerHTML = '';
    data.columns.forEach(col => {
      const th = document.createElement('th');
      th.textContent = col;
      tableHead.appendChild(th);
    });

    // Build table rows (up to 10)
    tableBody.innerHTML = '';
    data.preview_rows.forEach(row => {
      const tr = document.createElement('tr');
      data.columns.forEach(col => {
        const td = document.createElement('td');
        td.textContent = row[col] || '';
        tr.appendChild(td);
      });
      tableBody.appendChild(tr);
    });

    resultSec.style.display = 'block';
    proceedBtn.disabled = false;
  }

  proceedBtn.addEventListener('click', () => {
    if (!sessionId) return;
    const pendingTemplate = localStorage.getItem('pendingTemplate');
    if (pendingTemplate) {
      localStorage.removeItem('pendingTemplate');
      window.location.href = `/designer?session_id=${sessionId}&load_template=${pendingTemplate}`;
    } else {
      window.location.href = `/designer?session_id=${sessionId}`;
    }
  });
})();
