#!/usr/bin/env python3
"""
End-to-End Visualization Tests

Tests the complete hardware-verified visualization generation pipeline.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from ..generate_all import EndToEndVisualizationGenerator
from ..checkpoint_loader import HardwareVerifiedCheckpointLoader
from ..metrics_extractor import HardwareMetricsExtractor


class TestEndToEndVisualizationGenerator:
    """Test the complete visualization generation pipeline."""

    @pytest.fixture
    def generator(self):
        """Create a test generator instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield EndToEndVisualizationGenerator(temp_dir)

    @pytest.fixture
    def mock_checkpoint_loader(self):
        """Mock checkpoint loader for testing."""
        mock = MagicMock(spec=HardwareVerifiedCheckpointLoader)
        mock.list_available_hardware_verified_gates.return_value = [1, 2]
        return mock

    @pytest.fixture
    def mock_metrics_extractor(self):
        """Mock metrics extractor for testing."""
        mock = MagicMock(spec=HardwareMetricsExtractor)
        mock.extract_gate_metrics.return_value = {
            "gate_id": 1,
            "gate_name": "Test Gate",
            "passed": True,
            "execution_time_seconds": 1.0,
            "authenticity": "HARDWARE_VERIFIED",
            "proof_completeness": "HARDWARE_VERIFIED_COMPLETE"
        }
        mock.get_visualization_metrics_bundle.return_value = {
            "individual_metrics": {1: {}, 2: {}},
            "summary_stats": {
                "total_gates": 2,
                "passed_gates": 2,
                "hardware_verified_count": 2
            }
        }
        return mock

    def test_generator_initialization(self, generator):
        """Test that generator initializes correctly."""
        assert isinstance(generator.checkpoint_loader, HardwareVerifiedCheckpointLoader)
        assert isinstance(generator.metrics_extractor, HardwareMetricsExtractor)
        assert generator.output_base_dir.exists()

    def test_validate_hardware_integrity_success(self, generator, mock_checkpoint_loader):
        """Test successful hardware integrity validation."""
        with patch.object(generator, 'checkpoint_loader', mock_checkpoint_loader):
            # Mock verify_checkpoint_integrity to return True
            mock_checkpoint_loader.load_gate_result.return_value = {
                'gate_passed': True,
                'hardware_proofs': {'execution_authenticity': 'HARDWARE_VERIFIED'},
                'proof_completeness': 'HARDWARE_VERIFIED_COMPLETE'
            }

            result = generator.validate_hardware_integrity([1, 2])

            assert result is True
            assert 1 in generator.integrity_results
            assert 2 in generator.integrity_results
            assert generator.integrity_results[1]['valid'] is True

    def test_validate_hardware_integrity_failure(self, generator, mock_checkpoint_loader):
        """Test hardware integrity validation failure."""
        with patch.object(generator, 'checkpoint_loader', mock_checkpoint_loader):
            # Mock to raise FileNotFoundError
            mock_checkpoint_loader.load_gate_result.side_effect = FileNotFoundError()

            result = generator.validate_hardware_integrity([1])

            assert result is False
            assert 1 in generator.integrity_results
            assert 'error' in generator.integrity_results[1]

    def test_generate_complete_visualization_suite_no_gates(self, generator, mock_checkpoint_loader):
        """Test generation when no hardware-verified gates exist."""
        with patch.object(generator, 'checkpoint_loader', mock_checkpoint_loader):
            # Mock empty gate list
            mock_checkpoint_loader.list_available_hardware_verified_gates.return_value = []

            with pytest.raises(FileNotFoundError, match="No hardware-verified gates found"):
                generator.generate_complete_visualization_suite()

    def test_generate_complete_visualization_suite_validation_failure(self, generator, mock_checkpoint_loader):
        """Test generation when hardware validation fails."""
        with patch.object(generator, 'checkpoint_loader', mock_checkpoint_loader):
            mock_checkpoint_loader.list_available_hardware_verified_gates.return_value = [1]
            mock_checkpoint_loader.load_gate_result.side_effect = FileNotFoundError()

            with pytest.raises(ValueError, match="Hardware integrity validation failed"):
                generator.generate_complete_visualization_suite()

    def test_cleanup_outputs_safe(self, generator):
        """Test cleanup outputs with confirmation."""
        result = generator.cleanup_outputs(confirm=False)
        assert result is False  # Should not proceed without confirmation

    def test_cleanup_outputs_confirmed(self, generator):
        """Test cleanup outputs with confirmation."""
        # Create a test file
        test_file = generator.output_base_dir / "test.txt"
        test_file.write_text("test")

        result = generator.cleanup_outputs(confirm=True)
        assert result is True
        assert not generator.output_base_dir.exists()

    def test_generate_complete_visualization_suite_with_specific_gates(self, generator, mock_checkpoint_loader, mock_metrics_extractor):
        """Test complete suite generation with specific gate IDs."""
        with patch.object(generator, 'checkpoint_loader', mock_checkpoint_loader), \
             patch.object(generator, 'metrics_extractor', mock_metrics_extractor), \
             patch.object(generator, 'dashboard_generator') as mock_dash:

            # Mock successful validation
            mock_checkpoint_loader.load_gate_result.return_value = {
                'gate_passed': True,
                'hardware_proofs': {'execution_authenticity': 'HARDWARE_VERIFIED'},
                'proof_completeness': 'HARDWARE_VERIFIED_COMPLETE'
            }

            # Mock dashboard methods
            mock_dash.generate_gate_summary_chart.return_value = "chart1.png"
            mock_dash.generate_execution_timeline.return_value = "timeline.png"
            mock_dash.generate_propagation_comparison.return_value = "comparison.png"
            mock_dash.generate_html_dashboard.return_value = "dashboard.html"

            result = generator.generate_complete_visualization_suite(gate_ids=[1, 2])

            assert 'status' in result
            assert result['status'] == 'success'
            assert result['gate_ids_processed'] == [1, 2]
            assert 'individual_charts' in result
            assert 'html_dashboard' in result
            assert 'manifest' in result


class TestEndToEndVisualizationGeneratorIntegration:
    """Integration tests for complete visualization pipeline."""

    @pytest.fixture
    def real_generator(self):
        """Create generator with real components for integration testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gen = EndToEndVisualizationGenerator(temp_dir)
            # Mock to avoid real file dependencies in integration tests
            gen.checkpoint_loader = MagicMock(spec=HardwareVerifiedCheckpointLoader)
            gen.metrics_extractor = MagicMock(spec=HardwareMetricsExtractor)
            yield gen

    def test_integration_pipeline_structure(self, real_generator):
        """Test that integration pipeline has all required components."""
        assert hasattr(real_generator, 'validate_hardware_integrity')
        assert hasattr(real_generator, 'generate_complete_visualization_suite')
        assert hasattr(real_generator, 'cleanup_outputs')
        assert callable(real_generator.validate_hardware_integrity)
        assert callable(real_generator.generate_complete_visualization_suite)


# CLI testing
def test_cli_interface(capsys):
    """Test CLI interface parsing."""
    from ..generate_all import main
    import sys

    # Test help output
    old_argv = sys.argv
    try:
        sys.argv = ['generate_all.py', '--help']
        with pytest.raises(SystemExit):  # --help causes SystemExit
            main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    pytest.main([__file__])
