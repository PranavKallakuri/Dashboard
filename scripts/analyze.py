"""
analyze.py
----------
Reads your manually-extracted Shell financial data (data/shell_financials.csv)
and computes year-over-year variance and a next-year forecast, writing the
result to data/summary.json — the one file your website actually reads.
"""

import json
import pandas as pd

# ---------------------------------------------------------------
# STEP 1: Load the CSV. This is the pandas equivalent of opening a
# spreadsheet — pd.read_csv() reads the whole file into a
# "DataFrame", which is just Python's version of a table: rows and
# columns, same shape as what you see in Excel.
# ---------------------------------------------------------------
df = pd.read_csv("data/shell_financials.csv")
df = df.sort_values("Year").reset_index(drop=True)  # make sure years are in order

# The metrics we'll analyse — matching your column names exactly
METRICS = ["Revenue", "Cost of Sales", "Operating Expenses", "Operating Income", "Net Income"]

# ---------------------------------------------------------------
# STEP 2: Year-over-year variance.
# In Excel you'd write =B3-B2 (this year minus last year) then drag
# that formula down the column. This loop does the same thing, one
# year at a time, for every metric.
# ---------------------------------------------------------------
variance_rows = []
for i in range(1, len(df)):  # start at 1 — the first year has no "prior year" to compare to
    row = {"year": int(df.loc[i, "Year"]), "prior_year": int(df.loc[i - 1, "Year"])}
    for m in METRICS:
        current = df.loc[i, m]
        prior = df.loc[i - 1, m]
        change = current - prior                              # = B3-B2
        pct_change = (change / prior * 100) if prior else 0    # = (B3-B2)/B2
        row[m] = {
            "current": round(current, 2),
            "prior": round(prior, 2),
            "change": round(change, 2),
            "pct_change": round(pct_change, 2),
        }
    variance_rows.append(row)

# ---------------------------------------------------------------
# STEP 3: Forecast next year with a 3-year trailing average — same
# method as before, just yearly instead of monthly. In Excel this
# is =AVERAGE(B3:B5). Here, .tail(3) grabs the last 3 rows and
# .mean() averages them — two pandas steps doing what one Excel
# formula does.
# ---------------------------------------------------------------
last_3 = df.tail(3)
forecast = {
    "forecast_year": int(df["Year"].max()) + 1,
    "method": "3-year trailing average",
}
for m in METRICS:
    forecast[m] = round(last_3[m].mean(), 2)

# ---------------------------------------------------------------
# STEP 4: Write everything to summary.json. json.dump() is the
# Python equivalent of File > Save As — just saving to a format a
# website can read instead of a format Excel can read.
# ---------------------------------------------------------------
summary = {
    "generated_at": pd.Timestamp.today().strftime("%Y-%m-%d"),
    "data_source": "Shell plc Annual Reports 2021-2025 (manually extracted)",
    "yearly_data": df.to_dict(orient="records"),
    "variance": variance_rows,
    "forecast": forecast,
}

with open("data/summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("Done — wrote data/summary.json with variance and forecast for Shell.")
