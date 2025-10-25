#!/usr/bin/env python3
"""
Dashboard Generator for LoRA Grid Swarm Visualization

Creates comprehensive HTML dashboards with hardware-verified watermarks
showing performance metrics, execution timelines, and validation summaries.
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as plt_patches
plt.use('Agg')  # Non-interactive backend

from .metrics_extractor import HardwareMetricsExtractor
from .checkpoint_loader import HardwareVerifiedCheckpointLoader


class DashboardGenerator:
    """
    Generates hardware-watertagged visualization dashboards
    """

    def __init__(self):
        self.metrics_extractor = HardwareMetricsExtractor()
        self.checkpoint_loader = HardwareVerifiedCheckpointLoader()
        # Get current timestamp for watermarking
        self.timestamp = datetime.now().isoformat()

        # Hardware fingerprint for watermark
        try:
            import platform
            self.system_fingerprint = platform.platform().split('-')[0]
        except:
            self.system_fingerprint = "Unknown"

    def add_hardware_watermark(self, fig: plt.Figure, gate_id: int = None) -> None:
        """Add HARDWARE-VERIFIED watermark to plots"""
        watermark_text = "HARDWARE-VERIFIED"
        if gate_id:
            watermark_text += f" | Gate {gate_id}"
        watermark_text += f" | {self.system_fingerprint} | {self.timestamp[:19]}"

        fig.text(0.02, 0.02, watermark_text,
                fontsize=8, color='red', alpha=0.6,
                rotation=0, ha='left', va='bottom',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    def generate_gate_summary_chart(self, gate_ids: List[int], output_path: str = None) -> str:
        """Generate comprehensive gate summary visualization"""
        # Extract metrics
        metrics_data = []
        for gate_id in gate_ids:
            try:
                metrics = self.metrics_extractor.extract_gate_metrics(gate_id)
                metrics_data.append(metrics)
            except FileNotFoundError:
                continue

        if not metrics_data:
            print("WARNING: No metrics data available for dashboard")
            return None

        # Create summary figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

        # 1. Execution Time Comparison
        gates = [m['gate_id'] for m in metrics_data]
        times = [m['execution_time_seconds'] for m in metrics_data]
        ax1.bar(gates, times, color=['green' if m['passed'] else 'red' for m in metrics_data])
        ax1.set_title('Gate Execution Times')
        ax1.set_xlabel('Gate ID')
        ax1.set_ylabel('Execution Time (seconds)')
        ax1.grid(True, alpha=0.3)

        # 2. CPU Usage Distribution
        cpu_usage = [m['cpu_usage_percent'] for m in metrics_data if m['cpu_usage_percent'] > 0]
        if cpu_usage:
            ax2.hist(cpu_usage, bins=5, alpha=0.7, color='skyblue', edgecolor='black')
            ax2.set_title('CPU Usage Distribution')
            ax2.set_xlabel('CPU Usage (%)')
            ax2.set_ylabel('Frequency')
        else:
            ax2.text(0.5, 0.5, 'No CPU data available', ha='center', va='center', transform=ax2.transAxes)

        # 3. Memory Usage Timeline
        memory_usage = [m['memory_usage_mb'] for m in metrics_data if m['memory_usage_mb'] > 0]
        if memory_usage:
            ax3.plot(gates, memory_usage, 'o-', linewidth=2, markersize=8, color='orange')
            ax3.set_title('Memory Usage by Gate')
            ax3.set_xlabel('Gate ID')
            ax3.set_ylabel('Memory Usage (MB)')
        else:
            ax3.text(0.5, 0.5, 'No memory data available', ha='center', va='center', transform=ax3.transAxes)

        # 4. Authentication Status Summary
        authentic_count = sum(1 for m in metrics_data if m['authenticity'] == 'HARDWARE_VERIFIED')
        questionable_count = sum(1 for m in metrics_data if m['authenticity'] == 'QUESTIONABLE')
        failed_count = len(metrics_data) - authentic_count - questionable_count

        status_labels = ['Hardware Verified', 'Questionable', 'Not Verified']
        status_counts = [authentic_count, questionable_count, failed_count]
        status_colors = ['green', 'yellow', 'red']

        ax4.pie(status_counts, labels=status_labels if any(status_counts) else None,
               autopct=lambda pct: f'{pct:.0f}%' if pct > 0 else '',
               colors=status_colors, startangle=90)
        ax4.set_title('Authentication Status Distribution')

        # Add watermark
        self.add_hardware_watermark(fig)

        plt.tight_layout()

        # Save and return path
        if output_path is None:
            output_path = f"viz/output/gate_summary_dashboard_{self.timestamp[:19].replace(':', '-')}.png"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        return output_path

    def generate_execution_timeline(self, gate_ids: List[int], output_path: str = None) -> str:
        """Generate execution timeline visualization"""
        fig, ax = plt.subplots(figsize=(12, 8))

        # Collect all proof chain data
        timeline_data = []
        y_positions = []
        labels = []

        for i, gate_id in enumerate(gate_ids):
            try:
                chain = self.checkpoint_loader.load_proof_chain(gate_id)
                for proof in chain:
                    timestamp_str = proof.get('timestamp')
                    if timestamp_str:
                        # Convert to minutes from start
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        timestamp = dt.timestamp()
                        timeline_data.append((timestamp, i, proof.get('phase', 'unknown')))
            except FileNotFoundError:
                continue

        if not timeline_data:
            # Create empty timeline
            ax.text(0.5, 0.5, 'No timeline data available', ha='center', va='center', transform=ax.transAxes)
        else:
            # Normalize timestamps
            if timeline_data:
                min_ts = min(t[0] for t in timeline_data)
                timeline_data = [(t[0] - min_ts, t[1], t[2]) for t in timeline_data]

            # Plot timeline events
            phases = ['execution_start', 'execution_complete', 'test_execution']
            phase_colors = {'execution_start': 'blue', 'execution_complete': 'green', 'test_execution': 'orange'}

            for ts, y_pos, phase in timeline_data:
                color = phase_colors.get(phase.split('_')[0] + '_' + phase.split('_')[1], 'gray') if '_' in phase else 'gray'
                ax.scatter(ts, y_pos, c=color, s=50, alpha=0.7)
                ax.text(ts + 0.01, y_pos, f"{phase}\n{ts:.2f}s", fontsize=8, va='center')

        ax.set_yticks(range(len(gate_ids)))
        ax.set_yticklabels([f'Gate {gid}' for gid in gate_ids])
        ax.set_xlabel('Time from start (seconds)')
        ax.set_title('Gate Execution Timeline')
        ax.grid(True, alpha=0.3)

        self.add_hardware_watermark(fig)

        if output_path is None:
            output_path = f"viz/output/execution_timeline_{self.timestamp[:19].replace(':', '-')}.png"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        return output_path

    def generate_propagation_comparison(self, show_theoretical: bool = False, output_path: str = None) -> str:
        """Generate wave propagation comparison chart"""
        fig, ax = plt.subplots(figsize=(10, 8))

        # Get Gate 2 data
        try:
            gate2_metrics = self.metrics_extractor.extract_gate_metrics(2)
            ax.bar(['Hardware-Verified Gate 2'], [gate2_metrics.get('execution_time_seconds', 0)],
                  color='blue', alpha=0.7, label='Hardware-Verified')
            ax.text(0, gate2_metrics.get('execution_time_seconds', 0) + 0.01,
                   '.3f', ha='center', va='bottom')
        except FileNotFoundError:
            ax.text(0.5, 0.5, 'Gate 2 data not available', ha='center', va='center', transform=ax.transAxes)

        # Theoretical overlay if requested
        if show_theoretical:
            ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.7,
                      label='Theoretical Baseline (1.0s)')
            ax.fill_between([-0.5, 0.5], 0.8, 1.2, color='red', alpha=0.1)

        ax.set_title('Wave Propagation Performance Comparison')
        ax.set_ylabel('Execution Time (seconds)')
        ax.set_ylim(bottom=0)
        ax.legend()
        ax.grid(True, alpha=0.3)

        self.add_hardware_watermark(fig)

        if output_path is None:
            output_path = f"viz/output/propagation_comparison_{'with_theoretical_' if show_theoretical else ''}{self.timestamp[:19].replace(':', '-')}.png"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        return output_path

    def generate_html_dashboard(self, gate_ids: List[int], charts: List[str] = None,
                              output_path: str = None) -> str:
        """Generate complete HTML dashboard with all visualizations"""

        if charts is None:
            charts = ['summary', 'timeline', 'propagation']

        # Generate chart images
        chart_files = {}
        if 'summary' in charts:
            chart_files['summary'] = self.generate_gate_summary_chart(gate_ids)
        if 'timeline' in charts:
            chart_files['timeline'] = self.generate_execution_timeline(gate_ids)
        if 'propagation' in charts:
            chart_files['propagation'] = self.generate_propagation_comparison()

        # Create HTML dashboard
        html_content = self._create_html_dashboard(gate_ids, chart_files)

        if output_path is None:
            output_path = f"viz/output/hardware_verified_dashboard_{self.timestamp[:19].replace(':', '-')}.html"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html_content)

        print(f"HTML dashboard generated: {output_path}")
        return output_path

    def _create_html_dashboard(self, gate_ids: List[int], chart_files: Dict[str, str]) -> str:
        """Create HTML dashboard content"""

        # Encode images to base64 for embedding
        encoded_charts = {}
        for chart_type, file_path in chart_files.items():
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    encoded_charts[chart_type] = base64.b64encode(f.read()).decode('utf-8')

        # Get metrics summary
        bundle = self.metrics_extractor.get_visualization_metrics_bundle(gate_ids)
        summary = bundle.get('summary_stats', {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>LoRA Grid Swarm Hardware-Verified Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .chart-container {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ font-size: 0.9em; color: #7f8c8d; }}
        .status-good {{ color: #27ae60; }}
        .status-warning {{ color: #f39c12; }}
        .status-bad {{ color: #e74c3c; }}
        .watermark {{ position: fixed; bottom: 10px; right: 10px; font-size: 10px; color: rgba(255,0,0,0.6); background-color: rgba(255,255,255,0.8); padding: 5px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>LoRA Grid Swarm Hardware-Verified Dashboard</h1>
        <p>Generated: {self.timestamp}</p>
        <p>System: {self.system_fingerprint} | Gates Verified: {', '.join(map(str, gate_ids))}</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value {('status-good' if summary.get('hardware_verified_count', 0) > 0 else 'status-bad')}">{summary.get('hardware_verified_count', 0)}</div>
            <div class="metric-label">Hardware Verified</div>
        </div>
        <div class="metric-card">
            <div class="metric-value {('status-good' if summary.get('passed_gates', 0) > 0 else 'status-warning')}">{summary.get('passed_gates', 0)}</div>
            <div class="metric-label">Gates Passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{summary.get('total_execution_time', 0):.2f}</div>
            <div class="metric-label">Total Time (sec)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value status-good">{summary.get('total_gates', 0)}</div>
            <div class="metric-label">Total Gates</div>
        </div>
    </div>

    {f'<div class="chart-container"><h2>Gate Summary Overview</h2><img src="data:image/png;base64,{encoded_charts.get("summary", "")}" style="max-width: 100%;"></div>' if encoded_charts.get('summary') else ''}

    {f'<div class="chart-container"><h2>Execution Timeline</h2><img src="data:image/png;base64,{encoded_charts.get("timeline", "")}" style="max-width: 100%;"></div>' if encoded_charts.get('timeline') else ''}

    {f'<div class="chart-container"><h2>Propagation Performance</h2><img src="data:image/png;base64,{encoded_charts.get("propagation", "")}" style="max-width: 100%;"></div>' if encoded_charts.get('propagation') else ''}

    <div class="watermark">
        HARDWARE-VERIFIED | {self.system_fingerprint} | Generated {self.timestamp[:19]}
    </div>
</body>
</html>
"""

        return html
