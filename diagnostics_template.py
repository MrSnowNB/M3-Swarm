"""
Diagnostics Template - Error detection and recovery utilities
AI Agent: Implement this module to monitor health and detect bottlenecks
"""

import asyncio
import psutil
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import subprocess
import sys

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    check_name: str
    status: str  # 'healthy', 'warning', 'critical', 'unknown'
    value: Any
    threshold: Any
    message: str
    timestamp: float

@dataclass
class BottleneckAnalysis:
    """Analysis of performance bottlenecks"""
    bottleneck_type: str  # 'memory', 'cpu', 'ioload', 'ollama', 'network'
    severity: str  # 'minor', 'moderate', 'severe', 'critical'
    current_value: float
    threshold: float
    recommendation: str
    confidence: float  # 0.0 to 1.0

class Diagnostics:
    """
    Comprehensive diagnostics and health monitoring for Swarm-100

    Responsibilities:
    - Memory pressure detection
    - CPU utilization monitoring
    - Ollama service health checks
    - Performance bottleneck analysis
    - Automated recovery suggestions
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.baseline_metrics = {}
        self.alert_history = []

        # Hardware thresholds from config
        self.memory_critical_percent = 95
        self.cpu_critical_percent = 95
        self.max_acceptable_response_time = 5.0  # seconds

    async def check_system_health(self) -> List[HealthCheckResult]:
        """
        Perform comprehensive system health check

        Returns:
            List of HealthCheckResult objects
        """
        results = []

        # Memory check
        memory_result = await self._check_memory_health()
        results.append(memory_result)

        # CPU check
        cpu_result = await self._check_cpu_health()
        results.append(cpu_result)

        # Ollama connectivity check
        ollama_result = await self._check_ollama_health()
        results.append(ollama_result)

        # Swap/file system check
        swap_result = await self._check_swap_health()
        results.append(swap_result)

        return results

    async def _check_memory_health(self) -> HealthCheckResult:
        """Check memory utilization and pressure"""
        memory = psutil.virtual_memory()

        available_gb = memory.available / (1024 ** 3)
        percent_used = memory.percent
        total_gb = memory.total / (1024 ** 3)

        # Determine status based on thresholds
        if percent_used >= self.memory_critical_percent:
            status = 'critical'
            message = f"Critical memory usage: {percent_used:.1f}% ({available_gb:.1f}GB available)"
        elif percent_used >= 80:
            status = 'warning'
            message = f"High memory usage: {percent_used:.1f}% (Threshold: 80%)"
        else:
            status = 'healthy'
            message = f"Memory healthy: {percent_used:.1f}% used"

        return HealthCheckResult(
            check_name='system_memory',
            status=status,
            value=round(percent_used, 2),
            threshold=80,
            message=message,
            timestamp=time.time()
        )

    async def _check_cpu_health(self) -> HealthCheckResult:
        """Check CPU utilization"""
        cpu_percent = psutil.cpu_percent(interval=1)

        if cpu_percent >= self.cpu_critical_percent:
            status = 'critical'
            message = f"Critical CPU usage: {cpu_percent:.1f}%"
        elif cpu_percent >= 80:
            status = 'warning'
            message = f"High CPU usage: {cpu_percent:.1f}% (Threshold: 80%)"
        else:
            status = 'healthy'
            message = f"CPU healthy: {cpu_percent:.1f}% used"

        return HealthCheckResult(
            check_name='system_cpu',
            status=status,
            value=round(cpu_percent, 2),
            threshold=80,
            message=message,
            timestamp=time.time()
        )

    async def _check_ollama_health(self) -> HealthCheckResult:
        """Check Ollama service health"""
        try:
            # Try to connect to Ollama
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Count available models
                lines = result.stdout.strip().split('\n')
                model_count = max(0, len(lines) - 1)  # Subtract header line

                status = 'healthy'
                message = f"Ollama healthy: {model_count} models available"
                value = model_count
            else:
                status = 'critical'
                message = f"Ollama error: {result.stderr.strip()}"
                value = 0

        except subprocess.TimeoutExpired:
            status = 'critical'
            message = "Ollama service timeout"
            value = 0
        except FileNotFoundError:
            status = 'critical'
            message = "Ollama executable not found"
            value = 0
        except Exception as e:
            status = 'unknown'
            message = f"Ollama check failed: {str(e)}"
            value = 0

        return HealthCheckResult(
            check_name='ollama_service',
            status=status,
            value=value,
            threshold=1,  # At least 1 model
            message=message,
            timestamp=time.time()
        )

    async def _check_swap_health(self) -> HealthCheckResult:
        """Check swap usage and file system health"""
        swap = psutil.swap_memory()

        if swap.total > 0:
            swap_used_percent = swap.percent
            message = f"Swap usage: {swap_used_percent:.1f}%"
            status = 'warning' if swap_used_percent > 50 else 'healthy'
        else:
            swap_used_percent = 0
            message = "No swap configured or available"
            status = 'warning'

        return HealthCheckResult(
            check_name='swap_usage',
            status=status,
            value=round(swap_used_percent, 2),
            threshold=50,
            message=message,
            timestamp=time.time()
        )

    async def analyze_bottlenecks(self, metrics: Dict[str, Any]) -> List[BottleneckAnalysis]:
        """
        Analyze performance metrics to identify bottlenecks

        Args:
            metrics: Dictionary containing swarm and system metrics

        Returns:
            List of bottleneck analyses with recommendations
        """
        bottlenecks = []

        # Memory bottleneck
        memory_analysis = self._analyze_memory_bottleneck(metrics)
        if memory_analysis:
            bottlenecks.append(memory_analysis)

        # CPU bottleneck
        cpu_analysis = self._analyze_cpu_bottleneck(metrics)
        if cpu_analysis:
            bottlenecks.append(cpu_analysis)

        # Response time bottleneck
        response_analysis = self._analyze_response_time_bottleneck(metrics)
        if response_analysis:
            bottlenecks.append(response_analysis)

        # Ollama concurrency bottleneck
        ollama_analysis = self._analyze_ollama_bottleneck(metrics)
        if ollama_analysis:
            bottlenecks.append(ollama_analysis)

        return bottlenecks

    def _analyze_memory_bottleneck(self, metrics: Dict[str, Any]) -> Optional[BottleneckAnalysis]:
        """Analyze memory-related bottlenecks"""
        memory_percent = metrics.get('system_resources', {}).get('memory_percent_used', 0)

        if memory_percent >= 90:
            severity = 'critical'
            recommendation = "Reduce bot count or increase system memory. Current usage: {:.1f}%".format(memory_percent)
            confidence = 0.95
        elif memory_percent >= 80:
            severity = 'severe'
            recommendation = "Monitor closely, consider reducing bots by 25% if usage continues to climb."
            confidence = 0.85
        elif memory_percent >= 70:
            severity = 'moderate'
            recommendation = "Consider optimizing model context length or reducing concurrent bots."
            confidence = 0.75
        else:
            return None

        return BottleneckAnalysis(
            bottleneck_type='memory',
            severity=severity,
            current_value=memory_percent,
            threshold=80.0,
            recommendation=recommendation,
            confidence=confidence
        )

    def _analyze_cpu_bottleneck(self, metrics: Dict[str, Any]) -> Optional[BottleneckAnalysis]:
        """Analyze CPU-related bottlenecks"""
        cpu_percent = metrics.get('system_resources', {}).get('cpu_percent', 0)

        if cpu_percent >= 95:
            severity = 'critical'
            recommendation = "Critical CPU load. Reduce bot count immediately."
            confidence = 0.98
        elif cpu_percent >= 85:
            severity = 'severe'
            recommendation = "High CPU usage. Reduce bots by 30-50%."
            confidence = 0.90
        elif cpu_percent >= 70:
            severity = 'moderate'
            recommendation = "Medium CPU load. Monitor and consider gradual reduction."
            confidence = 0.70
        else:
            return None

        return BottleneckAnalysis(
            bottleneck_type='cpu',
            severity=severity,
            current_value=cpu_percent,
            threshold=70.0,
            recommendation=recommendation,
            confidence=confidence
        )

    def _analyze_response_time_bottleneck(self, metrics: Dict[str, Any]) -> Optional[BottleneckAnalysis]:
        """Analyze response time performance bottlenecks"""
        avg_response_time = metrics.get('swarm_metrics', {}).get('avg_response_time', 0)

        if avg_response_time >= 10.0:
            severity = 'critical'
            recommendation = "Response times critically high. Check Ollama service and reduce concurrency."
            confidence = 0.95
        elif avg_response_time >= self.max_acceptable_response_time:
            severity = 'severe'
            recommendation = "Response times above threshold. Investigate model parameters."
            confidence = 0.85
        else:
            return None

        return BottleneckAnalysis(
            bottleneck_type='responsetime',
            severity=severity,
            current_value=avg_response_time,
            threshold=self.max_acceptable_response_time,
            recommendation=recommendation,
            confidence=confidence
        )

    def _analyze_ollama_bottleneck(self, metrics: Dict[str, Any]) -> Optional[BottleneckAnalysis]:
        """Analyze Ollama-specific bottlenecks"""
        # This would need Ollama-specific metrics
        # For now, return None as we need more instrumentation
        return None

    def generate_scaling_recommendations(self, bottlenecks: List[BottleneckAnalysis]) -> Dict[str, Any]:
        """
        Generate scaling recommendations based on bottleneck analysis

        Args:
            bottlenecks: List of identified bottlenecks

        Returns:
            Dict with scaling recommendations
        """
        current_bots = 12  # Default, would come from config
        recommendations = {
            'recommended_bot_count': current_bots,
            'scaling_direction': 'maintain',  # 'up', 'down', 'maintain'
            'confidence': 0.5,
            'rationale': [],
            'immediate_actions': [],
            'long_term_actions': []
        }

        severe_bottlenecks = [b for b in bottlenecks if b.severity in ['severe', 'critical']]
        moderate_bottlenecks = [b for b in bottlenecks if b.severity == 'moderate']

        if severe_bottlenecks:
            # Reduce bots significantly
            reduction_factor = 0.5 if any(b.severity == 'critical' for b in severe_bottlenecks) else 0.7
            recommendations['recommended_bot_count'] = int(current_bots * reduction_factor)
            recommendations['scaling_direction'] = 'down'
            recommendations['confidence'] = 0.9
            recommendations['immediate_actions'].append("Scale down bots by {:.0f}% within next minute".format((1 - reduction_factor) * 100))

            for bottleneck in severe_bottlenecks:
                recommendations['rationale'].append(bottleneck.recommendation)

        elif moderate_bottlenecks and len(moderate_bottlenecks) >= 2:
            # Conservative reduction
            recommendations['recommended_bot_count'] = int(current_bots * 0.8)
            recommendations['scaling_direction'] = 'down'
            recommendations['confidence'] = 0.7
            recommendations['long_term_actions'].append("Monitor and consider reducing bots by 20%")

        elif not bottlenecks:
            # Could potentially scale up
            if current_bots < 24:  # Config max
                recommendations['recommended_bot_count'] = min(current_bots + 2, 24)
                recommendations['scaling_direction'] = 'up'
                recommendations['confidence'] = 0.6
                recommendations['long_term_actions'].append("Resources available for gradual scaling")

        return recommendations

    async def run_comprehensive_diagnostic(self) -> Dict[str, Any]:
        """
        Run comprehensive diagnostic suite

        Returns:
            Complete diagnostic report
        """
        health_results = await self.check_system_health()
        # Would need actual metrics, placeholder
        metrics = self._get_sample_metrics()

        bottlenecks = await self.analyze_bottlenecks(metrics)
        scaling_recommendations = self.generate_scaling_recommendations(bottlenecks)

        return {
            'timestamp': time.time(),
            'health_checks': [result.__dict__ for result in health_results],
            'bottlenecks': [b.__dict__ for b in bottlenecks],
            'scaling_recommendations': scaling_recommendations,
            'current_metrics': metrics
        }

    def _get_sample_metrics(self) -> Dict[str, Any]:
        """Get sample metrics for testing (would be replaced with real monitoring)"""
        return {
            'swarm_metrics': {
                'total_tasks': 100,
                'successful_tasks': 95,
                'failed_tasks': 5,
                'avg_response_time': 2.5
            },
            'system_resources': {
                'available_memory_gb': 20.0,
                'memory_percent_used': 45.0,
                'cpu_percent': 60.0,
                'can_spawn_bot': True,
                'current_bot_count': 10
            }
        }


# AI Agent Validation Tests:
# 1. Health checks run without errors
# 2. Memory pressure detection works accurately
# 3. CPU utilization monitoring is correct
# 4. Ollama service connectivity is properly tested
# 5. Bottleneck analysis identifies performance issues
# 6. Scaling recommendations are practical and safe
# 7. Comprehensive diagnostic report includes all required data
