"""
Edge Layer: Pre-Filtering Dispatcher Subsystem (PFDS)
Associated Research: arXiv:2605.17325 | License: Apache 2.0
"""
from typing import Set, Dict, Any
from .ingester import NormalizedEvent

class PreFilteringDispatcher:
    """Stateless edge-local triage layer engineered to shed high-volume benign noise."""
    def __init__(self, critical_function_codes: Set[int], monitored_registers: Set[int]):
        self.critical_function_codes = critical_function_codes
        self.monitored_registers = monitored_registers

    def evaluate_telemetry(self, event: NormalizedEvent) -> bool:
        """
        Executes line-rate stateless screening.
        Returns True if packet warrants stateful evaluation, False if benign noise.
        """
        func_code = event.payload.get("function_code")
        reg_addr = event.payload.get("register_address")

        # OT Triage: Shed standard cyclic reads; preserve state-altering writes/restarts
        if func_code in self.critical_function_codes:
            event.is_screened = True
            return True

        if reg_addr and reg_addr in self.monitored_registers:
            event.is_screened = True
            return True

        return False
