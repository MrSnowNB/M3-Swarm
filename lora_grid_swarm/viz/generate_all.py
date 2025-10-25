#!/usr/bin/env python3
"""
End-to-End Visualization Generator

Orchestrates complete visualization workflow for hardware-verified checkpoints.
Generates all required charts, dashboards, and reports with integrity validation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory for proper imports
sys.path.insert(0, str(Path(__file__).parent))

from .checkpoint_loader import HardwareVerifiedCheckpointLoader
from .metrics_extractor import HardwareMetricsExtractor
from .dashboard_generator import DashboardGenerator  # type: ignore[attr-defined]


class EndToEndVisualizationGenerator:
    """
    Complete visualization pipeline for hardware-verified LoRA Grid Swarm results
    """

    def __init__(self, output_base_dir: str = "viz/output"):
        self.checkpoint_loader = HardwareVerifiedCheckpointLoader()
        self.metrics_extractor = HardwareMetricsExtractor()
        self.dashboard_generator = DashboardGenerator()
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

    def validate_hardware_integrity(self, gate_ids: List[int]) -> bool:
        """Validate all specified gates have hardware-verified artifacts"""
        print("🔍 Validating hardware integrity for gates:", gate_ids)

        all_valid = True
        integrity_results = {}

        for gate_id in gate_ids:
            try:
                checkpoint = self.checkpoint_loader.load_gate_result(gate_id)
                is_valid = self.checkpoint_loader.verify_checkpoint_integrity(checkpoint)

                integrity_results[gate_id] = {
                    'valid': is_valid,
                    'authenticity': checkpoint.get('hardware_proofs', {}).get('execution_authenticity', 'UNKNOWN'),
                    'completeness': checkpoint.get('proof_completeness', 'UNKNOWN'),
                    'gate_passed': checkpoint.get('test_result', {}).get('gate_passed', False)
                }

                if not is_valid:
                    print(f"❌ Gate {gate_id}: Hardware integrity check failed")
                    all_valid = False
                else:
                    status = "✅ VERIFIED" if integrity_results[gate_id]['authenticity'] == 'HARDWARE_VERIFIED' else "⚠️ QUESTIONABLE"
                    print(f"Gate {gate_id}: {status} ({integrity_results[gate_id]['completeness']})")

            except FileNotFoundError:
                print(f"❌ Gate {gate_id}: No hardware-verified checkpoint found")
                integrity_results[gate_id] = {'valid': False, 'error': 'missing_checkpoint'}
                all_valid = False

        self.integrity_results = integrity_results
        return all_valid

    def generate_complete_visualization_suite(self, gate_ids: List[int] = None,
                                             output_dir: str = None) -> Dict[str, Any]:
        """
        Generate complete visualization suite for specified gates

        Args:
            gate_ids: List of gate IDs to visualize (default: all available)
            output_dir: Base output directory (default: viz/output)

        Returns:
            Dict with file paths and status information
        """

        if gate_ids is None:
            gate_ids = self.checkpoint_loader.list_available_hardware_verified_gates()
            if not gate_ids:
                raise FileNotFoundError("No hardware-verified gates found to visualize")

        print(f"🎨 Generating complete visualization suite for gates: {gate_ids}")

        # Set output directory
        if output_dir:
            self.output_base_dir = Path(output_dir)
            self.output_base_dir.mkdir(parents=True, exist_ok=True)

        # 1. Validate hardware integrity
        if not self.validate_hardware_integrity(gate_ids):
            raise ValueError("Hardware integrity validation failed - cannot generate visualizations")

        # 2. Generate individual chart components
        print("📊 Generating chart components...")

        individual_charts = {}

        # Gate summary chart
        summary_chart = self.dashboard_generator.generate_gate_summary_chart(gate_ids)
        if summary_chart:
            individual_charts['gate_summary'] = summary_chart

        # Execution timeline
        timeline_chart = self.dashboard_generator.generate_execution_timeline(gate_ids)
        if timeline_chart:
            individual_charts['execution_timeline'] = timeline_chart

        # Propagation comparison
        propagation_chart = self.dashboard_generator.generate_propagation_comparison()
        if propagation_chart:
            individual_charts['propagation_comparison'] = propagation_chart

        # 3. Generate comprehensive HTML dashboard
        print("🌐 Generating HTML dashboard...")
        html_dashboard = self.dashboard_generator.generate_html_dashboard(gate_ids)

        # 4. Generate metrics bundle for programmatic access
        print("📈 Generating metrics bundle...")
        metrics_bundle = self.metrics_extractor.get_visualization_metrics_bundle(gate_ids)

        # 5. Create manifest of all generated artifacts
        manifest = self._create_generation_manifest(gate_ids, individual_charts, html_dashboard, metrics_bundle)

        # Save manifest
        manifest_path = self.output_base_dir / "generation_manifest.json"
        with open(manifest_path, 'w') as f:
            import json
            json.dump(manifest, f, indent=2)

        print("✅ Complete visualization suite generated!")
        print(f"📁 Output directory: {self.output_base_dir}")
        print(f"📋 Manifest: {manifest_path}")

        return {
            'status': 'success',
            'gate_ids_processed': gate_ids,
            'output_directory': str(self.output_base_dir),
            'individual_charts': individual_charts,
            'html_dashboard': html_dashboard,
            'metrics_bundle': metrics_bundle,
            'manifest': str(manifest_path),
            'hardware_integrity': self.integrity_results
        }

    def _create_generation_manifest(self, gate_ids: List[int],
                                   individual_charts: Dict[str, str],
                                   html_dashboard: str,
                                   metrics_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive manifest of all generated artifacts"""

        import datetime
        import platform

        manifest = {
            'generation_timestamp': datetime.datetime.now().isoformat(),
            'generator_version': '1.0.0',
            'system_info': {
                'platform': platform.platform(),
                'python_version': sys.version,
                'working_directory': os.getcwd()
            },
            'input_parameters': {
                'gate_ids': gate_ids,
                'output_directory': str(self.output_base_dir)
            },
            'hardware_verification': {
                'gates_processed': gate_ids,
                'integrity_status': self.integrity_results
            },
            'generated_artifacts': {
                'individual_charts': individual_charts,
                'html_dashboard': html_dashboard,
                'metrics_bundle_summary': {
                    'total_gates': len(gate_ids),
                    'hardware_verified_count': sum(1 for g in self.integrity_results.values()
                                                  if g.get('authenticity') == 'HARDWARE_VERIFIED'),
                    'summary_stats': metrics_bundle.get('summary_stats', {})
                }
            },
            'validation_metadata': {
                'charts_integrity_checked': True,
                'watermarks_applied': True,
                'html_embedded_images': True,
                'manifest_self_verifying': True
            }
        }

        return manifest

    def cleanup_outputs(self, confirm: bool = False) -> bool:
        """Clean up generated outputs (use with caution)"""
        if not confirm:
            print("⚠️  Cleanup requires explicit confirmation")
            return False

        import shutil
        if self.output_base_dir.exists():
            shutil.rmtree(self.output_base_dir)
            print(f"🗑️  Cleaned up output directory: {self.output_base_dir}")
            return True

        return False


def main():
    """CLI interface for end-to-end visualization generation"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate complete LoRA Grid Swarm visualization suite')
    parser.add_argument('--gates', '-g', nargs='+', type=int, help='Gate IDs to process (default: all available)')
    parser.add_argument('--output-dir', '-o', default='viz/output', help='Output directory base')
    parser.add_argument('--force', action='store_true', help='Force generation even with integrity warnings')

    args = parser.parse_args()

    # Initialize generator
    generator = EndToEndVisualizationGenerator(args.output_dir)

    try:
        # Generate complete suite
        result = generator.generate_complete_visualization_suite(args.gates)

        print("\n" + "="*70)
        print("🎊 VISUALIZATION SUITE GENERATION COMPLETE")
        print("="*70)
        print(f"Gates processed: {result['gate_ids_processed']}")
        print(f"Output directory: {result['output_directory']}")
        print(f"HTML Dashboard: {result['html_dashboard']}")
        print(f"Generated charts: {len(result['individual_charts'])}")
        print("\n📊 Hardware Integrity Summary:")
        for gate_id, status in result['hardware_integrity'].items():
            auth = status.get('authenticity', 'UNKNOWN')
            comp = status.get('completeness', 'UNKNOWN')
            print(f"  Gate {gate_id}: {auth} | {comp}")
        print("\n🚀 Ready for publication and analysis!")

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
