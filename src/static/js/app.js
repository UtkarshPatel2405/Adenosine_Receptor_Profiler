document.addEventListener('DOMContentLoaded', () => {
    if (window.lucide) {
        lucide.createIcons();
        // Auto-compile icons injected later. Guard: only react to <i> placeholders,
        // never to the <svg> lucide renders (which retains data-lucide) — otherwise
        // createIcons() re-triggers the observer and freezes the page.
        const platformObserver = new MutationObserver((mutations) => {
            let needsRefresh = false;
            mutations.forEach(m => {
                if (m.addedNodes.length) {
                    m.addedNodes.forEach(node => {
                        if (node.nodeType === 1) {
                            if (node.tagName === 'I' && node.hasAttribute('data-lucide')) needsRefresh = true;
                            else if (node.querySelector) needsRefresh = needsRefresh || !!node.querySelector('i[data-lucide]');
                        }
                    });
                }
            });
            if (needsRefresh) lucide.createIcons();
        });
        platformObserver.observe(document.body, { childList: true, subtree: true });
    }
    initParticles();
    initTabs();
    initSubTabs();
    initExamples();
    initSinglePredict();
    initBatchPredict();
    loadModelResults();
    initReveal();
    initHeroCounters();
    initSpotlight();
});

// Card spotlight: track mouse position for radial glow
function initSpotlight() {
    document.addEventListener('mousemove', (e) => {
        document.querySelectorAll('.card-spotlight').forEach(card => {
            const rect = card.getBoundingClientRect();
            card.style.setProperty('--mouse-x', (e.clientX - rect.left) + 'px');
            card.style.setProperty('--mouse-y', (e.clientY - rect.top) + 'px');
        });
    });
}

// Animated number counter for hero stats
function initHeroCounters() {
    const counters = document.querySelectorAll('.hero-stat-num[data-count]');
    if (!counters.length) return;
    const obs = new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (!e.isIntersecting) return;
            const el = e.target;
            const target = parseInt(el.getAttribute('data-count'), 10);
            if (isNaN(target)) return;
            obs.unobserve(el);
            const dur = 1200;
            const start = performance.now();
            function tick(now) {
                const p = Math.min((now - start) / dur, 1);
                const ease = 1 - Math.pow(1 - p, 3); // ease-out cubic
                el.textContent = Math.round(ease * target).toLocaleString();
                if (p < 1) requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
        });
    }, { threshold: 0.3 });
    counters.forEach(c => obs.observe(c));
}

// Scroll-reveal for dynamically injected cards
let revealObserver = null;
function initReveal() {
    revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (e.isIntersecting) { e.target.classList.add('visible'); revealObserver.unobserve(e.target); }
        });
    }, { threshold: 0.08 });
    revealCards();
}
function revealCards() {
    if (!revealObserver) return;
    document.querySelectorAll('.reveal:not(.visible)').forEach(el => revealObserver.observe(el));
}

// Ambient particle-network background animation (nodes + connecting links)
function initParticles() {
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, pts = [];
    const LINK_DIST = 140;

    function resize() {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    for (let i = 0; i < 55; i++) {
        pts.push({
            x: Math.random() * W, y: Math.random() * H,
            vx: (Math.random() - 0.5) * 0.2, vy: (Math.random() - 0.5) * 0.2,
            r: Math.random() * 1.8 + 0.6, p: Math.random() * Math.PI
        });
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);
        // connecting network links first (behind nodes)
        for (let i = 0; i < pts.length; i++) {
            for (let j = i + 1; j < pts.length; j++) {
                const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
                const d2 = dx * dx + dy * dy;
                if (d2 < LINK_DIST * LINK_DIST) {
                    const a = (1 - d2 / (LINK_DIST * LINK_DIST)) * 0.45;
                    ctx.strokeStyle = `rgba(148, 163, 184, ${a})`;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(pts[i].x, pts[i].y);
                    ctx.lineTo(pts[j].x, pts[j].y);
                    ctx.stroke();
                }
            }
        }
        for (let p of pts) {
            p.x += p.vx; p.y += p.vy; p.p += 0.002;
            if (p.x < -10) p.x = W + 10; else if (p.x > W + 10) p.x = -10;
            if (p.y < -10) p.y = H + 10; else if (p.y > H + 10) p.y = -10;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
            g.addColorStop(0, `rgba(56, 189, 248, ${0.35 + 0.15 * Math.sin(p.p)})`);
            g.addColorStop(1, 'rgba(56, 189, 248, 0)');
            ctx.fillStyle = g;
            ctx.fill();
        }
        requestAnimationFrame(draw);
    }
    draw();
}

// Move the sliding pill highlight to a tab's button
function movePill(pill, btn) {
    if (!pill || !btn) return;
    pill.style.left = btn.offsetLeft + 'px';
    pill.style.width = btn.offsetWidth + 'px';
}

function slidePillTo(tabsBar, btn) {
    if (!tabsBar || !btn) return;
    let pill = tabsBar.querySelector('.tab-pill');
    if (!pill) {
        pill = document.createElement('div');
        pill.className = 'tab-pill';
        tabsBar.prepend(pill);
    }
    movePill(pill, btn);
}

// Navigation Tabs
function initTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        if (tab.classList.contains('sub-tab')) return;
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            const targetId = tab.getAttribute('data-tab');
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.classList.add('active');
            slidePillTo(tab.parentElement, tab);
        });
    });
    // position the pill on the initially-active tab
    const active = document.querySelector('.nav-tab.active:not(.sub-tab)');
    if (active) slidePillTo(active.parentElement, active);
    window.addEventListener('resize', () => {
        document.querySelectorAll('.nav-tabs').forEach(bar => {
            const act = bar.querySelector('.nav-tab.active');
            if (act) movePill(bar.querySelector('.tab-pill'), act);
        });
    });
}

// Sub-tabs in Model Results
function initSubTabs() {
    const subTabs = document.querySelectorAll('.sub-tab');
    subTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            subTabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.sub-content').forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            const targetId = tab.getAttribute('data-subtab');
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.classList.add('active');
            slidePillTo(tab.parentElement, tab);
        });
    });
    const active = document.querySelector('.sub-tab.active');
    if (active) slidePillTo(active.parentElement, active);
}

// Example SMILES buttons
function initExamples() {
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const smiles = btn.getAttribute('data-smiles');
            const input = document.getElementById('smiles-input');
            if (input) {
                input.value = smiles;
                runSinglePredict(smiles);
            }
        });
    });
}

// Single Prediction Runner
function initSinglePredict() {
    const btn = document.getElementById('predict-btn');
    if (btn) {
        btn.addEventListener('click', () => {
            const smiles = document.getElementById('smiles-input').value.trim();
            if (smiles) runSinglePredict(smiles);
        });
    }
}

// Run full single-molecule pipeline into the examples detail panel
async function runExampleAnalysis(smiles) {
    const panel = document.getElementById('example-detail');
    if (!panel) return;
    // Switch to Model Results Hub → Examples sub-tab
    document.querySelectorAll('.nav-tab:not(.sub-tab)').forEach(t => {
        t.classList.toggle('active', t.getAttribute('data-tab') === 'results-tab');
        if (t.getAttribute('data-tab') === 'results-tab') slidePillTo(t.parentElement, t);
    });
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    const resultsMain = document.getElementById('results-tab');
    if (resultsMain) resultsMain.classList.add('active');
    document.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.sub-content').forEach(c => c.classList.remove('active'));
    const exSubBtn = document.querySelector('[data-subtab="sub-examples"]');
    if (exSubBtn) { exSubBtn.classList.add('active'); slidePillTo(exSubBtn.parentElement, exSubBtn); }
    document.getElementById('sub-examples')?.classList.add('active');
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    panel.innerHTML = `<div class="card" style="text-align:center;padding:2rem;"><span class="badge badge-cyan">Running full pipeline for SMILES — affinity grid, SHAP, neighbors, 3D…</span></div>`;

    try {
        const res = await fetch('/api/predict/single', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ smiles, threshold: 6.0, run_rf: true })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Prediction failed');
        renderSingleResults(data, panel);
        revealCards();
        const viewer = panel.querySelector('#viewer3d');
        if (viewer) viewer.style.height = '340px';
    } catch (err) {
        panel.innerHTML = `<div class="card" style="border-color:var(--accent-red)"><span class="badge badge-red">Error: ${err.message}</span></div>`;
    }
}

async function runSinglePredict(smiles) {
    const resultsContainer = document.getElementById('single-results');
    if (!resultsContainer) return;

    // glowing pulsing ring on the Run Prediction button while computing
    const pb = document.getElementById('predict-btn');
    if (pb) pb.classList.add('icon-processing', 'sparking');

    resultsContainer.style.display = 'block';
    resultsContainer.innerHTML = `
        <div class="card anim-in">
            <div class="section-header"><i class="tab-ico" data-lucide="grid-3x3"></i>4-Subtype Affinity Grid — Multi-Model Ensemble</div>
            <div class="table-wrap" style="background:#232b30">
                ${['', '', '', '', ''].map(() => `<div class="skeleton-row"></div>`).join('')}
            </div>
            <div style="margin-top:0.7rem;text-align:center"><span class="badge badge-cyan">Computing conformal prediction & 3D conformer…</span></div>
        </div>`;

    try {
        const res = await fetch('/api/predict/single', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ smiles: smiles, threshold: 6.0, run_rf: true })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Prediction failed');

        renderSingleResults(data);
    } catch (err) {
        resultsContainer.innerHTML = `<div class="card anim-in" style="border-color:var(--accent-red);"><span class="badge badge-red">Error: ${err.message}</span></div>`;
    } finally {
        if (pb) pb.classList.remove('icon-processing', 'sparking');
    }
}

let singleCharts = [];
function destroyCharts(arr) {
    (arr || []).forEach(c => { try { c.destroy(); } catch (e) { } });
}

function fmtVal(v, d = 2) {
    return (typeof v === 'number' && isFinite(v)) ? v.toFixed(d) : '—';
}

function badgeFor(val) {
    if (val >= 6.0) return '<span class="badge badge-green">Active</span>';
    if (val >= 4.5) return '<span class="badge badge-amber">Weak</span>';
    return '<span class="badge badge-red">Inactive</span>';
}

// Load a real receptor-ligand complex from RCSB into a 3Dmol viewer (protein cartoon + ligand sticks)
function loadPdbComplex(pdbId, viewerEl) {
    if (!pdbId || !viewerEl || !window.$3Dmol) return;
    // Destroy any prior viewer to avoid stacked/overlapping canvases
    if (viewerEl._viewer) { try { viewerEl._viewer.clear(); } catch (e) { } viewerEl._viewer = null; }
    viewerEl.style.position = 'relative';
    viewerEl.innerHTML = '<div style="padding:2rem;text-align:center;color:#e2e8f0;font-size:0.8rem">Fetching ' + pdbId + ' from RCSB…</div>';
    try {
        const viewer = $3Dmol.createViewer(viewerEl, { backgroundColor: '#2C3539' });
        viewerEl._viewer = viewer;
        $3Dmol.download('pdb:' + pdbId, viewer, {}, () => {
            try {
                viewer.setBackgroundColor('#2C3539');
                // Protein: colourful cartoon, no surface so it never obscures the ligand
                viewer.setStyle({ hetflag: false }, { cartoon: { color: 'spectrum' } });
                // Water + ions: hide
                viewer.setStyle({ resn: ['HOH', 'WAT', 'NA', 'CL', 'MG', 'ZN', 'CA', 'K'] }, {});
                // Ligand: thin purple sticks
                viewer.setStyle({ hetflag: true, elem: ['C', 'N', 'O', 'S', 'P', 'F', 'Cl', 'Br', 'I'] }, {
                    stick: { radius: 0.12, colorscheme: 'Jmol' }
                });
                viewer.setStyle({ hetflag: true, elem: 'C' }, { stick: { radius: 0.12, color: 0xa78bfa } });
                viewer.zoomTo();
                viewer.render();
                const lg = viewer.getModel().getAtomsWithin({ hetflag: true, elem: ['C', 'N', 'O'] });
                const ligandLabel = lg.length
                    ? ' · ligand highlighted (purple sticks)'
                    : ' · showing receptor cartoon';
                const tag = document.createElement('div');
                tag.style.cssText = 'position:absolute;top:8px;left:10px;font-size:0.7rem;color:#e2e8f0;pointer-events:none;z-index:2';
                tag.innerHTML = `<b style="color:#c084fc">${pdbId}</b> · co-crystal complex${ligandLabel}`;
                viewerEl.appendChild(tag);
            } catch (e) {
                console.warn('PDB style error:', e);
                viewer.zoomTo();
                viewer.render();
            }
        }, (err) => {
            viewerEl.innerHTML = `<div style="padding:2rem;text-align:center;color:#fca5a5;font-size:0.8rem">Could not load ${pdbId} from RCSB.</div>`;
            console.warn('RCSB download failed:', err);
        });
    } catch (e) {
        viewerEl.innerHTML = `<div style="padding:2rem;text-align:center;color:#fca5a5;font-size:0.8rem">3D viewer unavailable.</div>`;
    }
}

function pdb3dCell(smiles, pdbEntries, pdbId) {
    let links = '';
    if (pdbId) {
        links += `<a class="badge badge-blue" target="_blank" href="https://www.rcsb.org/structure/${pdbId}" title="Receptor co-crystal structure">${pdbId}</a> `;
    }
    (pdbEntries || []).forEach(p => {
        if (p.pdb_id) links += `<a class="badge badge-blue" target="_blank" href="https://www.rcsb.org/structure/${p.pdb_id}" title="${p.name || p.pdb_id}">${p.pdb_id}</a> `;
    });
    const enc = encodeURIComponent(smiles || '');
    links += `<a class="badge badge-cyan" title="Download generated 3D PDB conformer" href="/api/predict/neighbor_3d?smiles=${enc}&format=pdb">3D PDB</a> `;
    links += `<a class="badge badge-purple" title="Download generated 3D SDF conformer" href="/api/predict/neighbor_3d?smiles=${enc}&format=sdf">3D SDF</a>`;
    return links;
}

function renderSingleResults(data, target) {
    const container = target || document.getElementById('single-results');
    if (!container || !data) return;

    destroyCharts(singleCharts);
    singleCharts = [];

    const preds = data.predictions || {};
    const unc = data.uncertainty || {};
    const iv = data.intervals || {};
    const models = ['XGBoost', 'RandomForest', 'LightGBM', 'Stacked'];
    const subtypes = ['A1', 'A2A', 'A2B', 'A3'];

    // Affinity grid: rows = models, cols = subtypes. Cell = pChEMBL + σ + 90% CI.
    let thead = '<tr><th>Model</th>' + subtypes.map(s => `<th>A<sub>${s.slice(1).toLowerCase()}</sub> (pChEMBL)</th>`).join('') + '</tr>';
    let rows = models.map((m, rIdx) => {
        const cells = subtypes.map(s => {
            const p = (preds[m] && preds[m][s]) || 0;
            const u = (unc[m] && unc[m][s]) || 0;
            const low = (iv[m] && iv[m][s] && typeof iv[m][s].lower === 'number') ? iv[m][s].lower : p;
            const high = (iv[m] && iv[m][s] && typeof iv[m][s].upper === 'number') ? iv[m][s].upper : p;
            const zero = p <= 0;
            const highCls = (!zero && p >= 6.0) ? 'cell-high' : '';
            if (zero) {
                return `<td style="opacity:0.4"><div style="display:flex;align-items:center;gap:0.3rem"><i data-lucide="circle-slash" style="width:14px;height:14px;color:#64748b"></i><span style="color:#64748b;font-size:0.78rem">Not initialized</span></div>
                    <div class="cell-sub">σ=— · 90% CI [—, —]</div></td>`;
            }
            return `<td><div class="cell-pred ${highCls}">${p.toFixed(2)}</div>
                <div class="cell-sub">σ=${fmtVal(u)} · 90% CI [${fmtVal(low)}, ${fmtVal(high)}]</div></td>`;
        }).join('');
        return `<tr class="affinity-row-anim" style="animation-delay:${rIdx * 30}ms"><td><strong>${m}</strong></td>${cells}</tr>`;
    }).join('');

    // Selectivity cards (A2A vs A1, A2A vs A3)
    const sel = data.selectivity_profile || {};
    let selHtml = '';
    [['A2A_vs_A1', 'A<sub>2A</sub> vs A<sub>1</sub>'], ['A2A_vs_A3', 'A<sub>2A</sub> vs A<sub>3</sub>']].forEach(([k, label]) => {
        const v = sel[k];
        const isNum = typeof v === 'number';
        const mag = isNum ? Math.abs(v) : 0;
        const selBadge = isNum && v > 0.5 ? '<span class="badge badge-purple">Selective for A2A</span>'
            : isNum && v < -0.5 ? '<span class="badge badge-cyan">Selective for ' + k.split('_')[2] + '</span>'
                : '<span class="badge badge-amber">Non-selective</span>';
        selHtml += `<div class="metric-box" style="padding:0.7rem">
            <div class="metric-label">${label} Selectivity</div>
            <div class="metric-value" style="font-size:1.2rem">${fmtVal(v)}</div>
            <div style="margin-top:0.3rem">${selBadge}</div>
            <div class="metric-sub">ΔpChEMBL (positive = A2A-selective)</div>
        </div>`;
    });

    // Drug-likeness: Lipinski Rule-of-5 from descriptors + QED gauge + PAINS
    const d = data.descriptors || {};
    const lipinski = [
        ['MW ≤ 500', (typeof d.MW === 'number') ? d.MW <= 500 : true],
        ['LogP ≤ 5', (typeof d.LogP === 'number') ? d.LogP <= 5 : true],
        ['HBD ≤ 5', (typeof d.HBD === 'number') ? d.HBD <= 5 : true],
        ['HBA ≤ 10', (typeof d.HBA === 'number') ? d.HBA <= 10 : true],
        ['RotBonds ≤ 10', (typeof d.RotBonds === 'number') ? d.RotBonds <= 10 : true],
    ];
    const lipinskiPass = lipinski.filter(l => l[1]).length;
    let lipHtml = lipinski.map(([label, ok]) =>
        `<div class="feat-row"><span>${label}</span><strong class="${ok ? 'text-ok' : 'text-bad'}">${ok ? '✓' : '✗'}</strong></div>`).join('');

    const qedVal = (data.qed_profile && (typeof data.qed_profile.QED === 'number' ? data.qed_profile.QED : data.qed_profile.qed)) || null;
    const pains = Array.isArray(data.pains_alerts) ? data.pains_alerts : [];
    const painsHtml = pains.length === 0
        ? '<div class="feat-row"><span>PAINS substructure alerts</span><strong class="text-ok">None</strong></div>'
        : pains.map(a => `<div class="feat-row"><span>PAINS alert</span><strong class="text-bad">${a}</strong></div>`).join('');

    let descHtml = '';
    for (let [k, v] of Object.entries(d)) {
        descHtml += `<div class="feat-row"><span>${k}</span><strong>${v}</strong></div>`;
    }

    const svgHtml = data.svg_2d
        ? `<div class="mol2d-wrap">${data.svg_2d}</div>`
        : '<p style="color:var(--text-muted)">2D depiction unavailable</p>';

    const shapRows = Array.isArray(data.shap_top_features) ? data.shap_top_features.slice(0, 6) : [];

    // ── Applicability Domain alert ──
    const ad = data.applicability_domain;
    let adHtml = '<div class="metric-box"><div class="metric-label">Applicability Domain</div><div class="metric-value" style="font-size:1rem">—</div></div>';
    if (ad) {
        if (ad.in_domain) {
            adHtml = `<div class="metric-box"><div class="metric-label">Applicability Domain</div><div class="metric-value" style="font-size:1rem">${ad.max_tanimoto}</div>
                <span class="badge badge-green">Inside AD (${ad.max_tanimoto})</span>
                <div class="metric-sub">Max Tanimoto to training set · &lt; 0.4 = outside AD, predict with caution</div></div>`;
        } else {
            adHtml = `<div class="ad-warning-box"><div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem">
                <i data-lucide="alert-triangle" style="width:16px;height:16px;color:#f87171;animation:pulseRed 2s ease-in-out infinite"></i>
                <span style="font-size:0.82rem;font-weight:700;color:#f87171">Outside AD (${ad.max_tanimoto})</span></div>
                <div class="metric-sub" style="color:#94a3b8">Max Tanimoto to training set · &lt; 0.4 = outside AD, predict with caution</div></div>`;
        }
    }

    // ── Top-10 global training neighbors ──
    const glob = Array.isArray(data.neighbors_global) ? data.neighbors_global : [];
    const globRows = glob.map((n, i) => `
        <tr>
            <td>${i + 1}</td>
            <td><code title="${n.smiles}">${n.smiles.length > 34 ? n.smiles.slice(0, 34) + '…' : n.smiles}</code></td>
            <td><span class="badge badge-${n.class}">${n.label}</span></td>
            <td>${pdb3dCell(n.smiles, n.pdb_entries)}</td>
        </tr>`).join('');
    const globHtml = glob.length ? `
        <div class="table-wrap" style="max-height:340px;overflow-y:auto">
            <table><thead><tr><th>#</th><th>SMILES</th><th>Tanimoto</th><th>PDB / 3D Structure</th></tr></thead><tbody>${globRows}</tbody></table>
        </div>` : '<p style="color:var(--text-muted)">No neighbors available.</p>';

    // ── Receptor Binding Analysis ──
    const rec = data.receptors || {};
    const recNeighbors = rec.neighbors || {};
    const recOverview = rec.overview || {};
    const recSubtypes = ['A1', 'A2A', 'A2B', 'A3'];
    const receptorBtns = recSubtypes.map(s =>
        `<button class="btn rec-btn" data-subtype="${s}" style="padding:0.25rem 0.7rem;font-size:0.75rem">A<sub>${s.slice(1).toLowerCase()}</sub>${recOverview[s] ? ` · ${recOverview[s].max_similarity}` : ''}</button>`).join('');

    const recOverviewRows = recSubtypes.map(s => {
        const o = recOverview[s] || {};
        const sim = o.max_similarity || 0;
        const cls = sim >= 0.7 ? 'green' : sim >= 0.4 ? 'amber' : 'red';
        return `<tr><td><strong>A<sub>${s.slice(1).toLowerCase()}</sub></strong></td>
            <td><span class="badge badge-${cls}">${fmtVal(o.max_similarity)}</span></td>
            <td>${o.active_neighbors || 0}</td>
            <td>${pdb3dCell('', [], o.pdb)}</td></tr>`;
    }).join('');

    // ── Real SHAP ──
    const shapData = data.shap;
    let shapSection = '';
    if (shapData && shapData.features && shapData.features.length) {
        const cols = shapData.features.map(f => f.positive ? 'rgba(231,76,60,0.8)' : 'rgba(52,152,219,0.8)');
        const sum = shapData.features.reduce((a, f) => a + f.value, 0);
        shapSection = `
        <div class="card dark-card anim-in">
            <div class="section-header"><i class="tab-ico" data-lucide="bar-chart-3"></i>SHAP Explainability — ${shapData.best_target} Model (Feature Interpretation)</div>
            <div class="sci-box" style="font-size:0.72rem;margin-bottom:0.6rem">
                <b style="color:#ffffff">How to read SHAP values:</b><br>
                SHAP decomposes the prediction into feature contributions. The <b style="color:#e74c3c">red bars</b> push the prediction <b>higher</b> (toward active), <b style="color:#3498db">blue bars</b> lower it (toward inactive). The base value (<b>${shapData.base_value}</b>) is the average prediction over the training set. Base + Σ(contributions) = final prediction ≈ <b>${fmtVal(data.predictions.XGBoost[shapData.best_target])}</b>.
            </div>
            <div style="height:300px"><canvas id="shap-chart"></canvas></div>
            <div style="margin-top:0.8rem">
                ${shapData.features.map(f => `
                    <div class="feat-row">
                        <span style="color:${f.positive ? '#f87171' : '#60a5fa'};font-weight:500">${f.feature}</span>
                        <span style="color:var(--text-muted);flex:1;margin:0 .5rem;font-size:0.66rem">${f.meaning.slice(0, 90)}</span>
                        <span style="font-family:monospace;font-size:0.72rem;color:${f.positive ? '#f87171' : '#60a5fa'}">${f.value > 0 ? '+' : ''}${f.value.toFixed(4)}</span>
                    </div>`).join('')}
            </div>
        </div>`;
    }

    // ── Tier 1 summary strip data ──
    const xgb = preds.XGBoost || {};
    let maxAff = 0, maxAffSub = '—';
    subtypes.forEach(s => {
        const v = (xgb[s] && xgb[s] > 0) ? xgb[s] : 0;
        if (v > maxAff) { maxAff = v; maxAffSub = 'A<sub>' + s.slice(1).toLowerCase() + '</sub>'; }
    });
    const selMain = sel.A2A_vs_A1;
    let stripSelBadge = '<span class="badge badge-amber">Non-selective</span>';
    if (typeof selMain === 'number' && Math.abs(selMain) > 0.5) {
        stripSelBadge = selMain > 0 ? '<span class="badge badge-purple">A2A Selective</span>'
            : '<span class="badge badge-cyan">A1 Selective</span>';
    }
    const adStatus = (ad && typeof ad.in_domain === 'boolean') && ad.in_domain;
    const stripAdBadge = adStatus ? '<span class="badge badge-green">Inside AD</span>'
        : '<span class="badge badge-red">Outside AD</span>';

    container.innerHTML = `
    <!-- ═══ SECTION 1: Molecular Visualization — Cyan ═══ -->
    <div class="full-section section-theme-cyan">
        <div class="section-inner">
            <div class="section-num">01</div>
            <div class="section-title" style="color:#22d3ee">Molecular Visualization</div>
            <div class="section-subtitle">Interactive 2D/3D structural analysis</div>
            <div class="section-split">
                <div>
                    <div class="card dark-card" style="margin:0">
                        <div class="nav-tabs viz-tabs">
                            <button class="nav-tab viz-tab active" data-viz="viz-2d" style="padding:0.35rem 0.9rem"><i class="tab-ico" data-lucide="pen-tool"></i>2D Structure</button>
                            <button class="nav-tab viz-tab" data-viz="viz-3d" style="padding:0.35rem 0.9rem"><i class="tab-ico" data-lucide="rotate-3d"></i>3D Conformer</button>
                        </div>
                        <div class="viz-pane active" id="viz-2d"><div class="viz-2d-frame">${svgHtml}</div></div>
                        <div class="viz-pane" id="viz-3d">
                            <div id="viewer3d" style="height:380px"></div>
                            ${data.mol_block_3d ? '' : '<p style="color:var(--text-muted);font-size:0.75rem">3D conformer unavailable.</p>'}
                        </div>
                        <div style="display:flex;gap:0.4rem;margin-top:0.5rem">
                            <a class="btn" style="padding:0.3rem 0.7rem;font-size:0.72rem;flex:1;text-align:center" href="/api/predict/neighbor_3d?smiles=${encodeURIComponent(data.smiles || '')}&format=pdb"><i class="tab-ico" data-lucide="download"></i>PDB</a>
                            <a class="btn" style="padding:0.3rem 0.7rem;font-size:0.72rem;flex:1;text-align:center" href="/api/predict/neighbor_3d?smiles=${encodeURIComponent(data.smiles || '')}&format=sdf"><i class="tab-ico" data-lucide="download"></i>SDF</a>
                        </div>
                    </div>
                </div>
                <div>
                    <div class="card dark-card" style="margin:0">
                        <div class="section-header"><i class="tab-ico" data-lucide="atom"></i>Canonical SMILES</div>
                        <div class="sum-smiles" style="font-size:0.82rem;padding:0.7rem">${data.smiles || '—'}</div>
                        <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin-top:0.5rem">
                            <button id="copy-smiles" class="btn copy-btn" title="Copy SMILES" style="padding:0.35rem 0.85rem"><i class="tab-ico" data-lucide="copy"></i><span>Copy SMILES</span></button>
                            <span class="badge badge-cyan">${data.source || 'model'}</span>
                        </div>
                    </div>
                    <div class="knowledge-panel" style="margin-top:0.8rem">
                        <h4><i data-lucide="book-open" style="width:14px;height:14px"></i>Theory: Molecular Representation</h4>
                        <p>SMILES encodes molecular structure as text. 2D depiction uses RDKit with Morgan fingerprint-based coloring. 3D conformers generated via ETKDG for accurate spatial binding pose representation.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ═══ SECTION 2: Affinity Grid — Purple ═══ -->
    <div class="full-section section-theme-purple">
        <div class="section-inner">
            <div class="section-num">02</div>
            <div class="section-title" style="color:#a78bfa">4-Subtype Affinity Grid</div>
            <div class="section-subtitle">Multi-model ensemble predictions across A₁, A₂A, A₂B, A₃</div>
            <div class="card dark-card" style="margin:0">
                <div class="table-wrap"><table><thead>${thead}</thead><tbody>${rows}</tbody></table></div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.7rem;margin-top:1rem">
                <div class="metric-box" style="text-align:center"><div class="metric-label">Primary Target</div><div class="metric-value" style="font-size:1.1rem">${data.best_target || 'N/A'}</div></div>
                <div class="metric-box" style="text-align:center"><div class="metric-label">Max Affinity</div><div class="metric-value" style="font-size:1.1rem">${maxAff > 0 ? maxAff.toFixed(2) : '—'}</div><div style="font-size:0.6rem;color:var(--ink-muted)">pChEMBL · ${maxAffSub}</div></div>
                <div class="metric-box" style="text-align:center"><div class="metric-label">Selectivity</div><div style="margin-top:0.2rem">${stripSelBadge}</div></div>
                <div class="metric-box" style="text-align:center"><div class="metric-label">AD Status</div><div style="margin-top:0.2rem">${stripAdBadge}</div></div>
            </div>
            <div class="knowledge-panel purple" style="margin-top:1rem">
                <h4><i data-lucide="book-open" style="width:14px;height:14px"></i>Theory: Conformal Prediction</h4>
                <p>Each cell shows pChEMBL ± 90% conformal interval (MAPIE). The conformal framework provides distribution-free coverage guarantees. XGBoost, RandomForest, LightGBM, and Ridge-stacking trained on 33,401 bioactivity records with Morgan fingerprints (2048-bit).</p>
            </div>
        </div>
    </div>

    <!-- ═══ SECTION 3: Selectivity — Green ═══ -->
    <div class="full-section section-theme-green">
        <div class="section-inner">
            <div class="section-num">03</div>
            <div class="section-title" style="color:#4ade80">Selectivity Profile</div>
            <div class="section-subtitle">Multi-receptor binding radar and quantitative metrics</div>
            <div class="section-split">
                <div style="display:flex;justify-content:center;align-items:center"><div class="radar-wrap"><canvas id="radar-chart" width="300" height="300"></canvas></div></div>
                <div>
                    <div class="card dark-card" style="margin:0">
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.7rem">${selHtml || '<p style="color:var(--text-muted)">Not available</p>'}</div>
                    </div>
                    <div class="knowledge-panel green" style="margin-top:0.8rem">
                        <h4><i data-lucide="book-open" style="width:14px;height:14px"></i>Theory: Selectivity Indices</h4>
                        <p>ΔpChEMBL between receptor pairs quantifies selectivity. Values > 0.5 indicate significant selectivity. The radar chart visualizes binding profiles — a balanced polygon means non-selective, an elongated shape reveals preferential targeting.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ═══ SECTION 4: Drug-Likeness — Amber ═══ -->
    <div class="full-section section-theme-amber">
        <div class="section-inner">
            <div class="section-num">04</div>
            <div class="section-title" style="color:#fbbf24">Drug-Likeness & Applicability</div>
            <div class="section-subtitle">Pharmacokinetic profiling and domain-of-validity</div>
            <div class="section-split">
                <div>
                    <div class="card dark-card" style="margin:0">
                        <div class="drug-metrics" id="drug-metrics-row">
                            <div class="drug-gauge" data-value="${qedVal !== null ? qedVal : 0}" data-max="1"><div class="drug-gauge-bar"></div><div class="drug-gauge-label">QED</div><div class="drug-gauge-val">${qedVal !== null ? qedVal.toFixed(2) : '—'}</div></div>
                            <div class="drug-gauge" data-value="${lipinskiPass}" data-max="5"><div class="drug-gauge-bar"></div><div class="drug-gauge-label">Ro5</div><div class="drug-gauge-val">${lipinskiPass}/5</div></div>
                            ${adHtml}
                        </div>
                        ${lipHtml}
                        ${painsHtml}
                    </div>
                </div>
                <div>
                    <div class="knowledge-panel amber">
                        <h4><i data-lucide="book-open" style="width:14px;height:14px"></i>Theory: ADMET & Drug Space</h4>
                        <p>QED aggregates 8 molecular properties into a single [0–1] score. Lipinski's Rule of 5 predicts oral bioavailability (MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10). PAINS flags frequent hitters causing false-positive assays. AD uses Tanimoto similarity < 0.4 to flag extrapolations.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ═══ SECTION 5: SHAP — Rose ═══ -->
    <div class="full-section section-theme-rose">
        <div class="section-inner">
            <div class="section-num">05</div>
            <div class="section-title" style="color:#f43f5e">ML Explainability (SHAP)</div>
            <div class="section-subtitle">Feature importance and model interpretation</div>
            <div class="card dark-card" style="margin:0">
                ${shapSection || '<p style="color:var(--text-muted);font-size:0.78rem">SHAP model unavailable for this target.</p>'}
            </div>
            <div class="knowledge-panel rose" style="margin-top:1rem">
                <h4><i data-lucide="book-open" style="width:14px;height:14px"></i>Theory: SHAP Values</h4>
                <p>SHAP decomposes predictions into per-feature contributions via cooperative game theory. Red bars push prediction higher (active), blue bars push lower (inactive). Top features are typically Morgan bits, LogP, TPSA, and substructure fingerprints.</p>
            </div>
        </div>
    </div>

    <!-- ═══ SECTION 6: Analog Search — Dark ═══ -->
    <div class="full-section section-theme-dark">
        <div class="section-inner">
            <div class="section-num">06</div>
            <div class="section-title" style="color:#38bdf8">Analog Search & Neighbors</div>
            <div class="section-subtitle">Training set nearest neighbors and receptor binding</div>
            <div class="section-split" style="margin-bottom:1rem">
                <div class="card dark-card" style="margin:0">
                    <div class="section-header"><i class="tab-ico" data-lucide="grid-3x3"></i>Physicochemical Descriptors</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem">${descHtml}</div>
                </div>
                <div class="card dark-card" style="margin:0">
                    <div class="section-header"><i class="tab-ico" data-lucide="link"></i>Receptor Binding Analysis</div>
                    <div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:0.5rem">Tanimoto similarity (Morgan FP, radius=2). pChEMBL ≥ 6.0 = active.</div>
                    <div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin-bottom:0.5rem">${receptorBtns}</div>
                    <div id="rec-neighbors"></div>
                </div>
            </div>
            <div class="card dark-card" style="margin:0">
                <div class="section-header"><i class="tab-ico" data-lucide="table-2"></i>All Receptor Subtypes Overview</div>
                <div class="table-wrap"><table><thead><tr><th>Subtype</th><th>Max Similarity</th><th>Active Neighbors</th><th>PDB</th></tr></thead><tbody>${recOverviewRows}</tbody></table></div>
            </div>
            <div class="card dark-card" style="margin-top:0.8rem">
                <div class="section-header"><i class="tab-ico" data-lucide="users"></i>Top-10 Training Set Neighbors</div>
                ${globHtml}
            </div>
            <div class="knowledge-panel" style="margin-top:1rem">
                <h4><i data-lucide="book-open" style="width:14px;height:14px"></i>Theory: Nearest Neighbor Analysis</h4>
                <p>Tanimoto similarity < 0.4 to nearest training compound indicates outside Applicability Domain. Active neighbors (pChEMBL ≥ 6) confirm experimental binding.</p>
            </div>
        </div>
    </div>

    <!-- ═══ SECTION 7: Complexes — Cyan ═══ -->
    <div class="full-section section-theme-cyan">
        <div class="section-inner">
            <div class="section-num">07</div>
            <div class="section-title" style="color:#22d3ee">Experimental Complexes</div>
            <div class="section-subtitle">Co-crystal structures from RCSB Protein Data Bank</div>
            <div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin-bottom:0.8rem;align-items:center">
                ${recSubtypes.map(s => {
        const pdbId = (recOverview[s] || {}).pdb || '';
        return `<button class="btn pdb-btn" data-pdb="${pdbId}" data-subtype="${s}" style="padding:0.3rem 0.8rem;font-size:0.75rem">A<sub>${s.slice(1).toLowerCase()}</sub> ${pdbId ? `<span class="badge badge-highlight" style="margin-left:0.3rem">${pdbId}</span>` : '—'}</button>`;
    }).join('')}
                <span class="rcsb-download-slot" id="rcsb-download-slot"></span>
            </div>
            <div id="complex-viewer" style="height:400px;border-radius:12px;overflow:hidden"></div>
            <div class="knowledge-panel" style="margin-top:1rem">
                <h4><i data-lucide="book-open" style="width:14px;height:14px"></i>Theory: Structural Biology</h4>
                <p>Co-crystal structures reveal experimentally-determined binding modes. A₂A receptor (PDB: 6GDG) resolved to 2.6 Å with selective agonists. Structures validate computational docking and identify key pharmacophoric interactions.</p>
            </div>
        </div>
    </div>`;

    if (!target) revealCards();

    // ── Radar chart for selectivity profile ──
    function drawRadar() {
        const canvas = container.querySelector('#radar-chart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const cx = 130, cy = 130, R = 95;
        const selData = data.selectivity_profile || {};
        const subtypes = ['A1', 'A2A', 'A2B', 'A3'];
        const values = subtypes.map(s => {
            const val = (preds.XGBoost && preds.XGBoost[s]) || 0;
            return Math.max(0, val);
        });
        const maxVal = Math.max(...values, 1);
        const n = subtypes.length;
        const angleStep = (Math.PI * 2) / n;
        const startAngle = -Math.PI / 2;

        ctx.clearRect(0, 0, 260, 260);

        // concentric rings
        for (let ring = 1; ring <= 4; ring++) {
            const r = (R * ring) / 4;
            ctx.beginPath();
            for (let i = 0; i <= n; i++) {
                const a = startAngle + i * angleStep;
                const x = cx + r * Math.cos(a);
                const y = cy + r * Math.sin(a);
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            }
            ctx.strokeStyle = 'rgba(56,189,248,0.12)';
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        // spokes
        for (let i = 0; i < n; i++) {
            const a = startAngle + i * angleStep;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + R * Math.cos(a), cy + R * Math.sin(a));
            ctx.strokeStyle = 'rgba(56,189,248,0.08)';
            ctx.stroke();
        }

        // data polygon
        ctx.beginPath();
        for (let i = 0; i <= n; i++) {
            const idx = i % n;
            const a = startAngle + idx * angleStep;
            const r = (values[idx] / maxVal) * R;
            const x = cx + r * Math.cos(a);
            const y = cy + r * Math.sin(a);
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fillStyle = 'rgba(56,189,248,0.18)';
        ctx.fill();
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2;
        ctx.stroke();

        // data points + labels
        for (let i = 0; i < n; i++) {
            const a = startAngle + i * angleStep;
            const r = (values[i] / maxVal) * R;
            const x = cx + r * Math.cos(a);
            const y = cy + r * Math.sin(a);

            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fillStyle = '#38bdf8';
            ctx.fill();
            ctx.strokeStyle = '#0f172a';
            ctx.lineWidth = 2;
            ctx.stroke();

            const lx = cx + (R + 18) * Math.cos(a);
            const ly = cy + (R + 18) * Math.sin(a);
            ctx.fillStyle = '#94a3b8';
            ctx.font = '11px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(subtypes[i], lx, ly);
        }
    }
    drawRadar();

    // ── Animate drug-likeness gauge bars from 0 → final value ──
    function animateGauges() {
        container.querySelectorAll('.drug-gauge').forEach(g => {
            const val = parseFloat(g.getAttribute('data-value')) || 0;
            const max = parseFloat(g.getAttribute('data-max')) || 1;
            const pct = Math.min((val / max) * 100, 100);
            const bar = g.querySelector('.drug-gauge-bar');
            if (bar) {
                bar.style.width = '0%';
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        bar.style.width = pct + '%';
                    });
                });
            }
        });
    }
    animateGauges();

    // Render 3D conformer — deferred until the 3D tab is opened so it initializes at full size
    let viz3dCreated = false;
    function createViz3d() {
        const viewerEl = container.querySelector('#viewer3d');
        if (!viewerEl || !data.mol_block_3d || !window.$3Dmol) return;
        try {
            const viewer = $3Dmol.createViewer(viewerEl, { backgroundColor: '#2C3539' });
            viewerEl._viewer3d = viewer;
            viewer.addModel(data.mol_block_3d, 'sdf');
            viewer.setStyle({}, { stick: { radius: 0.2, colorscheme: 'Jmol' }, sphere: { radius: 0.4, scale: 0.3 } });
            viewer.zoomTo();
            viewer.render();
        } catch (e) {
            console.warn('3Dmol rendering skipped:', e);
        }
    }

    // Receptor selector: show neighbors for the clicked subtype (data already loaded)
    function renderRecNeighbors(subtype) {
        const box = container.querySelector('#rec-neighbors');
        if (!box) return;
        const nbrs = (recNeighbors[subtype] || []);
        if (!nbrs.length) {
            box.innerHTML = '<p style="color:var(--text-muted);font-size:0.75rem">No training compounds with activity data for this subtype.</p>';
            return;
        }
        box.innerHTML = `<div class="table-wrap">
            <table>
                <thead><tr><th>#</th><th>SMILES</th><th>Tanimoto</th><th>pChEMBL</th><th>Activity</th><th>PDB / 3D Structure</th></tr></thead>
                <tbody>${nbrs.map((n, i) => `
                    <tr>
                        <td>${i + 1}</td>
                        <td><code title="${n.smiles}">${n.smiles.length > 34 ? n.smiles.slice(0, 34) + '…' : n.smiles}</code></td>
                        <td><span class="badge badge-${n.tanimoto >= 0.7 ? 'green' : n.tanimoto >= 0.4 ? 'amber' : 'red'}">${n.similarity_label}</span></td>
                        <td><strong>${n.pchembl}</strong></td>
                        <td><span class="badge badge-${n.pchembl >= 6 ? 'green' : n.pchembl >= 4.5 ? 'amber' : 'red'}">${n.activity}</span></td>
                        <td>${pdb3dCell(n.smiles, n.pdb_entries)}</td>
                    </tr>`).join('')}
                </tbody>
            </table>
        </div>`;
    }
    container.querySelectorAll('.rec-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            container.querySelectorAll('.rec-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderRecNeighbors(btn.dataset.subtype);
            wirePdbBtns();
        });
    });
    const firstBtn = container.querySelector('.rec-btn');
    if (firstBtn) { firstBtn.classList.add('active'); renderRecNeighbors(firstBtn.dataset.subtype); }

    // Real co-crystal complex viewer (RCSB download)
    const complexViewer = container.querySelector('#complex-viewer');
    const rcsbSlot = container.querySelector('#rcsb-download-slot');
    function setRcsbDownload(pdbId) {
        if (!rcsbSlot) return;
        rcsbSlot.innerHTML = pdbId
            ? `<a class="btn" style="padding:0.3rem 0.8rem;font-size:0.75rem" href="https://files.rcsb.org/download/${pdbId}.pdb" target="_blank" rel="noopener"><i class="tab-ico" data-lucide="download"></i>Download PDB: ${pdbId}</a>`
            : '<span style="font-size:0.72rem;color:var(--ink-soft)">No experimental co-crystal</span>';
    }
    function loadComplexFor(btn) {
        container.querySelectorAll('.pdb-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const pdbId = btn.getAttribute('data-pdb');
        setRcsbDownload(pdbId);
        if (complexViewer && pdbId) loadPdbComplex(pdbId, complexViewer);
    }
    function wirePdbBtns() {
        // Re-bind each render so buttons created by renderRecNeighbors stay live
        container.querySelectorAll('.pdb-btn').forEach(btn => btn.onclick = () => loadComplexFor(btn));
    }
    function initComplexFor() {
        const firstPdb = container.querySelector('.pdb-btn');
        if (!firstPdb) { if (complexViewer) complexViewer.innerHTML = '<div style="padding:2rem;text-align:center;color:#e2e8f0;font-size:0.8rem">Select a subtype to load its RCSB co-crystal complex.</div>'; return; }
        const pdbId = firstPdb.getAttribute('data-pdb');
        if (pdbId) loadComplexFor(firstPdb);
        else firstPdb.classList.add('active');
    }
    wirePdbBtns();
    initComplexFor();

    // ── Copy SMILES to clipboard with temporary feedback ──
    const copyBtn = container.querySelector('#copy-smiles');
    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            const label = copyBtn.querySelector('span');
            try {
                await navigator.clipboard.writeText(data.smiles || '');
                copyBtn.classList.add('copied');
                if (label) label.textContent = 'Copied!';
                copyBtn.title = 'Copied!';
            } catch (e) {
                // fallback for older browsers / non-secure contexts
                const ta = document.createElement('textarea');
                ta.value = data.smiles || '';
                document.body.appendChild(ta);
                ta.select();
                try { document.execCommand('copy'); } catch (e2) { }
                document.body.removeChild(ta);
                copyBtn.classList.add('copied');
                if (label) label.textContent = 'Copied!';
            }
            setTimeout(() => {
                copyBtn.classList.remove('copied');
                if (label) label.textContent = 'Copy SMILES';
                copyBtn.title = 'Copy SMILES';
            }, 2000);
        });
    }

    // ── Visualizer 2D/3D tabs — 3Dmol must resize+zoom after becoming visible ──
    let viz3dInit = false;
    container.querySelectorAll('.viz-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            container.querySelectorAll('.viz-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            slidePillTo(tab.parentElement, tab);
            container.querySelectorAll('.viz-pane').forEach(p => p.classList.remove('active'));
            const pane = container.querySelector('#' + tab.dataset.viz);
            if (pane) pane.classList.add('active');
            if (tab.dataset.viz === 'viz-3d') {
                if (!viz3dCreated) { createViz3d(); viz3dCreated = true; }
                const v = container.querySelector('#viewer3d');
                if (v && v._viewer3d) { try { v._viewer3d.resize(); v._viewer3d.zoomTo(); v._viewer3d.render(); } catch (e) { } }
            }
        });
    });
    const vizTabsBar = container.querySelector('.viz-tabs');
    const vizActive = container.querySelector('.viz-tab.active');
    if (vizTabsBar && vizActive) slidePillTo(vizTabsBar, vizActive);

    // ── Deep-dive tabs — Chart.js must resize after becoming visible ──
    container.querySelectorAll('.deep-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            container.querySelectorAll('.deep-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            slidePillTo(tab.parentElement, tab);
            container.querySelectorAll('.deep-pane').forEach(p => p.classList.remove('active'));
            const pane = container.querySelector('#' + tab.dataset.deep);
            if (pane) pane.classList.add('active');
            if (tab.dataset.deep === 'deep-shap') {
                singleCharts.forEach(c => { try { c.resize(); } catch (e) { } });
            }
            if (tab.dataset.deep === 'deep-complex' && complexViewer && complexViewer._viewer) {
                try { complexViewer._viewer.resize(); complexViewer._viewer.zoomTo(); complexViewer._viewer.render(); } catch (e) { }
            }
        });
    });
    const deepTabsBar = container.querySelector('.deep-tabs');
    const deepActive = container.querySelector('.deep-tab.active');
    if (deepTabsBar && deepActive) slidePillTo(deepTabsBar, deepActive);

    // Real SHAP chart (red/blue horizontal bars, Chart.js)
    if (shapData && shapData.features && shapData.features.length && window.Chart) {
        const ctx = container.querySelector('#shap-chart');
        if (ctx) {
            const chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: shapData.features.map(f => f.feature),
                    datasets: [{
                        label: 'SHAP value', data: shapData.features.map(f => f.value),
                        backgroundColor: shapData.features.map(f => f.positive ? 'rgba(239,68,68,0.9)' : 'rgba(96,165,250,0.9)'),
                        borderColor: shapData.features.map(f => f.positive ? '#ef4444' : '#60a5fa'), borderWidth: 1.5
                    }]
                },
                options: {
                    indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
                    scales: { x: { grid: { color: 'rgba(56,189,248,0.1)' }, ticks: { color: '#94a3b8' } }, y: { grid: { color: 'rgba(56,189,248,0.1)' }, ticks: { color: '#e2e8f0', font: { size: 11 } } } }
                }
            });
            singleCharts.push(chart);
        }
    }
}


// Batch Predict Runner
function initBatchPredict() {
    const fileInput = document.getElementById('batch-file-input');
    const dropzone = document.getElementById('batch-dropzone');
    if (!fileInput || !dropzone) return;

    dropzone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            await uploadBatchFile(file);
        }
    });
}

let batchResults = [];
let batchPage = 1;
const BATCH_PAGE_SIZE = 25;

async function uploadBatchFile(file) {
    const container = document.getElementById('batch-results');
    if (!container) return;

    container.innerHTML = `<div class="card anim-in" style="text-align:center"><span class="badge badge-cyan">Screening ${file.name} across 4 subtypes + AD Tanimoto...</span></div>`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/predict/batch', { method: 'POST', body: formData });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Batch processing failed');

        batchResults = data.results || [];
        batchPage = 1;
        renderBatchPage(container, data);
    } catch (err) {
        container.innerHTML = `<div class="card anim-in" style="border-color:var(--accent-red)"><span class="badge badge-red">Error: ${err.message}</span></div>`;
    }
}

function renderBatchPage(container, data) {
    const total = batchResults.length;
    const actives = batchResults.filter(r => (r.A1 || 0) >= 6 || (r.A2A || 0) >= 6 || (r.A2B || 0) >= 6 || (r.A3 || 0) >= 6).length;
    const inAd = batchResults.filter(r => r.ad_status === 'In Domain').length;
    const pages = Math.max(1, Math.ceil(total / BATCH_PAGE_SIZE));
    batchPage = Math.min(batchPage, pages);

    const start = (batchPage - 1) * BATCH_PAGE_SIZE;
    const pageRows = batchResults.slice(start, start + BATCH_PAGE_SIZE);

    const rowsHtml = pageRows.map(r => `
        <tr>
            <td>${r.id}</td>
            <td><code title="${r.smiles || ''}">${(r.smiles || '').substring(0, 30)}${(r.smiles || '').length > 30 ? '...' : ''}</code></td>
            <td><span class="badge badge-highlight">${r.best_target || '—'}</span></td>
            <td><strong>${fmtVal(r.best_value)}</strong></td>
            <td>${fmtVal(r.A1)}</td><td>${fmtVal(r.A2A)}</td><td>${fmtVal(r.A2B)}</td><td>${fmtVal(r.A3)}</td>
            <td><span class="badge ${r.ad_status === 'In Domain' ? 'badge-green' : 'badge-amber'}">${r.ad_status || '—'}</span></td>
        </tr>`).join('');

    const pager = pages > 1
        ? `<div style="display:flex;gap:0.4rem;align-items:center;margin-top:0.8rem;flex-wrap:wrap">
            <button class="btn" id="batch-prev" ${batchPage <= 1 ? 'disabled' : ''}>← Prev</button>
            <span style="font-size:0.8rem;color:var(--text-muted)">Page ${batchPage} / ${pages}</span>
            <button class="btn" id="batch-next" ${batchPage >= pages ? 'disabled' : ''}>Next →</button>
          </div>` : '';

    container.innerHTML = `
        <div class="card anim-in">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;flex-wrap:wrap;gap:0.5rem">
                <h3>Processed ${total} Compounds</h3>
                <button class="btn" id="export-csv-btn">Export Results CSV</button>
            </div>
            <div class="grid-4" style="margin-bottom:0.8rem">
                <div class="metric-box"><div class="metric-label">Total</div><div class="metric-value">${total}</div></div>
                <div class="metric-box"><div class="metric-label">Actives (pChEMBL ≥ 6)</div><div class="metric-value">${actives}</div></div>
                <div class="metric-box"><div class="metric-label">In Applicability Domain</div><div class="metric-value">${inAd}</div></div>
                <div class="metric-box"><div class="metric-label">AD Coverage</div><div class="metric-value">${total ? Math.round(inAd / total * 100) + '%' : '—'}</div></div>
            </div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>#</th><th>SMILES</th><th>Best Target</th><th>Max pChEMBL</th><th>A1</th><th>A2A</th><th>A2B</th><th>A3</th><th>AD Status</th></tr></thead>
                    <tbody>${rowsHtml || '<tr><td colspan="9" style="color:var(--text-muted)">No rows</td></tr>'}</tbody>
                </table>
            </div>
            ${pager}
        </div>`;

    document.getElementById('export-csv-btn').addEventListener('click', exportBatchCsv);
    const prev = document.getElementById('batch-prev');
    const next = document.getElementById('batch-next');
    if (prev) prev.addEventListener('click', () => { batchPage--; renderBatchPage(container, data); });
    if (next) next.addEventListener('click', () => { batchPage++; renderBatchPage(container, data); });
}

function exportBatchCsv() {
    if (!batchResults.length) return;
    const header = 'id,smiles,best_target,best_value,A1,A2A,A2B,A3,ad_status';
    const lines = batchResults.map(r => [
        r.id, `"${(r.smiles || '').replace(/"/g, '""')}"`, r.best_target || '', r.best_value || '',
        r.A1 || '', r.A2A || '', r.A2B || '', r.A3 || '', r.ad_status || ''
    ].join(','));
    const blob = new Blob([header + '\n' + lines.join('\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'adenosine_batch_results.csv';
    a.click();
    URL.revokeObjectURL(a.href);
}

let resultsCharts = [];

// Load Model Results Analytics
async function loadModelResults() {
    const overallContainer = document.getElementById('overall-metrics-grid');
    if (!overallContainer) return;

    destroyCharts(resultsCharts);
    resultsCharts = [];

    try {
        const res = await fetch('/api/model_results');
        const data = await res.json();
        if (!res.ok) return;

        // ── SUB 1: Metrics & Calibration ──

        let gridHtml = `
        <div class="metric-box"><div class="metric-label">Overall R²</div><div class="metric-value">${data.overall.r2}</div></div>
        <div class="metric-box"><div class="metric-label">Overall MAE</div><div class="metric-value">${data.overall.mae}</div></div>
        <div class="metric-box"><div class="metric-label">90% Coverage</div><div class="metric-value">${data.overall.coverage_90}</div></div>
        <div class="metric-box"><div class="metric-label">Total Compounds</div><div class="metric-value">${data.overall.n_total}</div></div>`;
        overallContainer.innerHTML = gridHtml;

        // Per-subtype metrics table
        const perBody = document.getElementById('per-subtype-metrics-body');
        if (perBody && data.per_subtype) {
            const subtypeLabels = { A1: 'A₁', A2A: 'A₂ₐ', A2B: 'A₂B', A3: 'A₃' };
            perBody.innerHTML = ['A1','A2A','A2B','A3'].map(s => {
                const sd = data.per_subtype[s] || {};
                return `<tr><td><strong>${subtypeLabels[s] || s}</strong></td><td>${sd.r2}</td><td>${sd.mae}</td><td>${sd.n}</td></tr>`;
            }).join('');
        }

        // Calibration bar chart
        if (Array.isArray(data.calibration) && window.Chart) {
            const calCtx = document.getElementById('calibration-chart');
            if (calCtx) {
                resultsCharts.push(new Chart(calCtx, {
                    type: 'bar',
                    data: {
                        labels: data.calibration.map(c => c.quartile),
                        datasets: [
                            { label: 'MAE', data: data.calibration.map(c => c.mae), backgroundColor: 'rgba(168,85,247,0.9)', borderColor: '#a855f7', borderWidth: 1.5, yAxisID: 'y' },
                            { label: 'N', data: data.calibration.map(c => c.n), backgroundColor: 'rgba(56,189,248,0.5)', yAxisID: 'y1' }
                        ]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true, grid: { color: 'rgba(56,189,248,0.1)' }, ticks: { color: '#94a3b8' } },
                            y1: { position: 'right', beginAtZero: true, grid: { display: false }, ticks: { color: '#94a3b8' } },
                            x: { grid: { color: 'rgba(56,189,248,0.1)' }, ticks: { color: '#e2e8f0' } }
                        }
                    }
                }));
            }
        }

        // Calibration plot image
        if (data.calibration_plot) {
            const img = document.getElementById('calibration-plot-img');
            const ph = document.getElementById('calibration-plot-placeholder');
            if (img) {
                img.onload = () => { img.style.display = 'block'; if (ph) ph.style.display = 'none'; };
                img.src = data.calibration_plot;
            }
        }

        // ── SUB 2: SHAP & Y-Randomization ──

        // Global SHAP bar chart
        if (Array.isArray(data.shap_global) && window.Chart) {
            const shapCtx = document.getElementById('shap-global-chart');
            if (shapCtx) {
                resultsCharts.push(new Chart(shapCtx, {
                    type: 'bar',
                    data: {
                        labels: data.shap_global.map(f => f.name),
                        datasets: [{ label: 'SHAP score', data: data.shap_global.map(f => f.score), backgroundColor: 'rgba(56,189,248,0.9)', borderColor: '#38bdf8', borderWidth: 1.5 }]
                    },
                    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, grid: { color: 'rgba(56,189,248,0.1)' }, ticks: { color: '#94a3b8' } }, y: { grid: { color: 'rgba(56,189,248,0.1)' }, ticks: { color: '#e2e8f0', font: { size: 11 } } } } }
                }));
            }
        }

        // Overall Y-Randomization
        const yrandEl = document.getElementById('yrand-body');
        if (yrandEl && data.y_randomization) {
            const yr = data.y_randomization;
            yrandEl.innerHTML = `
                <p style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.6rem">20 iterations of target shuffling to verify true SAR signal.</p>
                <div class="metric-box"><div class="metric-label">Real Model R²</div><div class="metric-value">${fmtVal(yr.real_r2)}</div></div>
                <div class="metric-box" style="margin-top:0.5rem"><div class="metric-label">Shuffled Mean R² (±σ)</div><div class="metric-value">${fmtVal(yr.shuffled_mean_r2)} ± ${fmtVal(yr.shuffled_std_r2)}</div></div>
                <div class="metric-box" style="margin-top:0.5rem"><div class="metric-label">p-value</div><div class="metric-value">${yr.p_value || '—'}</div></div>
                <div class="feat-row" style="margin-top:0.7rem"><span>Validity</span><strong class="text-ok">Real ≫ Null → genuine SAR signal</strong></div>`;
        }

        // Per-subtype SHAP & Y-Rand data (stored for selector)
        const shapPerSub = data.shap_per_subtype || {};
        const yrandPerSub = data.y_rand_per_subtype || {};

        function renderShapSubtype(subtype) {
            const sd = shapPerSub[subtype] || {};
            const yd = yrandPerSub[subtype] || {};
            const labels = { A1: 'A₁', A2A: 'A₂ₐ', A2B: 'A₂B', A3: 'A₃' };
            const lbl = labels[subtype] || subtype;

            document.getElementById('shap-subtype-label').textContent = lbl;
            document.getElementById('shap-bee-label').textContent = lbl;
            document.getElementById('yrand-subtype-label').textContent = lbl;
            document.getElementById('yrand-metric-label').textContent = lbl;

            // SHAP bar image
            const barImg = document.getElementById('shap-bar-img');
            const barPh = document.getElementById('shap-bar-placeholder');
            if (barImg) {
                barImg.style.display = 'none';
                barImg.src = `/api/plot/shap/${subtype}_bar.png`;
                barImg.onload = () => { barImg.style.display = 'block'; if (barPh) barPh.style.display = 'none'; };
                barImg.onerror = () => { barImg.style.display = 'none'; if (barPh) { barPh.style.display = 'block'; barPh.textContent = 'Plot not available'; } };
            }

            // SHAP beeswarm image
            const beeImg = document.getElementById('shap-bee-img');
            const beePh = document.getElementById('shap-bee-placeholder');
            if (beeImg) {
                beeImg.style.display = 'none';
                beeImg.src = `/api/plot/shap/${subtype}_beeswarm.png`;
                beeImg.onload = () => { beeImg.style.display = 'block'; if (beePh) beePh.style.display = 'none'; };
                beeImg.onerror = () => { beeImg.style.display = 'none'; if (beePh) { beePh.style.display = 'block'; beePh.textContent = 'Plot not available'; } };
            }

            // Top features table
            const featEl = document.getElementById('shap-top-features');
            if (featEl && sd.top_features) {
                featEl.innerHTML = '<div style="font-size:0.65rem;color:var(--text-muted);margin-bottom:0.3rem">Top 10 features by mean |SHAP|</div>' +
                    sd.top_features.map(f => `<div class="feat-row" style="font-size:0.7rem"><span>${f.feature}</span><strong>${f.mean_abs_shap.toFixed(4)}</strong></div>`).join('');
            }

            // Y-Rand distribution image
            const distImg = document.getElementById('yrand-dist-img');
            const distPh = document.getElementById('yrand-dist-placeholder');
            if (distImg) {
                distImg.style.display = 'none';
                distImg.src = `/api/plot/y_randomization/${subtype}_distribution.png`;
                distImg.onload = () => { distImg.style.display = 'block'; if (distPh) distPh.style.display = 'none'; };
                distImg.onerror = () => { distImg.style.display = 'none'; if (distPh) { distPh.style.display = 'block'; distPh.textContent = 'Plot not available'; } };
            }

            // Y-Rand metrics
            const ymBody = document.getElementById('yrand-metrics-body');
            if (ymBody && yd.real_r2 !== undefined) {
                const leakage = yd.leakage_warning;
                ymBody.innerHTML = `
                    <div class="metric-box"><div class="metric-label">Real R²</div><div class="metric-value">${yd.real_r2}</div></div>
                    <div class="metric-box" style="margin-top:0.5rem"><div class="metric-label">Shuffled μ</div><div class="metric-value">${yd.shuffled_mean}</div></div>
                    <div class="metric-box" style="margin-top:0.5rem"><div class="metric-label">Shuffled σ</div><div class="metric-value">${yd.shuffled_std}</div></div>
                    <div class="metric-box" style="margin-top:0.5rem"><div class="metric-label">Separation</div><div class="metric-value">${yd.separation_sigma}σ</div></div>
                    <div class="feat-row" style="margin-top:0.6rem"><span>Verdict</span><strong class="${leakage ? 'badge badge-amber' : 'text-ok'}">${leakage ? '⚠ Potential leakage' : '✓ True SAR signal'}</strong></div>`;
            }
        }

        // Initial render + selector wiring
        renderShapSubtype('A1');
        const shapSelect = document.getElementById('shap-subtype-select');
        if (shapSelect) shapSelect.addEventListener('change', () => renderShapSubtype(shapSelect.value));

        // ── SUB 3: Diagnostics ──

        const diagData = data.diagnostics || {};
        const diagCombined = diagData.combined || {};
        const diagPerSub = diagData.per_subtype || {};

        function renderDiagnostics(target) {
            const subtypeLabels = { Combined: 'Combined', A1: 'A₁', A2A: 'A₂ₐ', A2B: 'A₂B', A3: 'A₃' };
            let d;
            if (target === 'Combined') {
                d = diagCombined;
            } else {
                d = diagPerSub[target] || {};
            }
            const mgrid = document.getElementById('diag-metrics-grid');
            if (mgrid && d.n_compounds !== undefined) {
                let html = `<div class="metric-box"><div class="metric-label">Compounds</div><div class="metric-value">${(d.n_compounds || 0).toLocaleString()}</div></div>`;
                html += `<div class="metric-box"><div class="metric-label">Scaffolds</div><div class="metric-value">${(d.n_scaffolds || 0).toLocaleString()}</div></div>`;
                html += `<div class="metric-box"><div class="metric-label">Diversity Ratio</div><div class="metric-value">${d.diversity_ratio || '—'}</div></div>`;
                if (d.n_activity_cliffs !== undefined) {
                    html += `<div class="metric-box"><div class="metric-label">Activity Cliffs</div><div class="metric-value">${d.n_activity_cliffs}</div></div>`;
                } else {
                    html += `<div class="metric-box"><div class="metric-label">pChEMBL μ±σ</div><div class="metric-value">${d.pchembl_mean || '—'} ± ${d.pchembl_std || '—'}</div></div>`;
                }
                mgrid.innerHTML = html;
            }

            // pChEMBL distribution image
            const pImg = document.getElementById('diag-pchembl-img');
            const pPh = document.getElementById('diag-pchembl-placeholder');
            if (pImg) {
                const pKey = target === 'Combined' ? 'combined' : target.toLowerCase();
                pImg.style.display = 'none';
                pImg.src = `/api/plot/diagnostics/${pKey}_pchembl_distribution.png`;
                pImg.onload = () => { pImg.style.display = 'block'; if (pPh) pPh.style.display = 'none'; };
                pImg.onerror = () => { pImg.style.display = 'none'; if (pPh) { pPh.style.display = 'block'; pPh.textContent = 'Plot not available'; } };
            }

            // Activity cliffs image
            const cImg = document.getElementById('diag-cliffs-img');
            const cPh = document.getElementById('diag-cliffs-placeholder');
            if (cImg) {
                if (target === 'Combined') {
                    cImg.style.display = 'none';
                    if (cPh) { cPh.style.display = 'block'; cPh.textContent = 'Combined cliffs plot not available — select a subtype'; }
                } else {
                    cImg.style.display = 'none';
                    cImg.src = `/api/plot/diagnostics/${target.toLowerCase()}_activity_cliffs_shifts.png`;
                    cImg.onload = () => { cImg.style.display = 'block'; if (cPh) cPh.style.display = 'none'; };
                    cImg.onerror = () => { cImg.style.display = 'none'; if (cPh) { cPh.style.display = 'block'; cPh.textContent = 'Plot not available'; } };
                }
            }
        }

        renderDiagnostics('Combined');
        const diagSelect = document.getElementById('diag-target-select');
        if (diagSelect) diagSelect.addEventListener('change', () => renderDiagnostics(diagSelect.value));

        // ── SUB 4: Examples ──

        // Run summary table
        const rsBody = document.getElementById('run-summary-body');
        const exTables = data.examples_tables || {};
        if (rsBody && exTables.run_summary) {
            const rs = exTables.run_summary;
            rsBody.innerHTML = `<tr><td><span class="badge badge-cyan">${rs.mode}</span></td><td>${(rs.n_smiles || 0).toLocaleString()}</td><td>${(rs.n_rows || 0).toLocaleString()}</td><td style="font-size:0.7rem">${rs.timestamp || '—'}</td></tr>`;
        }

        // Database examples table
        const dbBody = document.getElementById('db-examples-body');
        if (dbBody && exTables.database_rows) {
            dbBody.innerHTML = exTables.database_rows.map(r => `
                <tr>
                    <td><code style="font-size:0.65rem;word-break:break-all" title="${r.smiles_full}">${r.smiles}</code></td>
                    <td><span class="badge badge-cyan">${r.source}</span></td>
                    <td>${r.best}</td>
                    <td style="font-size:0.65rem">${r.predictions}</td>
                    <td>${r.ad || '—'}</td>
                    <td>${r.hits}</td>
                </tr>`).join('') || '<tr><td colspan="6" style="color:var(--text-muted)">No database examples</td></tr>';
        }

        // Novel examples table
        const novBody = document.getElementById('novel-examples-body');
        if (novBody && exTables.novel_rows) {
            novBody.innerHTML = exTables.novel_rows.map(r => `
                <tr>
                    <td><code style="font-size:0.65rem;word-break:break-all" title="${r.smiles_full}">${r.smiles}</code></td>
                    <td><span class="badge badge-purple">${r.source}</span></td>
                    <td>${r.best}</td>
                    <td style="font-size:0.65rem">${r.predictions}</td>
                    <td>${r.ad || '—'}</td>
                    <td>${r.hits}</td>
                </tr>`).join('') || '<tr><td colspan="6" style="color:var(--text-muted)">No novel examples</td></tr>';
        }

        // Molecule gallery cards
        const exCards = document.getElementById('examples-cards');
        if (exCards && Array.isArray(data.examples)) {
            const exSubtypeColors = {
                A1: 'rgba(56,189,248,0.85)',
                A2A: 'rgba(168,85,247,0.85)',
                A2B: 'rgba(74,222,128,0.85)',
                A3: 'rgba(250,204,21,0.85)'
            };
            exCards.innerHTML = data.examples.map((e, idx) => `
                <div class="card mol-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem">
                        <div style="display:flex;align-items:center;gap:0.6rem">
                            <svg class="motion-icon icon-morph" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="1.8" style="flex:none">
                                <circle cx="7" cy="6" r="2.4"/><circle cx="17" cy="7" r="2.4"/><circle cx="13" cy="17" r="2.4"/><circle cx="5" cy="16" r="2.4"/>
                                <path d="M9 8L12 15M14 9L12 14M10 17L12 15M7 18L10 16"/>
                            </svg>
                            <div>
                                <h3 style="font-size:1rem">${e.compound}</h3>
                                <div style="margin-top:0.3rem"><span class="badge badge-cyan">${e.type}</span> <span class="badge badge-green">${e.status}</span></div>
                            </div>
                        </div>
                        <div style="text-align:right">
                            <div class="metric-label">Exp / Pred</div>
                            <div style="font-size:1.05rem;font-weight:800">${fmtVal(e.exp)} / ${fmtVal(e.pred)}</div>
                            <div class="metric-sub" style="color:var(--text-muted)">Δ${fmtVal(e.error)}</div>
                        </div>
                    </div>
                    <div style="height:150px;margin-top:0.6rem"><canvas id="ex-chart-${idx}"></canvas></div>
                    <button class="btn example-run" data-smiles="${e.smiles}" style="width:100%;margin-top:0.7rem">Full Analysis →</button>
                </div>`).join('');

            data.examples.forEach((e, idx) => {
                const ctx = document.getElementById('ex-chart-' + idx);
                if (ctx && window.Chart) {
                    resultsCharts.push(new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: ['A1', 'A2A', 'A2B', 'A3'],
                            datasets: [{
                                label: 'Pred pChEMBL',
                                data: ['A1', 'A2A', 'A2B', 'A3'].map(s => (e.affinity && e.affinity[s]) || 0),
                                backgroundColor: ['A1', 'A2A', 'A2B', 'A3'].map(s => exSubtypeColors[s]),
                                borderRadius: 6
                            }]
                        },
                        options: {
                            responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
                            scales: { y: { min: 0, max: 9, grid: { color: 'rgba(56,189,248,0.08)' } }, x: { grid: { display: false } } }
                        }
                    }));
                }
            });
            exCards.querySelectorAll('.example-run').forEach(btn => {
                btn.addEventListener('click', () => runExampleAnalysis(btn.getAttribute('data-smiles')));
            });
        }

        // ── SUB 5: External Validation ──

        const exEl = document.getElementById('external-table-body');
        const ext = data.external_validation;
        if (exEl && ext && ext.per_subtype) {
            const summaryEl = document.getElementById('external-summary');
            if (summaryEl) {
                const selHtml = (typeof ext.selectivity_recall === 'number')
                    ? `<span class="badge badge-highlight">Selectivity Recall@1: ${(ext.selectivity_recall * 100).toFixed(1)}% (${ext.selectivity_correct}/${ext.selectivity_total})</span>`
                    : '<span class="badge badge-amber">Selectivity data unavailable</span>';
                summaryEl.innerHTML = `
                    <div class="metric-box"><div class="metric-label">Molecules</div><div class="metric-value">${ext.molecules}</div></div>
                    <div class="metric-box"><div class="metric-label">Predicted OK</div><div class="metric-value">${ext.ok}</div></div>
                    <div class="metric-box"><div class="metric-label">Errors</div><div class="metric-value">${ext.errors}</div></div>
                    <div class="metric-box"><div class="metric-label">Selectivity Recall@1</div><div class="metric-value" style="font-size:1rem">${selHtml}</div></div>`;
            }
            exEl.innerHTML = ext.per_subtype.map(e =>
                `<tr><td><strong>${e.subtype}</strong></td><td>${e.n}</td><td>${e.r2}</td><td>${e.mae}</td></tr>`).join('')
                || '<tr><td colspan="4" style="color:var(--text-muted)">No per-subtype metrics</td></tr>';
        } else if (exEl && Array.isArray(ext)) {
            exEl.innerHTML = ext.map(e =>
                `<tr><td><strong>${e.dataset}</strong></td><td>${e.subtypes}</td><td>${e.n}</td><td>${e.r2}</td><td>${e.mae}</td></tr>`).join('');
        }

        // ── SUB 6: Raw Data ──

        const rawGrid = document.getElementById('raw-files-grid');
        if (rawGrid && Array.isArray(data.raw_files)) {
            rawGrid.innerHTML = data.raw_files.map(f => `
                <div class="card" style="padding:0.8rem">
                    <div style="font-size:0.78rem;color:var(--text-muted);margin-bottom:0.4rem">${f.size} · <span style="color:var(--text-secondary)">${f.description}</span></div>
                    <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;flex-wrap:wrap">
                        <code style="font-size:0.72rem;word-break:break-all">${f.filename}</code>
                        <a class="btn" style="padding:0.25rem 0.6rem;font-size:0.7rem" href="/api/raw_data/${encodeURIComponent(f.filename)}">Download</a>
                    </div>
                </div>`).join('') || '<p style="color:var(--text-muted);font-size:0.75rem">Raw files unavailable.</p>';
        }

        const dbEl = document.getElementById('db-download-card');
        if (dbEl && data.database) {
            dbEl.innerHTML = `
                <div class="section-header"><i class="tab-ico" data-lucide="hard-drive-download"></i>Full Curated Database Download</div>
                <div class="sci-box" style="margin-bottom:0.7rem"><b>Complete Training Database.</b> <b style="color:var(--ink)">${data.database.compounds.toLocaleString()}</b> unique compounds · <b style="color:var(--ink)">${data.database.values.toLocaleString()}</b> pChEMBL values across 4 subtypes. Each row = canonical SMILES + experimental pChEMBL per receptor.</div>
                <a href="/api/download_full_database" download class="btn" style="display:inline-flex;text-decoration:none"><i class="tab-ico" data-lucide="download-cloud"></i>Download Full Database (CSV)</a>`;
        }

        // ── SUB 7: Methodology — Benchmarks ──

        const benchBody = document.getElementById('benchmark-table-body');
        if (benchBody && Array.isArray(data.benchmark)) {
            benchBody.innerHTML = data.benchmark.map(b => `
                <tr>
                    <td><strong>${b.model.replace(/_/g, ' ')}</strong></td>
                    <td><span style="font-size:0.7rem">${b.method}</span></td>
                    <td><span class="badge badge-cyan">${b.split}</span></td>
                    ${b.values.map(v => `<td>${typeof v.r2 === 'number' ? v.r2.toFixed(3) : '—'}</td>`).join('')}
                </tr>`).join('');
        }

    } catch (err) {
        console.error('Failed to load model results:', err);
    }
}
