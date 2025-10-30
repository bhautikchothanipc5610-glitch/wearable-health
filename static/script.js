// Heart Rate & HRV Chart — smoother visuals
const ctx = document.getElementById('healthChart').getContext('2d');
const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      {
        label: 'Heart Rate (BPM)',
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239,68,68,0.15)',
        borderWidth: 2,
        data: [],
        tension: 0.4,
        fill: true,
        pointRadius: 3
      },
      {
        label: 'HRV',
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.15)',
        borderWidth: 2,
        data: [],
        tension: 0.4,
        fill: true,
        pointRadius: 3
      }
    ]
  },
  options: {
    animation: { duration: 500, easing: 'easeOutCubic' },
    plugins: { legend: { position: 'top', labels: { boxWidth: 12 } } },
    scales: {
      x: {
        ticks: { callback: (val, i) => chart.data.labels[i]?.split(' ')[1] || '' }
      },
      y: { beginAtZero: false }
    }
  }
});

// === Gauges ===
function createGauge(canvasId, color) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [0, 100],
        backgroundColor: [color, '#e5e7eb'],
        borderWidth: 0,
        borderRadius: [50, 0]
      }]
    },
    options: {
      rotation: -90,
      circumference: 360,
      cutout: '80%',
      animation: { duration: 800, easing: 'easeOutCubic' },
      plugins: { legend: { display: false } }
    }
  });
}

const stressGauge = createGauge('stressGauge', '#ef4444');
const tempGauge = createGauge('tempGauge', '#f59e0b');

function updateGauge(chart, value, max = 100) {
  const percent = Math.min((value / max) * 100, 100);
  chart.data.datasets[0].data = [percent, 100 - percent];
  chart.update();
}

async function loadData() {
  const res = await fetch('/api/data');
  const data = await res.json();

  const table = document.getElementById("data");
  table.innerHTML = `
    <tr>
      <th>Time</th>
      <th>Heart Rate</th>
      <th>Temperature</th>
      <th>HRV</th>
      <th>Alert</th>
    </tr>
  `;

  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.timestamp.split(' ')[1]}</td>
      <td>${row.heart_rate}</td>
      <td>${row.temperature}</td>
      <td>${row.hrv}</td>
      <td>${row.alert}</td>
    `;
    table.appendChild(tr);
  });

  const timestamps = data.map(r => r.timestamp).reverse();
  const heartRates = data.map(r => r.heart_rate).reverse();
  const hrvs = data.map(r => r.hrv).reverse();

  chart.data.labels = timestamps;
  chart.data.datasets[0].data = heartRates;
  chart.data.datasets[1].data = hrvs;
  chart.update();

  if (data.length > 0) {
    const last = data[data.length - 1];
    updateGauge(stressGauge, last.stress_score || 0, 50);
    document.getElementById('stressValue').innerText =
      `${Math.min(((last.stress_score || 0) / 50 * 100), 100).toFixed(0)}%`;
    updateGauge(tempGauge, last.temperature || 36, 40);
    document.getElementById('tempValue').innerText =
      `${last.temperature?.toFixed(1)} °C`;
  }
}

setInterval(loadData, 2000);
window.onload = loadData;
