import pandas as pd
import pytest

import sales_lib as sl


def orders():
    rows = []
    # customer, date, status, qty, price, discount
    data = [
        ("C1", "2024-01-10", "Delivered", 2, 100.0, 0.0),
        ("C1", "2024-06-01", "Delivered", 1, 50.0, 0.1),
        ("C2", "2023-01-05", "Delivered", 1, 20.0, 0.0),
        ("C2", "2023-02-05", "Cancelled", 3, 20.0, 0.0),
        ("C3", "2024-12-30", "Returned", 1, 10.0, 0.0),
    ]
    for i, (c, d, s, q, p, disc) in enumerate(data):
        total = q * p * (1 - disc)
        rows.append({"OrderID": f"O{i}", "OrderDate": d, "CustomerID": c, "ProductID": "P1", "Category": "Books", "Brand": "B",
                     "Quantity": q, "UnitPrice": p, "Discount": disc, "Tax": 0.0, "ShippingCost": 0.0, "TotalAmount": total,
                     "PaymentMethod": "UPI", "OrderStatus": s, "City": "X", "State": "TX", "Country": "United States"})
    df = pd.DataFrame(rows)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["Month"] = df["OrderDate"].dt.to_period("M").astype(str)
    df["Year"] = df["OrderDate"].dt.year
    df["IsLost"] = df["OrderStatus"].isin(sl.LOST)
    return df


def test_check_totals_detects_a_wrong_total():
    df = orders()
    assert sl.check_totals(df) == 1.0
    df.loc[0, "TotalAmount"] += 5
    assert sl.check_totals(df) == pytest.approx(0.8)


def test_repeat_rate_ignores_cancelled_and_returned():
    # C1 has 2 valid orders; C2 has 1 valid (the other is cancelled); C3 has none
    assert sl.repeat_rate(orders()) == pytest.approx(1 / 2)


def test_rfm_uses_valid_orders_only():
    g = sl.rfm(orders())
    assert set(g.index) == {"C1", "C2"}  # C3 only has a returned order
    assert g.loc["C1", "frequency"] == 2 and g.loc["C2", "frequency"] == 1
    assert g.loc["C1", "monetary"] == pytest.approx(245.0)
    # reference day is the day after the last order in the data (2024-12-30 -> 2024-12-31)
    assert g.loc["C1", "recency"] == (pd.Timestamp("2024-12-31") - pd.Timestamp("2024-06-01")).days


def test_rfm_scores_are_between_1_and_5_on_larger_data():
    import numpy as np
    rng = np.random.default_rng(0)
    n = 500
    df = pd.DataFrame({
        "OrderID": [f"O{i}" for i in range(n)],
        "OrderDate": pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 300, n), unit="D"),
        "CustomerID": [f"C{i}" for i in rng.integers(0, 120, n)],
        "TotalAmount": rng.uniform(10, 500, n), "IsLost": False})
    g = sl.rfm(df)
    for col in "RFM":
        assert g[col].between(1, 5).all()
    assert set(g["segment"]) <= {"Champions", "Loyal", "Recent", "At risk", "Lost", "Needs attention"}
    # every score level is used (scores are rank based)
    assert g["R"].nunique() == 5 and g["M"].nunique() == 5


@pytest.mark.parametrize("r,f,expected", [(5, 5, "Champions"), (2, 4, "Loyal"), (5, 1, "Recent"), (1, 3, "At risk"), (1, 1, "Lost"), (3, 2, "Needs attention")])
def test_segment_rules(r, f, expected):
    assert sl.segment(r, f) == expected


def test_segment_table_shares_sum_to_one():
    t = sl.segment_table(sl.rfm(orders()))
    assert t["share_of_value"].sum() == pytest.approx(1.0)


def test_discount_table():
    t = sl.discount_table(orders())
    assert t.loc[0.0, "orders"] == 4 and t.loc[0.1, "orders"] == 1
    assert t["share_of_orders"].sum() == pytest.approx(1.0)
    assert t.loc[0.1, "avg_order_value"] == pytest.approx(45.0)


def test_cube_sums_back_to_totals():
    df = orders()
    c = sl.cube(df)
    assert c["orders"].sum() == len(df)
    assert c["value"].sum() == pytest.approx(df["TotalAmount"].sum())


def test_weekday_profile_has_all_days():
    p = sl.weekday_profile(orders())
    assert list(p.index)[0] == "Monday" and len(p) == 7
    assert p.fillna(0).sum() == 5


def test_real_data_headline_numbers():
    from pathlib import Path
    df = sl.load_orders(Path(__file__).parent.parent / "Amazon.csv")
    assert len(df) == 100_000
    assert df["TotalAmount"].sum() == pytest.approx(91_825_647.92, abs=0.01)
    assert sl.check_totals(df) == 1.0
    assert df["CustomerID"].nunique() == 43_233
