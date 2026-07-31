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
        Two-Pass Implied State Resolver:
        1. Bottom-Up Pass (Leaves to Root): Overrides Lying Sensors if any downstream child is Live.
        2. Top-Down Pass (Root to Leaves): Propagates physical blackout to silent downstream children.
        """
        # Pass 1: Bottom-Up (Lying Sensor Override & DT/Feeder Outage Collapse)
        for node in reversed(list(nx.topological_sort(self.graph))):
            children = list(self.graph.successors(node))
            if children:
                # Check if any child is actively live (reported_state is True, or confirmed is_live)
                any_child_confirmed_live = any(
                    self.graph.nodes[c].get('is_live', True) and self.graph.nodes[c].get('reported_state') is True 
                    for c in children
                )
                
                # Check if all reporting children reported power loss
                reporting_children = [c for c in children if self.graph.nodes[c].get('reported_state') is not None]
                all_reporting_dark = len(reporting_children) > 0 and all(
                    self.graph.nodes[c].get('reported_state') is False for c in reporting_children
                )
                
                if all_reporting_dark and not any_child_confirmed_live:
                    self.graph.nodes[node]['is_live'] = False
                elif any_child_confirmed_live and self.graph.nodes[node].get('reported_state') is False:
                    self.graph.nodes[node]['is_live'] = True

        # Pass 2: Top-Down (Physical Blackout Propagation)
        for node in list(nx.topological_sort(self.graph)):
            parents = list(self.graph.predecessors(node))
            if parents:
                # If any parent is Dark, power cannot reach this child -> Child is Dark
                if any(not self.graph.nodes[p].get('is_live', True) for p in parents):
                    self.graph.nodes[node]['is_live'] = False

    def localize_faults(self, scheduled_outages: List[Dict] = None) -> List[Dict]:
        """
        Find all edges where Parent is Live and Child is Dark.
        Cross-references active scheduled outages feed.
        """
        self.resolve_implied_states()
        
        # Build map of active scheduled outages
        scheduled_map = {}
        if scheduled_outages:
            for outage in scheduled_outages:
                scheduled_map[outage.get('target_id')] = outage.get('reason', 'Scheduled Maintenance')

        faults = []
        
        # 1. Check for Feeder Faults
        feeders = {}
        for node, data in self.graph.nodes(data=True):
            if data['type'] == 'dt':
                f_id = data['feeder_id']
                if f_id not in feeders:
                    feeders[f_id] = []
                feeders[f_id].append(node)
                
        failed_feeders = set()
        for f_id, dts in feeders.items():
            dark_dts = [dt for dt in dts if not self.graph.nodes[dt].get('is_live', True)]
            if len(dts) > 0 and (len(dark_dts) / len(dts)) >= 0.5:
                is_sched = f_id in scheduled_map
                faults.append({
                    "fault_type": "feeder_fault",
                    "feeder_id": f_id,
                    "affected_dts": len(dts),
                    "is_scheduled": is_sched,
                    "reason": scheduled_map.get(f_id) if is_sched else None
                })
                failed_feeders.add(f_id)
                
        # 2. Check for DT Faults
        failed_dts = set()
        for node, data in self.graph.nodes(data=True):
            if data['type'] == 'dt' and data['feeder_id'] not in failed_feeders:
                if not data.get('is_live', True):
                    is_sched = node in scheduled_map
                    faults.append({
                        "fault_type": "dt_fault",
                        "dt_id": node,
                        "is_imputed": node in self.imputed_dts,
                        "is_scheduled": is_sched,
                        "reason": scheduled_map.get(node) if is_sched else None
                    })
                    failed_dts.add(node)
                    
        # 3. Check for Span Faults
        for u, v, data in self.graph.edges(data=True):
            u_data = self.graph.nodes[u]
            
            # Skip checking spans if the pole/DT belongs to a transformer or feeder that already failed
            if u in failed_dts or u_data.get('dt_id') in failed_dts:
                continue
                
            u_feeder = u_data.get('feeder_id') or self.graph.nodes.get(u_data.get('dt_id', ''), {}).get('feeder_id')
            if u_feeder in failed_feeders:
                continue
                
            u_live = u_data.get('is_live', True)
            v_live = self.graph.nodes[v].get('is_live', True)
            
            if u_live and not v_live:
                is_sched = u in scheduled_map or v in scheduled_map
                faults.append({
                    "fault_type": "span_fault",
                    "parent_id": u,
                    "child_id": v,
                    "is_imputed": data.get('is_imputed', False),
                    "is_scheduled": is_sched,
                    "reason": scheduled_map.get(u) or scheduled_map.get(v) if is_sched else None
                })
                
        return faults

