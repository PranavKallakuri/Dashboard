# Management Accounts — Real-Data FP&A Dashboard

An FP&A / management accounting portfolio project built on real
transactions, not sample data: your own bank account via Open
Banking, and real UK council spend data for supplier analysis.

## How it fits together

```
scripts/pull_transactions.py   -> connects to your real bank, saves data/raw_transactions.json (PRIVATE, gitignored)
scripts/analyze.py             -> reads raw_transactions.json + council_spend.csv, writes data/summary.json (aggregated, safe to publish)
index.html / style.css / script.js  -> reads data/summary.json and renders the dashboard
```

Only `data/summary.json` — totals, budget variance, forecast,
supplier concentration — is ever committed or deployed. Your real
transaction-level data never leaves your machine.

## What it covers

- **Overview** — income/expenses/net KPIs plus a written management commentary
- **Variance** — budget vs. actual by category, colour-coded favourable/unfavourable
- **Forecast** — next month's projected income/expenses (3-month trailing average)
- **Suppliers** — top supplier spend and concentration risk, from real council data
- **What-if** — live sliders to stress-test income/fixed/variable cost assumptions

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your real GoCardless keys
```

Get free GoCardless Bank Account Data API keys at
https://bankaccountdata.gocardless.com.

Download a council spend-over-£500 CSV from https://data.gov.uk
(search "[council name] spending over 500") and save it as
`data/council_spend.csv`. Open it and check the actual column
names — they vary by council — then update `SUPPLIER_COL` and
`AMOUNT_COL` near the top of `scripts/analyze.py` to match.

Set your own monthly budget per category in `MONTHLY_BUDGET` near
the top of `scripts/analyze.py` — this is what makes the variance
section a real exercise rather than just a description of what
happened.

## Run it

```bash
python scripts/pull_transactions.py   # opens your bank's real login in a browser
python scripts/analyze.py             # writes data/summary.json
```

Before running `analyze.py`, edit the `COMMENTARY` string near the
bottom with your own 2-3 sentence write-up of what happened this
period — this is the single highest-value line in the whole project
for an FP&A interview.

Then open `index.html` in a browser (or run `python -m http.server`
in this folder) to see the dashboard with your real numbers.

## Deploy to GitHub Pages

```bash
git init
git add .
git commit -m "Real-data FP&A dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

Then on GitHub: **Settings → Pages → Deploy from branch → main →
/ (root)**. Your live URL will be
`https://<your-username>.github.io/<repo-name>/`.
