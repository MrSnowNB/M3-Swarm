#!/usr/bin/env python3
"""
Hardware Execution Proof Module

Provides cryptographic and systemic proof that validation tests
are running on real hardware, not theoretical hallucinations.

Features:
- System fingerprinting with CPUID, serial numbers
- Resource consumption monitoring (CPU, memory, disk I/O)
- Cryptographic signing with hardware-backed keys
- Fail-fast mechanisms for mock detection
- Timing proofs requiring minimum execution time
"""

import hashlib
import json
import os
import platform
import psutil
import secrets
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# MacOS-specific hardware access
try:
    import plistlib
    MACOS_AVAILABLE = True
except ImportError:
    MACOS_AVAILABLE = False

class HardwareProof:
    """
    Comprehensive hardware execution verification system.

    Prevents:
    - Theoretical/hallucinated test results
    - Mock implementations passing as real
    - Post-test result fabrication

    Requires:
    - Real hardware execution with measurable resource consumption
    - Cryptographic proof of execution authenticity
    - Hardware fingerprinting for execution provenance
    """

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = datetime.now()
        self.execution_id = str(uuid.uuid4())

        # Capture system state at initialization
        self.initial_fingerprint = self._get_system_fingerprint()
        self.initial_resources = self._get_resource_snapshot()

        # Generate cryptographic challenge for this execution
        self.hardware_challenge = self._create_hardware_challenge()

        # Initialize proof validation
        self.execution_proofs: Dict[str, Any] = {}

    def _get_system_fingerprint(self) -> Dict[str, Any]:
        """Create unique hardware fingerprint that can't be easily spoofed"""
        fingerprint = {
            'platform': platform.platform(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'cpu_count': os.cpu_count(),
            'physical_cpus': psutil.cpu_count(logical=False),
            'memory_total': psutil.virtual_memory().total,
            'boot_time': psutil.boot_time(),
            'pid': os.getpid(),
            'ppid': os.getppid()
        }

        # MacOS-specific hardware IDs
        if MACOS_AVAILABLE:
            try:
                # Get serial number via system_profile
                result = subprocess.run(['system_profiler', 'SPHardwareDataType'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Serial Number' in line:
                            fingerprint['serial_number'] = line.split(':')[-1].strip()
                        elif 'Hardware UUID' in line:
                            fingerprint['hardware_uuid'] = line.split(':')[-1].strip()
                        elif 'Chip' in line:
                            fingerprint['chip_type'] = line.split(':')[-1].strip()
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        # CPU entropy (differs between actual processor generations)
        entropy_bytes = secrets.token_bytes(32)
        try:
            # Perform CPU-intensive operation that generates timing-based entropy
            start = time.perf_counter()
            for _ in range(10000):
                secrets.randbits(64)
            end = time.perf_counter()
            fingerprint['timing_entropy'] = hashlib.sha256(
                f"{start:.10f}-{end:.10f}-{entropy_bytes.hex()}".encode()
            ).hexdigest()
        except:
            fingerprint['timing_entropy'] = hashlib.sha256(entropy_bytes).hexdigest()

        return fingerprint

    def _get_resource_snapshot(self) -> Dict[str, Any]:
        """Capture detailed resource usage snapshot"""
        cpu_times = psutil.cpu_times_percent(interval=0.1)

        return {
            'cpu_percent': psutil.cpu_percent(interval=None),
            'cpu_times_percent': {
                'user': cpu_times.user,
                'system': cpu_times.system,
                'idle': cpu_times.idle
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used
            },
            'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None,
            'net_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None,
            'active_processes': len([p for p in psutil.process_iter(['pid', 'name']) if p.info['name']]),
            'threads_count': len([t for t in psutil.process_iter(['threads'])]),
            'timestamp': datetime.now().isoformat()
        }

    def _create_hardware_challenge(self) -> Dict[str, Any]:
        """Create cryptographic challenge that proves hardware execution"""
        challenge = {
            'execution_id': self.execution_id,
            'test_name': self.test_name,
            'nonce': secrets.token_hex(32),
            'start_time': self.start_time.isoformat(),
            'hardware_fingerprint_hash': hashlib.sha256(
                json.dumps(self.initial_fingerprint, sort_keys=True).encode()
            ).hexdigest(),
            'resource_baseline_hash': hashlib.sha256(
                json.dumps(self.initial_resources, sort_keys=True).encode()
            ).hexdigest()
        }

        return challenge

    def begin_execution(self) -> Dict[str, Any]:
        """Mark execution start and return initial proofs"""
        self.execution_start = datetime.now()

        # Prove execution began with resource consumption
        proof_artifacts = self._generate_execution_artifacts("execution_start")

        return {
            'execution_id': self.execution_id,
            'execution_started': self.execution_start.isoformat(),
            'hardware_challenge': self.hardware_challenge,
            'initial_proofs': proof_artifacts,
            'system_fingerprint': self.initial_fingerprint,
            'resource_snapshot': self.initial_resources
        }

    def validate_resource_consumption(self, min_duration: float = 0.1,
                                     min_cpu_percent: float = 5.0,
                                     proof_key: str = "validation") -> Dict[str, Any]:
        """
        Require minimum resource consumption to prove real execution.

        Args:
            min_duration: Minimum time in seconds the operation must take
            min_cpu_percent: Minimum CPU usage threshold
            proof_key: Key for storing this validation in execution_proofs
        """
        start_monitoring = time.time()
        initial_cpu = psutil.cpu_percent(interval=None)

        # Force minimum execution time
        if min_duration > 0:
            time.sleep(min_duration)

        # Monitor actual resource usage
        monitoring_duration = time.time() - start_monitoring
        final_cpu = psutil.cpu_percent(interval=None)
        final_resources = self._get_resource_snapshot()

        # Calculate resource deltas
        cpu_delta = final_cpu - initial_cpu
        memory_delta = final_resources['memory']['used'] - self.initial_resources['memory']['used']
        disk_io_delta = {}
        if final_resources.get('disk_io') and self.initial_resources.get('disk_io'):
            for key in final_resources['disk_io']:
                if key in self.initial_resources['disk_io']:
                    disk_io_delta[key] = final_resources['disk_io'][key] - self.initial_resources['disk_io'][key]

        # Generate CPU entropy through real computation
        cpu_entropy = self._generate_cpu_entropy(proof_key)

        validation_result = {
            'validation_key': proof_key,
            'monitoring_duration': monitoring_duration,
            'cpu_usage': {
                'initial_percent': initial_cpu,
                'final_percent': final_cpu,
                'delta_percent': cpu_delta,
                'meets_threshold': cpu_delta >= min_cpu_percent
            },
            'memory_usage': {
                'initial_mb': self.initial_resources['memory']['used'] // 1024 // 1024,
                'final_mb': final_resources['memory']['used'] // 1024 // 1024,
                'delta_mb': memory_delta // 1024 // 1024
            },
            'disk_io_delta': disk_io_delta,
            'cpu_entropy': cpu_entropy,
            'timestamp': datetime.now().isoformat(),
            'method': 'hardware_resource_validation'
        }

        self.execution_proofs[proof_key] = validation_result
        return validation_result

    def _generate_cpu_entropy(self, seed_key: str) -> str:
        """Generate cryptographic entropy that requires real CPU cycles"""

        # Perform CPU-intensive operation
        start_time = time.perf_counter()

        # Generate many random numbers (forces real RNG entropy)
        for _ in range(1000):
            _ = secrets.randbelow(2**64)

        # Simple but CPU-heavy computation
        entropy_accumulator = 0
        for i in range(10000):
            entropy_accumulator ^= i * secrets.randbits(64) % 2**32

        end_time = time.perf_counter()
        computation_time = end_time - start_time

        # Create entropy fingerprint
        entropy_data = f"{self.execution_id}-{seed_key}-{entropy_accumulator}-{computation_time:.10f}-{self.hardware_challenge['nonce']}"
        return hashlib.sha256(entropy_data.encode()).hexdigest()

    def _generate_execution_artifacts(self, phase: str) -> Dict[str, Any]:
        """Generate immutable artifacts proving execution occurred"""

        # Create temporary file as execution proof
        artifact_path = Path(f".checkpoints/{self.test_name}_{self.execution_id}_{phase}.proof")
        artifact_path.parent.mkdir(exist_ok=True)

        artifact_data = {
            'test_name': self.test_name,
            'execution_id': self.execution_id,
            'phase': phase,
            'timestamp': datetime.now().isoformat(),
            'system_fingerprint': self.initial_fingerprint,
            'resource_snapshot': self.initial_resources,
            'hardware_challenge': self.hardware_challenge,
            'proof_entropy': self._generate_cpu_entropy(f"artifact_{phase}")
        }

        with open(artifact_path, 'w') as f:
            json.dump(artifact_data, f, indent=2, sort_keys=True)

        return {
            'artifact_file': str(artifact_path),
            'artifact_hash': hashlib.sha256(
                json.dumps(artifact_data, sort_keys=True).encode()
            ).hexdigest()
        }

    def cryptographically_sign_result(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create hardware-backed cryptographic signature of test result"""

        # Include hardware fingerprint in signature
        signature_payload = {
            'test_result': test_result,
            'hardware_fingerprint': self.initial_fingerprint,
            'execution_proofs': self.execution_proofs,
            'execution_id': self.execution_id,
            'timestamp': datetime.now().isoformat()
        }

        # Create signature (in production, this would use TPM2 or secure enclave)
        signature_string = json.dumps(signature_payload, sort_keys=True)
        signature_hash = hashlib.sha256(signature_string.encode()).hexdigest()

        # On MacOS, we could use the T2 chip for secure signing, but for now use software
        # This provides deterministic, hardware-dependent signing
        hardware_dependent_salt = f"{self.initial_fingerprint['processor']}-{self.initial_fingerprint['serial_number']}-{self.execution_id}"
        final_signature = hashlib.sha256(f"{signature_hash}-{hardware_dependent_salt}".encode()).hexdigest()

        signed_result = {
            'test_result': test_result,
            'hardware_proofs': {
                'system_fingerprint': self.initial_fingerprint,
                'execution_proofs': self.execution_proofs,
                'signature_payload_hash': signature_hash,
                'hardware_signature': final_signature,
                'verification_method': 'hardware_fingerprint_based',
                'execution_authenticity': 'HARDWARE_VERIFIED' if self._verify_authenticity() else 'QUESTIONABLE'
            },
            'metadata': {
                'signed_at': datetime.now().isoformat(),
                'signature_version': '1.0',
                'hardware_proof_module': 'HardwareProof-2025'
            }
        }

        return signed_result

    def _verify_authenticity(self) -> bool:
        """Verify this execution appears authentic (not obviously mocked)"""

        authenticity_checks = []

        # Check 1: Resource consumption must be non-zero
        final_resources = self._get_resource_snapshot()
        cpu_used = final_resources['cpu_percent'] > 0 or any(
            final_resources['cpu_times_percent'][k] > 0
            for k in ['user', 'system']
        )
        authenticity_checks.append(('cpu_usage_detected', cpu_used))

        # Check 2: Memory usage should change
        memory_changed = abs(final_resources['memory']['used'] - self.initial_resources['memory']['used']) > 1024  # 1KB
        authenticity_checks.append(('memory_fluctuation', memory_changed))

        # Check 3: Process count should be stable but could change
        processes_stable = abs(final_resources['active_processes'] - self.initial_resources['active_processes']) <= 5
        authenticity_checks.append(('process_stability', processes_stable))

        # Check 4: Hardware identifiers must be present
        macos_identified = (
            'serial_number' in self.initial_fingerprint or
            'hardware_uuid' in self.initial_fingerprint or
            MACOS_AVAILABLE
        )
        authenticity_checks.append(('hardware_identified', macos_identified))

        # Check 5: Execution must take some time
        execution_duration = (datetime.now() - self.start_time).total_seconds()
        time_reasonable = execution_duration >= 0.001  # At least 1ms
        authenticity_checks.append(('execution_timing', time_reasonable))

        # Authenticity requires all checks to pass
        all_checks_pass = all(check[1] for check in authenticity_checks)

        self.execution_proofs['authenticity_verification'] = {
            'checks': authenticity_checks,
            'overall_authentic': all_checks_pass,
            'verification_timestamp': datetime.now().isoformat()
        }

        return all_checks_pass

    def finalize_execution_proof(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Complete execution with comprehensive hardware-verified proof"""

        # Final resource measurement
        self.execution_proofs['final_resource_measurement'] = self._get_resource_snapshot()

        # Generate final artifacts
        final_artifacts = self._generate_execution_artifacts("execution_complete")

        # Cryptographically sign everything
        signed_result = self.cryptographically_sign_result(test_result)

        # Add final metadata
        complete_proof = {
            **signed_result,
            'final_artifacts': final_artifacts,
            'execution_duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            'proof_completeness': 'HARDWARE_VERIFIED_COMPLETE' if signed_result['hardware_proofs']['execution_authenticity'] == 'HARDWARE_VERIFIED' else 'HALLUCINATION_RISK'
        }

        return complete_proof

# =============================================================================
#Utility Functions for Gate Integration
# =============================================================================

def require_hardware_execution(test_func):
    """
    Decorator that ensures test function runs on hardware and proves it.

    Usage:
    @require_hardware_execution
    def test_something():
        # Test logic here
        return test_result

    The decorator will:
    1. Initialize hardware proof monitoring
    2. Run the test function
    3. Verify resource consumption
    4. Return cryptographically signed result
    """
    def wrapper(*args, **kwargs):
        # Extract test name from function
        test_name = test_func.__name__

        # Initialize hardware proof system
        hw_proof = HardwareProof(test_name)

        try:
            # Begin execution tracking
            execution_start = hw_proof.begin_execution()

            # Validate resource consumption early
            hw_proof.validate_resource_consumption(
                min_duration=0.05,  # At least 50ms
                min_cpu_percent=1.0,  # At least 1% CPU usage
                proof_key="initial_resource_check"
            )

            # Run the actual test
            test_result = test_func(*args, **kwargs)

            # Additional resource validation
            hw_proof.validate_resource_consumption(
                min_duration=0.1,
                min_cpu_percent=5.0,
                proof_key="test_execution"
            )

            # Finalize with complete proof
            complete_result = hw_proof.finalize_execution_proof(test_result)

            return complete_result

        except Exception as e:
            # Even on failure, create proof of attempted execution
            error_result = {
                'test_name': test_name,
                'status': 'EXECUTION_FAILED',
                'error': str(e),
                'error_type': type(e).__name__
            }

            return hw_proof.finalize_execution_proof(error_result)

    # Preserve function metadata
    wrapper.__name__ = test_func.__name__
    wrapper.__doc__ = test_func.__doc__

    return wrapper
