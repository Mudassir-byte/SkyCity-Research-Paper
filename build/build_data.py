"""Preprocess the CSV (rename, alias, true shares, validation, KPIs, risk tiers) and postprocess into js/data.js.
Run: python build/build_data.py   (needs pandas, numpy)"""
import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
from src.config import *
from src.data_loader import load_raw
from src.validation import validate
from src.kpis import *
raw = load_raw(); checks, anomalies = validate(raw); df = flag_risk(add_kpis(raw))
SEG = ["Full-service", "Cafe", "QSR", "Ghost Kitchen"]; r4 = lambda x: round(float(x), 6)
ct = channel_table(df); fs = df[df.Segment == "Full-service"]; arev = lambda x: x[REV["Uber Eats"]] + x[REV["DoorDash"]]
D = {"venues": len(df), "orders": int(df.MonthlyOrders.sum()), "revenue": r4(df.TotalRevenue.sum()), "profit": r4(df.TotalNetProfit.sum()),
     "channels": {c: {"orders": int(ct.Orders[c]), "rev": r4(ct.Revenue[c]), "profit": r4(ct.NetProfit[c]), "os": r4(ct.OrderShare[c]), "ps": r4(ct.ProfitShare[c]), "margin": r4(ct.Margin[c])} for c in CHANNELS},
     "agg_os": r4(ct.loc[AGGREGATORS, "OrderShare"].sum()), "agg_ps": r4(ct.loc[AGGREGATORS, "ProfitShare"].sum()), "agg_margin": r4(ct.loc[AGGREGATORS, "NetProfit"].sum() / ct.loc[AGGREGATORS, "Revenue"].sum()),
     "direct_ps": r4(ct.loc[["In-Store", "Self-Delivery"], "ProfitShare"].sum()), "subregions": {}, "cuisines": [], "segments": {}, "venueRows": [],
     "fs": {"venues": len(fs), "agg_profit": r4(fs.Agg_NetProfit.sum()), "agg_margin": r4(fs.Agg_NetProfit.sum() / arev(fs).sum()), "sd_margin": r4(fs[PRF["Self-Delivery"]].sum() / fs[REV["Self-Delivery"]].sum())},
     "comm": {"min": r4(df.CommissionRate.min()), "max": r4(df.CommissionRate.max()), "wtd": r4((arev(df) * df.CommissionRate).sum() / arev(df).sum()), "monthly": r4((arev(df) * df.CommissionRate).sum())},
     "sdCostMax": r4((df.DeliveryCostOrder / df.AOV).max()), "checks": [[n, ok, d] for n, ok, d in checks], "anomalies": anomalies,
     "risk": {"combined_ge_70": int((df.ADI_Total >= .7).sum()), "single_ge_70": int((df.Single_Agg_Max >= .7).sum()), "single_max": r4(df.Single_Agg_Max.max()), "tier2": int(df.Tier2.sum()), "tier2_other": int(df[df.Segment != "Full-service"].Tier2.sum()), "defaults": [TIER1_COMBINED, TIER1_SINGLE]}}
st = group_table(df, "Subregion")
for s, row in st.iterrows():
    g = df[df.Subregion == s]; assert g.GrowthFactor.nunique() == 1; gf = float(g.GrowthFactor.iloc[0])
    D["subregions"][s] = {"venues": int(row.Venues), "orders": int(row.Orders), "gf": gf, "share": {c: r4(row[f"Share_{TAG[c]}"]) for c in CHANNELS}, "margin": {c: r4(row[f"Margin_{TAG[c]}"]) for c in CHANNELS},
                          "proj": [round(float((g.MonthlyOrders * gf ** m).sum()), 1) for m in range(13)]}
for c, g in df.groupby("CuisineType"):
    dl = g.DeliveryOrders.sum(); D["cuisines"].append({"name": c, "venues": len(g), "aggDel": r4((g[ORD["Uber Eats"]].sum() + g[ORD["DoorDash"]].sum()) / dl), "sdDel": r4(g[ORD["Self-Delivery"]].sum() / dl), "aggAll": r4((g[ORD["Uber Eats"]].sum() + g[ORD["DoorDash"]].sum()) / g.MonthlyOrders.sum())})
sg = group_table(df, "Segment")
for s in SEG: D["segments"][s] = {"venues": int(sg.Venues[s]), "tier2": int(df[df.Segment == s].Tier2.sum()), "margin": {c: r4(sg.loc[s, f"Margin_{TAG[c]}"]) for c in CHANNELS}}
D["venueRows"] = [[SEG.index(a), round(float(b), 4), round(float(c), 4), int(t)] for a, b, c, t in zip(df.Segment, df.ADI_Total, df.Single_Agg_Max, df.Tier2)]
# scenario precompute: gain is linear in shift; cap saving is linear in (1 - shift)
G = {t: float(sum((df[ORD[a]] * (df[PRF[t]] / df[ORD[t]] - df[PRF[a]] / df[ORD[a]])).sum() for a in AGGREGATORS)) for t in ("Self-Delivery", "In-Store")}
caps = {f"{c/100:.2f}": float(((df.CommissionRate - c / 100).clip(lower=0) * arev(df)).sum()) for c in range(15, 34)}
D["sim"] = {"base": r4(df.TotalNetProfit.sum()), "G": G, "caps": caps, "aggOrders": int(df[[ORD[a] for a in AGGREGATORS]].sum().sum())}
for sh, t, cp in ((0.15, "Self-Delivery", None), (0.15, "In-Store", .2), (0.3, "Self-Delivery", .25), (0, "Self-Delivery", .2)):   # JS formula must equal the Python simulator
    py = simulate(df, sh, t, cp); js = sh * G[t] + ((1 - sh) * caps[f"{cp:.2f}"] if cp else 0); assert abs(py["shift_gain"] + py["cap_gain"] - js) < 1e-3, (sh, t, cp)
(ROOT.parent / "js/data.js").write_text("window.PAPER_DATA=" + json.dumps(D, separators=(",", ":"), default=float) + ";", encoding="utf8")
print("ok", len(df), "rows; checks passed:", sum(ok for _, ok, _ in checks), "/", len(checks))
