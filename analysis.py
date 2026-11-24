"""Customer & sales analysis of Amazon.csv with pandas (no database needed).

Run:  python analysis.py
Writes charts to figures/ and prints the key numbers used in the README.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

HERE = Path(__file__).parent
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)

df = pd.read_csv(HERE / "Amazon.csv", parse_dates=["OrderDate"])
millions = FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M")

# ---- Data checks ----------------------------------------------------------
print(f"Rows: {len(df):,}  |  duplicate OrderIDs: {df['OrderID'].duplicated().sum()}")
print(f"Missing values: {int(df.isna().sum().sum())}")
print(f"Order dates: {df['OrderDate'].min().date()} to {df['OrderDate'].max().date()}")
expected = df["Quantity"] * df["UnitPrice"] * (1 - df["Discount"]) + df["Tax"] + df["ShippingCost"]
print(f"TotalAmount matches qty*price*(1-discount)+tax+shipping: {((expected - df['TotalAmount']).abs() < 0.02).mean():.1%}")

# ---- Revenue --------------------------------------------------------------
total = df["TotalAmount"].sum()
lost = df.loc[df["OrderStatus"].isin(["Cancelled", "Returned"]), "TotalAmount"].sum()
print(f"\nTotal order value (all statuses): {total:,.2f}")
print(f"Cancelled + Returned: {lost:,.2f} ({lost / total:.1%})")
print(f"Net of cancelled/returned: {total - lost:,.2f}")
print("\nOrders by status:\n", df["OrderStatus"].value_counts().to_string())
print("\nPayment methods (share of orders):\n", (df["PaymentMethod"].value_counts(normalize=True) * 100).round(1).to_string())

# ---- Charts ---------------------------------------------------------------
def barh(series, title, color, name):
    series = series.sort_values()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(series.index, series.values, color=color)
    for i, v in enumerate(series.values):
        ax.text(v, i, f" {v / 1e6:.1f}M", va="center")
    ax.set_title(title, fontsize=14, weight="bold")
    ax.set_xlabel("Order value")
    ax.xaxis.set_major_formatter(millions)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=150)
    plt.close(fig)

by_cat = df.groupby("Category")["TotalAmount"].sum().sort_values(ascending=False)
print("\nRevenue by category:\n", by_cat.round(0).to_string())
print(f"Spread between top and bottom category: {by_cat.iloc[0] / by_cat.iloc[-1] - 1:.1%}")
barh(by_cat, "Order value by category", "#4CAF50", "top_categories.png")

by_state = df.groupby("State")["TotalAmount"].sum().sort_values(ascending=False).head(10)
print("\nTop 10 states:\n", by_state.round(0).to_string())
barh(by_state, "Top 10 states by order value", "#FF9800", "top_states.png")

monthly = df.groupby(df["OrderDate"].dt.to_period("M"))["TotalAmount"].sum()
print(f"\nMonthly order value: mean {monthly.mean():,.0f}, min {monthly.min():,.0f} ({monthly.idxmin()}), max {monthly.max():,.0f} ({monthly.idxmax()})")
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(monthly.index.to_timestamp(), monthly.values, marker="o", color="#2196F3")
ax.set_title("Monthly order value", fontsize=14, weight="bold")
ax.set_ylabel("Order value")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x / 1e6:.2f}M"))
ax.grid(alpha=0.3)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(FIG / "monthly_revenue.png", dpi=150)
plt.close(fig)
print("\nCharts saved to figures/")
