# Shell plc — Real-Data FP&A Dashboard

A management accounting / FP&A portfolio project analysing Shell
plc's real financial statements (2021-2025), manually extracted
from their public annual reports.

## How it fits together

```
data/shell_financials.csv   -> your manually-extracted figures from Shell's real annual reports
scripts/analyze.py          -> reads the CSV, computes variance + forecast, writes data/summary.json
index.html / style.css / script.js  -> reads data/summary.json and renders the dashboard
```

## What it covers

- **Overview** — latest-year KPIs plus a written management commentary
- **Trend** — Revenue, Cost of Sales and Operating Expenses, 2021-2025
- **Variance** — year-over-year % change in Revenue and Net Income
- **Forecast** — next year's projection (3-year trailing average)
- **What-if** — live sliders to stress-test Revenue/Cost of Sales/Opex assumptions

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run it

Edit `scripts/analyze.py` first — update `COMMENTARY` near the bottom
with your own write-up of what actually drove the numbers.

```bash
python scripts/analyze.py
```

Then open `index.html` in a browser to check it with your real numbers.

## Deploy to GitHub Pages

Commit and push as normal through GitHub Desktop. Under
**Settings → Pages** on GitHub, make sure it's set to deploy from
`main` / `/(root)`. Live URL: `https://<your-username>.github.io/<repo-name>/`.
