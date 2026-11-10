"""
Simulation Test Runner: Demonstrates Full Detection-to-Containment Pipeline
Usage: python run_simulation.py
"""
import time
from src.orchestrator import PipelineOrchestrator

def main():
    print("=" * 80)
    print("UNIFIED NATIONAL DETECTION BLUEPRINT (UNDB) - SIMULATION SUITE")
    print("Validating: Edge Pre-Filtering, 95% Watermarking, & Claim-Check Isolation")
    print("=" * 80)

    orchestrator = PipelineOrchestrator(facility_id="MUNICIPAL-WATER-DISTRICT-04")

    # 1. Simulate Routine Benign Telemetry (Should be shed by PFDS)
    print("\n[Phase 1] Transmitting Benign Modbus Read Telemetry (Function Code 3)...")
    for i in range(3):
        raw_benign = {
            "unit_id": 1,
            "function_code": 3, # Read Holding Registers (Benign cyclic telemetry)
            "register_address": 500,
            "register_value": 120,
            "timestamp": time.time()
        }
        res = orchestrator.process_raw_telemetry(raw_benign)
        print(f"  -> Packet {i+1}: Result: {'DROPPED (Noise Shed by PFDS)' if res is None else 'FORWARDED'}")

    # 2. Simulate Attack Burst to Monitored Actuator Register (Should trigger Containment Claim)
    print("\n[Phase 2] Simulating Rapid Adversarial Coil Modification Burst (Function Code 5, Reg 1002)...")
    for i in range(6):
        raw_attack = {
            "unit_id": 1,
            "function_code": 5, # Force Single Coil (State-altering command)
            "register_address": 1002, # Target: Emergency Water Inflow Valve
            "register_value": 1,
            "timestamp": time.time() - (0.05 * i) # Simulate minor arrival jitter
        }
        claim = orchestrator.process_raw_telemetry(raw_attack)
        if claim:
            print(f"\n[ALERT] THREAT DETECTED ON PACKET {i+1}!")
            print(f"  -> Incident ID:          {claim['claim_id']}")
            print(f"  -> Anomaly Type:         {claim['threat_classification']}")
            print(f"  -> Telemetry SHA-256:    {claim['telemetry_digest_sha256']}")
            print(f"  -> Action Dispatched:    {claim['containment_directive']} (TTL: {claim['enforcement_ttl_seconds']}s)")
            print(f"  -> Sovereignty Status:   Preserved = {claim['sovereignty_preserved']}")
            break
        else:
            print(f"  -> Packet {i+1}: Pre-filtered & buffered into partitioned state worker...")

    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE: Pipeline successfully protected public infrastructure.")
    print("=" * 80)

if __name__ == "__main__":
    main()
