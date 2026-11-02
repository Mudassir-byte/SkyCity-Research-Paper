import numpy as np, pandas as pd
from .config import *

def add_true_shares(df):
    """Shares of MonthlyOrders (sum to 1). Raw delivery-only shares are kept untouched."""
    df = df.copy()
    for ch in CHANNELS: df[f"True_{TAG[ch]}_Share"] = df[ORD[ch]] / df["MonthlyOrders"]
    df["DeliveryOrders"] = df[[ORD[c] for c in CHANNELS[1:]]].sum(axis=1)
    return df

def add_kpis(df):
    df = add_true_shares(df)
    s = df[[f"True_{TAG[c]}_Share" for c in CHANNELS]]
    df["ADI_Total"] = df["True_UE_Share"] + df["True_DD_Share"]            # aggregator share of all orders
    df["ADI_Delivery"] = (df[ORD["Uber Eats"]] + df[ORD["DoorDash"]]) / df["DeliveryOrders"]
    df["IRR"] = df["True_InStore_Share"]                                    # In-Store Reliance Ratio
    hhi = (s ** 2).sum(axis=1); df["HHI"] = hhi
    df["CDS"] = 100 * (1 - (hhi - 0.25) / 0.75)                             # Diversification Score 0-100
    df["Single_Agg_Max"] = df[["True_UE_Share", "True_DD_Share"]].max(axis=1)
    inv = {f"True_{v}_Share": k for k, v in TAG.items()}
    df["Dominant_Order_Channel"] = s.idxmax(axis=1).map(inv)
    df["TotalRevenue"] = df[list(REV.values())].sum(axis=1)
    df["TotalNetProfit"] = df[list(PRF.values())].sum(axis=1)
    df["NetMargin"] = df["TotalNetProfit"] / df["TotalRevenue"]
    df["Agg_NetProfit"] = df[PRF["Uber Eats"]] + df[PRF["DoorDash"]]
    return df

def flag_risk(df, combined=TIER1_COMBINED, single=TIER1_SINGLE):
    df = df.copy()
    df["Tier1"] = (df["ADI_Total"] >= combined) | (df["Single_Agg_Max"] >= single)
    df["Tier2"] = (df[PRF["Uber Eats"]] < 0) & (df[PRF["DoorDash"]] < 0)
    df["LossOnEither"] = (df[PRF["Uber Eats"]] < 0) | (df[PRF["DoorDash"]] < 0)
    df["Risk"] = np.select([df.Tier1 & df.Tier2, df.Tier1, df.Tier2], ["Tier 1 + Tier 2", "Tier 1", "Tier 2"], "Balanced")
    return df

def channel_table(df):
    o = {c: df[ORD[c]].sum() for c in CHANNELS}; r = {c: df[REV[c]].sum() for c in CHANNELS}; p = {c: df[PRF[c]].sum() for c in CHANNELS}
    t = pd.DataFrame({"Orders": o, "Revenue": r, "NetProfit": p})
    t["OrderShare"] = t.Orders / t.Orders.sum(); t["RevenueShare"] = t.Revenue / t.Revenue.sum()
    t["ProfitShare"] = t.NetProfit / t.NetProfit.sum(); t["Margin"] = t.NetProfit / t.Revenue
    return t

def group_table(df, by):
    g = df.groupby(by, observed=True)
    out = pd.DataFrame({"Venues": g.size(), "Orders": g["MonthlyOrders"].sum(), "Revenue": g["TotalRevenue"].sum(),
                        "NetProfit": g["TotalNetProfit"].sum(), "GrowthFactor": g["GrowthFactor"].mean(),
                        "ADI_Total": (g[ORD["Uber Eats"]].sum() + g[ORD["DoorDash"]].sum()) / g["MonthlyOrders"].sum(),
                        "IRR": g[ORD["In-Store"]].sum() / g["MonthlyOrders"].sum(),
                        "SD_Share": g[ORD["Self-Delivery"]].sum() / g["MonthlyOrders"].sum(),
                        "CDS": g["CDS"].mean(), "AggNetProfit": g["Agg_NetProfit"].sum()})
    for c in CHANNELS: out[f"Share_{TAG[c]}"] = g[ORD[c]].sum() / g["MonthlyOrders"].sum()
    for c in CHANNELS: out[f"Margin_{TAG[c]}"] = g[PRF[c]].sum() / g[REV[c]].sum()
    out["NetMargin"] = out.NetProfit / out.Revenue
    return out

def share_matrix(df, by, basis="total"):
    """Rows = groups, cols = channels. basis 'total' = share of all orders; 'delivery' = share of delivery orders."""
    g = df.groupby(by, observed=True)[[ORD[c] for c in CHANNELS]].sum(); g.columns = CHANNELS
    if basis == "delivery": g = g[CHANNELS[1:]]
    return g.div(g.sum(axis=1), axis=0)

def dominance(df):
    """Subregion Channel Dominance KPI: leading channel by orders and by net profit."""
    ct = {s: channel_table(g) for s, g in df.groupby("Subregion")}
    return pd.DataFrame({"Top_Order_Channel": {s: t.Orders.idxmax() for s, t in ct.items()},
                         "Top_Order_Share": {s: t.OrderShare.max() for s, t in ct.items()},
                         "Top_Profit_Channel": {s: t.NetProfit.idxmax() for s, t in ct.items()},
                         "Top_Profit_Share": {s: t.ProfitShare.max() for s, t in ct.items()}})

def projection(df, months=(6, 12)):
    """Order volume if each subregion's month-over-month GrowthFactor held constant (scenario, not a forecast)."""
    out = pd.DataFrame({"Now": df.groupby("Subregion").MonthlyOrders.sum()})
    for m in months: out[f"M{m}"] = (df.MonthlyOrders * df.GrowthFactor ** m).groupby(df.Subregion).sum()
    out["Change12"] = out["M12"] / out["Now"] - 1
    return out

def simulate(df, shift=SIM_SHIFT, target="Self-Delivery", cap=None):
    """Move `shift` of aggregator orders to `target` at each venue's own per-order profit; optionally cap commission."""
    base = df[list(PRF.values())].sum().sum(); pt = df[PRF[target]] / df[ORD[target]]; gain = 0.0
    for a in AGGREGATORS: gain = gain + (shift * df[ORD[a]] * (pt - df[PRF[a]] / df[ORD[a]])).sum()
    cap_gain = 0.0
    if cap is not None:
        arev = df[REV["Uber Eats"]] + df[REV["DoorDash"]]
        cap_gain = ((df.CommissionRate - cap).clip(lower=0) * arev * (1 - shift)).sum()
    return {"baseline": base, "shift_gain": gain, "cap_gain": cap_gain, "new_profit": base + gain + cap_gain,
            "pct_change": (gain + cap_gain) / base, "orders_moved": shift * df[[ORD[a] for a in AGGREGATORS]].sum().sum()}

def breakeven_share(df, cap):
    """Share of venues whose aggregator margin is >= 0 if commission were `cap` (margin before commission = 1-COGS-OPEX)."""
    return float(((1 - df.COGSRate - df.OPEXRate) >= cap).mean())
