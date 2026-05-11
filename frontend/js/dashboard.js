(async function loadDashboard() {
  try {
    // 从告警列表获取统计
    const data = await API.qa('当前未关闭的告警有多少？严重告警呢？');
    // 尝试从 QA 回复中提取数字
    const text = data.answer || '';

    // 用正则粗略提取数字
    const criticalMatch = text.match(/(\d+)\s*条.*?(CRITICAL|严重)/i);
    const totalMatch = text.match(/(\d+)\s*条.*(?:告警|OPEN|未关)/i);

    // 默认用硬编码获取实际统计
    const resp = await fetch(`${API.base}/api/agent/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: '返回一个JSON：列出所有未关闭告警的总数、WARNING数量、CRITICAL数量，只输出JSON格式。' }),
    }).then(r => r.json());

    let total = '--', warning = '--', critical = '--';
    try {
      const obj = JSON.parse((resp.answer || '').replace(/```json|```/g, '').trim());
      total = obj.total || obj['总数'] || '--';
      warning = obj.WARNING || obj['警告'] || '--';
      critical = obj.CRITICAL || obj['严重'] || '--';
    } catch {}

    document.getElementById('statStations').querySelector('.stat-value').textContent = warning;
    document.getElementById('statStations').querySelector('.stat-label').textContent = 'WARNING 告警';
    document.getElementById('statAlerts').querySelector('.stat-value').textContent = total;
    document.getElementById('statAlerts').querySelector('.stat-label').textContent = '未关闭告警';
    document.getElementById('statCritical').querySelector('.stat-value').textContent = critical;
    document.getElementById('statCritical').querySelector('.stat-label').textContent = 'CRITICAL 告警';
  } catch (e) {
    console.error('Dashboard load error:', e);
  }
})();
