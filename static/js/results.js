/* Results page: expand/collapse cards + Plotly chart rendering */

const NOTE_NAMES = ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B'];
function midiName(m) {
  return NOTE_NAMES[m % 12] + (Math.floor(m / 12) - 1);
}

function toggleCard(cardId) {
  const card = document.getElementById(cardId);
  if (!card) return;
  const wasExpanded = card.classList.contains('expanded');
  card.classList.toggle('expanded');

  if (!wasExpanded) {
    // Plotly measures the container; defer until after .result-detail is visible and laid out.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        card.querySelectorAll('.plotly-chart').forEach(renderChart);
      });
    });
  }
}

function renderChart(el) {
  if (el.dataset.rendered === 'true') return;
  if (typeof Plotly === 'undefined') {
    el.textContent = 'Chart library failed to load (check network / CDN).';
    return;
  }

  const normedRaw = el.getAttribute('data-normed');
  const idealRaw = el.getAttribute('data-ideal');
  let normed;
  let ideal;
  try {
    normed = JSON.parse(normedRaw || '{}');
    ideal = JSON.parse(idealRaw || '{}');
  } catch (e) {
    el.textContent = 'Chart data could not be parsed';
    return;
  }
  const title = el.getAttribute('data-chart-title') || '';

  const allMidis = new Set([
    ...Object.keys(normed).map(Number),
    ...Object.keys(ideal).map(Number),
  ]);
  if (allMidis.size === 0) {
    el.textContent = 'No data';
    return;
  }

  const sorted = Array.from(allMidis).sort((a, b) => a - b);
  const labels = sorted.map(m => midiName(m) + ' (' + m + ')');
  const songVals = sorted.map(m => normed[m] || 0);
  const idealVals = sorted.map(m => ideal[m] || 0);

  const n = labels.length;
  const colors = [];
  for (let i = 0; i < n; i++) {
    const t = n > 1 ? i / (n - 1) : 0.5;
    const r = Math.round(180 + t * 50);
    const g = Math.round(120 + t * 60);
    const b = Math.round(200 + (1 - t) * 40);
    colors.push('rgb(' + r + ',' + g + ',' + b + ')');
  }

  const barTrace = {
    x: labels,
    y: songVals,
    type: 'bar',
    name: 'Song (normalised)',
    marker: { color: colors, line: { color: '#fff', width: 0.5 } },
  };

  const lineTrace = {
    x: labels,
    y: idealVals,
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Ideal vector',
    line: { color: '#d4619b', width: 2.5 },
    marker: { size: 4 },
  };

  const layout = {
    title: { text: title, font: { size: 13, family: 'Poppins', color: '#3a2d3d' } },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(253,240,247,0.5)',
    font: { color: '#8a7a8e', size: 9, family: 'Inter' },
    xaxis: {
      tickangle: -45,
      tickfont: { size: 7 },
      gridcolor: '#ead6e6',
      automargin: true,
    },
    yaxis: {
      title: { text: 'Proportion of singing time', font: { size: 10 } },
      gridcolor: '#ead6e6',
      automargin: true,
    },
    legend: { x: 0, y: 1.12, orientation: 'h', font: { size: 9 } },
    margin: { t: 50, b: 100, l: 60, r: 20 },
    bargap: 0.2,
  };

  try {
    Plotly.newPlot(el, [barTrace, lineTrace], layout, {
      responsive: true,
      displayModeBar: false,
    });
    el.dataset.rendered = 'true';
    requestAnimationFrame(() => {
      if (typeof Plotly !== 'undefined' && Plotly.Plots && Plotly.Plots.resize) {
        Plotly.Plots.resize(el);
      }
    });
  } catch (e) {
    el.textContent = 'Chart could not be drawn.';
  }
}
