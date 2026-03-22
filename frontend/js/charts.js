/* ===== Chart.js Global Config ===== */
Chart.defaults.color = '#8b95a5';
Chart.defaults.borderColor = 'rgba(255,255,255,0.04)';
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;

const CHART_COLORS = {
    fixed_1:  { bg: 'rgba(239,68,68,0.25)',  border: '#ef4444' },
    fixed_4:  { bg: 'rgba(245,158,11,0.25)', border: '#f59e0b' },
    fixed_8:  { bg: 'rgba(139,92,246,0.25)', border: '#8b5cf6' },
    adaptive: { bg: 'rgba(0,212,255,0.30)',   border: '#00d4ff' },
};

const CHART_LABELS = {
    fixed_1: 'Fixed-1', fixed_4: 'Fixed-4',
    fixed_8: 'Fixed-8', adaptive: 'Adaptive',
};

/* ===== Comparison Charts (Demo) ===== */
let compareSamplesChart = null;
let compareTokensChart = null;

function renderCompareCharts(data) {
    const strategies = Object.keys(data);
    const labels = strategies.map(s => CHART_LABELS[s] || s);
    const samples = strategies.map(s => data[s].total_samples);
    const tokens = strategies.map(s => data[s].total_tokens);
    const bgColors = strategies.map(s => (CHART_COLORS[s] || {}).bg || '#66666644');
    const borderColors = strategies.map(s => (CHART_COLORS[s] || {}).border || '#666');

    const barOpts = {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.03)' } }, x: { grid: { display: false } } }
    };

    const ctx1 = document.getElementById('compare-samples-chart');
    if (compareSamplesChart) compareSamplesChart.destroy();
    compareSamplesChart = new Chart(ctx1, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Samples', data: samples, backgroundColor: bgColors, borderColor: borderColors, borderWidth: 2, borderRadius: 6 }] },
        options: { ...barOpts, scales: { ...barOpts.scales, y: { ...barOpts.scales.y, title: { display: true, text: 'Samples' } } } }
    });

    const ctx2 = document.getElementById('compare-tokens-chart');
    if (compareTokensChart) compareTokensChart.destroy();
    compareTokensChart = new Chart(ctx2, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Tokens', data: tokens, backgroundColor: bgColors, borderColor: borderColors, borderWidth: 2, borderRadius: 6 }] },
        options: { ...barOpts, scales: { ...barOpts.scales, y: { ...barOpts.scales.y, title: { display: true, text: 'Tokens' } } } }
    });
}

/* ===== Experiment Charts ===== */
let chartAccuracy = null;
let chartSamples = null;
let chartTokens = null;
let chartDistribution = null;
let chartTradeoff = null;

function renderExperimentCharts(result) {
    const summary = result.summary;
    const strategies = Object.keys(summary);
    const labels = strategies.map(s => CHART_LABELS[s] || s);
    const bgColors = strategies.map(s => (CHART_COLORS[s] || {}).bg || '#66666644');
    const borderColors = strategies.map(s => (CHART_COLORS[s] || {}).border || '#666');

    const gridStyle = { color: 'rgba(255,255,255,0.03)' };
    const noGrid = { display: false };

    // 1. Accuracy
    const ctx1 = document.getElementById('chart-accuracy');
    if (chartAccuracy) chartAccuracy.destroy();
    chartAccuracy = new Chart(ctx1, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Accuracy %', data: strategies.map(s => summary[s].accuracy_pct), backgroundColor: bgColors, borderColor: borderColors, borderWidth: 2, borderRadius: 6 }] },
        options: {
            responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => c.parsed.y.toFixed(1) + '%' } } },
            scales: { y: { beginAtZero: true, max: 100, title: { display: true, text: 'Accuracy (%)' }, grid: gridStyle }, x: { grid: noGrid } }
        }
    });

    // 2. Avg Samples
    const ctx2 = document.getElementById('chart-samples');
    if (chartSamples) chartSamples.destroy();
    chartSamples = new Chart(ctx2, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Avg Samples', data: strategies.map(s => summary[s].avg_samples), backgroundColor: bgColors, borderColor: borderColors, borderWidth: 2, borderRadius: 6 }] },
        options: {
            responsive: true, plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, title: { display: true, text: 'Avg Samples' }, grid: gridStyle }, x: { grid: noGrid } }
        }
    });

    // 3. Avg Tokens
    const ctx3 = document.getElementById('chart-tokens');
    if (chartTokens) chartTokens.destroy();
    chartTokens = new Chart(ctx3, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Avg Tokens', data: strategies.map(s => summary[s].avg_tokens), backgroundColor: bgColors, borderColor: borderColors, borderWidth: 2, borderRadius: 6 }] },
        options: {
            responsive: true, plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, title: { display: true, text: 'Avg Tokens' }, grid: gridStyle }, x: { grid: noGrid } }
        }
    });

    // 4. Adaptive distribution
    const dist = result.adaptive_sample_distribution || [];
    if (dist.length > 0) {
        const counts = {};
        dist.forEach(v => { counts[v] = (counts[v] || 0) + 1; });
        const buckets = Object.keys(counts).sort((a, b) => +a - +b);
        const ctx4 = document.getElementById('chart-distribution');
        if (chartDistribution) chartDistribution.destroy();
        chartDistribution = new Chart(ctx4, {
            type: 'bar',
            data: {
                labels: buckets.map(b => b + ' samples'),
                datasets: [{ label: 'Questions', data: buckets.map(b => counts[b]), backgroundColor: 'rgba(0,212,255,0.30)', borderColor: '#00d4ff', borderWidth: 2, borderRadius: 6 }]
            },
            options: {
                responsive: true, plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Questions' }, ticks: { stepSize: 1 }, grid: gridStyle },
                    x: { title: { display: true, text: 'Samples Used' }, grid: noGrid }
                }
            }
        });
    }

    // 5. Tradeoff scatter — THE KEY CHART
    const ctx5 = document.getElementById('chart-tradeoff');
    if (chartTradeoff) chartTradeoff.destroy();
    chartTradeoff = new Chart(ctx5, {
        type: 'scatter',
        data: {
            datasets: strategies.map(s => ({
                label: CHART_LABELS[s] || s,
                data: [{ x: summary[s].avg_samples, y: summary[s].accuracy_pct }],
                backgroundColor: (CHART_COLORS[s] || {}).border || '#666',
                borderColor: (CHART_COLORS[s] || {}).border || '#666',
                pointRadius: s === 'adaptive' ? 14 : 10,
                pointHoverRadius: s === 'adaptive' ? 17 : 13,
                pointStyle: s === 'adaptive' ? 'star' : 'circle',
            }))
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: { callbacks: { label: c => `${c.dataset.label}: ${c.parsed.y.toFixed(1)}% acc @ ${c.parsed.x.toFixed(1)} avg samples` } },
                legend: { position: 'top' },
            },
            scales: {
                x: { title: { display: true, text: 'Avg Samples per Question (Compute →)' }, beginAtZero: true, grid: gridStyle },
                y: { title: { display: true, text: 'Accuracy (%)' }, beginAtZero: true, max: 100, grid: gridStyle }
            }
        }
    });
}
