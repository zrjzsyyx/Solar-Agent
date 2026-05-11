const API = {
  base: window.location.origin,

  async qa(question) {
    const resp = await fetch(`${this.base}/api/agent/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },

  /** 返回 SSE EventSource，通过 GET + query param 连接 */
  qaStream(question) {
    const q = encodeURIComponent(question);
    return new EventSource(`${this.base}/api/agent/qa/stream?q=${q}`);
  },

  alertStream() {
    return new EventSource(`${this.base}/api/sse/agent-alerts`);
  },

  async health() {
    const resp = await fetch(`${this.base}/api/health`);
    return resp.json();
  },
};
