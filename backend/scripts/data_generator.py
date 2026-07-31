import csv
import random
import uuid
import math
import os

# --- Configuration ---
NUM_FEEDERS = 5
NUM_DTS = 40
POLES_PER_DT_RANGE = (40, 100) # Aiming for ~2,800 poles total
MISSING_TOPOLOGY_PERCENTAGE = 0.60
MISSING_DEVICE_PERCENTAGE = 0.09
BASE_LAT = 12.9680
BASE_LON = 77.5940

def generate_feeders():
    return [f"F-07-{i:02d}" for i in range(1, NUM_FEEDERS + 1)]

def generate_dts(feeders):
    dts = []
    # 60% missing topology
    num_missing = int(NUM_DTS * MISSING_TOPOLOGY_PERCENTAGE)
    topology_flags = [False] * num_missing + [True] * (NUM_DTS - num_missing)
    random.shuffle(topology_flags)

    for i in range(1, NUM_DTS + 1):
        dt_id = f"D-{i:04d}"
        feeder_id = random.choice(feeders)
        # Scatter DTs around base location (approx 0.01 deg is ~1km)
        lat = BASE_LAT + random.uniform(-0.02, 0.02)
        lon = BASE_LON + random.uniform(-0.02, 0.02)
        capacity = random.choice([100, 250, 500])
        houses = int(capacity * random.uniform(1.0, 1.5))
        has_topology = topology_flags[i-1]
        dts.append({
            "dt_id": dt_id,
            "feeder_id": feeder_id,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "capacity_kva": capacity,
            "households_served": houses,
            "_has_topology": has_topology
        })
    return dts

def generate_poles_for_dt(dt, start_pole_idx):
    poles = []
    num_poles = random.randint(POLES_PER_DT_RANGE[0], POLES_PER_DT_RANGE[1])
    has_topology = dt["_has_topology"]
    
    dt_lat = dt["lat"]
    dt_lon = dt["lon"]
    
    # We will build a simple tree structure physically starting from the DT
    # Node 0 is the DT (implicitly).
    # parent_map[i] will store the index of the parent of pole i.
    parent_map = {}
    
    for i in range(num_poles):
        pole_idx = start_pole_idx + i
        pole_id = f"P-{pole_idx:06d}"
        
        # Decide parent to form a tree.
        # Pole 0 connects to DT (no parent pole).
        # Pole i connects to some random pole j where j < i.
        if i == 0:
            parent_idx = None
            parent_pole_id = ""
            seq_on_line = 1
            # Coordinate slightly offset from DT
            plat = dt_lat + random.uniform(-0.0005, 0.0005)
            plon = dt_lon + random.uniform(-0.0005, 0.0005)
        else:
            # Pick a parent pole to branch off
            parent_idx = random.randint(max(0, i-5), i-1) # Long lines, occasional branching
            parent_pole = poles[parent_idx]
            parent_pole_id = parent_pole["pole_id"]
            seq_on_line = parent_pole["_seq_on_line"] + 1
            # Coordinate slightly offset from parent
            plat = parent_pole["lat"] + random.uniform(-0.0002, 0.0002)
            plon = parent_pole["lon"] + random.uniform(-0.0002, 0.0002)
        
        # Hardware logic
        has_device = random.random() > MISSING_DEVICE_PERCENTAGE
        device_id = f"KSPDB-SD07-{dt['dt_id']}-{pole_idx}" if has_device else ""
        
        pole = {
            "pole_id": pole_id,
            "lat": round(plat, 6),
            "lon": round(plon, 6),
            "feeder_id": dt["feeder_id"],
            "dt_id": dt["dt_id"],
            "seq_on_line": seq_on_line if has_topology else "",
            "_seq_on_line": seq_on_line,
            "parent_pole_id": parent_pole_id if has_topology else "",
            "_parent_pole_id": parent_pole_id,
            "pole_type": random.choice(["LT-8m-PCC", "LT-9m-PCC", "LT-8m-Steel"]),
            "ward": f"W-{random.randint(10, 99)}",
            "pincode": 560078 if random.random() > 0.03 else "", # 3% missing pincode
            "device_id": device_id
        }
        poles.append(pole)
        
    return poles, start_pole_idx + num_poles

def main():
    feeders = generate_feeders()
    dts = generate_dts(feeders)
    
    all_poles = []
    current_pole_idx = 1
    
    for dt in dts:
        dt_poles, current_pole_idx = generate_poles_for_dt(dt, current_pole_idx)
        all_poles.extend(dt_poles)
        
    print(f"Generated {len(dts)} DTs and {len(all_poles)} Poles.")
    
    # Write DTs
    dt_path = os.path.join(os.path.dirname(__file__), '../data/dts.csv')
    with open(dt_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["dt_id", "feeder_id", "lat", "lon", "capacity_kva", "households_served"])
        writer.writeheader()
        for dt in dts:
            dt_clean = {k: v for k, v in dt.items() if not k.startswith('_')}
            writer.writerow(dt_clean)
            
    # Write Ground Truth Poles (for Simulator only)
    ground_truth_path = os.path.join(os.path.dirname(__file__), '../data/ground_truth_poles.csv')
    with open(ground_truth_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["pole_id", "lat", "lon", "feeder_id", "dt_id", "seq_on_line", "parent_pole_id", "pole_type", "ward", "pincode", "device_id"])
        writer.writeheader()
        for p in all_poles:
            p_gt = {k: v for k, v in p.items() if not k.startswith('_')}
            p_gt["seq_on_line"] = p.get("_seq_on_line", "")
            p_gt["parent_pole_id"] = p.get("_parent_pole_id", "")
            writer.writerow(p_gt)

    # Write Poles (for Control Room)
    pole_path = os.path.join(os.path.dirname(__file__), '../data/poles.csv')
    with open(pole_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["pole_id", "lat", "lon", "feeder_id", "dt_id", "seq_on_line", "parent_pole_id", "pole_type", "ward", "pincode", "device_id"])
        writer.writeheader()
        for p in all_poles:
            p_clean = {k: v for k, v in p.items() if not k.startswith('_')}
            writer.writerow(p_clean)

    print(f"Data saved to {os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))}")

if __name__ == "__main__":
    main()
