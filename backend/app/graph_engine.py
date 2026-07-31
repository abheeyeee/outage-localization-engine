import csv
import os
import networkx as nx
import math
from typing import Dict, List, Tuple

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth."""
    R = 6371  # Radius of the earth in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

class GraphEngine:
    def __init__(self, data_dir: str):
        self.graph = nx.DiGraph()
        self.data_dir = data_dir
        self.dts = {}
        self.poles = {}
        self.imputed_dts = set() # Track which DTs had to be guessed
        
        self.load_and_build()

    def load_and_build(self):
        # 1. Load DTs
        dt_path = os.path.join(self.data_dir, 'dts.csv')
        with open(dt_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dt_id = row['dt_id']
                feeder_id = row['feeder_id']
                self.dts[dt_id] = row
                # Add DT as root node
                self.graph.add_node(dt_id, type='dt', lat=float(row['lat']), lon=float(row['lon']), 
                                    is_live=True, feeder_id=feeder_id)

        # 2. Load Poles
        pole_path = os.path.join(self.data_dir, 'poles.csv')
        with open(pole_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pole_id = row['pole_id']
                self.poles[pole_id] = row
                self.graph.add_node(pole_id, type='pole', lat=float(row['lat']), lon=float(row['lon']), 
                                    dt_id=row['dt_id'], is_live=True, seq=int(row.get('seq_on_line') or 0))

        self._connect_poles()
        
    def _connect_poles(self):
        # Group poles by DT to build trees
        dt_to_poles = {dt_id: [] for dt_id in self.dts}
        for pole_id, pole in self.poles.items():
            dt_to_poles[pole['dt_id']].append(pole)

        for dt_id, poles_list in dt_to_poles.items():
            # Check if this DT has topology data by looking at the first pole
            has_topology = any(p['parent_pole_id'] for p in poles_list)
            
            if has_topology:
                # Build deterministic tree
                for p in poles_list:
                    parent_id = p['parent_pole_id']
                    if not parent_id:
                        parent_id = dt_id # Root connects to DT
                    self.graph.add_edge(parent_id, p['pole_id'], is_imputed=False)
            else:
                # SPATIAL IMPUTATION (MST based on geography)
                self.imputed_dts.add(dt_id)
                self._impute_topology_for_dt(dt_id, poles_list)

    def _impute_topology_for_dt(self, dt_id: str, poles_list: List[Dict]):
        """ Use greedy closest-neighbor to build a radial tree from the DT """
        unconnected = set(p['pole_id'] for p in poles_list)
        connected = {dt_id}
        
        while unconnected:
            best_dist = float('inf')
            best_parent = None
            best_child = None
            
            # Find the shortest physical jump from ANY connected node to ANY unconnected node
            for c_node in connected:
                c_lat = self.graph.nodes[c_node]['lat']
                c_lon = self.graph.nodes[c_node]['lon']
                
                for u_node in unconnected:
                    u_lat = self.graph.nodes[u_node]['lat']
                    u_lon = self.graph.nodes[u_node]['lon']
                    
                    dist = haversine_distance(c_lat, c_lon, u_lat, u_lon)
                    if dist < best_dist:
                        best_dist = dist
                        best_parent = c_node
                        best_child = u_node
            
            # Create the imputed wire
            self.graph.add_edge(best_parent, best_child, is_imputed=True)
            connected.add(best_child)
            unconnected.remove(best_child)

    def resolve_implied_states(self):
        """
        Evaluate silent nodes from the bottom up (post-order traversal).
        If ANY child is Live -> Node is Live.
        If ALL children are Dark -> Node is Dark.
        """
        # Get nodes in reverse topological order (leaves to root)
        for node in reversed(list(nx.topological_sort(self.graph))):
            children = list(self.graph.successors(node))
            if children:
                # Check children states
                any_child_live = any(self.graph.nodes[c].get('is_live', True) for c in children)
                all_children_dark = all(not self.graph.nodes[c].get('is_live', True) for c in children)
                
                # Rule 1: The Lying Sensor Override. 
                # If ANY child is live, power MUST be flowing through this node.
                # Even if it explicitly reported it was Dark, we override it to Live.
                if any_child_live:
                    self.graph.nodes[node]['is_live'] = True
                    
                # Rule 2: The Silent Sensor Implied Dark
                # If it hasn't reported a state, and all children are dark, it's implied dark.
                elif self.graph.nodes[node].get('reported_state') is None and all_children_dark:
                    self.graph.nodes[node]['is_live'] = False

    def localize_faults(self) -> List[Dict]:
        """
        Find all edges where Parent is Live and Child is Dark.
        """
        self.resolve_implied_states()
        
        faults = []
        
        # 1. Check for Feeder Faults
        # Group DTs by feeder
        feeders = {}
        for node, data in self.graph.nodes(data=True):
            if data['type'] == 'dt':
                f_id = data['feeder_id']
                if f_id not in feeders:
                    feeders[f_id] = []
                feeders[f_id].append(node)
                
        failed_feeders = set()
        for f_id, dts in feeders.items():
            # If every DT on this feeder is completely dark (all children dark), it's a feeder fault
            # We check the DT node itself (since its state is implied by its children via post-order traversal)
            if all(not self.graph.nodes[dt].get('is_live', True) for dt in dts):
                faults.append({
                    "fault_type": "feeder_fault",
                    "feeder_id": f_id,
                    "affected_dts": len(dts)
                })
                failed_feeders.add(f_id)
                
        # 2. Check for DT Faults
        failed_dts = set()
        for node, data in self.graph.nodes(data=True):
            if data['type'] == 'dt' and data['feeder_id'] not in failed_feeders:
                if not data.get('is_live', True):
                    faults.append({
                        "fault_type": "dt_fault",
                        "dt_id": node,
                        "is_imputed": node in self.imputed_dts
                    })
                    failed_dts.add(node)
                    
        # 3. Check for Span Faults
        for u, v, data in self.graph.edges(data=True):
            u_data = self.graph.nodes[u]
            
            # Skip checking spans if the parent is already part of a massive Feeder/DT blackout
            if u_data['type'] == 'dt' and u in failed_dts:
                continue
            if u_data.get('feeder_id') in failed_feeders:
                continue
                
            u_live = u_data.get('is_live', True)
            v_live = self.graph.nodes[v].get('is_live', True)
            
            if u_live and not v_live:
                faults.append({
                    "fault_type": "span_fault",
                    "parent_id": u,
                    "child_id": v,
                    "is_imputed": data.get('is_imputed', False)
                })
                
        return faults

