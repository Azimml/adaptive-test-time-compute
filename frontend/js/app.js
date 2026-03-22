/* ===== State ===== */
let selectedStrategy = 'adaptive';
let presets = [];
let isRunning = false;

const LABELS = {
    fixed_1: 'Fixed-1',
    fixed_4: 'Fixed-4',
    fixed_8: 'Fixed-8',
    adaptive: 'Adaptive',
};

/* ===== Init ===== */
document.addEventListener('DOMContentLoaded', () => {
    loadPresets();
    setupStrategyButtons();
    setupThresholdSlider();
    setupRunButton();
    setupExperimentButton();
    loadSavedResults();
});

/* ===== Load saved experiment results on page load ===== */
async function loadSavedResults() {
    try {
        const res = await fetch('/data_latest.json');
        if (res.ok) {
            const data = await res.json();
            if (data.summary) {
                displayExperimentResults(data);
            }
        }
    } catch (e) {
        /* no saved results, that's fine */
    }
}

/* ===== Presets ===== */
async function loadPresets() {
    try {
        const res = await fetch('/api/presets');
        presets = await res.json();
        renderPresetButtons();
    } catch (e) {
        console.error('Failed to load presets:', e);
    }
}

function renderPresetButtons() {
    const container = document.getElementById('preset-buttons');
    container.innerHTML = '';
    presets.forEach(p => {
        const btn = document.createElement('button');
        btn.className = `preset-btn ${p.difficulty}`;
        btn.textContent = p.question.length > 36 ? p.question.slice(0, 36) + '...' : p.question;
        btn.title = p.question;
        btn.onclick = () => {
            document.getElementById('question-input').value = p.question;
            const gtDisplay = document.getElementById('ground-truth-display');
            const gtValue = document.getElementById('gt-value');
            gtDisplay.style.display = 'block';
            gtValue.textContent = p.answer;
        };
        container.appendChild(btn);
    });
}

/* ===== Strategy Buttons ===== */
function setupStrategyButtons() {
    document.querySelectorAll('.strat-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.strat-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedStrategy = btn.dataset.strategy;
        });
    });
}

/* ===== Threshold Slider ===== */
function setupThresholdSlider() {
    const slider = document.getElementById('threshold-slider');
    const display = document.getElementById('threshold-value');
    slider.addEventListener('input', () => {
        display.textContent = parseFloat(slider.value).toFixed(2);
    });
}

/* ===== Run Button ===== */
function setupRunButton() {
    document.getElementById('run-btn').addEventListener('click', () => {
        if (isRunning) return;
        const question = document.getElementById('question-input').value.trim();
        if (!question) return;

        if (selectedStrategy === 'compare') {
            runComparison(question);
        } else {
            runSolve(question, selectedStrategy);
        }
    });
}

/* ===== Run Single Strategy via WebSocket ===== */
async function runSolve(question, strategy) {
    isRunning = true;
    setRunButtonLoading(true);
    clearViz();
    hidePanel('results-panel');
    hidePanel('compare-panel');
    document.getElementById('live-tag').style.display = 'inline';

    const threshold = parseFloat(document.getElementById('threshold-slider').value);
    const groundTruth = document.getElementById('gt-value')?.textContent || null;

    const ws = new WebSocket(`ws://${window.location.host}/ws/solve`);

    ws.onopen = () => {
        ws.send(JSON.stringify({
            question,
            strategy,
            ground_truth: groundTruth,
            config: { confidence_threshold: threshold }
        }));
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'start') {
            showVizStatus(`Running ${LABELS[msg.strategy] || msg.strategy}...`);
        } else if (msg.type === 'round') {
            renderRound(msg.data);
        } else if (msg.type === 'complete') {
            renderFinalResult(msg.data);
            document.getElementById('live-tag').style.display = 'none';
            isRunning = false;
            setRunButtonLoading(false);
            ws.close();
        } else if (msg.type === 'error') {
            showVizError(msg.message);
            document.getElementById('live-tag').style.display = 'none';
            isRunning = false;
            setRunButtonLoading(false);
            ws.close();
        }
    };

    ws.onerror = () => {
        showVizError('WebSocket connection failed. Is the server running?');
        document.getElementById('live-tag').style.display = 'none';
        isRunning = false;
        setRunButtonLoading(false);
    };
}

/* ===== Run Comparison ===== */
async function runComparison(question) {
    isRunning = true;
    setRunButtonLoading(true);
    clearViz();
    hidePanel('results-panel');
    hidePanel('compare-panel');
    showVizStatus('Running all 4 strategies...');

    const threshold = parseFloat(document.getElementById('threshold-slider').value);
    const groundTruth = document.getElementById('gt-value')?.textContent || null;

    try {
        const res = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question,
                ground_truth: groundTruth,
                config: { confidence_threshold: threshold }
            })
        });
        const data = await res.json();
        clearViz();
        renderComparisonResult(data);
        renderCompareCharts(data);
    } catch (e) {
        showVizError('Request failed: ' + e.message);
    }

    isRunning = false;
    setRunButtonLoading(false);
}

/* ===== Viz Helpers ===== */
function clearViz() {
    document.getElementById('process-viz').innerHTML = '';
}

function showVizStatus(msg) {
    document.getElementById('process-viz').innerHTML =
        `<div class="empty-state"><div class="spinner"></div><p class="pulse" style="margin-top:12px;">${msg}</p></div>`;
}

function showVizError(msg) {
    document.getElementById('process-viz').innerHTML =
        `<div class="empty-state" style="color:var(--red);"><p>${msg}</p></div>`;
}

function renderRound(data) {
    const viz = document.getElementById('process-viz');
    const spinner = viz.querySelector('.empty-state');
    if (spinner) spinner.remove();

    const threshold = parseFloat(document.getElementById('threshold-slider').value);
    const block = document.createElement('div');
    block.className = 'round-block';

    const isStop = data.decision === 'stop';
    const decClass = isStop ? 'decision-stop' : 'decision-continue';
    let decText;
    if (data.stop_reason === 'confidence_met') decText = 'STOP — Confident';
    else if (data.stop_reason === 'budget_exhausted') decText = 'STOP — Budget';
    else decText = 'CONTINUE — Need More';

    let html = `
        <div class="round-header">
            <span class="round-label">Round ${data.round} &mdash; ${data.total_samples} total samples</span>
            <span class="round-decision ${decClass}">${decText}</span>
        </div>
        <div class="samples-row">
    `;

    data.samples.forEach((s, i) => {
        const num = (data.round - 1) * 2 + i + 1;
        const ans = s.extracted_answer || '—';
        const preview = (s.reasoning_preview || '').replace(/</g, '&lt;').slice(0, 180);
        html += `
            <div class="sample-card">
                <div class="sample-label">Sample #${num}</div>
                <div class="sample-answer">${ans}</div>
                <div class="sample-preview">${preview}...</div>
            </div>
        `;
    });
    html += `</div>`;

    // Confidence bar
    const conf = data.confidence;
    const confPct = (conf * 100).toFixed(1);
    const threshPct = (threshold * 100).toFixed(0);
    let confClass = 'confidence-low';
    if (conf >= threshold) confClass = 'confidence-high';
    else if (conf >= 0.5) confClass = 'confidence-mid';

    html += `
        <div class="confidence-bar-wrap">
            <div class="confidence-bar-label">
                <span>Agreement: <strong>${confPct}%</strong> (${data.majority_count || '?'}/${data.total_samples} agree)</span>
                <span>Threshold: ${threshPct}%</span>
            </div>
            <div class="confidence-bar">
                <div class="confidence-fill ${confClass}" style="width: ${confPct}%"></div>
            </div>
        </div>
    `;

    if (data.distribution && Object.keys(data.distribution).length > 0) {
        html += `<div class="answer-dist">
            Answers: ${Object.entries(data.distribution).map(([k, v]) => `<span class="mono">${k}</span>&times;${v}`).join(' &nbsp; ')}
        </div>`;
    }

    block.innerHTML = html;
    viz.appendChild(block);
    block.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function renderFinalResult(data) {
    const panel = document.getElementById('results-panel');
    const grid = document.getElementById('results-grid');
    panel.style.display = 'block';

    const isCorrect = data.correct;
    const correctClass = isCorrect === true ? 'result-correct' : isCorrect === false ? 'result-incorrect' : '';
    const correctText = isCorrect === true ? 'Correct' : isCorrect === false ? 'Incorrect' : '—';

    grid.innerHTML = `
        <div class="result-item">
            <div class="result-value" style="color:var(--accent);">${data.answer || '—'}</div>
            <div class="result-label">Final Answer</div>
        </div>
        <div class="result-item">
            <div class="result-value">${data.total_samples}</div>
            <div class="result-label">Samples Used</div>
        </div>
        <div class="result-item">
            <div class="result-value">${(data.confidence * 100).toFixed(0)}%</div>
            <div class="result-label">Confidence</div>
        </div>
        <div class="result-item">
            <div class="result-value">${data.total_tokens || 0}</div>
            <div class="result-label">Total Tokens</div>
        </div>
        <div class="result-item">
            <div class="result-value">${data.elapsed_ms || 0}<small>ms</small></div>
            <div class="result-label">Latency</div>
        </div>
        <div class="result-item">
            <div class="result-value ${correctClass}">${correctText}</div>
            <div class="result-label">${data.ground_truth ? 'GT: ' + data.ground_truth : 'Correctness'}</div>
        </div>
    `;
}

function renderComparisonResult(data) {
    const panel = document.getElementById('compare-panel');
    const tbody = document.getElementById('compare-tbody');
    panel.style.display = 'block';

    tbody.innerHTML = '';
    Object.entries(data).forEach(([s, r]) => {
        const isAdaptive = s === 'adaptive';
        const isCorrect = r.correct;
        const cClass = isCorrect === true ? 'badge-correct' : isCorrect === false ? 'badge-incorrect' : '';
        const cText = isCorrect === true ? 'Yes' : isCorrect === false ? 'No' : '—';

        const tr = document.createElement('tr');
        if (isAdaptive) tr.className = 'highlight';
        tr.innerHTML = `
            <td><strong>${LABELS[s] || s}</strong></td>
            <td class="mono">${r.answer || '—'}</td>
            <td class="mono">${r.total_samples}</td>
            <td class="mono">${(r.confidence * 100).toFixed(0)}%</td>
            <td class="mono">${r.total_tokens}</td>
            <td class="mono">${r.elapsed_ms}ms</td>
            <td class="${cClass}">${cText}</td>
        `;
        tbody.appendChild(tr);
    });
}

/* ===== Experiment ===== */
function setupExperimentButton() {
    document.getElementById('run-experiment-btn').addEventListener('click', runExperiment);
}

async function runExperiment() {
    if (isRunning) return;
    isRunning = true;

    const btn = document.getElementById('run-experiment-btn');
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loading').style.display = 'inline-flex';
    btn.disabled = true;

    const nSamples = parseInt(document.getElementById('exp-n-samples').value);
    const checks = document.querySelectorAll('.exp-strats input[type=checkbox]:checked');
    const strategies = Array.from(checks).map(cb => cb.value);

    const progressWrap = document.getElementById('exp-progress');
    const progressFill = document.getElementById('exp-progress-fill');
    const progressText = document.getElementById('exp-progress-text');
    progressWrap.style.display = 'block';
    progressFill.style.width = '0%';

    document.getElementById('exp-results').style.display = 'none';
    document.getElementById('exp-key-result').style.display = 'none';

    try {
        const ws = new WebSocket(`ws://${window.location.host}/ws/experiment`);

        ws.onopen = () => {
            ws.send(JSON.stringify({ n_samples: nSamples, strategies }));
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'progress') {
                const pct = msg.percent || 0;
                progressFill.style.width = pct + '%';
                progressText.textContent = `Q${msg.question_idx + 1}/${msg.total_questions} | ${LABELS[msg.strategy] || msg.strategy} | ${pct}%`;
            } else if (msg.type === 'complete') {
                progressFill.style.width = '100%';
                progressText.textContent = 'Complete!';
                displayExperimentResults(msg.data);
                ws.close();
                finishExperiment(btn);
            } else if (msg.type === 'error') {
                progressText.textContent = 'Error: ' + msg.message;
                ws.close();
                finishExperiment(btn);
            }
        };

        ws.onerror = () => {
            progressText.textContent = 'WebSocket failed. Is the server running?';
            finishExperiment(btn);
        };
    } catch (e) {
        document.getElementById('exp-progress-text').textContent = 'Error: ' + e.message;
        finishExperiment(btn);
    }
}

function finishExperiment(btn) {
    isRunning = false;
    btn.querySelector('.btn-text').style.display = 'inline';
    btn.querySelector('.btn-loading').style.display = 'none';
    btn.disabled = false;
}

function displayExperimentResults(result) {
    const container = document.getElementById('exp-results');
    container.style.display = 'block';

    // Meta
    document.getElementById('exp-meta').innerHTML =
        `${result.n_questions} questions &bull; ${result.strategies.length} strategies &bull; ${result.elapsed_seconds}s`;

    // Key result banner
    const summary = result.summary;
    if (summary.adaptive && summary.fixed_8) {
        const ad = summary.adaptive;
        const f8 = summary.fixed_8;
        const sampleSave = ((1 - ad.avg_samples / f8.avg_samples) * 100).toFixed(0);
        const tokenSave = ((1 - ad.avg_tokens / f8.avg_tokens) * 100).toFixed(0);
        const accDiff = (ad.accuracy_pct - f8.accuracy_pct).toFixed(1);
        const accSign = accDiff >= 0 ? '+' : '';

        document.getElementById('kr-compute').textContent = `↓${sampleSave}%`;
        document.getElementById('kr-accuracy').textContent = `${accSign}${accDiff}%`;
        document.getElementById('kr-tokens').textContent = `↓${tokenSave}%`;

        // Color the accuracy diff
        const accEl = document.getElementById('kr-accuracy');
        accEl.style.color = accDiff >= 0 ? 'var(--green)' : 'var(--red)';

        document.getElementById('exp-key-result').style.display = 'flex';
    }

    // Table
    const tbody = document.getElementById('exp-results-tbody');
    tbody.innerHTML = '';
    const strategies = Object.keys(summary);

    strategies.forEach(s => {
        const d = summary[s];
        const tr = document.createElement('tr');
        if (s === 'adaptive') tr.className = 'best-row';
        tr.innerHTML = `
            <td><strong>${LABELS[s] || s}</strong></td>
            <td class="mono">${d.accuracy_pct}%</td>
            <td class="mono">${d.total_correct}/${d.total_questions}</td>
            <td class="mono">${d.avg_samples}</td>
            <td class="mono">${d.avg_tokens}</td>
            <td class="mono">${d.total_tokens}</td>
        `;
        tbody.appendChild(tr);
    });

    renderExperimentCharts(result);
    container.scrollIntoView({ behavior: 'smooth' });
}

/* ===== Utils ===== */
function setRunButtonLoading(loading) {
    const btn = document.getElementById('run-btn');
    btn.querySelector('.btn-text').style.display = loading ? 'none' : 'inline';
    btn.querySelector('.btn-loading').style.display = loading ? 'inline-flex' : 'none';
    btn.disabled = loading;
}

function hidePanel(id) {
    document.getElementById(id).style.display = 'none';
}
