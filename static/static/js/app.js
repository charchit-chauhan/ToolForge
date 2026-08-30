/* Tool Forge — shared frontend helpers */

// Mobile nav toggle
document.getElementById('menuToggle')?.addEventListener('click', () => {
  document.getElementById('navLinks')?.classList.toggle('open');
});

// Tool tabs
document.querySelectorAll('.tool-tabs').forEach(tabBar => {
  tabBar.querySelectorAll('.tool-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const panelId = tab.dataset.panel;
      tabBar.querySelectorAll('.tool-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      // Find sibling panels — look in the nearest container
      const container = tabBar.parentElement;
      container.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
      const panel = document.getElementById('panel-' + panelId);
      if (panel) panel.classList.add('active');
    });
  });
});

// Dropzone helpers
document.querySelectorAll('.dropzone').forEach(dz => {
  const inputId = dz.dataset.input;
  const input = document.getElementById(inputId);
  if (!input) return;

  dz.addEventListener('click', () => input.click());

  dz.addEventListener('dragover', e => {
    e.preventDefault();
    dz.classList.add('dragover');
  });
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
    const listId = inputId + 'List';
    let list = document.getElementById(listId);
    // Try common list ids
    if (!list) {
      const parent = dz.parentElement;
      list = parent?.querySelector('.file-list');
    }
    if (list) {
      list.innerHTML = '';
      Array.from(input.files).forEach(f => {
        const li = document.createElement('li');
        li.innerHTML = `<span>📎 ${f.name}</span><span class="text-muted">${(f.size/1024).toFixed(1)} KB</span>`;
        list.appendChild(li);
      });
    }
    // Update dropzone text
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
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
