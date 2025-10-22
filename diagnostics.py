"""
Diagnostic utilities for error detection and recovery
AI Agent: Use these functions to monitor and diagnose issues
"""

import psutil
import time
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class DiagnosticResult:
    """Result of diagnostic check"""
    check_name: str
    status: str  # OK | WARNING | ERROR
    message: str
    data: Dict[str, Any]
    timestamp: float

class SystemDiagnostics:
    """Monitor and diagnose system health"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.history: List[DiagnosticResult] = []
        self.logger = logging.getLogger(__name__)

    def check_memory_pressure(self) -> DiagnosticResult:
        """Check if system is under memory pressure"""
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        available_gb = memory.available / (1024 ** 3)

        max_threshold = self.config.get('swarm', {}).get('resource_limits', {}).get('max_memory_percent', 80)

        if percent_used > max_threshold:
            status = "ERROR"
            message = f"Memory usage {percent_used:.1f}% exceeds threshold {max_threshold}%"
        elif percent_used > max_threshold * 0.8:
            status = "WARNING"
            message = f"Memory usage {percent_used:.1f}% approaching threshold"
        else:
            status = "OK"
            message = f"Memory usage {percent_used:.1f}% is healthy"

        result = DiagnosticResult(
            check_name="memory_pressure",
            status=status,
            message=message,
            data={
                'percent_used': percent_used,
                'available_gb': available_gb,
                'threshold': max_threshold
            },
            timestamp=time.time()
        )

        self.history.append(result)
        return result

    def check_cpu_load(self) -> DiagnosticResult:
        """Check CPU utilization"""
        cpu_percent = psutil.cpu_percent(interval=1)
        max_threshold = self.config.get('swarm', {}).get('resource_limits', {}).get('max_cpu_percent', 90)

        if cpu_percent > max_threshold:
            status = "ERROR"
            message = f"CPU usage {cpu_percent:.1f}% exceeds threshold"
        elif cpu_percent > max_threshold * 0.8:
            status = "WARNING"
            message = f"CPU usage {cpu_percent:.1f}% approaching threshold"
        else:
            status = "OK"
            message = f"CPU usage {cpu_percent:.1f}% is healthy"

        result = DiagnosticResult(
            check_name="cpu_load",
            status=status,
            message=message,
            data={'cpu_percent': cpu_percent, 'threshold': max_threshold},
            timestamp=time.time()
        )

        self.history.append(result)
        return result

    def recommend_scaling(self, current_bots: int, success_rate: float) -> Dict[str, Any]:
        """Recommend scaling action based on current state"""
        memory_check = self.check_memory_pressure()
        cpu_check = self.check_cpu_load()

        recommendation = {
            'action': 'maintain',
            'suggested_bots': current_bots,
            'reason': 'System performing well'
        }

        # Check for problems
        if memory_check.status == "ERROR" or cpu_check.status == "ERROR":
            recommendation['action'] = 'scale_down'
            recommendation['suggested_bots'] = max(2, current_bots // 2)
            recommendation['reason'] = 'Resource exhaustion detected'

        elif success_rate < 0.75:
            recommendation['action'] = 'scale_down'
            recommendation['suggested_bots'] = max(2, int(current_bots * 0.75))
            recommendation['reason'] = f'Low success rate: {success_rate:.1%}'

        elif (memory_check.status == "OK" and 
              cpu_check.status == "OK" and 
              success_rate > 0.9):
            recommendation['action'] = 'scale_up'
            recommendation['suggested_bots'] = current_bots + 2
            recommendation['reason'] = 'System has capacity for more bots'

        return recommendation

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        recent_checks = self.history[-10:] if len(self.history) > 10 else self.history

        error_count = sum(1 for c in recent_checks if c.status == "ERROR")
        warning_count = sum(1 for c in recent_checks if c.status == "WARNING")

        if error_count > 0:
            health = "CRITICAL"
        elif warning_count > 3:
            health = "DEGRADED"
        else:
            health = "HEALTHY"

        return {
            'overall_health': health,
            'recent_errors': error_count,
            'recent_warnings': warning_count,
            'total_checks': len(self.history)
        }
