import argparse
import os
import glob
import ast
import pandas as pd
from demoparser2 import DemoParser

# --- CONFIGURATION ---
# 0=Primary, 1=Pistol, 2=Zeus, 3=Nades, 4=Gear
BUCKETS = {
    # RANK 0: PRIMARIES
    "AK-47": 0, "M4A4": 0, "M4A1-S": 0, "AWP": 0, "G3SG1": 0, "SCAR-20": 0,
    "Galil AR": 0, "FAMAS": 0, "AUG": 0, "SG 553": 0, "SSG 08": 0,
    "MAC-10": 0, "MP9": 0, "MP7": 0, "MP5-SD": 0, "UMP-45": 0, "P90": 0, "PP-Bizon": 0,
    "XM1014": 0, "MAG-7": 0, "Nova": 0, "Sawed-Off": 0, "Negev": 0, "M249": 0,
    "Riot Shield": 0,

    # RANK 1: PISTOLS
    "Desert Eagle": 1, "R8 Revolver": 1, "CZ75-Auto": 1, "Five-SeveN": 1, 
    "Tec-9": 1, "P250": 1, "Dual Berettas": 1,
    "Glock-18": 1, "USP-S": 1, "P2000": 1,

    # RANK 2: MELEE / ZEUS
    "Zeus x27": 2,

    # RANK 3: GRENADES
    "Molotov": 3, "Incendiary Grenade": 3, "High Explosive Grenade": 3,
    "Flashbang": 3, "Smoke Grenade": 3, "Decoy Grenade": 3,

    # RANK 4: EQUIPMENT
    "Defuse Kit": 4, "Kevlar": 4, "Kevlar + Helmet": 4
}

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", required=True)
    parser.add_argument("-n", "--name", required=True)
    return parser.parse_args()

def get_bucket(item_name):
    return BUCKETS.get(item_name, 99)

def process_inventory(inv_list):
    if not inv_list: return "Knife Only / Dead"
    unique = list(set(inv_list))
    
    # Initialize Buckets
    sorted_buckets = {0: [], 1: [], 2: [], 3: [], 4: [], 99: []}
    
    for item in unique:
        # FILTER: Junk, Knife, and C4
        if any(x in item for x in ["Knife", "Bayonet", "Karambit", "Charm", "Tag", "C4"]):
            continue
            
        b_id = get_bucket(item)
        sorted_buckets[b_id].append(item)
        
    # Sort inside buckets
    for b in sorted_buckets:
        sorted_buckets[b].sort()
        
    # Flatten
    final = (sorted_buckets[0] + sorted_buckets[1] + sorted_buckets[2] + 
             sorted_buckets[3] + sorted_buckets[4])
    
    return ", ".join(final) if final else "Knife Only"

def is_strong_loadout(inv_list):
    for item in inv_list:
        b_id = get_bucket(item)
        if b_id == 0: return True 
        if b_id == 1 and item not in ["Glock-18", "USP-S", "P2000"]:
            return True
    return False

def extract_ticks_robust(events):
    ticks = []
    if isinstance(events, pd.DataFrame):
        if 'tick' in events.columns:
            return events['tick'].dropna().astype(int).tolist()
    if isinstance(events, list):
        for item in events:
            if isinstance(item, tuple) and len(item) > 1:
                data = item[1]
                if isinstance(data, pd.DataFrame) and 'tick' in data.columns:
                    ticks.extend(data['tick'].dropna().astype(int).tolist())
                elif isinstance(data, dict):
                    t = data.get('tick')
                    if t: ticks.append(int(t))
            elif isinstance(item, dict):
                t = item.get('tick')
                if t: ticks.append(int(t))
    return sorted(list(set(ticks)))

def get_players_in_demo(parser):
    """Use item_purchase or player_death events to get player names without triggering EntityNotFound."""
    for event_name in ["player_death", "item_purchase", "round_end"]:
        try:
            raw = parser.parse_events([event_name])
            if isinstance(raw, list) and raw:
                df = raw[0][1] if isinstance(raw[0], tuple) else raw[0]
                for col in ["player_name", "name", "attacker_name"]:
                    if col in df.columns:
                        return set(df[col].dropna().tolist())
        except:
            continue
    return set()

def analyze_demo(file_path, player_name):
    print(f"\n>>> Processing: {os.path.basename(file_path)}")
    try:
        parser = DemoParser(file_path)
        events = parser.parse_events(["round_freeze_end"])
        base_ticks = extract_ticks_robust(events)
        
        if not base_ticks:
            events = parser.parse_events(["round_start"])
            base_ticks = extract_ticks_robust(events)
            
        if not base_ticks:
            print("   [!] No rounds found.")
            return

        # Check player exists without calling parse_ticks (which throws EntityNotFound)
        players = get_players_in_demo(parser)
        if players and player_name not in players:
            print(f"   [!] Player '{player_name}' not found in this demo. Skipping.")
            return

        buy_df = pd.DataFrame()
        try:
            raw_buys = parser.parse_events(["item_purchase"])
            if isinstance(raw_buys, list):
                for item in raw_buys:
                    if len(item) > 1 and isinstance(item[1], pd.DataFrame):
                        buy_df = pd.concat([buy_df, item[1]])
            elif isinstance(raw_buys, pd.DataFrame):
                buy_df = raw_buys
            if not buy_df.empty and 'name' in buy_df.columns:
                buy_df = buy_df[buy_df['name'] == player_name]
        except: pass

        tick_map = {}
        all_query_ticks = []
        for t in base_ticks:
            t_5 = t + (64 * 5)
            t_10 = t + (64 * 10)
            tick_map[t] = [t, t_5, t_10]
            all_query_ticks.extend([t, t_5, t_10])

        try:
            df = parser.parse_ticks(["player_name", "inventory"], ticks=all_query_ticks)
            player_df = df[df['player_name'] == player_name]
        except Exception as e:
            print(f"   [!] Failed to parse ticks: {e}")
            return

        print(f"   --- Loadout for {player_name} ---")
        
        for r_num, base_tick in enumerate(base_ticks, 1):
            candidates = tick_map[base_tick]
            final_inv = []
            found_upgrade = False
            
            round_rows = player_df[player_df['tick'].isin(candidates)].sort_values('tick')
            
            for t in candidates:
                row = round_rows[round_rows['tick'] == t]
                if row.empty: continue
                raw = row.iloc[0]['inventory']
                try: curr = ast.literal_eval(raw) if isinstance(raw, str) else raw
                except: curr = []
                if not isinstance(curr, list): curr = []
                
                if not final_inv: final_inv = curr 
                
                if is_strong_loadout(curr):
                    final_inv = curr
                    found_upgrade = True
                    break
            
            if not found_upgrade and not buy_df.empty:
                limit_tick = base_tick + (64 * 22)
                round_buys = buy_df[(buy_df['tick'] >= base_tick) & (buy_df['tick'] <= limit_tick)]
                if not round_buys.empty:
                    check_tick = int(round_buys['tick'].max() + 64)
                    try:
                        late_data = parser.parse_ticks(["player_name", "inventory"], ticks=[check_tick])
                        late_row = late_data[late_data['player_name'] == player_name]
                        if not late_row.empty:
                            raw = late_row.iloc[0]['inventory']
                            try: curr = ast.literal_eval(raw) if isinstance(raw, str) else raw
                            except: curr = []
                            final_inv = curr if isinstance(curr, list) else []
                    except: pass

            print(f"   Round {r_num}: {process_inventory(final_inv)}")

    except Exception as e:
        print(f"   [!] Error: {e}")

def main():
    args = parse_arguments()
    files = glob.glob(os.path.join(args.path, "*.dem")) if os.path.isdir(args.path) else [args.path]
    for f in files:
        analyze_demo(f, args.name)

if __name__ == "__main__":
    main()