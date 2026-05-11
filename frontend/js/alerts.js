(function initAlertStream() {
  const list = document.getElementById('alertList');
  let first = true;

  const es = API.alertStream();

  es.onopen = () => {
    document.getElementById('statusDot').classList.add('online');
  };

  es.onerror = () => {
    document.getElementById('statusDot').classList.remove('online');
    document.getElementById('statusDot').classList.add('offline');
  };

  es.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      // SSE heartbeat
      if (msg.type === 'heartbeat') return;

      const data = msg.data || msg;

      if (first) { list.innerHTML = ''; first = false; }

      const card = document.createElement('div');
      card.className = `alert-card${data.severity === 'CRITICAL' ? ' critical' : ''}`;

      card.innerHTML = `
        <div class="alert-meta">
          <span class="badge ${(data.severity || '').toLowerCase()}">${data.severity || ''}</span>
          <span>${data.station_name || ''}</span>
          ${data.deviation_pct ? `<span>偏差 ${data.deviation_pct}%</span>` : ''}
        </div>
        <div class="alert-body">
          ${data.analysis ? `<div class="analysis">${escapeHtml(data.analysis).slice(0, 200)}</div>` : ''}
          ${data.suggestion ? `<div class="suggestion">${escapeHtml(data.suggestion).slice(0, 300)}</div>` : ''}
        </div>
      `;

      list.insertBefore(card, list.firstChild);
      if (list.children.length > 30) list.lastChild.remove();

    } catch (e) {
      console.error('SSE parse error:', e);
    }
  };

  function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }
})();
