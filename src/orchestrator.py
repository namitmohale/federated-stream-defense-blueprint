"""
Orchestration Subsystem: End-to-End Pipeline Coordination
Associated Research: arXiv:2605.17325 | License: Apache 2.0
"""
import time
from typing import Dict, Any, Optional
from .ingester import TelemetryIngester, NormalizedEvent
from .pfds import PreFilteringDispatcher
from .watermark_engine import StatisticalWatermarkEngine, LockShardedStateWorker
from .claim_check import CryptographicClaimCheckDispatcher

class PipelineOrchestrator:
    """Coordinates edge-local triage, watermark generation, partitioned workers, and containment claims."""
    def __init__(self, facility_id: str):
        self.ingester = TelemetryIngester(facility_id=facility_id)
        # Modbus 0x05 (Force Single Coil), 0x06 (Preset Single Register); Regs 1000-1050 (Pumps/Valves)
        self.pfds = PreFilteringDispatcher(critical_function_codes={5, 6, 15, 16}, monitored_registers=set(range(1000, 1051)))
        self.watermark_engine = StatisticalWatermarkEngine()
        self.workers: Dict[str, LockShardedStateWorker] = {}
        self.dispatcher = CryptographicClaimCheckDispatcher()

    def process_raw_telemetry(self, raw_frame: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # 1. Normalize
        event = self.ingester.parse_modbus_frame(raw_frame)

        # 2. Edge Pre-Filtering (PFDS)
        warrants_inspection = self.pfds.evaluate_telemetry(event)
        if not warrants_inspection:
            return None # Shed benign noise

        # 3. Statistical Watermarking
        watermark = self.watermark_engine.record_packet_arrival(event.event_timestamp, event.arrival_timestamp)

        # 4. Lock-Sharded Stateful Processing
        partition_key = f"{event.source_facility}_reg_{event.payload.get('register_address')}"
        if partition_key not in self.workers:
            self.workers[partition_key] = LockShardedStateWorker(partition_key=partition_key)

        worker = self.workers[partition_key]
        anomaly = worker.ingest_to_partition(event)

        # 5. Cryptographic Claim-Check Containment
        if anomaly:
            incident_id = f"INC-{int(time.time())}"
            claim = self.dispatcher.generate_signed_claim(
                incident_id=incident_id,
                anomaly_data=anomaly,
                raw_event=raw_frame
            )
            return claim

        return None
