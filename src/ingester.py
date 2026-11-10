"""
Ingestion Subsystem: Multi-Protocol Industrial Telemetry Ingestion
Associated Research: arXiv:2605.17325 | License: Apache 2.0
"""
import time
from typing import Dict, Any, Generator, Optional
from dataclasses import dataclass, field

@dataclass
class NormalizedEvent:
	event_id: str
    source_facility: str
    protocol: str
    event_timestamp: float
    arrival_timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)
    is_screened: bool = False

class TelemetryIngester:
    """Ingests and normalizes raw industrial sensor and control packets (Modbus, DNP3, Syslog)."""
    def __init__(self, facility_id: str):
        self.facility_id = facility_id

    def parse_modbus_frame(self, raw_frame: Dict[str, Any]) -> NormalizedEvent:
        """Normalizes Modbus/TCP application data units into standardized telemetry events."""
        return NormalizedEvent(
            event_id=f"MDB-{int(time.time() * 1000)}-{raw_frame.get('unit_id', 0)}",
            source_facility=self.facility_id,
            protocol="MODBUS_TCP",
            event_timestamp=raw_frame.get("timestamp", time.time()),
            payload={
                "unit_id": raw_frame.get("unit_id"),
                "function_code": raw_frame.get("function_code"),
                "register_address": raw_frame.get("register_address"),
                "register_value": raw_frame.get("register_value")
            }
        )

    def parse_dnp3_frame(self, raw_frame: Dict[str, Any]) -> NormalizedEvent:
        """Normalizes DNP3 outstation control commands into standardized telemetry events."""
        return NormalizedEvent(
            event_id=f"DNP-{int(time.time() * 1000)}-{raw_frame.get('outstation_id', 0)}",
            source_facility=self.facility_id,
            protocol="DNP3",
            event_timestamp=raw_frame.get("timestamp", time.time()),
            payload={
                "outstation_id": raw_frame.get("outstation_id"),
                "function_code": raw_frame.get("function_code"),
                "control_point": raw_frame.get("control_point"),
                "command_action": raw_frame.get("command_action")
            }
        )
