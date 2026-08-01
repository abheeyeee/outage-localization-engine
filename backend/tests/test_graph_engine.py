"""
Tests for the core fault localization algorithm.

Constructs small, known topologies using raw NetworkX graphs and verifies
that the GraphEngine correctly identifies fault boundaries, handles lying
sensors, groups symptoms via hierarchical aggregation, and tags scheduled outages.
"""
import pytest
import sys
import os
import networkx as nx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.graph_engine import GraphEngine


def make_engine_with_linear_topology():
    """
    Build a simple linear topology directly with NetworkX:
        DT-001 -> P-001 -> P-002 -> P-003 -> P-004
    """
    engine = GraphEngine.__new__(GraphEngine)
    engine.graph = nx.DiGraph()
    engine.dts = {
        "DT-001": {"dt_id": "DT-001", "feeder_id": "F-01"},
        "DT-002": {"dt_id": "DT-002", "feeder_id": "F-01"},
        "DT-003": {"dt_id": "DT-003", "feeder_id": "F-01"},
    }
    engine.poles = {}
    engine.imputed_dts = set()

    # Add DT nodes
    for dt_id in ["DT-001", "DT-002", "DT-003"]:
        engine.graph.add_node(dt_id, type="dt", lat=12.97, lon=77.59,
                              is_live=True, feeder_id="F-01", reported_state=None)

    # Add poles
    poles = [
        ("P-001", 12.971, 77.591),
        ("P-002", 12.972, 77.592),
        ("P-003", 12.973, 77.593),
        ("P-004", 12.974, 77.594),
    ]
    for pid, lat, lon in poles:
        engine.graph.add_node(pid, type="pole", lat=lat, lon=lon,
                              dt_id="DT-001", feeder_id="F-01",
                              device_id=f"DEV-{pid}", pincode="560001",
                              is_live=True, reported_state=None, last_seq=-1)

    # Connect: DT -> P-001 -> P-002 -> P-003 -> P-004
    engine.graph.add_edge("DT-001", "P-001", is_imputed=False)
    engine.graph.add_edge("P-001", "P-002", is_imputed=False)
    engine.graph.add_edge("P-002", "P-003", is_imputed=False)
    engine.graph.add_edge("P-003", "P-004", is_imputed=False)

    return engine


class TestSpanFaultLocalization:
    """Verify that a known fault in a known topology produces the expected span."""

    def test_mid_line_span_fault(self):
        """
        Fault between P-002 and P-003.
        P-001, P-002: LIVE.  P-003, P-004: DARK.
        Expected: exactly 1 span_fault between P-002 and P-003.
        """
        engine = make_engine_with_linear_topology()
        engine.graph.nodes["P-003"]["is_live"] = False
        engine.graph.nodes["P-003"]["reported_state"] = False
        engine.graph.nodes["P-004"]["is_live"] = False
        engine.graph.nodes["P-004"]["reported_state"] = False

        faults = engine.localize_faults()
        span_faults = [f for f in faults if f["fault_type"] == "span_fault"]

        assert len(span_faults) == 1, f"Expected 1 span fault, got {len(span_faults)}"
        assert span_faults[0]["parent_id"] == "P-002"
        assert span_faults[0]["child_id"] == "P-003"

    def test_fault_at_head_of_line(self):
        """
        All poles and DT go dark -> should produce 1 dt_fault, not 4 span faults.
        This tests hierarchical aggregation / ticket suppression.
        """
        engine = make_engine_with_linear_topology()
        engine.graph.nodes["DT-001"]["is_live"] = False
        for pid in ["P-001", "P-002", "P-003", "P-004"]:
            engine.graph.nodes[pid]["is_live"] = False
            engine.graph.nodes[pid]["reported_state"] = False

        faults = engine.localize_faults()
        dt_faults = [f for f in faults if f["fault_type"] == "dt_fault"]
        span_faults = [f for f in faults if f["fault_type"] == "span_fault"]

        assert len(dt_faults) == 1, f"Expected 1 DT fault, got {len(dt_faults)}"
        assert dt_faults[0]["dt_id"] == "DT-001"
        assert len(span_faults) == 0, f"Expected 0 span faults (suppressed), got {len(span_faults)}"


class TestLyingSensorOverride:
    """Verify that the implied-state resolver correctly handles lying sensors."""

    def test_lying_parent_with_live_child(self):
        """
        P-002 falsely reports DARK, but P-003 (its child) is LIVE.
        The algorithm should infer P-002 is actually LIVE. No fault generated.
        """
        engine = make_engine_with_linear_topology()
        engine.graph.nodes["P-002"]["is_live"] = False
        engine.graph.nodes["P-002"]["reported_state"] = False
        # Child reports actively live
        engine.graph.nodes["P-003"]["reported_state"] = True

        faults = engine.localize_faults()

        assert engine.graph.nodes["P-002"]["is_live"] == True, \
            "P-002 should be overridden to LIVE because its child P-003 is live"
        assert len(faults) == 0, f"Expected 0 faults (lying sensor), got {len(faults)}"


class TestSimultaneousFaults:
    """Verify that multiple simultaneous faults generate distinct tickets."""

    def test_two_separate_faults(self):
        """
        Two independent lines under two DTs.
        Fault on each -> should produce 2 distinct span_fault tickets.
        """
        engine = GraphEngine.__new__(GraphEngine)
        engine.graph = nx.DiGraph()
        engine.dts = {
            "DT-A": {"dt_id": "DT-A", "feeder_id": "F-01"},
            "DT-B": {"dt_id": "DT-B", "feeder_id": "F-01"},
        }
        engine.poles = {}
        engine.imputed_dts = set()

        engine.graph.add_node("DT-A", type="dt", lat=12.97, lon=77.59,
                              is_live=True, feeder_id="F-01", reported_state=None)
        engine.graph.add_node("DT-B", type="dt", lat=12.98, lon=77.60,
                              is_live=True, feeder_id="F-01", reported_state=None)

        for pid, dt, lat, lon, pin in [
            ("PA-1", "DT-A", 12.971, 77.591, "560001"),
            ("PA-2", "DT-A", 12.972, 77.592, "560001"),
            ("PB-1", "DT-B", 12.981, 77.601, "560002"),
            ("PB-2", "DT-B", 12.982, 77.602, "560002"),
        ]:
            engine.graph.add_node(pid, type="pole", lat=lat, lon=lon,
                                  dt_id=dt, feeder_id="F-01", device_id=f"D-{pid}",
                                  pincode=pin, is_live=True, reported_state=None, last_seq=-1)

        engine.graph.add_edge("DT-A", "PA-1", is_imputed=False)
        engine.graph.add_edge("PA-1", "PA-2", is_imputed=False)
        engine.graph.add_edge("DT-B", "PB-1", is_imputed=False)
        engine.graph.add_edge("PB-1", "PB-2", is_imputed=False)

        # Fault on line A: PA-2 goes dark
        engine.graph.nodes["PA-2"]["is_live"] = False
        engine.graph.nodes["PA-2"]["reported_state"] = False

        # Fault on line B: PB-2 goes dark
        engine.graph.nodes["PB-2"]["is_live"] = False
        engine.graph.nodes["PB-2"]["reported_state"] = False

        faults = engine.localize_faults()
        span_faults = [f for f in faults if f["fault_type"] == "span_fault"]

        assert len(span_faults) == 2, f"Expected 2 span faults, got {len(span_faults)}"
        parents = {f["parent_id"] for f in span_faults}
        children = {f["child_id"] for f in span_faults}
        assert "PA-1" in parents and "PA-2" in children
        assert "PB-1" in parents and "PB-2" in children


class TestScheduledOutageSuppression:
    """Verify that scheduled outages are tagged, not false-alarmed."""

    def test_scheduled_outage_tagged(self):
        """
        When a DT is in the scheduled outage list and goes dark,
        the fault should be tagged is_scheduled=True.
        """
        engine = make_engine_with_linear_topology()
        engine.graph.nodes["DT-001"]["is_live"] = False
        for pid in ["P-001", "P-002", "P-003", "P-004"]:
            engine.graph.nodes[pid]["is_live"] = False

        scheduled = [{"target_id": "DT-001", "reason": "Load shedding"}]
        faults = engine.localize_faults(scheduled)

        dt_faults = [f for f in faults if f["fault_type"] == "dt_fault"]
        assert len(dt_faults) == 1
        assert dt_faults[0]["is_scheduled"] == True
        assert dt_faults[0]["reason"] == "Load shedding"
