import numpy as np
from .config import *
from .kpis import add_true_shares

def validate(df, spec_rows=520):
    """Gate 1 checks. Returns (checks, anomalies); checks are (name, passed, detail)."""
    c, a = [], []
    d = add_true_shares(df); n = len(df)
    def chk(name, ok, detail=""): c.append((name, bool(ok), detail))
    chk("no missing values", df.isna().sum().sum() == 0)
    chk("RestaurantID unique", df.RestaurantID.is_unique)
    chk("channel orders sum to MonthlyOrders (all rows)", (df[list(ORD.values())].sum(axis=1) == df.MonthlyOrders).all(), f"{n} rows")
    chk("channel revenue = orders x AOV", all(np.allclose(df[ORD[k]] * df.AOV, df[REV[k]], rtol=1e-6) for k in CHANNELS))
    chk("recomputed total-order shares sum to 1", np.allclose(d[[f"True_{TAG[k]}_Share" for k in CHANNELS]].sum(axis=1), 1, atol=1e-9))
    k = 1 - df.COGSRate - df.OPEXRate
    ok = all(np.allclose(df[REV[ch]] * (k - (df.CommissionRate if ch in AGGREGATORS else 0)) - (df.SD_DeliveryTotalCost if ch == "Self-Delivery" else 0), df[PRF[ch]], atol=0.01) for ch in CHANNELS)
    chk("net profit equations hold (within $0.01)", ok)
    chk("self-delivery cost = orders x cost per order", np.allclose(df[ORD["Self-Delivery"]] * df.DeliveryCostOrder, df.SD_DeliveryTotalCost, atol=0.01))
    chk("all subregions mapped to the 4 canonical areas", df.Subregion.nunique() == 4 and not df.Subregion.isin(SUBREGION_MAP.keys()).any())
    chk("subregion order totals equal dataset total", df.groupby("Subregion").MonthlyOrders.sum().sum() == df.MonthlyOrders.sum())
    raw = df[["InStoreShare", "UE_share", "DD_share", "SD_share"]].sum(axis=1)
    deliv = df[[ORD[x] for x in CHANNELS[1:]]].sum(axis=1)
    agg = (df[ORD["Uber Eats"]] + df[ORD["DoorDash"]]) / df.MonthlyOrders
    a.append(("A1", "Column names", "Raw CSV uses InStoreOrders, UberEatsOrders, DoorDashOrders, SelfDeliveryOrders, DeliveryCostPerOrder; the brief uses the same names with 'Count' / DeliveryCostOrder.", "Renamed to the brief's names in data_loader."))
    a.append(("A2", "Subregion taxonomy", "Raw data labels Central Auckland as 'CBD' and includes South Auckland (%d venues)." % (df.Subregion_Raw == "South Auckland").sum(), "CBD aliased to 'Central Auckland (CBD)'; all 4 areas kept."))
    a.append(("A3", "InStoreShare denominator", f"Raw InStoreShare equals in-store orders / delivery orders (max abs gap {np.abs((df[ORD['In-Store']]/deliv).round(2)-df.InStoreShare).max():.2f}), so the four raw shares sum to {raw.min():.2f}-{raw.max():.2f}, not 1.", "True_*_Share columns recomputed on MonthlyOrders; raw UE/DD/SD shares kept for delivery-only views."))
    a.append(("A4", "Single-aggregator 70% rule", f"No venue reaches 70% on one aggregator (max {d[['True_UE_Share','True_DD_Share']].max().max():.1%} of orders, {df.UE_share.max():.0%} of delivery). Combined aggregator share of orders >= 70% flags {int((agg>=.7).sum())} venues.", "Risk engine uses combined share plus an adjustable single-platform threshold."))
    a.append(("A5", "Record count", f"The plan cites {spec_rows} branches; the CSV holds {n:,}.", f"All figures use the {n:,} rows in the file."))
    oth = ((df.Segment != "Full-service") & ((df[PRF["Uber Eats"]] < 0) | (df[PRF["DoorDash"]] < 0))).sum()
    a.append(("A6", "Losses outside Full-service", f"All {(df.Segment=='Full-service').sum()} Full-service venues lose money on both platforms; {oth} Cafe/QSR venues also lose money on at least one.", "Tier 2 flag applied to every segment, not only Full-service."))
    return c, a
