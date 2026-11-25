"""Cleaning and aggregation helpers for Amazon.csv (order-level data).

No plotting or file output here, so everything can be unit tested.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LOST = ["Cancelled", "Returned"]


def load_orders(path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["OrderDate"])
    df["Month"] = df["OrderDate"].dt.to_period("M").astype(str)
    df["Year"] = df["OrderDate"].dt.year
    df["IsLost"] = df["OrderStatus"].isin(LOST)
    return df


def check_totals(df: pd.DataFrame) -> float:
    """Share of rows where TotalAmount = qty * price * (1 - discount) + tax + shipping."""
    expected = df["Quantity"] * df["UnitPrice"] * (1 - df["Discount"]) + df["Tax"] + df["ShippingCost"]
    return float(((expected - df["TotalAmount"]).abs() < 0.02).mean())


def rfm(df: pd.DataFrame) -> pd.DataFrame:
    """Recency, frequency and monetary value per customer, using orders that were not cancelled or returned.

    Recency is days between the customer's last valid order and the day after the last order in the data.
    Scores run 1 (worst) to 5 (best) by rank, so ties are split by first appearance.
    """
    valid = df[~df["IsLost"]]
    ref = df["OrderDate"].max() + pd.Timedelta(days=1)
    g = valid.groupby("CustomerID").agg(
        last=("OrderDate", "max"), frequency=("OrderID", "count"), monetary=("TotalAmount", "sum"))
    g["recency"] = (ref - g["last"]).dt.days
    g["R"] = 6 - pd.qcut(g["recency"].rank(method="first"), 5, labels=False) - 1
    g["F"] = pd.qcut(g["frequency"].rank(method="first"), 5, labels=False) + 1
    g["M"] = pd.qcut(g["monetary"].rank(method="first"), 5, labels=False) + 1
    g["segment"] = [segment(r, f) for r, f in zip(g["R"], g["F"])]
    return g.drop(columns="last")


def segment(r: int, f: int) -> str:
    if r >= 4 and f >= 4:
        return "Champions"
    if f >= 4:
        return "Loyal"
    if r >= 4:
        return "Recent"
    if r <= 2 and f >= 3:
        return "At risk"
    if r <= 2:
        return "Lost"
    return "Needs attention"


def segment_table(g: pd.DataFrame) -> pd.DataFrame:
    t = g.groupby("segment").agg(customers=("monetary", "size"), value=("monetary", "sum"),
                                 avg_orders=("frequency", "mean"), avg_recency_days=("recency", "mean"))
    t["share_of_value"] = t["value"] / t["value"].sum()
    return t.sort_values("value", ascending=False)


def discount_table(df: pd.DataFrame) -> pd.DataFrame:
    """How order size and value change with the discount level."""
    t = df.groupby("Discount").agg(orders=("OrderID", "count"), avg_quantity=("Quantity", "mean"),
                                   avg_unit_price=("UnitPrice", "mean"), avg_order_value=("TotalAmount", "mean"),
                                   lost_rate=("IsLost", "mean"))
    t["share_of_orders"] = t["orders"] / t["orders"].sum()
    return t


def repeat_rate(df: pd.DataFrame) -> float:
    """Share of customers with more than one order that was not cancelled or returned."""
    n = df[~df["IsLost"]].groupby("CustomerID").size()
    return float((n > 1).mean())


def cube(df: pd.DataFrame) -> pd.DataFrame:
    """Orders and order value per month, category, country and status. The web explorer sums this."""
    return (df.groupby(["Month", "Category", "Country", "OrderStatus"])
              .agg(orders=("OrderID", "count"), value=("TotalAmount", "sum"))
              .reset_index())


def top(df: pd.DataFrame, col: str, n: int = 10) -> pd.Series:
    return df.groupby(col)["TotalAmount"].sum().sort_values(ascending=False).head(n)


def weekday_profile(df: pd.DataFrame) -> pd.Series:
    return df.groupby(df["OrderDate"].dt.day_name())["OrderID"].count().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
