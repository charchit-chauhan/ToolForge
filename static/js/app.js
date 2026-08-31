/* Tool Forge — Soft Studio UI helpers */

// History (local only)
window.TFHistory = {
  key: 'tf-history',
  max: 50,
  add(title, detail) {
    try {
      const items = this.list();
      items.unshift({ title, detail: (detail||'').slice(0,200), ts: Date.now() });
      localStorage.setItem(this.key, JSON.stringify(items.slice(0, this.max)));
    } catch(e) {}
  },
  list() {
    try { return JSON.parse(localStorage.getItem(this.key) || '[]'); } catch(e) { return []; }
  },
  clear() { localStorage.removeItem(this.key); }
};

// Theme
(function() {
  const btn = document.getElementById('themeToggle');
  const root = document.documentElement;
  function apply(t) {
    if (t === 'dark') root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
    if (btn) btn.textContent = t === 'dark' ? '☀️' : '🌓';
  }
  apply(localStorage.getItem('tf-theme') || 'light');
  btn?.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    localStorage.setItem('tf-theme', next);
    apply(next);
  });
})();

// Sidebar mobile
document.getElementById('menuToggle')?.addEventListener('click', () => {
  document.getElementById('sidebar')?.classList.toggle('open');
  document.getElementById('sidebarOverlay')?.classList.toggle('show');
});
document.getElementById('sidebarOverlay')?.addEventListener('click', () => {
  document.getElementById('sidebar')?.classList.remove('open');
  document.getElementById('sidebarOverlay')?.classList.remove('show');
});

// Command palette
(function() {
  const tools = [
    { name: 'Home', path: '/', icon: '🏠' },
    { name: 'Translator', path: '/translator', icon: '🌐' },
    { name: 'PDF Tools', path: '/pdf', icon: '📄' },
    { name: 'Convert Word ⇄ PDF', path: '/convert', icon: '🔄' },
    { name: 'OCR', path: '/ocr', icon: '🔍' },
    { name: 'Image Tools', path: '/images', icon: '🖼️' },
    { name: 'Text to Speech', path: '/tts', icon: '🔊' },
    { name: 'QR Code', path: '/qr', icon: '📱' },
    { name: 'Utilities', path: '/utilities', icon: '🧮' },
    { name: 'History', path: '/history', icon: '🕐' },
  ];
  const overlay = document.getElementById('cmdOverlay');
  const input = document.getElementById('cmdInput');
  const list = document.getElementById('cmdList');
  if (!overlay || !input || !list) return;
  let active = 0;
  let filtered = tools;

  function render() {
    const q = input.value.toLowerCase().trim();
    filtered = tools.filter(t => t.name.toLowerCase().includes(q));
    active = 0;
    if (!filtered.length) {
      list.innerHTML = '<div class="cmd-empty">No tools found</div>';
      return;
    }
    list.innerHTML = filtered.map((t,i) =>
      `<button type="button" class="cmd-item ${i===0?'active':''}" data-i="${i}">${t.icon} ${t.name}<span>${t.path}</span></button>`
    ).join('');
    list.querySelectorAll('.cmd-item').forEach(el => {
      el.onclick = () => { location.href = filtered[+el.dataset.i].path; };
    });
  }
  function open() {
    overlay.classList.add('show');
    input.value = '';
    render();
    setTimeout(() => input.focus(), 10);
  }
  function close() { overlay.classList.remove('show'); }
  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      overlay.classList.contains('show') ? close() : open();
    }
    if (!overlay.classList.contains('show')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowDown') { e.preventDefault(); active = Math.min(active+1, filtered.length-1); highlight(); }
    if (e.key === 'ArrowUp') { e.preventDefault(); active = Math.max(active-1, 0); highlight(); }
    if (e.key === 'Enter' && filtered[active]) location.href = filtered[active].path;
  });
  function highlight() {
    list.querySelectorAll('.cmd-item').forEach((el,i) => el.classList.toggle('active', i===active));
  }
  input.addEventListener('input', render);
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
  // topbar search focuses palette
  document.getElementById('toolSearch')?.addEventListener('focus', open);
})();

// Tool tabs
document.querySelectorAll('.tool-tabs').forEach(tabBar => {
  tabBar.querySelectorAll('.tool-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const panelId = tab.dataset.panel;
      tabBar.querySelectorAll('.tool-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const container = tabBar.parentElement;
      container.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
      const panel = document.getElementById('panel-' + panelId);
      if (panel) panel.classList.add('active');
    });
  });
});

// Dropzones
document.querySelectorAll('.dropzone').forEach(dz => {
  const inputId = dz.dataset.input;
  const input = document.getElementById(inputId);
  if (!input) return;
  dz.addEventListener('click', () => input.click());
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      input.dispatchEvent(new Event('change'));
    }
  });
  input.addEventListener('change', () => {
    const parent = dz.parentElement;
    const list = parent?.querySelector('.file-list');
    if (list) {
      list.innerHTML = '';
      Array.from(input.files).forEach(f => {
        const li = document.createElement('li');
        li.innerHTML = `<span>📎 ${f.name}</span><span class="text-muted">${(f.size/1024).toFixed(1)} KB</span>`;
        list.appendChild(li);
      });
    }
    if (input.files.length === 1) {
      const hint = dz.querySelector('.dropzone-text');
      if (hint) hint.textContent = input.files[0].name;
    } else if (input.files.length > 1) {
      const hint = dz.querySelector('.dropzone-text');
      if (hint) hint.textContent = `${input.files.length} files selected`;
    }
  });
});

function showLoading(msg) {
  const el = document.getElementById('loadingOverlay');
  const txt = document.getElementById('loadingText');
  if (txt) txt.textContent = msg || 'Processing…';
  if (el) el.classList.add('show');
}
function hideLoading() {
  document.getElementById('loadingOverlay')?.classList.remove('show');
}
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  TFHistory.add('Download', filename);
}

// Prefill from clipboard helper
document.addEventListener('DOMContentLoaded', () => {
  const clip = sessionStorage.getItem('tf-clip');
  if (!clip) return;
  sessionStorage.removeItem('tf-clip');
  const candidates = ['inputText', 'ttsText', 'qrData', 'caseIn', 'clipText'];
  for (const id of candidates) {
    const el = document.getElementById(id);
    if (el) { el.value = clip; break; }
  }
});
