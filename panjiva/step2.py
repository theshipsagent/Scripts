import os
import re
import pandas as pd
import traceback
from datetime import datetime

# Hardcoded paths
INPUT_FILE = r"/Output/merged_raw.csv"  # <-- update to latest raw if needed
OUTPUT_DIR = r"/Output"
BERTH_DICT_PATH = r"/berthdictionary.csv"

# Ensure output dir exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Vessel names to exclude (case-insensitive)
EXCLUDE_NAMES = {
    "allisonk", "allins k", "keeneland", "chesapeake bay", "jadwin discharge",
    "dixie raider", "mack b", "texas star", "dodge island", "ginny lab",
    "kennington", "randy martin", "white star"
}

def stamp(message: str):
    """Print timestamped messages to console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_input_file():
    """Load the designated merged_raw file."""
    try:
        df = pd.read_csv(INPUT_FILE, dtype=str)  # keep all as string
        stamp(f"Loaded {INPUT_FILE}: {len(df)} rows")
        return df
    except Exception as e:
        stamp(f"ERROR reading {INPUT_FILE}: {e}")
        traceback.print_exc()
        raise

def standardize_data(df):
    """Standardize IMO, Name, Action, and parse Time. Apply exclusions."""
    df = df.copy()
    df["IMO"] = df["IMO"].astype(str).str[:7]
    df["Name"] = df["Name"].astype(str).str.strip()

    # Exclusion (case-insensitive)
    df["NameLower"] = df["Name"].str.lower()
    before = len(df)
    df = df[~df["NameLower"].isin(EXCLUDE_NAMES)].copy()
    after = len(df)
    stamp(f"Excluded {before - after} rows based on vessel exclusion list")

    # Normalize Action for case-insensitive matching
    df["ActionLower"] = df["Action"].astype(str).str.lower()
    df["TimeParsed"] = pd.to_datetime(df["Time"], errors="coerce")
    return df

def align_events(df):
    """Arrive/Depart pairing with SWP handling. Case-insensitive actions."""
    aligned_rows = []
    counter = 1
    df_sorted = df.sort_values(by=["IMO", "TimeParsed", "Zone"]).copy()

    for (imo, zone), group in df_sorted.groupby(["IMO", "Zone"], dropna=False):
        group = group.reset_index(drop=True)
        i = 0
        while i < len(group):
            row = group.iloc[i]
            action = row["ActionLower"]
            zone_lower = str(zone).strip().lower()
            mmYY = row["TimeParsed"].strftime("%m%y") if pd.notna(row["TimeParsed"]) else "NA"

            # SWP Cross logic
            if zone_lower == "swp cross":
                if action == "enter":
                    aligned_rows.append({
                        "PairID": f"Pair_{counter:06d}_{imo}_{mmYY}",
                        "IMO": imo, "Name": row["Name"], "Zone": zone,
                        "Agent": row.get("Agent", None), "Type": row.get("Type", None),
                        "Draft": row.get("Draft", None), "Mile": row.get("Mile", None),
                        "ArriveTime": row["TimeParsed"], "DepartTime": None,
                        "SourceFile": row["SourceFile"], "MatchStatus": "SWP_EnterExit"
                    }); counter += 1
                elif action == "exit":
                    aligned_rows.append({
                        "PairID": f"Pair_{counter:06d}_{imo}_{mmYY}",
                        "IMO": imo, "Name": row["Name"], "Zone": zone,
                        "Agent": row.get("Agent", None), "Type": row.get("Type", None),
                        "Draft": row.get("Draft", None), "Mile": row.get("Mile", None),
                        "ArriveTime": None, "DepartTime": row["TimeParsed"],
                        "SourceFile": row["SourceFile"], "MatchStatus": "SWP_EnterExit"
                    }); counter += 1
                i += 1
                continue

            # Arrive/Depart pairing
            if action == "arrive":
                depart_time, depart_index = None, None
                for j in range(i+1, len(group)):
                    if group.iloc[j]["ActionLower"] == "depart":
                        depart_time, depart_index = group.iloc[j]["TimeParsed"], j
                        break

                if depart_time is not None:
                    aligned_rows.append({
                        "PairID": f"Pair_{counter:06d}_{imo}_{mmYY}",
                        "IMO": imo, "Name": row["Name"], "Zone": zone,
                        "Agent": row.get("Agent", None), "Type": row.get("Type", None),
                        "Draft": row.get("Draft", None), "Mile": row.get("Mile", None),
                        "ArriveTime": row["TimeParsed"], "DepartTime": depart_time,
                        "SourceFile": row["SourceFile"], "MatchStatus": "Matched"
                    }); counter += 1
                    i = depart_index + 1
                    continue
                else:
                    aligned_rows.append({
                        "PairID": f"Mismatch_{counter:06d}_{imo}_{mmYY}",
                        "IMO": imo, "Name": row["Name"], "Zone": zone,
                        "Agent": row.get("Agent", None), "Type": row.get("Type", None),
                        "Draft": row.get("Draft", None), "Mile": row.get("Mile", None),
                        "ArriveTime": row["TimeParsed"], "DepartTime": None,
                        "SourceFile": row["SourceFile"], "MatchStatus": "Mismatch_Arrive"
                    }); counter += 1; i += 1; continue

            elif action == "depart":
                aligned_rows.append({
                    "PairID": f"Mismatch_{counter:06d}_{imo}_{mmYY}",
                    "IMO": imo, "Name": row["Name"], "Zone": zone,
                    "Agent": row.get("Agent", None), "Type": row.get("Type", None),
                    "Draft": row.get("Draft", None), "Mile": row.get("Mile", None),
                    "ArriveTime": None, "DepartTime": row["TimeParsed"],
                    "SourceFile": row["SourceFile"], "MatchStatus": "Mismatch_Depart"
                }); counter += 1; i += 1

            else:
                aligned_rows.append({
                    "PairID": f"Mismatch_{counter:06d}_{imo}_{mmYY}",
                    "IMO": imo, "Name": row["Name"], "Zone": zone,
                    "Agent": row.get("Agent", None), "Type": row.get("Type", None),
                    "Draft": row.get("Draft", None), "Mile": row.get("Mile", None),
                    "ArriveTime": None, "DepartTime": None,
                    "SourceFile": row["SourceFile"], "MatchStatus": "Other"
                }); counter += 1; i += 1

    stamp(f"Aligned {len(aligned_rows)} events total")
    return pd.DataFrame(aligned_rows)

def normalize_zone(value: str) -> str:
    """Normalize zone name: lowercase, strip, remove punctuation, collapse spaces."""
    if pd.isna(value):
        return ""
    val = value.lower()
    val = re.sub(r"[^\w\s]", "", val)       # remove punctuation
    val = re.sub(r"\s+", " ", val)          # collapse spaces
    return val.strip()

def enrich_with_facility(aligned_df):
    """Fuzzy, case-insensitive zone merge with berth dictionary, keep dict formatting."""
    berth_dict = pd.read_csv(BERTH_DICT_PATH, dtype=str)
    aligned_df["ZoneKey"] = aligned_df["Zone"].apply(normalize_zone)
    berth_dict["ZoneKey"] = berth_dict["Zone"].apply(normalize_zone)

    merged = aligned_df.merge(
        berth_dict[["ZoneKey", "Facility", "Type"]],
        on="ZoneKey", how="left"
    )
    merged = merged.drop(columns=["ZoneKey"])
    return merged

def save_output(aligned_df):
    suffix = datetime.now().strftime("%m%d%y%H%M")
    aligned_path = os.path.join(OUTPUT_DIR, f"merged_aligned_v2_{suffix}.csv")
    aligned_df.to_csv(aligned_path, index=False)
    stamp(f"Aligned merged file saved: {aligned_path}")

def main():
    stamp("=== Starting Align + Enrich Script (Step 2) ===")
    raw_df = load_input_file()
    raw_df = standardize_data(raw_df)
    aligned_df = align_events(raw_df)
    aligned_df = enrich_with_facility(aligned_df)
    save_output(aligned_df)
    stamp("=== Script Complete ===")

if __name__ == "__main__":
    main()
