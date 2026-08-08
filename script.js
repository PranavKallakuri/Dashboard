// Reads data/summary.json (written by scripts/analyze.py) and
// renders every number and chart on the page from it.

const usd = (n) => `$${n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}M`;
const signedUsd = (n) => `${n >= 0 ? "+" : "\u2212"}$${Math.abs(n).toLocaleString("en-US", { maximumFractionDigits: 0 })}M`;

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function countUp(el, target, prefix = "$", suffix = "M") {
  if (reduceMotion) { el.textContent = prefix + Math.round(target).toLocaleString("en-US") + suffix; return; }
  const duration = 1200;
  const start = performance.now();
  function frame(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = prefix + Math.round(target * eased).toLocaleString("en-US") + suffix;
    if (progress < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function chartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: "#a9a89c", font: { family: "IBM Plex Mono", size: 11 } } } },
    scales: {
      x: { ticks: { color: "#a9a89c", font: { family: "IBM Plex Mono", size: 10 } }, grid: { color: "#2a3240" } },
      y: { ticks: { color: "#a9a89c", font: { family: "IBM Plex Mono", size: 10 } }, grid: { color: "#2a3240" } },
    },
  };
}

async function loadDashboard() {
  const res = await fetch("data/summary.json");
  const data = await res.json();
  const latest = data.yearly_data[data.yearly_data.length - 1];

  // Hero
  countUp(document.getElementById("heroCounter"), latest["Net Income"]);
  document.getElementById("heroYear").textContent = latest.Year;
  document.getElementById("generatedAt").textContent = data.generated_at;

  // KPI cards (latest year)
  document.getElementById("kpiRevenue").textContent = usd(latest.Revenue);
  document.getElementById("kpiCos").textContent = usd(latest["Cost of Sales"]);
  document.getElementById("kpiOpex").textContent = usd(latest["Operating Expenses"]);
  document.getElementById("kpiOpIncome").textContent = usd(latest["Operating Income"]);

  // Commentary
  document.getElementById("commentaryText").textContent = data.commentary;

  // Trend chart — Revenue, Cost of Sales, Operating Expenses across all years
  new Chart(document.getElementById("trendChart"), {
    type: "bar",
    data: {
      labels: data.yearly_data.map((y) => y.Year),
      datasets: [
        { label: "Revenue", data: data.yearly_data.map((y) => y.Revenue), backgroundColor: "#c9a15a" },
        { label: "Cost of Sales", data: data.yearly_data.map((y) => y["Cost of Sales"]), backgroundColor: "#c1614a" },
        { label: "Operating Expenses", data: data.yearly_data.map((y) => y["Operating Expenses"]), backgroundColor: "#4a5568" },
      ],
    },
    options: chartOptions(),
  });

  // Variance chart + table — Revenue % change year over year
  new Chart(document.getElementById("varianceChart"), {
    type: "bar",
    data: {
      labels: data.variance.map((v) => `${v.prior_year}\u2192${v.year}`),
      datasets: [
        { label: "Revenue % change", data: data.variance.map((v) => v.Revenue.pct_change), backgroundColor: "#3f8f68" },
        { label: "Net Income % change", data: data.variance.map((v) => v["Net Income"].pct_change), backgroundColor: "#c9a15a" },
      ],
    },
    options: chartOptions(),
  });

  const tbody = document.getElementById("varianceTableBody");
  data.variance.forEach((v) => {
    const tr = document.createElement("tr");
    const rev = v.Revenue;
    const ni = v["Net Income"];
    tr.innerHTML = `
      <td>${v.prior_year} \u2192 ${v.year}</td>
      <td class="amount">${usd(rev.current)}</td>
      <td class="amount ${rev.change >= 0 ? "positive" : "negative"}">${signedUsd(rev.change)} (${rev.pct_change >= 0 ? "+" : ""}${rev.pct_change}%)</td>
      <td class="amount">${usd(ni.current)}</td>
      <td class="amount ${ni.change >= 0 ? "positive" : "negative"}">${signedUsd(ni.change)} (${ni.pct_change >= 0 ? "+" : ""}${ni.pct_change}%)</td>
    `;
    tbody.appendChild(tr);
  });

  // Forecast
  const f = data.forecast;
  document.getElementById("forecastLabel").textContent = f.forecast_year;
  document.getElementById("forecastRevenue").textContent = usd(f.Revenue);
  document.getElementById("forecastOpIncome").textContent = usd(f["Operating Income"]);
  document.getElementById("forecastNetIncome").textContent = usd(f["Net Income"]);
  document.getElementById("forecastMethod").textContent = f.method;

  // What-if calculator — based on latest year actuals
  const baseRevenue = latest.Revenue, baseCos = latest["Cost of Sales"], baseOpex = latest["Operating Expenses"];
  const baseNet = latest["Net Income"];
  const revSlider = document.getElementById("revenueSlider");
  const cosSlider = document.getElementById("cosSlider");
  const opexSlider = document.getElementById("opexSlider");

  function recalc() {
    const revAdj = Number(revSlider.value), cosAdj = Number(cosSlider.value), opexAdj = Number(opexSlider.value);
    const projRevenue = baseRevenue * (1 + revAdj / 100);
    const projCos = baseCos * (1 + cosAdj / 100);
    const projOpex = baseOpex * (1 + opexAdj / 100);
    const projOpIncome = projRevenue - projCos - projOpex;
    const delta = projOpIncome - (baseRevenue - baseCos - baseOpex);

    document.getElementById("revenueSliderVal").textContent = `${revAdj >= 0 ? "+" : ""}${revAdj}%`;
    document.getElementById("cosSliderVal").textContent = `${cosAdj >= 0 ? "+" : ""}${cosAdj}%`;
    document.getElementById("opexSliderVal").textContent = `${opexAdj >= 0 ? "+" : ""}${opexAdj}%`;
    document.getElementById("whatIfResult").textContent = usd(projOpIncome);
    const deltaEl = document.getElementById("whatIfDelta");
    deltaEl.textContent = `${signedUsd(delta)} vs ${latest.Year} actual`;
    deltaEl.className = delta >= 0 ? "kpi__value positive" : "kpi__value negative";
  }
  [revSlider, cosSlider, opexSlider].forEach((el) => el.addEventListener("input", recalc));
  recalc();

  document.getElementById("dataSource").textContent = data.data_source;
}

loadDashboard();
