"""Writes docs/summary.json: the numbers and aggregates behind the web explorer.

Run:  python build_site_data.py
"""
import json
from pathlib import Path

import sales_lib as sl

HERE = Path(__file__).parent
DOCS = HERE / "docs"
DOCS.mkdir(exist_ok=True)

df = sl.load_orders(HERE / "Amazon.csv")
g = sl.rfm(df)
seg = sl.segment_table(g)
disc = sl.discount_table(df)
cube = sl.cube(df)

def r(x, n=2):
    return round(float(x), n)

summary = {
    "orders": len(df),
    "customers": int(df["CustomerID"].nunique()),
    "date_range": [str(df["OrderDate"].min().date()), str(df["OrderDate"].max().date())],
    "total_value": r(df["TotalAmount"].sum()),
    "lost_value": r(df.loc[df["IsLost"], "TotalAmount"].sum()),
    "repeat_rate": r(sl.repeat_rate(df), 4),
    "avg_order_value": r(df["TotalAmount"].mean()),
    "totals_check": sl.check_totals(df),
    "segments": [{"segment": k, "customers": int(v.customers), "value": r(v.value), "share_of_value": r(v.share_of_value, 4),
                  "avg_orders": r(v.avg_orders), "avg_recency_days": r(v.avg_recency_days, 0)} for k, v in seg.iterrows()],
    "discounts": [{"discount": r(k, 2), "orders": int(v.orders), "share_of_orders": r(v.share_of_orders, 4),
                   "avg_quantity": r(v.avg_quantity), "avg_unit_price": r(v.avg_unit_price),
                   "avg_order_value": r(v.avg_order_value), "lost_rate": r(v.lost_rate, 4)} for k, v in disc.iterrows()],
    "top_states": {k: r(v) for k, v in sl.top(df, "State").items()},
    "top_brands": {k: r(v) for k, v in sl.top(df, "Brand").items()},
    "weekday_orders": {k: int(v) for k, v in sl.weekday_profile(df).items()},
    "cube_columns": ["month", "category", "country", "status", "orders", "value"],
    "cube": [[m, c, k, s, int(o), r(v)] for m, c, k, s, o, v in cube.itertuples(index=False)],
}
(DOCS / "summary.json").write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
print(len(cube), "cube rows")
print(json.dumps({k: v for k, v in summary.items() if k not in ("cube",)}, indent=1)[:3500])
