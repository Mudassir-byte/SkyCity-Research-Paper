"""Single source of truth for names, taxonomy and thresholds."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/SkyCity_Auckland_Restaurants_Bars.csv"
PROC = ROOT / "data/processed"

# Raw CSV header -> header used in the Unified Mentor project instructions
RAW_TO_SPEC = {"InStoreOrders": "InStoreOrdersCount", "UberEatsOrders": "UberEatsOrdersCount",
               "DoorDashOrders": "DoorDashOrdersCount", "SelfDeliveryOrders": "SelfDeliveryOrdersCount",
               "DeliveryCostPerOrder": "DeliveryCostOrder"}
# Raw Subregion value -> canonical label (the instructions say "Central Auckland")
SUBREGION_MAP = {"CBD": "Central Auckland (CBD)"}

CHANNELS = ["In-Store", "Uber Eats", "DoorDash", "Self-Delivery"]
AGGREGATORS = ["Uber Eats", "DoorDash"]
TAG = {"In-Store": "InStore", "Uber Eats": "UE", "DoorDash": "DD", "Self-Delivery": "SD"}
ORD = {"In-Store": "InStoreOrdersCount", "Uber Eats": "UberEatsOrdersCount",
       "DoorDash": "DoorDashOrdersCount", "Self-Delivery": "SelfDeliveryOrdersCount"}
REV = {"In-Store": "InStoreRevenue", "Uber Eats": "UberEatsRevenue",
       "DoorDash": "DoorDashRevenue", "Self-Delivery": "SelfDeliveryRevenue"}
PRF = {"In-Store": "InStoreNetProfit", "Uber Eats": "UberEatsNetProfit",
       "DoorDash": "DoorDashNetProfit", "Self-Delivery": "SelfDeliveryNetProfit"}

# Risk-engine defaults. The instruction's 70% single-aggregator rule flags nobody in this
# data (max 58.3% of orders / 60% of delivery), so both thresholds are user-adjustable.
# The 0.45 single-platform default is this project's calibration, not a figure from the brief.
TIER1_COMBINED = 0.70
TIER1_SINGLE = 0.45
# Illustrative scenario defaults for the profit-recovery simulator (adjustable in the app)
SIM_SHIFT = 0.15
SIM_CAP = 0.20
