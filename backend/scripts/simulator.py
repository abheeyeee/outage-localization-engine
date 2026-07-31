import csv
import os
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict
import urllib.request
import json

# Configuration for simulation
API_URL = "http://localhost:8000/telemetry" # Where we will post data later
FIRMWARE_V1_2_RATE = 0.08  # 8% never send dying gasp
CAPACITOR_SUCCESS_RATE = 0.70 # 70% success if not on v1.2
CLOCK_SKEW_SECONDS = 90

class Simulator:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.dts = {}
        self.poles = {}
        self.children_map = {} # parent_id -> list of child_ids
        
        self.load_data()
        self.build_topology()

    def load_data(self):
        # Load DTs
        dt_path = os.path.join(self.data_dir, 'dts.csv')
        with open(dt_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.dts[row['dt_id']] = row
                
        # Load Ground Truth Poles
        gt_path = os.path.join(self.data_dir, 'ground_truth_poles.csv')
        with open(gt_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.poles[row['pole_id']] = row

    def build_topology(self):
        for pole_id, pole in self.poles.items():
            parent_id = pole['parent_pole_id']
            if not parent_id:
                parent_id = pole['dt_id'] # Connect directly to DT
            
            if parent_id not in self.children_map:
                self.children_map[parent_id] = []
            self.children_map[parent_id].append(pole_id)

    def get_all_downstream_poles(self, start_id: str) -> List[Dict]:
        """ Recursively find all poles downstream of a given node (DT or Pole) """
        downstream = []
        queue = [start_id]
        
        while queue:
            current = queue.pop(0)
            # If current is a pole, add it to our affected list
            if current in self.poles and current != start_id:
                downstream.append(self.poles[current])
            
            # Add its children to the queue
            if current in self.children_map:
                queue.extend(self.children_map[current])
                
        # If the start_id was a pole itself (e.g. span fault just above it), it is also affected
        if start_id in self.poles:
            downstream.append(self.poles[start_id])
            
        return downstream

    def generate_telemetry(self, affected_poles: List[Dict], event_type: str = "power_lost"):
        messages = []
        base_time = datetime.utcnow()
        
        for pole in affected_poles:
            device_id = pole.get('device_id')
            if not device_id:
                continue # 9% of poles have no device
                
            if event_type == "power_lost":
                # Enforce physical constraints for power loss
                if random.random() < FIRMWARE_V1_2_RATE:
                    continue # Firmware 1.2 silently dies
                if random.random() > CAPACITOR_SUCCESS_RATE:
                    continue # Capacitor failed to send dying gasp
            
            # Jitter the timestamp
            skew = random.uniform(-CLOCK_SKEW_SECONDS, CLOCK_SKEW_SECONDS)
            event_time = base_time + timedelta(seconds=skew)
            
            # Sequence number (mocked for simulation)
            seq = random.randint(1000, 90000)
            
            messages.append({
                "device_id": device_id,
                "pole_id": pole['pole_id'],
                "event": event_type,
                "energized": False if event_type == "power_lost" else True,
                "ts": event_time.isoformat() + "Z",
                "seq": seq,
                "battery_mv": random.randint(3200, 3800),
                "rssi": random.randint(-100, -50),
                "fw": "1.4.2"
            })
            
        # Sort messages by their scrambled timestamps to simulate network arrival out-of-order
        messages.sort(key=lambda x: x['ts'])
        return messages

    def inject_span_fault(self, parent_id: str, child_id: str):
        print(f"--- INJECTING SPAN FAULT between {parent_id} and {child_id} ---")
        affected = self.get_all_downstream_poles(child_id)
        print(f"Physical Reality: {len(affected)} poles instantly lost power.")
        
        telemetry = self.generate_telemetry(affected, "power_lost")
        print(f"Telemetry Generated: Only {len(telemetry)} messages successfully sent.")
        
        for msg in telemetry[:5]:
            print(msg)
        if len(telemetry) > 5:
            print(f"... and {len(telemetry) - 5} more.")
            
        return telemetry

    def inject_dt_fault(self, dt_id: str):
        print(f"--- INJECTING DT FAULT on Transformer {dt_id} ---")
        affected = self.get_all_downstream_poles(dt_id)
        return self.generate_telemetry(affected, "power_lost")

    def inject_feeder_fault(self, feeder_id: str):
        print(f"--- INJECTING FEEDER FAULT on Feeder {feeder_id} ---")
        dt_ids = [dt for dt, data in self.dts.items() if data.get('feeder_id') == feeder_id]
        affected = []
        for dt_id in dt_ids:
            affected.extend(self.get_all_downstream_poles(dt_id))
        return self.generate_telemetry(affected, "power_lost")

    def post_telemetry(self, telemetry: List[Dict]):
        print(f"\n--- POSTING TELEMETRY TO API ({API_URL}) ---")
        try:
            req = urllib.request.Request(
                API_URL, 
                data=json.dumps(telemetry).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode('utf-8')
                print("API Response:", res_body)
        except Exception as e:
            print(f"Failed to post telemetry to API: {e}")

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), '../data')
    sim = Simulator(data_dir)
    
    # Pick a random pole that has children to simulate a mid-line span fault
    poles_with_children = [p for p in sim.children_map.keys() if p.startswith("P-")]
    if poles_with_children:
        parent = random.choice(poles_with_children)
        child = sim.children_map[parent][0]
        telemetry = sim.inject_span_fault(parent, child)
        sim.post_telemetry(telemetry)
