(function () {
  const sessionId   = document.getElementById('sessionId').value;
  const prevBtn     = document.getElementById('prevBtn');
  const nextBtn     = document.getElementById('nextBtn');
  const counter     = document.getElementById('previewCounter');
  const nameEl      = document.getElementById('previewName');
  const img         = document.getElementById('previewImg');
  const spinner     = document.getElementById('previewSpinner');
  const errDiv      = document.getElementById('previewError');
  const proceedBtn  = document.getElementById('proceedBtn');
  const backBtn     = document.getElementById('backBtn');

  backBtn.href = `/designer?session_id=${sessionId}`;

  let current = 0;
  let total   = 0;

  function loadPreview(index) {
    img.style.display    = 'none';
    spinner.style.display = 'block';
    errDiv.style.display = 'none';

    fetch(`/api/preview-certificate?session_id=${sessionId}&row_index=${index}`)
      .then(r => r.json())
      .then(data => {
        spinner.style.display = 'none';
        if (data.error) {
          errDiv.textContent  = data.error;
          errDiv.style.display = 'block';
          return;
        }
        img.src = data.image_url + '?t=' + Date.now();
        img.onload = () => { img.style.display = 'block'; };
        nameEl.textContent = data.recipient_name;
        total = data.total;
        current = data.row_index;
        counter.textContent = `${current + 1} / ${total}`;
        prevBtn.disabled = current === 0;
        nextBtn.disabled = current >= total - 1;
        proceedBtn.disabled = false;
      })
      .catch(err => {
        spinner.style.display = 'none';
        errDiv.textContent  = 'Failed to load preview: ' + err.message;
        errDiv.style.display = 'block';
      });
  }

  prevBtn.addEventListener('click', () => { if (current > 0) loadPreview(current - 1); });
  nextBtn.addEventListener('click', () => { if (current < total - 1) loadPreview(current + 1); });

  proceedBtn.addEventListener('click', () => {
    window.location.href = `/send?session_id=${sessionId}`;
  });

  if (sessionId) loadPreview(0);
  else {
    errDiv.textContent  = 'No session found. Please start from the upload step.';
    errDiv.style.display = 'block';
  }
})();
