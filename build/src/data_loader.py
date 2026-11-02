import pandas as pd
from .config import RAW, RAW_TO_SPEC, SUBREGION_MAP

def load_raw(path=RAW) -> pd.DataFrame:
    """Ingest the CSV, align headers to the project spec and alias the CBD subregion."""
    df = pd.read_csv(path)
    df = df.rename(columns=RAW_TO_SPEC)
    df["Subregion_Raw"] = df["Subregion"]
    df["Subregion"] = df["Subregion"].replace(SUBREGION_MAP)
    return df
