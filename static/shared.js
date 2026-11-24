const token = window.location.pathname.split("/").pop();

async function loadSharedDashboard() {
  try {
    const response = await fetch(`/api/shared/${encodeURIComponent(token)}`);
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Share link unavailable" }));
      throw new Error(body.detail || "Share link unavailable");
    }

    const dashboard = await response.json();
    document.querySelector("#sharedTitle").textContent = dashboard.name;
    document.querySelector("#sharedDescription").textContent = dashboard.description;
    const grid = document.querySelector("#sharedGrid");

    for (const section of dashboard.sections) {
      const card = document.createElement("article");
      card.className = "shared-card";
      card.innerHTML = `<h3>${section.name}</h3>${renderSharedChart(section)}`;
      grid.appendChild(card);
    }
  } catch (error) {
    const message = document.querySelector("#sharedError");
    message.textContent = error.message;
    message.classList.remove("hidden");
  }
}

function renderSharedChart(section) {
  const labels = section.chart_labels || [];
  const values = section.chart_values || [];
  if (!labels.length || !values.length) {
    return `<div class="chart chart-empty"><strong>${section.name}</strong><span>No chart data available</span></div>`;
  }

  if (section.chart_type === "pie") {
    const total = values.reduce((sum, value) => sum + value, 0);
    const colors = ["#315fbd", "#78a99b", "#e9a23b", "#e56b6f"];
    let start = 0;
    const segments = values.map((value, index) => {
      const degrees = (value / total) * 360;
      const segment = `${colors[index]} ${start}deg ${start + degrees}deg`;
      start += degrees;
      return segment;
    }).join(", ");

    return `<div class="chart chart-pie-wrap"><div class="chart-pie" style="background:conic-gradient(${segments})"><div class="chart-pie-center"><strong>${section.chart_headline}</strong><span>total</span></div></div><div class="chart-legend">${labels.map((label, index) => `<div><span style="background:${colors[index]}"></span>${label}<b>${values[index]}</b></div>`).join("")}</div></div>`;
  }

  if (section.chart_type === "line") {
    const width = 260;
    const height = 120;
    const padding = 16;
    const max = Math.max(...values) * 1.12;
    const min = Math.min(...values) * 0.85;
    const points = values.map((value, index) => {
      const x = padding + index * ((width - padding * 2) / (values.length - 1));
      const y = height - padding - ((value - min) / (max - min)) * (height - padding * 2);
      return `${x},${y}`;
    }).join(" ");
    const circles = values.map((value, index) => {
      const x = padding + index * ((width - padding * 2) / (values.length - 1));
      const y = height - padding - ((value - min) / (max - min)) * (height - padding * 2);
      return `<circle cx="${x}" cy="${y}" r="4"/>`;
    }).join("");

    return `<div class="chart chart-line"><div class="chart-summary"><strong>${section.chart_headline}</strong><span>${section.chart_change}</span></div><svg viewBox="0 0 ${width} ${height}" aria-label="${section.name}"><line x1="16" y1="104" x2="244" y2="104"/><polyline points="${points}"/>${circles}</svg><div class="chart-axis">${labels.map(label => `<span>${label}</span>`).join("")}</div></div>`;
  }

  const max = Math.max(...values);
  return `<div class="chart chart-bar"><div class="chart-summary"><strong>${section.chart_headline}</strong><span>${section.chart_change}</span></div><div class="bar-grid">${values.map((value, index) => `<div class="bar-column"><span class="bar-value">${value}%</span><div class="bar-track"><div class="bar-fill" style="height:${Math.max((value / max) * 100, 8)}%"></div></div><span class="bar-label">${labels[index]}</span></div>`).join("")}</div></div>`;
}

loadSharedDashboard();
