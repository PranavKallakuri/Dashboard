// ---------------------------------------------------------
// Loads data/summary.json (written by scripts/analyze.py)
// and renders every number, chart and interactive element
// on the page from it. Nothing here is hard-coded — swap
// the JSON and the whole dashboard updates.
// ---------------------------------------------------------

const GBP = (n) => `£${n.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const SIGNED_GBP = (n) => `${n >= 0 ? "+" : "\u2212"}£${Math.abs(n).toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let DATA = null; // holds the loaded JSON for the what-if calculator to reuse

function countUp(el, target, prefix = "£") {
  if (reduceMotion) {
    el.textContent = prefix + target.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return;
  }
  const duration = 1200;
  const start = performance.now();
  function frame(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = target * eased;
    el.textContent = prefix + value.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (progress < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function chartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: "#a9a89c", font: { family: "IBM Plex Mono", size: 11 } } },
    },
    scales: {
      x: { ticks: { color: "#a9a89c", font: { family: "IBM Plex Mono", size: 10 } }, grid: { color: "#2a3240" } },
      y: { ticks: { color: "#a9a89c", font: { family: "IBM Plex Mono", size: 10 } }, grid: { color: "#2a3240" } },
    },
  };
}

async function loadDashboard() {
  const res = await fetch("data/summary.json");
  DATA = await res.json();

  renderHero(DATA);
  renderKpis(DATA);
  renderCommentary(DATA);
  renderMonthlyChart(DATA);
  renderForecastCard(DATA);
  renderVariance(DATA);
  renderSuppliers(DATA);
  setupWhatIf(DATA);

  document.getElementById("sourcesList").innerHTML = DATA.data_sources.map((s) => `<li>${s}</li>`).join("");
}

function renderHero(data) {
  countUp(document.getElementById("heroCounter"), data.totals.net);
  document.getElementById("generatedAt").textContent = data.generated_at;
}

function renderKpis(data) {
  document.getElementById("kpiIncome").textContent = GBP(data.totals.income);
  document.getElementById("kpiExpenses").textContent = GBP(data.totals.expenses);
  document.getElementById("kpiNet").textContent = GBP(data.totals.net);
  document.getElementById("kpiCount").textContent = data.totals.transactions_analyzed;
}

function renderCommentary(data) {
  document.getElementById("commentaryText").textContent = data.commentary;
}

function renderMonthlyChart(data) {
  new Chart(document.getElementById("monthlyChart"), {
    type: "bar",
    data: {
      labels: data.monthly.map((m) => m.month),
      datasets: [
        { label: "Income", data: data.monthly.map((m) => m.income), backgroundColor: "#3f8f68" },
        { label: "Expenses", data: data.monthly.map((m) => m.expenses), backgroundColor: "#c1614a" },
      ],
    },
    options: chartOptions(),
  });
}

function renderForecastCard(data) {
  const f = data.forecast;
  document.getElementById("forecastLabel").textContent = f.next_month_label;
  document.getElementById("forecastIncome").textContent = GBP(f.forecast_income);
  document.getElementById("forecastExpenses").textContent = GBP(f.forecast_expenses);
  document.getElementById("forecastNet").textContent = GBP(f.forecast_income - f.forecast_expenses);
  document.getElementById("forecastMethod").textContent = f.method;
}

function renderVariance(data) {
  const rows = data.budget_categories;

  new Chart(document.getElementById("varianceChart"), {
    type: "bar",
    data: {
      labels: rows.map((r) => r.name),
      datasets: [
        { label: "Budget", data: rows.map((r) => r.budget), backgroundColor: "#4a5568" },
        { label: "Actual", data: rows.map((r) => r.actual), backgroundColor: "#c9a15a" },
      ],
    },
    options: chartOptions(),
  });

  const tbody = document.getElementById("varianceTableBody");
  rows.forEach((r) => {
    const variance = r.actual - r.budget;
    const isIncome = r.type === "income";
    const favourable = isIncome ? variance >= 0 : variance <= 0;
    const pct = r.budget !== 0 ? (variance / r.budget) * 100 : 0;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.name}</td>
      <td class="amount">${GBP(r.budget)}</td>
      <td class="amount">${GBP(r.actual)}</td>
      <td class="amount ${favourable ? "positive" : "negative"}">${SIGNED_GBP(variance)}</td>
      <td class="amount ${favourable ? "positive" : "negative"}">${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderSuppliers(data) {
  const s = data.supplier_spend;

  new Chart(document.getElementById("supplierChart"), {
    type: "bar",
    data: {
      labels: s.top_suppliers.map((x) => x.name),
      datasets: [{ label: "Spend", data: s.top_suppliers.map((x) => x.amount), backgroundColor: "#c9a15a" }],
    },
    options: { ...chartOptions(), indexAxis: "y" },
  });

  document.getElementById("supplierConcentration").textContent =
    `Top 5 suppliers account for ${s.top5_concentration_pct}% of ${GBP(s.total_spend)} total spend across ${s.total_suppliers} suppliers.`;
}

function setupWhatIf(data) {
  const income = data.totals.income;
  const fixed = data.budget_categories.filter((c) => c.type === "expense" && c.fixed).reduce((sum, c) => sum + c.actual, 0);
  const variable = data.budget_categories.filter((c) => c.type === "expense" && !c.fixed).reduce((sum, c) => sum + c.actual, 0);
  const baseNet = income - fixed - variable;

  const incomeSlider = document.getElementById("incomeSlider");
  const fixedSlider = document.getElementById("fixedSlider");
  const variableSlider = document.getElementById("variableSlider");

  function recalc() {
    const incomeAdj = Number(incomeSlider.value);
    const fixedAdj = Number(fixedSlider.value);
    const variableAdj = Number(variableSlider.value);

    const projIncome = income * (1 + incomeAdj / 100);
    const projFixed = fixed * (1 + fixedAdj / 100);
    const projVariable = variable * (1 + variableAdj / 100);
    const projNet = projIncome - projFixed - projVariable;
    const delta = projNet - baseNet;

    document.getElementById("incomeSliderVal").textContent = `${incomeAdj >= 0 ? "+" : ""}${incomeAdj}%`;
    document.getElementById("fixedSliderVal").textContent = `${fixedAdj >= 0 ? "+" : ""}${fixedAdj}%`;
    document.getElementById("variableSliderVal").textContent = `${variableAdj >= 0 ? "+" : ""}${variableAdj}%`;

    document.getElementById("whatIfNet").textContent = GBP(projNet);
    const deltaEl = document.getElementById("whatIfDelta");
    deltaEl.textContent = `${SIGNED_GBP(delta)} vs current net position`;
    deltaEl.className = delta >= 0 ? "kpi__value positive" : "kpi__value negative";
  }

  [incomeSlider, fixedSlider, variableSlider].forEach((el) => el.addEventListener("input", recalc));
  recalc();
}

loadDashboard();
