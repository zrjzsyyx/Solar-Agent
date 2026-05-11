(function initChat() {
  const messages = document.getElementById('messages');
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSend');
  const statusEl = document.getElementById('headerStatus');

  let streamActive = false;

  // ── render ───────────────────────────────────────

  function renderMd(text) {
    if (typeof marked !== 'undefined' && marked.parse) {
      return marked.parse(text);
    }
    return text.replace(/\n/g, '<br>');
  }

  // ── message helpers ──────────────────────────────

  function addMsg(role) {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.innerHTML = '<div class="bubble"></div>';
    messages.appendChild(div);
    scrollDown();
    return div;
  }

  function setBubble(msgEl, html) {
    msgEl.querySelector('.bubble').innerHTML = html;
    scrollDown();
  }

  function removeMsg(el) {
    el.remove();
    scrollDown();
  }

  function addThinking() {
    const div = document.createElement('div');
    div.className = 'msg bot thinking';
    div.innerHTML = '<div class="bubble"><span class="dots"><span></span><span></span><span></span></span> 思考中</div>';
    messages.appendChild(div);
    scrollDown();
    return div;
  }

  function updateThinking(el, text) {
    el.querySelector('.bubble').innerHTML = `<span class="dots"><span></span><span></span><span></span></span> ${text}`;
    scrollDown();
  }

  function setStatus(text, ok) {
    statusEl.textContent = text;
    statusEl.style.color = ok ? 'var(--green)' : 'var(--red)';
  }

  function scrollDown() {
    messages.scrollTop = messages.scrollHeight;
  }

  // ── send ─────────────────────────────────────────

  async function send(question) {
    const q = question || input.value.trim();
    if (!q || streamActive) return;
    input.value = '';

    // Remove welcome if present
    const welcome = messages.querySelector('.welcome');
    if (welcome) welcome.remove();

    addMsg('user').querySelector('.bubble').textContent = q;

    streamActive = true;
    sendBtn.disabled = true;
    input.disabled = true;

    const thinkingDiv = addThinking();
    let answerDiv = null;
    let rawText = '';
    let hasContent = false;

    const es = API.qaStream(q);

    es.addEventListener('thinking', (e) => {
      updateThinking(thinkingDiv, JSON.parse(e.data));
    });

    es.addEventListener('tool', (e) => {
      updateThinking(thinkingDiv, JSON.parse(e.data));
    });

    es.addEventListener('generating', () => {
      thinkingDiv.remove();
      answerDiv = addMsg('bot');
      hasContent = true;
    });

    es.addEventListener('token', (e) => {
      if (!hasContent) {
        thinkingDiv.remove();
        answerDiv = addMsg('bot');
        hasContent = true;
      }
      rawText += JSON.parse(e.data);
      setBubble(answerDiv, renderMd(rawText));
    });

    es.addEventListener('done', (e) => {
      const full = JSON.parse(e.data);
      if (!hasContent) {
        thinkingDiv.remove();
        answerDiv = addMsg('bot');
        hasContent = true;
      }
      rawText = full;
      setBubble(answerDiv, renderMd(full));
      finish();
    });

    es.addEventListener('error', () => {
      thinkingDiv.remove();
      setStatus('出错了', false);
      finish();
    });

    es.onerror = () => {
      if (!hasContent) {
        thinkingDiv.remove();
        addMsg('bot').querySelector('.bubble').textContent = '连接失败，请确认 Agent 服务是否运行';
      }
      finish();
    };

    function finish() {
      es.close();
      streamActive = false;
      sendBtn.disabled = false;
      input.disabled = false;
      input.focus();
    }
  }

  // ── events ────────────────────────────────────────

  sendBtn.addEventListener('click', () => send());

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') send();
  });

  // Welcome hint buttons
  messages.addEventListener('click', (e) => {
    const btn = e.target.closest('.hint-btn');
    if (btn) send(btn.dataset.q);
  });

  // ── health check ──────────────────────────────────

  async function healthCheck() {
    try {
      await API.health();
      setStatus('在线', true);
    } catch {
      setStatus('离线', false);
    }
  }
  healthCheck();
  setInterval(healthCheck, 30000);
})();
