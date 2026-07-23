"""
analyze.py
----------
Reads:
  - data/raw_transactions.json   (from pull_transactions.py — real, private)
  - data/council_spend.csv        (downloaded from data.gov.uk — already public)

Writes:
  - data/summary.json             (aggregated only — safe to commit and publish)

This version is built for an FP&A / management accounting narrative:
budget vs. actual variance, a simple forecast, and supplier spend
concentration — rather than an audit-style analysis.

Raw transaction-level data never leaves your machine. summary.json
only has totals, categories and monthly numbers, which is what the
dashboard actually displays.
"""

import json
import pandas as pd

# ---------------------------------------------------------------
# 1. Load and clean your real bank transactions
# ---------------------------------------------------------------
with open("data/raw_transactions.json") as f:
    raw = json.load(f)

rows = []
for account in raw:
    for t in account["transactions"]["booked"]:
        rows.append({
            "date": t.get("bookingDate"),
            "amount": float(t["transactionAmount"]["amount"]),
            "description": t.get("remittanceInformationUnstructured", ""),
        })

df = pd.DataFrame(rows)
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.strftime("%b %Y")

# ---------------------------------------------------------------
# 2. Categorise transactions with simple keyword matching.
#    Edit this dictionary to match your own real transaction
#    descriptions — this is the part that makes it YOUR ledger.
# ---------------------------------------------------------------
CATEGORY_RULES = {
    "Rent": ["rent", "landlord"],
    "Groceries": ["tesco", "sainsbury", "aldi", "lidl", "asda"],
    "Transport": ["tfl", "uber", "trainline", "national rail"],
    "Subscriptions": ["netflix", "spotify", "amazon prime"],
}

# Which categories are "fixed" (roughly the same every month) vs
# "variable" (fluctuate) — used later by the dashboard's what-if
# calculator. Anything not listed here defaults to variable.
FIXED_CATEGORIES = {"Rent"}

# ---------------------------------------------------------------
# 3. Set your own monthly budget per category. This is the number
#    YOU decide — a target, a prior average, whatever you want to
#    be held accountable against. This is what makes the variance
#    section a genuine management-accounting exercise rather than
#    just a description of what happened.
# ---------------------------------------------------------------
MONTHLY_BUDGET = {
    "Income": 3100.00,
    "Rent": 650.00,
    "Groceries": 280.00,
    "Transport": 110.00,
    "Subscriptions": 45.00,
    "Other": 150.00,
}


def categorise(description: str) -> str:
    desc = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(k in desc for k in keywords):
            return category
    return "Other"


df["category"] = df["description"].apply(categorise)

income_df = df[df["amount"] > 0]
expense_df = df[df["amount"] < 0].copy()
expense_df["amount"] = expense_df["amount"].abs()

# ---------------------------------------------------------------
# 4. Monthly income vs expenses (for the trend chart)
# ---------------------------------------------------------------
monthly = (
    df.assign(type=lambda d: d["amount"].gt(0).map({True: "income", False: "expenses"}))
    .assign(amount=lambda d: d["amount"].abs())
    .groupby(["month", "type"])["amount"].sum()
    .unstack(fill_value=0)
    .reset_index()
)
monthly_out = [
    {"month": row["month"], "income": round(row.get("income", 0), 2), "expenses": round(row.get("expenses", 0), 2)}
    for _, row in monthly.iterrows()
]

# ---------------------------------------------------------------
# 5. Forecast next month using a 3-month trailing average.
#    Simple on purpose — this is meant to be explainable, which
#    matters more than sophistication for a portfolio piece.
# ---------------------------------------------------------------
last_3 = monthly.tail(3)
forecast_income = round(last_3.get("income", pd.Series([0])).mean(), 2)
forecast_expenses = round(last_3.get("expenses", pd.Series([0])).mean(), 2)

forecast_out = {
    "next_month_label": "Next month",   # replace with the actual label, e.g. "Aug 2026"
    "forecast_income": float(forecast_income),
    "forecast_expenses": float(forecast_expenses),
    "method": "3-month trailing average",
}

# ---------------------------------------------------------------
# 6. Budget vs actual, by category
# ---------------------------------------------------------------
category_totals = expense_df.groupby("category")["amount"].sum()

budget_rows = [{
    "name": "Income",
    "type": "income",
    "fixed": False,
    "budget": MONTHLY_BUDGET.get("Income", 0),
    "actual": round(income_df["amount"].sum(), 2),
}]

for category, budget_amount in MONTHLY_BUDGET.items():
    if category == "Income":
        continue
    budget_rows.append({
        "name": category,
        "type": "expense",
        "fixed": category in FIXED_CATEGORIES,
        "budget": budget_amount,
        "actual": round(float(category_totals.get(category, 0)), 2),
    })

# ---------------------------------------------------------------
# 7. Supplier spend concentration from the council data.
#    Check your CSV's actual column names first — they vary by
#    council — and update SUPPLIER_COL / AMOUNT_COL to match.
# ---------------------------------------------------------------
spend = pd.read_csv("data/council_spend.csv")

SUPPLIER_COL = "Supplier Name"   # <- change to match your CSV's actual column name
AMOUNT_COL = "Amount"            # <- change to match your CSV's actual column name

supplier_totals = spend.groupby(SUPPLIER_COL)[AMOUNT_COL].sum().sort_values(ascending=False)
total_spend = float(supplier_totals.sum())
top5_total = float(supplier_totals.head(5).sum())
top5_pct = round((top5_total / total_spend) * 100, 1) if total_spend else 0

supplier_out = {
    "top_suppliers": [{"name": name, "amount": round(amt, 2)} for name, amt in supplier_totals.head(5).items()],
    "total_spend": round(total_spend, 2),
    "total_suppliers": int(supplier_totals.shape[0]),
    "top5_concentration_pct": top5_pct,
}

# ---------------------------------------------------------------
# 8. Write your own management commentary here each time you
#    regenerate the dashboard — two or three sentences narrating
#    the story behind the numbers, the way a real MA pack would.
#    This one line does more for an FP&A CV than any chart does.
# ---------------------------------------------------------------
COMMENTARY = (
    "Write 2-3 sentences here summarising what actually happened this month: "
    "what drove any variance, what's trending in the right/wrong direction, "
    "and anything worth flagging ahead of next month."
)

# ---------------------------------------------------------------
# 9. Write the aggregated, publish-safe summary
# ---------------------------------------------------------------
summary = {
    "generated_at": pd.Timestamp.today().strftime("%Y-%m-%d"),
    "data_sources": [
        "Open Banking (GoCardless Bank Account Data API) — personal transactions",
        "data.gov.uk — local council spend over £500",
    ],
    "totals": {
        "income": round(income_df["amount"].sum(), 2),
        "expenses": round(expense_df["amount"].sum(), 2),
        "net": round(income_df["amount"].sum() - expense_df["amount"].sum(), 2),
        "transactions_analyzed": int(len(df)),
    },
    "monthly": monthly_out,
    "forecast": forecast_out,
    "budget_categories": budget_rows,
    "supplier_spend": supplier_out,
    "commentary": COMMENTARY,
}

with open("data/summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("Wrote data/summary.json — this is the only file the dashboard reads.")
print("Don't forget to edit COMMENTARY above with your own narrative before the next run.")
