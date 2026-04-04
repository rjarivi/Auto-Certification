(function () {
  const sessionId    = document.getElementById('sessionId').value;
  const form         = document.getElementById('smtpForm');
  const sendBtn      = document.getElementById('sendBtn');
  const backBtn      = document.getElementById('backBtn');
  const errDiv       = document.getElementById('sendError');
  const progressSec  = document.getElementById('progressSection');
  const progressFill = document.getElementById('progressFill');
  const progressSum  = document.getElementById('progressSummary');
  const statusList   = document.getElementById('statusList');
  const doneMsg      = document.getElementById('doneMessage');

  backBtn.href = `/preview?session_id=${sessionId}`;

  // Mode toggle
  document.querySelectorAll('input[name="smtpMode"]').forEach(radio => {
    radio.addEventListener('change', () => {
      const isGmail = radio.value === 'gmail';
      document.getElementById('gmailFields').style.display  = isGmail ? 'block' : 'none';
      document.getElementById('customFields').style.display = isGmail ? 'none'  : 'block';
    });
  });

  form.addEventListener('submit', e => {
    e.preventDefault();
    sendCertificates();
  });

  function buildSmtpConfig() {
    const mode = document.querySelector('input[name="smtpMode"]:checked').value;
    const base = {
      mode,
      sender_name:  document.getElementById('senderName').value.trim(),
      subject:      document.getElementById('emailSubject').value.trim(),
      body_text:    document.getElementById('emailBody').value.trim(),
    };
    if (mode === 'gmail') {
      base.sender_email = document.getElementById('gmailAddress').value.trim();
      base.app_password = document.getElementById('gmailAppPass').value.trim();
    } else {
      base.sender_email = document.getElementById('smtpUser').value.trim();
      base.host         = document.getElementById('smtpHost').value.trim();
      base.port         = document.getElementById('smtpPort').value;
      base.username     = document.getElementById('smtpUser').value.trim();
      base.password     = document.getElementById('smtpPass').value.trim();
      base.use_tls      = document.getElementById('useTls').checked;
    }
    return base;
  }

  function validate(cfg) {
    if (!cfg.sender_email) return 'Sender email is required.';
    if (cfg.mode === 'gmail' && !cfg.app_password) return 'Gmail App Password is required.';
    if (cfg.mode === 'custom' && !cfg.host) return 'SMTP Host is required.';
    return null;
  }

  function sendCertificates() {
    errDiv.style.display = 'none';
    const smtp = buildSmtpConfig();
    const err  = validate(smtp);
    if (err) { errDiv.textContent = err; errDiv.style.display = 'block'; return; }

    form.style.display    = 'none';
    progressSec.style.display = 'block';
    statusList.innerHTML  = '';
    progressFill.style.width = '0%';
    progressSum.textContent  = 'Connecting to SMTP…';

    fetch('/api/send-certificates', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id: sessionId, smtp }),
    })
      .then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        function read() {
          reader.read().then(({ done, value }) => {
            if (done) return;
            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop();
            parts.forEach(part => {
              const line = part.trim();
              if (line.startsWith('data:')) {
                try {
                  const ev = JSON.parse(line.slice(5).trim());
                  handleEvent(ev);
                } catch (_) {}
              }
            });
            read();
          });
        }
        read();
      })
      .catch(err => {
        progressSum.textContent = 'Connection error: ' + err.message;
      });
  }

  function handleEvent(ev) {
    if (ev.type === 'error') {
      errDiv.textContent  = ev.message;
      errDiv.style.display = 'block';
      progressSec.style.display = 'none';
      form.style.display = 'block';
      return;
    }

    if (ev.type === 'generating') {
      progressSum.textContent = `Generating certificate for ${ev.name}… (${ev.index + 1}/${ev.total})`;
      const pct = ((ev.index) / ev.total) * 100;
      progressFill.style.width = pct + '%';
      addStatusItem(ev.name, '', 'generating');
      return;
    }

    if (ev.type === 'progress') {
      const pct = ((ev.index + 1) / ev.total) * 100;
      progressFill.style.width = pct + '%';
      progressSum.textContent = `Sent ${ev.index + 1} of ${ev.total}`;
      updateLastStatusItem(ev.name, ev.email, ev.status, ev.error);
      return;
    }

    if (ev.type === 'done') {
      progressFill.style.width = '100%';
      progressSum.textContent  = `Completed: ${ev.sent} sent, ${ev.failed} failed`;
      doneMsg.innerHTML = `All done! <strong>${ev.sent}</strong> certificate(s) sent successfully.` +
        (ev.failed ? ` <strong>${ev.failed}</strong> failed.` : '');
      doneMsg.style.display = 'block';
    }
  }

  function addStatusItem(name, email, status) {
    const div  = document.createElement('div');
    div.className = 'status-item';
    div.dataset.name = name;
    div.innerHTML = `<span class="status-dot ${status}"></span><span>${name}</span><span class="text-muted">${email}</span>`;
    statusList.prepend(div);
  }

  function updateLastStatusItem(name, email, status, errorMsg) {
    // Update the last item that matches by name
    const items = statusList.querySelectorAll('.status-item');
    for (const item of items) {
      if (item.dataset.name === name) {
        item.querySelector('.status-dot').className = 'status-dot ' + status;
        item.querySelector('.text-muted').textContent = email;
        if (errorMsg) {
          const e = document.createElement('span');
          e.style.color = 'var(--danger)';
          e.style.fontSize = '0.8rem';
          e.textContent = ' – ' + errorMsg;
          item.appendChild(e);
        }
        break;
      }
    }
  }
})();
