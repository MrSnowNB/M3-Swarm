#!/usr/bin/env python3
"""
GATE 1: Code Audit Verification
Verify implementation uses threading, not asyncio
"""

import subprocess
import json
import os
from datetime import datetime

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def main():
    print("="*80)
    print("🔬 GATE 1: CODE AUDIT VERIFICATION")
    print("="*80)
    print("Verifying implementation uses threading, not asyncio...\n")

    results = {
        "gate": "1_code_audit",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {}
    }

    # Check 1: Count asyncio usage
    print("📊 Counting asyncio usage...")
    asyncio_cmd = "grep -r 'async def\|await\|asyncio' core/ tests/ --include='*.py' 2>/dev/null | wc -l"
    asyncio_count, _ = run_command(asyncio_cmd)
    asyncio_count = int(asyncio_count.strip()) if asyncio_count.strip().isdigit() else 0
    results["checks"]["asyncio_line_count"] = asyncio_count
    print(f"   Asyncio lines: {asyncio_count}")

    # Check 2: Count threading usage
    print("📊 Counting threading usage...")
    threading_cmd = "grep -r 'threading\.Thread\|concurrent\.futures\|Queue' core/ tests/ --include='*.py' 2>/dev/null | wc -l"
    threading_count, _ = run_command(threading_cmd)
    threading_count = int(threading_count.strip()) if threading_count.strip().isdigit() else 0
    results["checks"]["threading_line_count"] = threading_count
    print(f"   Threading lines: {threading_count}")

    # Check 3: Verify bot_agent.py uses threading
    print("🔍 Checking bot_agent.py...")
    bot_check, bot_rc = run_command("grep -q 'threading.Thread' core/bot_agent.py 2>/dev/null")
    bot_has_threading = (bot_rc == 0)
    results["checks"]["bot_agent_threading"] = bot_has_threading
    print(f"   bot_agent.py uses threading: {bot_has_threading}")

    # Check 4: Verify swarm_manager.py uses threading
    print("🔍 Checking swarm_manager.py...")
    swarm_check, swarm_rc = run_command("grep -q 'threading.Thread' core/swarm_manager.py 2>/dev/null")
    swarm_has_threading = (swarm_rc == 0)
    results["checks"]["swarm_manager_threading"] = swarm_has_threading
    print(f"   swarm_manager.py uses threading: {swarm_has_threading}")

    # Determine pass/fail
    pass_criteria = [
        threading_count > asyncio_count,
        bot_has_threading,
        swarm_has_threading
    ]

    results["passed"] = all(pass_criteria)
    results["summary"] = {
        "threading_dominant": threading_count > asyncio_count,
        "bot_agent_ok": bot_has_threading,
        "swarm_manager_ok": swarm_has_threading
    }

    # Save results
    os.makedirs(".checkpoints", exist_ok=True)
    with open(".checkpoints/gate1_code_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*80)
    if results["passed"]:
        print("✅ GATE 1 PASSED: Threading implementation verified")
    else:
        print("❌ GATE 1 FAILED: Code audit shows asyncio, not threading")
        if asyncio_count >= threading_count:
            print("   Issue: Asyncio usage >= threading usage")
        if not bot_has_threading:
            print("   Issue: bot_agent.py does not use threading")
        if not swarm_has_threading:
            print("   Issue: swarm_manager.py does not use threading")
    print("="*80)

    return 0 if results["passed"] else 1

if __name__ == "__main__":
    exit(main())
