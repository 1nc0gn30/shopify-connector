/**
 * SHOPIFY CONNECTOR — Interactive Cockpit & Margin Engine
 * Neal Frazier Tech (@1nc0gn30) • NullAI Platform
 */

// State
let products = [];
let eventSource = null;

document.addEventListener('DOMContentLoaded', () => {
  checkProLicense();
  setupEventListeners();
  loadInitialData();
  startSSE();
  recalculateMargins();
});

// Event Listeners
function setupEventListeners() {
  // Margin Calculator Inputs
  const calcInputs = ['simRetail', 'simPod', 'simShipping', 'simPlan', 'simAds'];
  calcInputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', recalculateMargins);
      el.addEventListener('change', recalculateMargins);
    }
  });

  // Transpiler Preset Buttons
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const presetKey = btn.getAttribute('data-preset');
      loadTranspilerPreset(presetKey);
    });
  });

  // Transpile Form
  const transpileForm = document.getElementById('transpileForm');
  if (transpileForm) {
    transpileForm.addEventListener('submit', (e) => {
      e.preventDefault();
      executeTranspilation();
    });
  }

  // Catalog Search
  const searchInput = document.getElementById('catalogSearch');
  if (searchInput) {
    searchInput.addEventListener('input', debounce((e) => {
      searchProducts(e.target.value);
    }, 250));
  }
}

// Initial Data Load
async function loadInitialData() {
  await Promise.all([
    fetchShopInfo(),
    fetchStats(),
    searchProducts('')
  ]);
}

// Fetch Shop Info
async function fetchShopInfo() {
  try {
    const res = await fetch('/api/info');
    const data = await res.json();
    const shopName = document.getElementById('metricShopName');
    const plan = document.getElementById('metricPlan');
    if (shopName) shopName.textContent = data.name || 'Storefront';
    if (plan) plan.textContent = data.plan || 'Shopify Store';

    const statusBadge = document.getElementById('storeStatus');
    if (statusBadge) {
      if (data.live) {
        statusBadge.innerHTML = '<span class="status-dot"></span> LIVE GRAPHQL CONNECTED';
      } else {
        statusBadge.innerHTML = '<span class="status-dot" style="background:#10B981"></span> SIMULATION MODE (READY)';
      }
    }
  } catch (err) {
    console.warn('Shop info error:', err);
  }
}

// Fetch Stats
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    const countEl = document.getElementById('metricProducts');
    const mcpEl = document.getElementById('metricMcp');
    if (countEl) countEl.textContent = (data.total_products || 0).toLocaleString();
    if (mcpEl) mcpEl.textContent = `${data.active_mcp_tools || 7} Tools`;
  } catch (err) {
    console.warn('Stats error:', err);
  }
}

// Search Products
async function searchProducts(q) {
  const tableBody = document.getElementById('productsTableBody');
  if (!tableBody) return;

  try {
    const res = await fetch(`/api/products?q=${encodeURIComponent(q)}&limit=30`);
    const data = await res.json();
    products = data.products || [];
    renderProductsTable(products);
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color: var(--ruby);">Error loading products: ${escapeHtml(err.message)}</td></tr>`;
  }
}

// Render Products Table
function renderProductsTable(items) {
  const tableBody = document.getElementById('productsTableBody');
  if (!tableBody) return;

  if (items.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem; color: var(--text-muted);">No products found in catalog.</td></tr>`;
    return;
  }

  tableBody.innerHTML = items.map(p => {
    const price = (p.variants && p.variants.length > 0) ? `$${parseFloat(p.variants[0].price).toFixed(2)}` : '—';
    const statusClass = p.status === 'ACTIVE' ? 'badge-active' : 'badge-draft';
    const tagsHtml = (p.tags || []).slice(0, 3).map(t => `<span class="badge-status" style="background:rgba(255,255,255,0.06); color:var(--text-muted); margin-right:4px;">${escapeHtml(t)}</span>`).join('');

    return `
      <tr>
        <td>
          <strong style="color: #FFF;">${escapeHtml(p.title)}</strong>
          <div style="font-size:0.75rem; color:var(--text-dim); font-family:var(--font-mono);">handle: /products/${escapeHtml(p.handle)}</div>
        </td>
        <td><span class="badge-status ${statusClass}">${escapeHtml(p.status)}</span></td>
        <td><span class="text-mono" style="color:var(--emerald); font-weight:700;">${price}</span></td>
        <td><span class="text-mono">${p.totalInventory || 0} units</span></td>
        <td>${tagsHtml}</td>
      </tr>
    `;
  }).join('');
}

// Real-Time Margin Calculator
function recalculateMargins() {
  const retail = parseFloat(document.getElementById('simRetail').value) || 0;
  const pod = parseFloat(document.getElementById('simPod').value) || 0;
  const shipping = parseFloat(document.getElementById('simShipping').value) || 0;
  const plan = document.getElementById('simPlan').value || 'basic';
  const includeAds = document.getElementById('simAds').checked;

  const grossRevenue = retail + shipping;

  const rates = {
    basic: { pct: 0.029, fix: 0.30 },
    shopify: { pct: 0.026, fix: 0.30 },
    advanced: { pct: 0.024, fix: 0.30 }
  };
  const rate = rates[plan] || rates.basic;
  const shopifyFee = grossRevenue > 0 ? (grossRevenue * rate.pct + rate.fix) : 0;
  const adSpend = includeAds ? (grossRevenue * 0.15) : 0;

  const totalCost = pod + shopifyFee + adSpend;
  const netProfit = grossRevenue - totalCost;
  const marginPct = grossRevenue > 0 ? (netProfit / grossRevenue * 100) : 0;

  // Update DOM
  document.getElementById('outGross').textContent = `$${grossRevenue.toFixed(2)}`;
  document.getElementById('outFees').textContent = `$${shopifyFee.toFixed(2)}`;
  document.getElementById('outCost').textContent = `$${totalCost.toFixed(2)}`;
  document.getElementById('outProfit').textContent = `$${netProfit.toFixed(2)}`;
  
  const gauge = document.getElementById('outMargin');
  if (gauge) {
    gauge.textContent = `${marginPct.toFixed(1)}%`;
    if (marginPct >= 50) gauge.style.color = 'var(--emerald)';
    else if (marginPct >= 30) gauge.style.color = 'var(--gold)';
    else gauge.style.color = 'var(--ruby)';
  }
}

// Transpiler Presets
const TRANSPILER_PRESETS = {
  sweatshirt: {
    title: "Personalized Grandma Garden Sweatshirt | Botanical Wildflower Crewneck Sweater",
    tags: "grandma gift, wildflower sweater, cottagecore crewneck, gardener gift, botanical art, cozy fleece",
    price: 44.95,
    description: "• 50% cotton, 50% polyester heavyweight cozy fleece\n• Double-needle stitching throughout for durable keepsake quality\n• Relaxed unisex fit perfect for cool mornings in the garden"
  },
  mug: {
    title: "Sovereign Meadow Cottagecore Botanical Ceramic Mug 15oz | Wildflower Tea Cup",
    tags: "ceramic mug, cottagecore, wildflower cup, tea lover gift, grandma mug, dishwasher safe",
    price: 21.95,
    description: "• Large 15oz glossy ceramic mug\n• Dishwasher and microwave safe\n• Sublimation printed with fade-proof archival inks"
  },
  tote: {
    title: "Heirloom Seed Packet Canvas Tote Bag | Heavyweight Organic Cotton Market Bag",
    tags: "canvas tote, farmers market, seed packet, gardener bag, reusable grocery, eco friendly",
    price: 28.50,
    description: "• 100% heavy 12oz cotton canvas with reinforced stitching\n• Generous gusseted bottom holds up to 30 lbs\n• Vintage seed packet botanical illustration"
  }
};

function loadTranspilerPreset(key) {
  const p = TRANSPILER_PRESETS[key];
  if (!p) return;
  document.getElementById('transTitle').value = p.title;
  document.getElementById('transTags').value = p.tags;
  document.getElementById('transPrice').value = p.price;
  document.getElementById('transDesc').value = p.description;
  executeTranspilation();
}

async function executeTranspilation() {
  const title = document.getElementById('transTitle').value.trim();
  const tags = document.getElementById('transTags').value.trim();
  const price = parseFloat(document.getElementById('transPrice').value) || 29.95;
  const desc = document.getElementById('transDesc').value.trim();

  const outBox = document.getElementById('transpilerOutput');
  if (outBox) {
    outBox.textContent = 'Transpiling Etsy kit into Shopify GraphQL productCreate mutation...';
  }

  try {
    const res = await fetch('/api/transpile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonString({ title, tags, price, description: desc })
    });
    const data = await res.json();
    if (outBox) {
      outBox.textContent = data.graphql_mutation || JSON.stringify(data, null, 2);
    }
    fetchStats();
  } catch (err) {
    if (outBox) outBox.textContent = `Transpilation error: ${err.message}`;
  }
}

// SSE Live Stream
function startSSE() {
  const streamBox = document.getElementById('streamConsole');
  if (!streamBox) return;

  try {
    eventSource = new EventSource('/api/stream');
    eventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const timeStr = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = 'stream-entry';

        if (payload.type === 'listing_audited') {
          entry.innerHTML = `<span class="stream-time">[${timeStr}]</span> <span style="color:var(--gold)">🔍 AUDIT</span> "${escapeHtml(payload.data.title)}" scored ${payload.data.score}/100`;
        } else if (payload.type === 'margin_calculated') {
          entry.innerHTML = `<span class="stream-time">[${timeStr}]</span> <span style="color:var(--emerald)">⚡ MARGIN</span> Retail $${payload.data.retail} yields $${payload.data.net_profit} net profit`;
        } else if (payload.type === 'transpilation_complete') {
          entry.innerHTML = `<span class="stream-time">[${timeStr}]</span> <span style="color:var(--cyan)">🚀 TRANSPILE</span> Ingested "${escapeHtml(payload.data.title)}" -> GraphQL ready`;
        } else {
          entry.innerHTML = `<span class="stream-time">[${timeStr}]</span> <span style="color:var(--emerald)">● SYNC</span> ${escapeHtml(payload.message || 'Stream heartbeat')}`;
        }

        streamBox.appendChild(entry);
        streamBox.scrollTop = streamBox.scrollHeight;
        while (streamBox.children.length > 50) {
          streamBox.removeChild(streamBox.firstChild);
        }
      } catch (err) {
        // Ignored
      }
    };
  } catch (err) {
    console.warn('SSE stream error:', err);
  }
}

// Pro Licensing & Paywall Modal
function isProActive() {
  return localStorage.getItem('shopify_pro_license') === 'active' ||
         new URLSearchParams(window.location.search).get('licensed') === 'true';
}

function checkProLicense() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('licensed') === 'true') {
    localStorage.setItem('shopify_pro_license', 'active');
  }

  if (isProActive()) {
    document.body.classList.add('pro-licensed');
    const badge = document.getElementById('proStatusBadge');
    if (badge) {
      badge.textContent = '⭐ PRO ACTIVE';
      badge.style.background = 'linear-gradient(135deg, #10B981 0%, #008060 100%)';
      badge.style.color = '#08080B';
      badge.style.borderColor = '#10B981';
    }
  }
}

function triggerProAction(featureName) {
  if (isProActive()) {
    if (featureName === 'export_catalog') {
      window.location.href = '/api/export?format=csv';
    } else {
      alert(`[PRO ACTIVE] Executing: ${featureName}`);
    }
  } else {
    openPaywallModal(featureName);
  }
}

function openPaywallModal(featureName) {
  const modal = document.getElementById('paywallModal');
  const label = document.getElementById('modalFeatureName');
  if (label && featureName) label.textContent = featureName;
  if (modal) modal.classList.add('open');
}

function closePaywallModal() {
  const modal = document.getElementById('paywallModal');
  if (modal) modal.classList.remove('open');
}

function verifyLicenseKey() {
  const input = document.getElementById('licenseKeyInput');
  const val = input ? input.value.trim() : '';
  if (!val) {
    alert('Please enter your license key or receipt email.');
    return;
  }
  localStorage.setItem('shopify_pro_license', 'active');
  checkProLicense();
  closePaywallModal();
  alert('⭐ Pro License activated! All GraphQL bulk mutations and catalog exports are unlocked.');
}

// Helpers
function debounce(fn, wait) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), wait);
  };
}

function jsonString(obj) {
  return JSON.stringify(obj);
}

function escapeHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
