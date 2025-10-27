#!/usr/bin/env python3
"""
Dashboard Generator Tests
"""

import pytest
import tempfile
from pathlib import Path

from ..dashboard_generator import DashboardGenerator, MATPLOTLIB_AVAILABLE


def test_matplotlib_available():
    """Test that matplotlib availability flag is set."""
    assert MATPLOTLIB_AVAILABLE is True


def test_dashboard_generator_initialization():
    """Test that DashboardGenerator can be initialized."""
    generator = DashboardGenerator()
    assert generator is not None
    assert hasattr(generator, 'timestamp')  # Simple smoke test


def test_hardware_watermark_with_gate_id():
    """Test hardware watermark with gate ID."""
    import matplotlib.pyplot as plt

    # Skip if matplotlib not available
    if not MATPLOTLIB_AVAILABLE:
        pytest.skip("Matplotlib not available")

    generator = DashboardGenerator()
    fig, ax = plt.subplots()

    # Should not raise an exception
    generator.add_hardware_watermark(fig, gate_id=1)

    # Verify watermark was added to figure
    assert len(fig.texts) > 0
    assert "HARDWARE-VERIFIED" in fig.texts[0].get_text()
    assert "Gate 1" in fig.texts[0].get_text()

    plt.close(fig)


def test_hardware_watermark_without_gate_id():
    """Test hardware watermark without gate ID."""
    import matplotlib.pyplot as plt

    # Skip if matplotlib not available
    if not MATPLOTLIB_AVAILABLE:
        pytest.skip("Matplotlib not available")

    generator = DashboardGenerator()
    fig, ax = plt.subplots()

    # Should not raise an exception
    generator.add_hardware_watermark(fig)

    # Verify watermark was added to figure
    assert len(fig.texts) > 0
    assert "HARDWARE-VERIFIED" in fig.texts[0].get_text()

    plt.close(fig)
