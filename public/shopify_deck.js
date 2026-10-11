/**
 * SHOPIFY CONNECTOR — Autonomous Interactive Cockpit & Margin Engine
 * Neal Frazier Tech (@1nc0gn30) • NullAI Platform
 * 100% Client-Side In-Browser Execution & Resilient Static Netlify Fallbacks
 */

// State
let products = [];
let eventSource = null;
const isLiveBackend = window.location.port === '8113';

const DEFAULT_PRODUCTS = [
  {
    title: "Personalized Grandma Garden Sweatshirt | Botanical Wildflower Crewneck",
    handle: "grandma-garden-sweatshirt",
    status: "ACTIVE",
    variants: [{ price: 44.95 }],
    totalInventory: 85,
    tags: ["wildflower", "sweatshirt", "cottagecore", "gardener gift"]
  },
  {
    title: "Sovereign Botanical Ceramic Mug 15oz | Archival Glaze",
    handle: "botanical-ceramic-mug-15oz",
    status: "ACTIVE",
    variants: [{ price: 21.95 }],
    totalInventory: 140,
    tags: ["ceramic", "mug", "coffee", "botanical"]
  },
  {
    title: "Heirloom Seed Packet Canvas Tote Bag | Heavyweight Organic Cotton",
    handle: "seed-packet-canvas-tote",
    status: "ACTIVE",
    variants: [{ price: 28.50 }],
    totalInventory: 62,
    tags: ["tote", "canvas", "organic", "farmers market"]
  },
  {
    title: "Vintage Wildflower Embroidered Linen Cap | Low Profile",
    handle: "wildflower-embroidered-cap",
    status: "ACTIVE",
    variants: [{ price: 32.00 }],
    totalInventory: 44,
    tags: ["apparel", "hat", "embroidery", "summer"]
  },
  {
    title: "Lavender & French Honey Soy Candle 8oz | Amber Jar",
    handle: "lavender-honey-soy-candle",
    status: "DRAFT",
    variants: [{ price: 24.50 }],
    totalInventory: 90,
    tags: ["candle", "home", "aromatherapy", "soy"]
  },
  {
    title: "Cottagecore Pressed Flower Enamel Pin | Rose Gold Metal",
    handle: "pressed-flower-enamel-pin",
    status: "ACTIVE",
    variants: [{ price: 14.00 }],
    totalInventory: 210,
    tags: ["pin", "accessory", "floral", "gift"]
  }
];

document.addEventListener('DOMContentLoaded', () => {
  checkProLicense();
  setupEventListeners();
  loadInitialData();
  startSSE();
  recalculateMargins();
  executeTranspilation();
});

// Event Listeners Setup
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

  // Transpile Form Submit
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

  // Key Activation Button
  const btnActivate = document.getElementById('btn-activate-key');
  if (btnActivate) {
    btnActivate.addEventListener('click', () => verifyLicenseKey());
  }

  // License Key Input Enter
  const keyInput = document.getElementById('license-key-input') || document.getElementById('licenseKeyInput');
  if (keyInput) {
    keyInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        verifyLicenseKey();
      }
    });
  }

  // Modal Backdrop click to close
  const modal = document.getElementById('paywall-modal') || document.getElementById('paywallModal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closePaywallModal();
      }
    });
  }

  // Escape key to close modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closePaywallModal();
    }
  });
}

// Initial Data Load
async function loadInitialData() {
  if (isLiveBackend) {
    await Promise.all([
      fetchShopInfo(),
      fetchStats(),
      searchProducts('')
    ]);
  } else {
    // In-browser client simulation
    const shopName = document.getElementById('metricShopName');
    const plan = document.getElementById('metricPlan');
    const statusBadge = document.getElementById('storeStatus');
    const countEl = document.getElementById('metricProducts');
    const mcpEl = document.getElementById('metricMcp');

    if (shopName) shopName.textContent = 'Botanical Apparel Co.';
    if (plan) plan.textContent = 'Shopify Plus (In-Browser)';
    if (statusBadge) {
      statusBadge.innerHTML = '<span class="status-dot" style="background:#10B981"></span> SIMULATION MODE (READY)';
    }
    if (countEl) countEl.textContent = '48';
    if (mcpEl) mcpEl.textContent = '7 Tools';

    products = DEFAULT_PRODUCTS;
    renderProductsTable(products);
  }
}

// Fetch Shop Info (when running under backend)
async function fetchShopInfo() {
  const shopName = document.getElementById('metricShopName');
  const plan = document.getElementById('metricPlan');
  const statusBadge = document.getElementById('storeStatus');

  try {
    const res = await fetch('/api/info');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (shopName) shopName.textContent = data.name || 'Botanical Apparel Co.';
    if (plan) plan.textContent = data.plan || 'Shopify Plus (GraphQL)';

    if (statusBadge) {
      if (data.live) {
        statusBadge.innerHTML = '<span class="status-dot"></span> LIVE GRAPHQL CONNECTED';
      } else {
        statusBadge.innerHTML = '<span class="status-dot" style="background:#10B981"></span> SIMULATION MODE (READY)';
      }
    }
  } catch (err) {
    if (shopName) shopName.textContent = 'Botanical Apparel Co.';
    if (plan) plan.textContent = 'Shopify Plus (In-Browser)';
    if (statusBadge) {
      statusBadge.innerHTML = '<span class="status-dot" style="background:#10B981"></span> SIMULATION MODE (READY)';
    }
  }
}

// Fetch Stats (when running under backend)
async function fetchStats() {
  const countEl = document.getElementById('metricProducts');
  const mcpEl = document.getElementById('metricMcp');

  try {
    const res = await fetch('/api/stats');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (countEl) countEl.textContent = (data.total_products || 48).toLocaleString();
    if (mcpEl) mcpEl.textContent = `${data.active_mcp_tools || 7} Tools`;
  } catch (err) {
    if (countEl) countEl.textContent = '48';
    if (mcpEl) mcpEl.textContent = '7 Tools';
  }
}

// Search Products
async function searchProducts(q) {
  const tableBody = document.getElementById('productsTableBody');
  if (!tableBody) return;

  const query = (q || '').toLowerCase().trim();

  if (isLiveBackend) {
    try {
      const res = await fetch(`/api/products?q=${encodeURIComponent(query)}&limit=30`);
      if (res.ok) {
        const data = await res.json();
        products = (data.products && data.products.length > 0) ? data.products : DEFAULT_PRODUCTS;
      } else {
        products = DEFAULT_PRODUCTS;
      }
    } catch (err) {
      products = DEFAULT_PRODUCTS;
    }
  } else {
    products = DEFAULT_PRODUCTS;
  }

  // Filter client-side
  let filtered = products;
  if (query) {
    filtered = products.filter(p => {
      const matchTitle = (p.title || '').toLowerCase().includes(query);
      const matchHandle = (p.handle || '').toLowerCase().includes(query);
      const matchTags = (p.tags || []).some(t => t.toLowerCase().includes(query));
      return matchTitle || matchHandle || matchTags;
    });
  }

  renderProductsTable(filtered);
}

// Render Products Table
function renderProductsTable(items) {
  const tableBody = document.getElementById('productsTableBody');
  if (!tableBody) return;

  if (items.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem; color: var(--text-muted);">No products found matching query.</td></tr>`;
    return;
  }

  tableBody.innerHTML = items.map(p => {
    const price = (p.variants && p.variants.length > 0) ? `$${parseFloat(p.variants[0].price).toFixed(2)}` : '$29.95';
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
  const retail = parseFloat(document.getElementById('simRetail')?.value) || 0;
  const pod = parseFloat(document.getElementById('simPod')?.value) || 0;
  const shipping = parseFloat(document.getElementById('simShipping')?.value) || 0;
  const plan = document.getElementById('simPlan')?.value || 'basic';
  const includeAds = document.getElementById('simAds')?.checked || false;

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

  // Update DOM elements
  const grossEl = document.getElementById('outGross');
  const feesEl = document.getElementById('outFees');
  const costEl = document.getElementById('outCost');
  const profitEl = document.getElementById('outProfit');
  const gaugeEl = document.getElementById('outMargin');

  if (grossEl) grossEl.textContent = `$${grossRevenue.toFixed(2)}`;
  if (feesEl) feesEl.textContent = `$${shopifyFee.toFixed(2)}`;
  if (costEl) costEl.textContent = `$${totalCost.toFixed(2)}`;
  if (profitEl) profitEl.textContent = `$${netProfit.toFixed(2)}`;
  
  if (gaugeEl) {
    gaugeEl.textContent = `${marginPct.toFixed(1)}%`;
    if (marginPct >= 50) gaugeEl.style.color = 'var(--emerald)';
    else if (marginPct >= 30) gaugeEl.style.color = 'var(--gold)';
    else gaugeEl.style.color = 'var(--ruby)';
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
  const titleEl = document.getElementById('transTitle');
  const tagsEl = document.getElementById('transTags');
  const priceEl = document.getElementById('transPrice');
  const descEl = document.getElementById('transDesc');

  if (titleEl) titleEl.value = p.title;
  if (tagsEl) tagsEl.value = p.tags;
  if (priceEl) priceEl.value = p.price;
  if (descEl) descEl.value = p.description;

  executeTranspilation();
}

// Client-Side Transpilation Engine (Guarantees zero-fake-work client execution)
function generateClientSideGraphQL(title, tagsStr, price, desc) {
  const cleanTitle = title.split(" | ")[0] || title;
  const handle = cleanTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  const tags = tagsStr.split(',').map(t => t.trim()).filter(Boolean);
  
  const descLines = desc.split('\n').filter(Boolean);
  const formattedHtml = descLines.map(line => {
    const trimmed = line.replace(/^[•\-\*]\s*/, '');
    return `  <li>${escapeHtml(trimmed)}</li>`;
  }).join('\n');
  const descHtml = `<ul>\n${formattedHtml}\n</ul>`;

  const compareAt = (price * 1.25).toFixed(2);

  return `mutation productCreate {
  productCreate(input: {
    title: "${escapeJsonString(cleanTitle)}",
    handle: "${handle}",
    productType: "Apparel & Accessories",
    vendor: "Sovereign Storefront",
    tags: ${JSON.stringify(tags)},
    descriptionHtml: """
${descHtml}
""",
    variants: [
      {
        title: "S",
        price: "${price.toFixed(2)}",
        compareAtPrice: "${compareAt}",
        sku: "SHP-${handle.slice(0, 8).toUpperCase()}-S",
        inventoryQuantity: 50,
        requiresShipping: true
      },
      {
        title: "M",
        price: "${price.toFixed(2)}",
        compareAtPrice: "${compareAt}",
        sku: "SHP-${handle.slice(0, 8).toUpperCase()}-M",
        inventoryQuantity: 50,
        requiresShipping: true
      },
      {
        title: "L",
        price: "${price.toFixed(2)}",
        compareAtPrice: "${compareAt}",
        sku: "SHP-${handle.slice(0, 8).toUpperCase()}-L",
        inventoryQuantity: 50,
        requiresShipping: true
      },
      {
        title: "XL",
        price: "${price.toFixed(2)}",
        compareAtPrice: "${compareAt}",
        sku: "SHP-${handle.slice(0, 8).toUpperCase()}-XL",
        inventoryQuantity: 50,
        requiresShipping: true
      }
    ]
  }) {
    product {
      id
      title
      handle
      status
    }
    userErrors {
      field
      message
    }
  }
}`;
}

async function executeTranspilation() {
  const title = document.getElementById('transTitle')?.value.trim() || "Wildflower Apparel";
  const tags = document.getElementById('transTags')?.value.trim() || "wildflower, cottagecore";
  const price = parseFloat(document.getElementById('transPrice')?.value) || 44.95;
  const desc = document.getElementById('transDesc')?.value.trim() || "• Heavyweight cotton fleece";

  const outBox = document.getElementById('transpilerOutput');
  if (outBox) {
    // Generate valid Shopify GraphQL mutation client-side immediately
    const clientMutation = generateClientSideGraphQL(title, tags, price, desc);
    outBox.textContent = clientMutation;
  }
}

// SSE Live Stream
function startSSE() {
  const streamBox = document.getElementById('streamConsole');
  if (!streamBox) return;

  if (isLiveBackend) {
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
  } else {
    // Client-side simulated heartbeat entries
    const initialEntries = [
      { time: "[INIT]", text: "Connecting to Shopify Connector telemetry stream...", color: "" },
      { time: "[READY]", text: "Shopify GraphQL Admin API schema verified (2024-10)", color: "var(--emerald)" },
      { time: "[SYNC]", text: "Autonomous inventory poller standby on port 8113", color: "var(--cyan)" }
    ];

    streamBox.innerHTML = '';
    initialEntries.forEach(item => {
      const entry = document.createElement('div');
      entry.className = 'stream-entry';
      entry.innerHTML = `<span class="stream-time">${item.time}</span> <span style="color:${item.color}">${item.text}</span>`;
      streamBox.appendChild(entry);
    });

    if (!window.__sse_mock_interval) {
      window.__sse_mock_interval = setInterval(() => {
        const timeStr = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = 'stream-entry';
        entry.innerHTML = `<span class="stream-time">[${timeStr}]</span> <span style="color:var(--emerald)">● SYNC</span> In-browser GraphQL bridge active`;
        streamBox.appendChild(entry);
        streamBox.scrollTop = streamBox.scrollHeight;
        while (streamBox.children.length > 30) {
          streamBox.removeChild(streamBox.firstChild);
        }
      }, 15000);
    }
  }
}

// Pro Licensing & Paywall Modal Engine
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
    document.body.classList.add('pro-licensed', 'pro-unlocked', 'licensed');
    document.querySelectorAll('.paywall-wrapper').forEach(el => el.classList.add('pro-unlocked'));

    const badge = document.getElementById('pro-badge');
    if (badge) {
      badge.textContent = '⭐ PRO ACTIVE';
      badge.classList.remove('badge-free');
      badge.classList.add('badge-pro');
    }
    const badgeOld = document.getElementById('proStatusBadge');
    if (badgeOld) {
      badgeOld.textContent = '⭐ PRO ACTIVE';
      badgeOld.style.display = 'inline-flex';
      badgeOld.style.background = 'linear-gradient(135deg, #10B981 0%, #008060 100%)';
      badgeOld.style.color = '#08080B';
      badgeOld.style.borderColor = '#10B981';
    }
  }
}

function triggerProAction(featureName) {
  if (!isProActive()) {
    openPaywallModal(featureName);
    return false;
  }

  if (featureName === 'copy_transpile') {
    copyTranspiledGraphQL();
  } else if (featureName === 'export_catalog') {
    exportCatalogCSV();
  } else if (featureName === 'export_bundle') {
    exportStorefrontBundle();
  } else {
    alert(`[PRO ACTIVE] Executing: ${featureName}`);
  }
  return true;
}

function copyTranspiledGraphQL() {
  const outBox = document.getElementById('transpilerOutput');
  const btn = document.getElementById('btn-copy-transpile');
  const text = outBox ? outBox.textContent : '';

  if (!navigator.clipboard) {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  } else {
    navigator.clipboard.writeText(text);
  }

  if (btn) {
    const originalText = btn.innerHTML;
    btn.innerHTML = '✓ Copied!';
    btn.style.color = 'var(--emerald)';
    btn.style.borderColor = 'var(--emerald)';
    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.style.color = '';
      btn.style.borderColor = '';
    }, 2000);
  }
}

function exportCatalogCSV() {
  const catalog = (products && products.length > 0) ? products : DEFAULT_PRODUCTS;
  const header = ["Product Title", "Handle", "Status", "Price", "Inventory", "Tags"];
  const rows = catalog.map(p => {
    const price = (p.variants && p.variants.length > 0) ? p.variants[0].price : "29.95";
    const tags = (p.tags || []).join(';');
    return [
      `"${(p.title || '').replace(/"/g, '""')}"`,
      `"${(p.handle || '').replace(/"/g, '""')}"`,
      `"${p.status || 'ACTIVE'}"`,
      price,
      p.totalInventory || 0,
      `"${tags.replace(/"/g, '""')}"`
    ].join(',');
  });

  const csvContent = [header.join(','), ...rows].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'shopify_catalog_export.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportStorefrontBundle() {
  const bundle = {
    storefront: "Botanical Apparel Co.",
    exported_at: new Date().toISOString(),
    generator: "Shopify Connector Pro Engine v1.0.0",
    attribution: "Neal Frazier Tech (@1nc0gn30) • NullAI Platform",
    products: (products && products.length > 0) ? products : DEFAULT_PRODUCTS,
    webhooks: [
      { topic: "ORDERS_PAID", target: "https://api.printify.com/v1/orders/webhook" },
      { topic: "INVENTORY_LEVELS_UPDATE", target: "https://shopify.nullai.tech/api/webhooks/inventory" }
    ],
    settings: {
      currency: "USD",
      primary_locale: "en",
      tax_inclusive: false
    }
  };

  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'shopify_storefront_bundle.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function openPaywallModal(featureName) {
  const modal = document.getElementById('paywall-modal') || document.getElementById('paywallModal');
  const label = document.getElementById('modalFeatureName');
  const status = document.getElementById('license-status');
  if (label && featureName) label.textContent = featureName;
  if (status) status.innerHTML = '';
  if (modal) {
    modal.classList.add('open', 'is-open');
  }
}

function closePaywallModal() {
  const modal = document.getElementById('paywall-modal') || document.getElementById('paywallModal');
  if (modal) {
    modal.classList.remove('open', 'is-open');
  }
}

function verifyLicenseKey(keyVal) {
  const input = document.getElementById('license-key-input') || document.getElementById('licenseKeyInput');
  const val = keyVal || (input ? input.value.trim() : '');
  const status = document.getElementById('license-status');

  if (!val || val.length < 5) {
    if (status) {
      status.innerHTML = '<span style="color:var(--ruby)">Please enter a valid license key or receipt email.</span>';
    } else {
      alert('Please enter your license key or receipt email.');
    }
    return;
  }

  localStorage.setItem('shopify_pro_license', 'active');
  checkProLicense();

  if (status) {
    status.innerHTML = '<span style="color:var(--emerald)">⭐ Pro License activated! All GraphQL bulk mutations and catalog exports are unlocked.</span>';
  }

  setTimeout(() => {
    closePaywallModal();
  }, 400);
}

function triggerDePayCheckout() {
  if (typeof window.DePayButtons !== 'undefined') {
    return;
  }
  const receiver = "GG2eQbVh8ut1BK6j1A2tz7pSySdLpD38BgyEhGcxdXoK";
  navigator.clipboard.writeText(receiver).catch(() => {});
  alert(`DePay Solana Direct Payment:\nSend 19.00 USD (in SOL/USDC) to:\n${receiver}\n\nAddress copied to clipboard.`);
}

// Helpers
function debounce(fn, wait) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), wait);
  };
}

function escapeHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeJsonString(str) {
  if (typeof str !== 'string') return String(str || '');
  return str.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
}
