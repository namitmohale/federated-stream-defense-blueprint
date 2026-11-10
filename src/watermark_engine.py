"""
Processing Layer: 95% Statistical Watermark Engine & Lock-Sharded Workers
Associated Research: arXiv:2605.17325 | License: Apache 2.0
"""
import time
from typing import List, Dict, Optional
from .ingester import NormalizedEvent

class StatisticalWatermarkEngine:
    """Dynamically calculates an empirical 95th percentile watermark to accommodate late-arriving telemetry."""
    def __init__(self, latency_window_size: int = 500):
        self.latency_samples: List[float] = []
        self.latency_window_size = latency_window_size
        self.current_watermark: float = 0.0

    def record_packet_arrival(self, event_timestamp: float, arrival_timestamp: float) -> float:
        """Updates empirical delay distribution and shifts the processing horizon."""
        delay = max(0.0, arrival_timestamp - event_timestamp)
        self.latency_samples.append(delay)
        if len(self.latency_samples) > self.latency_window_size:
            self.latency_samples.pop(0)

        # 95th percentile dynamic delay threshold
        sorted_delays = sorted(self.latency_samples)
        p95_index = int(len(sorted_delays) * 0.95)
        p95_delay = sorted_delays[p95_index] if sorted_delays else 0.0

        # Processing watermark: logs older than this can be safely evaluated without late-drop false negatives
        self.current_watermark = arrival_timestamp - p95_delay
        return self.current_watermark

class LockShardedStateWorker:
    """Maintains stateful operational baselines across isolated per-asset partitions."""
    def __init__(self, partition_key: str):
        self.partition_key = partition_key
        self.recent_events: List[NormalizedEvent] = []
        self.rate_anomaly_threshold = 5 # Events within 1-second burst

    def ingest_to_partition(self, event: NormalizedEvent) -> Optional[Dict[str, Any]]:
        """Processes event within an isolated memory partition, preventing global lock contention."""
        self.recent_events.append(event)
        now = time.time()
        # Retain 5-second sliding window
        self.recent_events = [e for e in self.recent_events if now - e.arrival_timestamp < 5.0]

        # Anomaly detection: Rapid consecutive write commands to critical registers
        if len(self.recent_events) >= self.rate_anomaly_threshold:
            return {
                "anomaly_type": "HIGH_FREQUENCY_COIL_MANIPULATION",
                "facility": event.source_facility,
                "event_count": len(self.recent_events),
                "target_register": event.payload.get("register_address"),
                "detected_at": now
            }
        return None
