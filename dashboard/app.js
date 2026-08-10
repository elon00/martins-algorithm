/* ============================================================
   Martin's Algorithm — Dashboard JavaScript
   ============================================================ */

const API = "http://localhost:8000";

// ─── Feature values store ────────────────────────────────────
const features = {
  market_activity:    0.50,
  liquidity:          0.50,
  onchain_activity:   0.50,
  developer_activity: 0.50,
  recovery_evidence:  0.50,
  ownership_evidence: 0.50,
  volume:             0.50,
  project_health:     0.50,
  risk:               0.20,
  confidence:         0.80,
};

// ─── Nav: show/hide sections ─────────────────────────────────
function showSection(name) {
  ['dashboard','scanner','optimizer','policy'].forEach(s => {
    document.getElementById(`section-${s}`)?.classList.add('hidden');
    document.getElementById(`btn-${s}`)?.classList.remove('active');
  });
  // Dashboard shows hero + score tool + architecture
  if (name === 'dashboard') {
    document.getElementById('section-dashboard').classList.remove('hidden');
    document.getElementById('section-score-tool').classList.remove('hidden');
    document.getElementById('section-architecture').classList.remove('hidden');
  } else {
    document.getElementById('section-dashboard').classList.add('hidden');
    document.getElementById('section-score-tool').classList.add('hidden');
    document.getElementById('section-architecture').classList.add('hidden');
    document.getElementById(`section-${name}`).classList.remove('hidden');
  }
  document.getElementById(`btn-${name}`)?.classList.add('active');
}

// ─── API Health ───────────────────────────────────────────────
async function checkHealth() {
  const dot  = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  try {
    const res = await fetch(`${API}/health`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) {
      const d = await res.json();
      dot.className  = 'status-dot online';
      text.textContent = `API Online · v${d.version}`;
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch {
    dot.className  = 'status-dot offline';
    text.textContent = 'API Offline — run uvicorn martin_api.main:app';
  }
}

// ─── Slider update ───────────────────────────────────────────
function updateSlider(input, key) {
  const val = parseFloat(input.value);
  features[key] = val;
  const label = input.parentElement.querySelector('.slider-val');
  if (label) label.textContent = val.toFixed(2);
}

// ─── Score an asset ──────────────────────────────────────────
async function scoreAsset() {
  const assetId = document.getElementById('inp-asset-id').value.trim() || 'demo:asset';
  const btn = document.getElementById('btn-score');
  const resultEl = document.getElementById('score-result');

  btn.disabled = true;
  btn.textContent = 'Computing...';

  const featurePayload = {};
  FEATURE_KEYS.forEach(k => { featurePayload[k] = features[k] ?? 0; });

  const payload = {
    asset_id: assetId,
    features: featurePayload,
    risk: features.risk ?? 0.2,
    confidence: features.confidence ?? 0.8,
  };

  try {
    // Score
    const [scoreRes, classRes] = await Promise.all([
      apiFetch('/score', payload),
      apiFetch('/classify', payload),
    ]);

    const score = scoreRes.martin_score;
    const pRec  = scoreRes.recovery_probability;
    const cls   = classRes;

    const scoreClass = score >= 0.65 ? 'high' : score >= 0.35 ? 'medium' : 'low';

    resultEl.innerHTML = `
      <div class="result-card">
        <div class="score-gauge">
          <div class="score-big ${scoreClass}">${(score*100).toFixed(1)}</div>
          <div class="score-label">Martin Score (out of 100)</div>
        </div>
        <div class="result-rows">
          <div class="result-row">
            <span class="result-row-label">Status</span>
            <span class="status-badge status-${cls.status}">${cls.status}</span>
          </div>
          <div class="result-row">
            <span class="result-row-label">Recovery Probability</span>
            <span class="result-row-val">${(pRec*100).toFixed(1)}%</span>
          </div>
          <div class="result-row">
            <span class="result-row-label">Asset ID</span>
            <span class="result-row-val" style="font-size:11px">${assetId}</span>
          </div>
          <div class="result-row" style="flex-direction:column;align-items:flex-start;gap:6px">
            <span class="result-row-label">Explanation</span>
            <span style="font-size:13px;color:var(--text2);line-height:1.5">${cls.explanation}</span>
          </div>
        </div>
      </div>
    `;

    // Update stats
    updateStats(score, pRec, cls.status);

  } catch (err) {
    resultEl.innerHTML = `
      <div class="result-empty">
        <div class="result-empty-icon">⚠️</div>
        <p style="color:var(--red)">API not available. Start the server:<br/>
        <code style="font-size:12px;color:var(--text2)">uvicorn martin_api.main:app --reload</code></p>
        <p style="font-size:12px;color:var(--text3);margin-top:12px">Local score: <strong>${localScore(payload).toFixed(3)}</strong></p>
      </div>
    `;
  }

  btn.disabled = false;
  btn.textContent = 'Compute Score';
}

// ─── Local (offline) score calculation ──────────────────────
function localScore(payload) {
  const w = {
    market_activity: 0.12, liquidity: 0.12, volume: 0.08,
    onchain_activity: 0.15, developer_activity: 0.10,
    exchange_activity: 0.08, project_health: 0.10,
    recovery_evidence: 0.15, ownership_evidence: 0.10,
  };
  const f = payload.features;
  let S = 0;
  Object.entries(w).forEach(([k,v]) => { S += v * (f[k] || 0); });

  const rec = f.recovery_evidence || 0;
  const own = f.ownership_evidence || 0;
  const logit = 2*rec + 1.5*own - 2*payload.risk;
  const pRec = 1 / (1 + Math.exp(-logit));

  const raw = 0.60*S + 0.25*pRec + 0.15*(payload.confidence||0) - 0.50*payload.risk;
  return Math.max(0, Math.min(1, raw));
}

// ─── Stats update ────────────────────────────────────────────
let statsHistory = [];
function updateStats(score, pRec, status) {
  statsHistory.push({ score, pRec, status });
  document.getElementById('stat-scanned').textContent = statsHistory.length;
  const rec = statsHistory.filter(s => s.status === 'RECOVERABLE').length;
  const dor = statsHistory.filter(s => ['DORMANT','DEAD','MIGRATED'].includes(s.status)).length;
  document.getElementById('stat-recoverable').textContent = rec;
  document.getElementById('stat-dormant').textContent = dor;
  const avg = statsHistory.reduce((a,s) => a+s.score, 0) / statsHistory.length;
  document.getElementById('stat-score').textContent = (avg*100).toFixed(1);
}

// ─── Live scanner ────────────────────────────────────────────
async function runScan() {
  const btn  = document.getElementById('btn-scan');
  const text = document.getElementById('scan-btn-text');
  const list = document.getElementById('scan-results');

  btn.disabled = true;
  text.textContent = '⏳ Scanning...';
  list.innerHTML = '<div style="text-align:center;padding:40px"><div class="spinner"></div><p style="color:var(--text2)">Scanning CoinMarketCap...</p></div>';

  const payload = {
    pages:               parseInt(document.getElementById('scan-pages').value),
    page_size:           parseInt(document.getElementById('scan-page-size').value),
    top_k_opportunities: parseInt(document.getElementById('scan-top-k').value),
  };

  try {
    const result = await apiFetch('/scan', payload);
    renderOpportunities(list, result.opportunities, result);
  } catch (err) {
    list.innerHTML = `
      <div style="text-align:center;padding:40px;color:var(--text2)">
        <p>⚠️ Could not connect to the API.<br/>
        Make sure the server is running and CMC_API_KEY is set in .env</p>
        <p style="font-size:12px;margin-top:12px;color:var(--text3)">${err.message}</p>
      </div>
    `;
  }

  btn.disabled = false;
  text.textContent = '▶ Start Scan';
}

function renderOpportunities(container, opportunities, meta) {
  if (!opportunities || opportunities.length === 0) {
    container.innerHTML = '<p style="color:var(--text2);text-align:center;padding:32px">No opportunities found. Try scanning more pages or check your CMC_API_KEY.</p>';
    return;
  }

  let html = '';
  if (meta) {
    html += `<div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:20px;font-size:13px;color:var(--text2)">
      <span>📊 Scanned: <strong style="color:var(--text)">${meta.total_scanned}</strong></span>
      <span>🎯 Opportunities: <strong style="color:var(--green)">${opportunities.length}</strong></span>
      ${meta.errors?.length ? `<span style="color:var(--red)">⚠️ Errors: ${meta.errors.length}</span>` : ''}
    </div>`;
  }

  opportunities.forEach(opp => {
    const scoreClass = opp.martin_score >= 0.65 ? 'high' : opp.martin_score >= 0.35 ? 'medium' : 'low';
    const scoreColor = opp.martin_score >= 0.65 ? 'var(--green)' : opp.martin_score >= 0.35 ? 'var(--yellow)' : 'var(--red)';
    html += `
      <div class="opportunity-card">
        <div class="opp-score" style="color:${scoreColor}">${(opp.martin_score*100).toFixed(0)}</div>
        <div class="opp-body">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
            <span class="opp-id">${opp.asset_id}</span>
            <span class="status-badge status-${opp.status}">${opp.status}</span>
          </div>
          <div class="opp-explain">${opp.explanation}</div>
          <div style="margin-top:8px;font-size:12px;color:var(--text3);font-family:'JetBrains Mono',monospace">
            P(recovery) = ${(opp.recovery_probability*100).toFixed(1)}%
          </div>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

// ─── Optimizer ───────────────────────────────────────────────
async function runOptimizer() {
  const resultEl = document.getElementById('opt-result');
  resultEl.innerHTML = '<div class="spinner"></div><p style="color:var(--text2);text-align:center">Optimizing...</p>';

  let assets;
  try {
    assets = JSON.parse(document.getElementById('opt-assets').value);
  } catch {
    resultEl.innerHTML = '<div class="result-empty"><div class="result-empty-icon">❌</div><p style="color:var(--red)">Invalid JSON in assets field.</p></div>';
    return;
  }

  const payload = {
    assets,
    k:       parseInt(document.getElementById('opt-k').value),
    penalty: parseFloat(document.getElementById('opt-penalty').value),
  };

  try {
    const result = await apiFetch('/optimize/classical', payload);
    resultEl.innerHTML = `
      <div style="width:100%;display:flex;flex-direction:column;gap:16px">
        <div style="text-align:center">
          <div style="font-size:13px;color:var(--text2);margin-bottom:6px">Solver: <code style="color:var(--accent2)">${result.solver}</code></div>
          <div style="font-size:13px;color:var(--text2)">Objective: <code style="color:var(--accent2)">${result.objective.toFixed(4)}</code></div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--text2);margin-bottom:10px;text-transform:uppercase;letter-spacing:0.06em">Selected Assets (k=${result.k})</div>
          ${result.selected_asset_ids.map(id => `
            <div class="result-row" style="margin-bottom:8px">
              <span class="result-row-val" style="font-size:13px">✅ ${id}</span>
            </div>
          `).join('')}
        </div>
        <div style="font-size:12px;color:var(--text3)">
          Candidates: ${result.n_candidates} · QUBO penalty λ=${payload.penalty}
        </div>
      </div>
    `;
  } catch (err) {
    resultEl.innerHTML = `<div class="result-empty"><div class="result-empty-icon">⚠️</div><p style="color:var(--red)">${err.message}</p></div>`;
  }
}

// ─── Policy check ────────────────────────────────────────────
async function checkPolicy() {
  const resultEl = document.getElementById('policy-result');
  resultEl.innerHTML = '<div class="spinner"></div><p style="color:var(--text2);text-align:center">Checking policy...</p>';

  const payload = {
    action:        document.getElementById('pol-action').value,
    risk_level:    document.getElementById('pol-risk').value,
    value:         parseFloat(document.getElementById('pol-value').value) || 0,
    user_approved: document.getElementById('pol-approved').checked,
  };

  try {
    const result = await apiFetch('/policy/check', payload);
    const icon    = result.approved ? '✅' : '⛔';
    const decText = result.approved ? 'APPROVED' : 'DENIED';
    const decCls  = result.approved ? 'yes' : 'no';

    resultEl.innerHTML = `
      <div class="policy-approved">
        <div class="policy-icon">${icon}</div>
        <div class="policy-decision ${decCls}">${decText}</div>
        <div class="policy-reason">${result.reason}</div>
        <div style="display:flex;gap:16px;font-size:12px;color:var(--text3);margin-top:8px">
          <span>Risk: <strong style="color:var(--text2)">${result.risk_level}</strong></span>
          <span>Value: <strong style="color:var(--text2)">$${payload.value.toFixed(2)}</strong></span>
        </div>
      </div>
    `;
  } catch (err) {
    resultEl.innerHTML = `<div class="result-empty"><div class="result-empty-icon">⚠️</div><p style="color:var(--red)">${err.message}</p></div>`;
  }
}

// ─── API helper ──────────────────────────────────────────────
async function apiFetch(path, body) {
  const res = await fetch(`${API}${path}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
    signal:  AbortSignal.timeout(30000),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

// ─── Feature keys ────────────────────────────────────────────
const FEATURE_KEYS = [
  'market_activity','liquidity','volume','onchain_activity',
  'developer_activity','exchange_activity','project_health',
  'recovery_evidence','ownership_evidence',
];

// ─── Init ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  setInterval(checkHealth, 30000);

  // Show initial dashboard sections
  document.getElementById('section-score-tool').classList.remove('hidden');
  document.getElementById('section-architecture').classList.remove('hidden');
});
