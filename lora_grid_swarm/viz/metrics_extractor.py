#!/usr/bin/env python3
"""
Hardware Metrics Extractor

Extracts hardware execution metrics from verified checkpoints and proof files.
Creates visualization-ready data structures from hardware-proven results.

Part of the Hardware-Proven Visualization Implementation Plan Phase 2.
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from pathlib import Path

# Import the checkpoint loader we created in Phase 1
from .checkpoint_loader import HardwareVerifiedCheckpointLoader

class HardwareMetricsExtractor:
    """
    Extracts hardware execution metrics from verified checkpoints and proof files.
    """

    def __init__(self):
        self.checkpoint_loader = HardwareVerifiedCheckpointLoader()

    def extract_gate_metrics(self, gate_id: int) -> Dict[str, Any]:
        """
        Returns comprehensive hardware metrics for a single gate:

        {
            "gate_id": int,
            "gate_name": str,
            "passed": bool,
            "execution_time_seconds": float,
            "cpu_usage_percent": float,
            "memory_usage_mb": float,
            "process_count": int,
            "thread_count": int,
            "authenticity": str,
            "proof_completeness": str,
            "timestamp": str,
            "system_fingerprint_hash": str
        }
        """
        # Load checkpoint and proof chain
        try:
            checkpoint = self.checkpoint_loader.load_gate_result(gate_id)
            proof_chain = self.checkpoint_loader.load_proof_chain(gate_id)
        except FileNotFoundError:
            return self._empty_metrics(gate_id)

        # Extract core metrics from checkpoint
        metrics = {
            "gate_id": gate_id,
            "gate_name": self._get_gate_name(gate_id),
            "passed": checkpoint.get("test_result", {}).get("gate_passed", False),
            "execution_time_seconds": checkpoint.get("execution_duration_seconds", 0.0),
            "authenticity": checkpoint.get("hardware_proofs", {}).get("execution_authenticity", "UNKNOWN"),
            "proof_completeness": checkpoint.get("proof_completeness", "UNKNOWN"),
            "timestamp": self.checkpoint_loader._get_timestamp_from_checkpoint(checkpoint),
            "system_fingerprint_hash": self._get_fingerprint_hash(checkpoint)
        }

        # Extract performance metrics from proof chain
        perf_metrics = self._extract_performance_metrics(proof_chain)
        metrics.update(perf_metrics)

        return metrics

    def extract_comparison_data(self, gate_ids: List[int]) -> pd.DataFrame:
        """
        Returns DataFrame for cross-gate comparison with columns:
        - gate_id, gate_name, execution_time, cpu_usage, memory_usage, passed, authenticity
        """
        all_metrics = []

        for gate_id in gate_ids:
            metrics = self.extract_gate_metrics(gate_id)
            # Flatten for DataFrame
            row = {
                "gate_id": metrics["gate_id"],
                "gate_name": metrics["gate_name"],
                "execution_time": metrics["execution_time_seconds"],
                "cpu_usage": metrics["cpu_usage_percent"],
                "memory_usage": metrics["memory_usage_mb"],
                "process_count": metrics["process_count"],
                "thread_count": metrics["thread_count"],
                "passed": metrics["passed"],
                "authenticity": metrics["authenticity"],
                "proof_completeness": metrics["proof_completeness"],
                "timestamp": metrics["timestamp"]
            }
            all_metrics.append(row)

        df = pd.DataFrame(all_metrics)
        return df

    def extract_proof_chain_metrics(self, gate_id: int) -> Dict[str, Any]:
        """
        Parses .proof files to extract detailed timing and resource consumption traces.
        Returns comprehensive proof chain analysis.
        """
        try:
            proof_chain = self.checkpoint_loader.load_proof_chain(gate_id)
        except FileNotFoundError:
            return {"proof_chain_analysis": "No proof files available"}

        # Analyze proof chain for metrics
        analysis = {
            "total_proofs": len(proof_chain),
            "executions_found": len([p for p in proof_chain if "execution" in p.get("phase", "")]),
            "start_proofs": len([p for p in proof_chain if "start" in p.get("phase", "") or "_start." in str(p.get("file", ""))]),
            "complete_proofs": len([p for p in proof_chain if "complete" in p.get("phase", "") or "_complete." in str(p.get("file", ""))]),
            "earliest_timestamp": None,
            "latest_timestamp": None,
            "execution_spans": []
        }

        # Extract timestamps
        timestamps = []
        for proof in proof_chain:
            ts = proof.get("timestamp")
            if ts:
                timestamps.append(ts)

        if timestamps:
            analysis["earliest_timestamp"] = min(timestamps)
            analysis["latest_timestamp"] = max(timestamps)

        # Calculate execution spans between start/complete pairs
        execution_spans = self._calculate_execution_spans(proof_chain)
        analysis["execution_spans"] = execution_spans

        return analysis

    def get_visualization_metrics_bundle(self, gate_ids: List[int]) -> Dict[str, Any]:
        """
        Creates a comprehensive metrics bundle for dashboard generation.
        """
        bundle = {
            "gate_ids": gate_ids,
            "individual_metrics": {},
            "comparison_data": None,
            "proof_chain_analyses": {},
            "summary_stats": {}
        }

        # Extract metrics for each gate
        for gate_id in gate_ids:
            bundle["individual_metrics"][gate_id] = self.extract_gate_metrics(gate_id)
            bundle["proof_chain_analyses"][gate_id] = self.extract_proof_chain_metrics(gate_id)

        # Create comparison DataFrame
        bundle["comparison_data"] = self.extract_comparison_data(gate_ids)

        # Calculate summary statistics
        bundle["summary_stats"] = self._calculate_summary_stats(bundle["individual_metrics"])

        return bundle

    def _extract_performance_metrics(self, proof_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract CPU, memory, and other performance metrics from proof chain.
        """
        metrics = {
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0,
            "process_count": 0,
            "thread_count": 0
        }

        if not proof_chain:
            return metrics

        # Extract from resource measurements in proofs
        cpu_usages = []
        memory_usages = []

        for proof in proof_chain:
            # Extract CPU usage
            cpu_data = proof.get("cpu_usage", {})
            if cpu_data and isinstance(cpu_data, dict):
                initial = cpu_data.get("initial_percent", 0)
                final = cpu_data.get("final_percent", 0)
                if final > 0:
                    cpu_usages.append(final)

            # Extract memory usage
            memory_data = proof.get("memory_usage", {})
            if memory_data and isinstance(memory_data, dict):
                final_mb = memory_data.get("final_mb", 0)
                if final_mb > 0:
                    memory_usages.append(final_mb)

            # Extract system metrics
            final_measurements = proof.get("final_resource_measurement", {})
            if final_measurements:
                metrics["process_count"] = max(metrics["process_count"], final_measurements.get("active_processes", 0))
                metrics["thread_count"] = max(metrics["thread_count"], final_measurements.get("threads_count", 0))

        # Calculate averages/maximums
        if cpu_usages:
            metrics["cpu_usage_percent"] = max(cpu_usages)  # Peak CPU usage
        if memory_usages:
            metrics["memory_usage_mb"] = max(memory_usages)  # Peak memory usage

        return metrics

    def _calculate_execution_spans(self, proof_chain: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate execution time spans by pairing start/complete proof files.
        """
        spans = []

        # Group by execution ID
        executions = {}
        for proof in proof_chain:
            exec_id = proof.get("execution_id", "unknown")
            phase = proof.get("phase", "")

            if exec_id not in executions:
                executions[exec_id] = {}

            if "start" in phase or "_start." in str(proof.get("file", "")):
                executions[exec_id]["start"] = proof
            if "complete" in phase or "_complete." in str(proof.get("file", "")):
                executions[exec_id]["complete"] = proof

        # Calculate spans
        for exec_id, phases in executions.items():
            start_proof = phases.get("start")
            complete_proof = phases.get("complete")

            if start_proof and complete_proof:
                start_ts = start_proof.get("timestamp")
                complete_ts = complete_proof.get("timestamp")

                if start_ts and complete_ts:
                    span = {
                        "execution_id": exec_id,
                        "start_timestamp": start_ts,
                        "complete_timestamp": complete_ts,
                        "start_proof_file": start_proof.get("file"),
                        "complete_proof_file": complete_proof.get("file")
                    }
                    spans.append(span)

        return spans

    def _get_gate_name(self, gate_id: int) -> str:
        """Get human-readable gate name."""
        gate_names = {
            1: "Compression Validation",
            2: "Wave Propagation Validation",
            3: "Glider Emergence Validation",
            4: "Half-Life Decay Validation",
            5: "144-Agent Stability Validation"
        }
        return gate_names.get(gate_id, f"Gate {gate_id}")

    def _get_fingerprint_hash(self, checkpoint: Dict[str, Any]) -> str:
        """Extract system fingerprint hash."""
        hw_proofs = checkpoint.get("hardware_proofs", {})
        fingerprint = hw_proofs.get("system_fingerprint", {})

        # Create a simple hash-like identifier from key components
        components = [
            fingerprint.get("machine", ""),
            fingerprint.get("processor", ""),
            fingerprint.get("chip_type", ""),
            fingerprint.get("serial_number", "")
        ]

        # Simple hash of concatenated components
        import hashlib
        hash_input = "|".join(components).encode('utf-8')
        hash_digest = hashlib.md5(hash_input).hexdigest()[:16]

        return hash_digest

    def _empty_metrics(self, gate_id: int) -> Dict[str, Any]:
        """Return empty metrics structure for missing gates."""
        return {
            "gate_id": gate_id,
            "gate_name": self._get_gate_name(gate_id),
            "passed": False,
            "execution_time_seconds": 0.0,
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0,
            "process_count": 0,
            "thread_count": 0,
            "authenticity": "NOT_AVAILABLE",
            "proof_completeness": "NO_PROOFS",
            "timestamp": None,
            "system_fingerprint_hash": "unknown"
        }

    def _calculate_summary_stats(self, individual_metrics: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics across all gates."""
        stats = {
            "total_gates": len(individual_metrics),
            "passed_gates": sum(1 for m in individual_metrics.values() if m.get("passed", False)),
            "total_execution_time": sum(m.get("execution_time_seconds", 0) for m in individual_metrics.values()),
            "average_execution_time": 0.0,
            "max_execution_time": 0.0,
            "min_execution_time": float('inf'),
            "total_cpu_usage": sum(m.get("cpu_usage_percent", 0) for m in individual_metrics.values()),
            "max_memory_usage": max(m.get("memory_usage_mb", 0) for m in individual_metrics.values()),
            "hardware_verified_count": sum(1 for m in individual_metrics.values() if m.get("authenticity") == "HARDWARE_VERIFIED"),
            "questionable_count": sum(1 for m in individual_metrics.values() if m.get("authenticity") == "QUESTIONABLE")
        }

        # Calculate averages and ranges
        if stats["total_gates"] > 0:
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_gates"]

        execution_times = [m.get("execution_time_seconds", 0) for m in individual_metrics.values()]
        execution_times = [t for t in execution_times if t > 0]

        if execution_times:
            stats["max_execution_time"] = max(execution_times)
            stats["min_execution_time"] = min(execution_times)

        return stats
