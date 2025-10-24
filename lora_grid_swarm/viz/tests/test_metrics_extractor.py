#!/usr/bin/env python3
"""
Test suite for HardwareMetricsExtractor.

Acceptance Gate 2.1 Validation.
"""

import pytest
import pandas as pd
import os
from pathlib import Path

# Set up path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from viz.metrics_extractor import HardwareMetricsExtractor


class TestHardwareMetricsExtractor:
    """Test cases for HardwareMetricsExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = HardwareMetricsExtractor()

    def test_extract_gate1_metrics(self):
        """Test extraction of Gate 1 hardware metrics."""
        metrics = self.extractor.extract_gate_metrics(1)

        # Verify structure
        required_keys = [
            "gate_id", "gate_name", "passed", "execution_time_seconds",
            "cpu_usage_percent", "memory_usage_mb", "process_count", "thread_count",
            "authenticity", "proof_completeness", "timestamp", "system_fingerprint_hash"
        ]

        for key in required_keys:
            assert key in metrics

        # Verify gate-specific data
        assert metrics["gate_id"] == 1
        assert metrics["gate_name"] == "Compression Validation"
        assert isinstance(metrics["passed"], bool)
        assert isinstance(metrics["execution_time_seconds"], (int, float))
        assert metrics["execution_time_seconds"] > 0
        assert isinstance(metrics["cpu_usage_percent"], (int, float))
        assert isinstance(metrics["memory_usage_mb"], (int, float))
        assert isinstance(metrics["authenticity"], str)
        assert isinstance(metrics["proof_completeness"], str)

    def test_extract_gate2_metrics(self):
        """Test extraction of Gate 2 hardware metrics."""
        metrics = self.extractor.extract_gate_metrics(2)

        # Verify structure
        required_keys = [
            "gate_id", "gate_name", "passed", "execution_time_seconds",
            "cpu_usage_percent", "memory_usage_mb", "process_count", "thread_count",
            "authenticity", "proof_completeness", "timestamp", "system_fingerprint_hash"
        ]

        for key in required_keys:
            assert key in metrics

        # Verify gate-specific data
        assert metrics["gate_id"] == 2
        assert metrics["gate_name"] == "Wave Propagation Validation"
        assert isinstance(metrics["passed"], bool)
        assert isinstance(metrics["execution_time_seconds"], (int, float))
        assert metrics["execution_time_seconds"] > 0
        assert isinstance(metrics["cpu_usage_percent"], (int, float))

    def test_extract_nonexistent_gate_metrics(self):
        """Test metrics extraction for non-existent gate."""
        metrics = self.extractor.extract_gate_metrics(99)

        # Should return empty metrics structure
        assert metrics["gate_id"] == 99
        assert metrics["passed"] == False
        assert metrics["execution_time_seconds"] == 0.0
        assert metrics["authenticity"] == "NOT_AVAILABLE"
        assert metrics["proof_completeness"] == "NO_PROOFS"

    def test_extract_comparison_data(self):
        """Test DataFrame creation for comparison data."""
        gate_ids = [1, 2]
        df = self.extractor.extract_comparison_data(gate_ids)

        # Verify DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

        expected_columns = [
            "gate_id", "gate_name", "execution_time", "cpu_usage", "memory_usage",
            "process_count", "thread_count", "passed", "authenticity", "proof_completeness", "timestamp"
        ]

        for col in expected_columns:
            assert col in df.columns

        # Verify data integrity
        assert df["gate_id"].tolist() == [1, 2]
        assert all(df["gate_name"].notna())
        assert all(df["execution_time"] > 0)

    def test_extract_proof_chain_metrics_gate1(self):
        """Test proof chain analysis for Gate 1."""
        analysis = self.extractor.extract_proof_chain_metrics(1)

        # Should have proof files for Gate 1
        assert "total_proofs" in analysis
        assert analysis["total_proofs"] >= 2  # At least start and complete

        expected_keys = [
            "total_proofs", "executions_found", "start_proofs", "complete_proofs",
            "earliest_timestamp", "latest_timestamp", "execution_spans"
        ]

        for key in expected_keys:
            assert key in analysis

        # Timestamps should be present
        assert analysis["earliest_timestamp"] is not None
        assert analysis["latest_timestamp"] is not None

        # Should have execution spans
        assert isinstance(analysis["execution_spans"], list)

    def test_extract_proof_chain_metrics_gate2(self):
        """Test proof chain analysis for Gate 2."""
        analysis = self.extractor.extract_proof_chain_metrics(2)

        # Should have many proof files for Gate 2
        assert "total_proofs" in analysis
        assert analysis["total_proofs"] >= 4  # Multiple execution runs

        expected_keys = [
            "total_proofs", "executions_found", "start_proofs", "complete_proofs",
            "earliest_timestamp", "latest_timestamp", "execution_spans"
        ]

        for key in expected_keys:
            assert key in analysis

    def test_extract_proof_chain_nonexistent_gate(self):
        """Test proof chain analysis for non-existent gate."""
        analysis = self.extractor.extract_proof_chain_metrics(99)

        # Should return simple dict indicating no proofs
        assert analysis == {"proof_chain_analysis": "No proof files available"}

    def test_get_visualization_metrics_bundle(self):
        """Test comprehensive metrics bundle creation."""
        gate_ids = [1, 2]
        bundle = self.extractor.get_visualization_metrics_bundle(gate_ids)

        # Verify bundle structure
        expected_keys = [
            "gate_ids", "individual_metrics", "comparison_data",
            "proof_chain_analyses", "summary_stats"
        ]

        for key in expected_keys:
            assert key in bundle

        # Verify gate IDs
        assert bundle["gate_ids"] == gate_ids

        # Verify individual metrics for each gate
        assert 1 in bundle["individual_metrics"]
        assert 2 in bundle["individual_metrics"]

        # Verify comparison data is DataFrame
        assert isinstance(bundle["comparison_data"], pd.DataFrame)
        assert len(bundle["comparison_data"]) == 2

        # Verify proof chain analyses
        assert 1 in bundle["proof_chain_analyses"]
        assert 2 in bundle["proof_chain_analyses"]

        # Verify summary statistics
        summary = bundle["summary_stats"]
        assert "total_gates" in summary
        assert "passed_gates" in summary
        assert "total_execution_time" in summary
        assert summary["total_gates"] == 2

    def test_fingerprint_hash_calculation(self):
        """Test system fingerprint hash generation."""
        metrics = self.extractor.extract_gate_metrics(1)

        fingerprint_hash = metrics["system_fingerprint_hash"]
        assert isinstance(fingerprint_hash, str)
        assert len(fingerprint_hash) > 0

        # Hash should be consistent
        metrics2 = self.extractor.extract_gate_metrics(1)
        assert fingerprint_hash == metrics2["system_fingerprint_hash"]

    def test_execution_span_calculation(self):
        """Test execution span calculation from proof pairs."""
        analysis = self.extractor.extract_proof_chain_metrics(2)

        spans = analysis["execution_spans"]

        # Should have at least some execution spans
        assert isinstance(spans, list)

        if spans:  # If spans exist, verify structure
            for span in spans:
                assert "execution_id" in span
                assert "start_timestamp" in span
                assert "complete_timestamp" in span
                assert "start_proof_file" in span
                assert "complete_proof_file" in span

    def test_summary_stats_calculation(self):
        """Test summary statistics calculation."""
        bundle = self.extractor.get_visualization_metrics_bundle([1, 2])
        summary = bundle["summary_stats"]

        # Basic structure checks
        assert summary["total_gates"] == 2
        assert "passed_gates" in summary
        assert "total_execution_time" in summary
        assert "average_execution_time" in summary
        assert "max_execution_time" in summary
        assert "min_execution_time" in summary
        assert "hardware_verified_count" in summary
        assert "questionable_count" in summary

        # Derived calculations
        assert summary["average_execution_time"] >= 0
        assert summary["max_execution_time"] >= summary["min_execution_time"]

    def test_metrics_consistency(self):
        """Test that metrics extraction is consistent across multiple calls."""
        metrics1 = self.extractor.extract_gate_metrics(1)
        metrics2 = self.extractor.extract_gate_metrics(1)

        # Should be identical (deterministic)
        assert metrics1["execution_time_seconds"] == metrics2["execution_time_seconds"]
        assert metrics1["system_fingerprint_hash"] == metrics2["system_fingerprint_hash"]
        assert metrics1["authenticity"] == metrics2["authenticity"]

    def test_performance_metrics_extraction(self):
        """Test CPU and memory metrics extraction from proofs."""
        metrics = self.extractor.extract_gate_metrics(1)

        # Performance metrics should be present
        assert isinstance(metrics["cpu_usage_percent"], (int, float))
        assert isinstance(metrics["memory_usage_mb"], (int, float))
        assert isinstance(metrics["process_count"], int)
        assert isinstance(metrics["thread_count"], int)

        # Sensible ranges
        assert metrics["cpu_usage_percent"] >= 0
        assert metrics["cpu_usage_percent"] <= 100  # Percentage
        assert metrics["memory_usage_mb"] >= 0
        assert metrics["process_count"] >= 0
        assert metrics["thread_count"] >= 0


if __name__ == "__main__":
    # Run basic smoke test when executed directly
    print("🧪 Testing HardwareMetricsExtractor...")

    extractor = HardwareMetricsExtractor()

    try:
        # Test basic functionality
        print("  • Testing Gate 1 metrics extraction...")
        gate1_metrics = extractor.extract_gate_metrics(1)
        required_keys = ["gate_id", "gate_name", "passed", "execution_time_seconds", "authenticity"]
        for key in required_keys:
            assert key in gate1_metrics, f"Missing key: {key}"
        print("    ✅ Gate 1 metrics extracted")
        print("  • Testing Gate 2 metrics extraction...")
        gate2_metrics = extractor.extract_gate_metrics(2)
        for key in required_keys:
            assert key in gate2_metrics, f"Missing key: {key}"
        print("    ✅ Gate 2 metrics extracted")

        print("  • Testing comparison DataFrame...")
        df = extractor.extract_comparison_data([1, 2])
        assert isinstance(df, pd.DataFrame), "Not a DataFrame"
        assert len(df) == 2, f"Expected 2 rows, got {len(df)}"
        print("    ✅ Comparison DataFrame created")

        print("  • Testing proof chain analysis...")
        proof_analysis_1 = extractor.extract_proof_chain_metrics(1)
        proof_analysis_2 = extractor.extract_proof_chain_metrics(2)
        assert proof_analysis_1["total_proofs"] >= 2, f"Gate 1 needs >=2 proofs, has {proof_analysis_1['total_proofs']}"
        assert proof_analysis_2["total_proofs"] >= 4, f"Gate 2 needs >=4 proofs, has {proof_analysis_2['total_proofs']}"
        print("    ✅ Proof chain analysis completed")

        print("  • Testing visualization metrics bundle...")
        bundle = extractor.get_visualization_metrics_bundle([1, 2])
        assert "individual_metrics" in bundle, "Missing individual_metrics"
        assert "comparison_data" in bundle, "Missing comparison_data"
        assert "summary_stats" in bundle, "Missing summary_stats"
        assert len(bundle["individual_metrics"]) == 2, "Expected 2 individual metrics"
        assert isinstance(bundle["comparison_data"], pd.DataFrame), "Comparison data not DataFrame"
        print("    ✅ Metrics bundle created successfully")

        print("  • Testing summary statistics...")
        summary = bundle["summary_stats"]
        assert summary["total_gates"] == 2, f"Expected 2 total gates, got {summary['total_gates']}"
        assert summary["average_execution_time"] >= 0, "Average execution time negative"
        print("    ✅ Summary statistics calculated")

        print("\n🎯 ALL ACCEPTANCE GATE 2.1 TESTS PASSED!")
        print("✅ HardwareMetricsExtractor is ready for Phase 3 implementation.")
        print("🧮 Hardware-Verified Visualization Pipeline Phase 2 COMPLETE!")

    except Exception as e:
        print(f"\n❌ ACCEPTANCE GATE 2.1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
