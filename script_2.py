
# 2. TROUBLESHOOTING GUIDE - Separate diagnostic document for AI agents
troubleshooting_guide = """# 🔧 AI-First Troubleshooting Guide - Swarm-100 MacOS

## Purpose
This guide provides diagnostic procedures and recovery steps for autonomous AI coding agents building the Swarm-100 MacOS system.

## Critical Rules for AI Agents
1. **NEVER skip diagnostic steps**
2. **ALWAYS log every action and result**
3. **Request human intervention after 3 failed attempts**
4. **Document unexpected behavior immediately**

---

## Common Issues and Recovery Procedures

### ISSUE-001: Ollama Not Found

**Symptoms:**
```
Command 'ollama' not found
which ollama returns empty
```

**Diagnostic Steps:**
```bash
# 1. Check if installed via Homebrew
brew list | grep ollama

# 2. Check PATH
echo $PATH

# 3. Check common locations
ls -la /usr/local/bin/ollama
ls -la /opt/homebrew/bin/ollama
```

**Recovery:**
```bash
# Option 1: Install via Homebrew
brew install ollama

# Option 2: Direct download
curl https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

**Validation:**
- ollama --version returns valid version string
- Log: ISSUE-001 RESOLVED

---

### ISSUE-002: Ollama Service Not Running

**Symptoms:**
```
Error: could not connect to ollama app
Connection refused on localhost:11434
```

**Diagnostic Steps:**
```bash
# 1. Check if process is running
ps aux | grep ollama

# 2. Try to connect
curl http://localhost:11434/api/tags
```

**Recovery:**
```bash
# Start Ollama service
ollama serve > logs/ollama.log 2>&1 &

# Wait for startup
sleep 5

# Verify
curl http://localhost:11434/api/tags
```

**Validation:**
- curl returns JSON response (not connection error)
- ps aux shows ollama process
- Log: ISSUE-002 RESOLVED

---

### ISSUE-003: Model Not Available

**Symptoms:**
```
Error: model 'gemma3:270m' not found
ollama list doesn't show model
```

**Diagnostic Steps:**
```bash
# Check available models
ollama list

# Check disk space
df -h
```

**Recovery:**
```bash
# Pull the model
ollama pull gemma3:270m

# Monitor progress
# This may take 2-5 minutes depending on connection

# Verify
ollama list | grep gemma3:270m
```

**Validation:**
- Model appears in ollama list
- Can run: ollama run gemma3:270m "test"
- Log: ISSUE-003 RESOLVED

---

### ISSUE-004: Python Dependencies Failed

**Symptoms:**
```
pip install failed
ModuleNotFoundError: No module named 'X'
Import errors
```

**Diagnostic Steps:**
```bash
# Check Python version
python3 --version

# Check pip version
pip3 --version

# Check virtual environment
which python

# List installed packages
pip list
```

**Recovery:**
```bash
# Update pip
pip3 install --upgrade pip

# Clean install dependencies
pip3 install --no-cache-dir -r requirements.txt

# If specific package fails, try individually
pip3 install ollama --force-reinstall
pip3 install psutil --force-reinstall

# Verify imports
python3 -c "import ollama, asyncio, psutil, yaml; print('SUCCESS')"
```

**Validation:**
- All imports succeed
- pip list shows all required packages
- Log: ISSUE-004 RESOLVED

---

### ISSUE-005: Bot Agent Test Fails

**Symptoms:**
```
tests/test_bot_agent.py fails
Bot cannot execute prompts
Timeout errors
```

**Diagnostic Steps:**
```bash
# 1. Test Ollama connection manually
python3 -c "import ollama; client = ollama.Client(); print(client.list())"

# 2. Test single inference
ollama run gemma3:270m "Hello"

# 3. Check logs
cat logs/bot_agent_debug.log

# 4. Review implementation
diff core/bot_agent.py templates/bot_agent_template.py
```

**Recovery:**
```bash
# 1. Verify Ollama is responsive
curl -X POST http://localhost:11434/api/generate -d '{"model":"gemma3:270m","prompt":"test"}'

# 2. Increase timeouts in bot_agent.py
# Edit: timeout=30 to timeout=60

# 3. Add debug logging
# Edit bot_agent.py to add print statements

# 4. Test with minimal configuration
python3 tests/test_bot_agent.py --debug --single-test
```

**AI Agent Actions:**
1. Compare implementation vs template line by line
2. Check for async/await mistakes
3. Verify Ollama client initialization
4. Test with simplified prompt
5. If 3 attempts fail: REQUEST HUMAN REVIEW

**Validation:**
- Single bot can execute "test" prompt successfully
- Response is received and logged
- No timeout errors
- Log: ISSUE-005 RESOLVED

---

### ISSUE-006: Swarm Manager Crashes

**Symptoms:**
```
Multiple bots spawn but system hangs
OOM (Out of Memory) errors
Process killed by OS
```

**Diagnostic Steps:**
```bash
# 1. Check system resources
top -l 1 | grep PhysMem
ps aux | grep python

# 2. Check Ollama memory usage
ps aux | grep ollama

# 3. Review error logs
tail -100 logs/errors.log

# 4. Check for resource leaks
lsof -p $(pgrep python)
```

**Recovery:**
```bash
# 1. Reduce concurrency
# Edit config/swarm_config.yaml:
# max_concurrent_bots: 6  # Down from 12

# 2. Reduce context window
# Edit config/models.yaml:
# num_ctx: 1024  # Down from 2048

# 3. Enable memory monitoring
# Edit core/swarm_manager.py:
# Add: check_memory_before_spawn()

# 4. Test with minimal load
python3 tests/test_swarm_manager.py --bots 2
```

**AI Agent Actions:**
1. Calculate available memory: 36GB - system_usage
2. Estimate per-bot memory: ~1GB for gemma3:270m
3. Set safe limit: max_bots = available_memory / 1.5GB
4. Add memory check before each bot spawn
5. Implement graceful degradation

**Validation:**
- System remains responsive with 2 bots
- Gradually increase to 4, 6, 8 bots
- Memory stays below 80% usage
- Log: ISSUE-006 RESOLVED with max_bots=X

---

### ISSUE-007: Task Router Fails

**Symptoms:**
```
Tasks not distributed correctly
Bots idle while tasks queued
Deadlock or infinite wait
```

**Diagnostic Steps:**
```bash
# 1. Test task router in isolation
python3 tests/test_task_router.py --verbose

# 2. Check async implementation
# Review for blocking calls in async functions

# 3. Monitor queue state
# Add debugging to see queue sizes

# 4. Test with single bot
python3 tests/test_task_router.py --bots 1 --tasks 5
```

**Recovery:**
```python
# Common fixes in task_router.py:

# 1. Ensure proper asyncio usage
await asyncio.gather(*tasks)  # Not asyncio.wait

# 2. Add timeout to task execution
asyncio.wait_for(task, timeout=30)

# 3. Handle task exceptions properly
try:
    result = await bot.execute(task)
except Exception as e:
    log_error(e)
    # Don't let one failure stop the router

# 4. Implement queue monitoring
if queue.qsize() > threshold:
    log_warning("Queue backing up")
```

**AI Agent Actions:**
1. Review asyncio patterns vs template
2. Check for blocking I/O in async functions
3. Verify exception handling
4. Add queue size monitoring
5. Test with single bot first, then scale

**Validation:**
- 10 tasks distributed to 2 bots successfully
- All tasks complete within reasonable time
- No tasks stuck in queue
- Log: ISSUE-007 RESOLVED

---

### ISSUE-008: High Failure Rate in Testing

**Symptoms:**
```
Success rate < 80%
Many timeout errors
Inconsistent results
```

**Diagnostic Steps:**
```bash
# 1. Analyze failure patterns
python3 utils/analyze_failures.py logs/test_results.json

# 2. Check Ollama configuration
ollama show gemma3:270m

# 3. Monitor during test
watch -n 1 'ollama ps'

# 4. Check system load
iostat 5
```

**Recovery:**
```bash
# 1. Reduce parallel requests to Ollama
export OLLAMA_NUM_PARALLEL=4  # Down from 6

# 2. Increase individual timeouts
# Edit config: bot_timeout: 60  # Up from 30

# 3. Add retry logic
# Edit bot_agent.py: max_retries=3

# 4. Stagger bot starts
# Add delay between spawns: await asyncio.sleep(0.5)
```

**AI Agent Actions:**
1. Group failures by error type
2. If timeouts: increase timeout + reduce concurrency
3. If model errors: check Ollama health
4. If memory errors: reduce bot count
5. Implement exponential backoff for retries

**Validation:**
- Rerun test with adjusted parameters
- Success rate > 85%
- Consistent results across multiple runs
- Log: ISSUE-008 RESOLVED

---

### ISSUE-009: Checkpoint Validation Fails

**Symptoms:**
```
Cannot find checkpoint file
Checkpoint exists but validation fails
Phase dependencies not satisfied
```

**Diagnostic Steps:**
```bash
# 1. Check checkpoint directory
ls -la .checkpoints/

# 2. Verify checkpoint content
cat .checkpoints/phase_X_complete.json

# 3. Check file permissions
stat .checkpoints/phase_X_complete.json
```

**Recovery:**
```python
# 1. Ensure checkpoint directory exists
import os
os.makedirs('.checkpoints', exist_ok=True)

# 2. Write checkpoint with validation
import json
checkpoint = {
    'phase': 'phase_1',
    'timestamp': time.time(),
    'validations_passed': [...],
    'status': 'complete'
}
with open('.checkpoints/phase_1_complete.json', 'w') as f:
    json.dump(checkpoint, f, indent=2)

# 3. Verify immediately after writing
assert os.path.exists('.checkpoints/phase_1_complete.json')
```

**AI Agent Actions:**
1. Create .checkpoints directory if missing
2. Validate checkpoint schema
3. Ensure all required fields present
4. Re-run previous phase if checkpoint invalid

**Validation:**
- Checkpoint file exists and is readable
- Contains all required fields
- Timestamp is recent
- Log: ISSUE-009 RESOLVED

---

### ISSUE-010: Import Errors on macOS

**Symptoms:**
```
ImportError: cannot import name 'X'
Module works on Linux but not macOS
Architecture-specific errors
```

**Diagnostic Steps:**
```bash
# 1. Check Python architecture
python3 -c "import platform; print(platform.machine())"

# 2. Check package installation
pip3 show package-name

# 3. Try importing with details
python3 -c "import sys; print(sys.path)"
python3 -c "import package; print(package.__file__)"
```

**Recovery:**
```bash
# 1. Install with architecture specification
pip3 install --force-reinstall package-name

# 2. If native dependencies needed
brew install dependencies
pip3 install package-name

# 3. For problematic packages
pip3 install --no-binary :all: package-name

# 4. Use conda as alternative
conda install -c conda-forge package-name
```

**AI Agent Actions:**
1. Identify if issue is ARM64-specific
2. Check for available wheels for arm64
3. Install build dependencies if needed
4. Document workaround in logs

**Validation:**
- Import succeeds without errors
- Package version confirmed
- Log: ISSUE-010 RESOLVED

---

## Diagnostic Commands Reference

### System Health Check
```bash
# Memory
vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-16s % 16.2f Mi\n", "$1:", $2 * $size / 1048576);'

# CPU
sysctl -n machdep.cpu.brand_string
sysctl -n hw.ncpu

# Disk
df -h

# Processes
top -l 1 -stats pid,command,cpu,mem

# Network
netstat -an | grep 11434
```

### Ollama Diagnostics
```bash
# Service status
pgrep -l ollama

# API health
curl http://localhost:11434/api/tags

# Model info
ollama show gemma3:270m

# Current usage
ollama ps

# Logs (if available)
tail -f ~/.ollama/logs/server.log
```

### Python Diagnostics
```bash
# Environment
python3 -m site

# Installed packages
pip3 list --format=freeze

# Import test
python3 -c "import sys; [print(p) for p in sys.path]"

# Memory profiling
python3 -m memory_profiler script.py
```

---

## AI Agent Decision Tree

```
┌─────────────────────────────────────────┐
│  Issue Detected                         │
└────────────┬────────────────────────────┘
             │
             ▼
   ┌─────────────────────┐
   │ Check Issue Number  │
   └─────────┬───────────┘
             │
             ▼
   ┌─────────────────────────────────────┐
   │ Run Diagnostic Steps                │
   └─────────┬───────────────────────────┘
             │
             ▼
   ┌─────────────────────────────────────┐
   │ Execute Recovery Procedure          │
   └─────────┬───────────────────────────┘
             │
             ▼
   ┌─────────────────────────────────────┐
   │ Validate Fix                        │
   └─────────┬───────────────────────────┘
             │
        ┌────┴────┐
        │         │
        ▼         ▼
   ┌────────┐ ┌─────────────┐
   │Success │ │   Failed    │
   └────┬───┘ └──────┬──────┘
        │            │
        │            ▼
        │     ┌──────────────┐
        │     │ Retry Count? │
        │     └──────┬───────┘
        │            │
        │       ┌────┴────┐
        │       │         │
        │       ▼         ▼
        │   ┌───────┐ ┌────────────────┐
        │   │< 3    │ │>= 3            │
        │   └───┬───┘ └────────┬───────┘
        │       │              │
        │       │              ▼
        │       │     ┌─────────────────────┐
        │       │     │ REQUEST HUMAN       │
        │       │     │ INTERVENTION        │
        │       │     └─────────────────────┘
        │       │
        │       └──────┐
        │              │
        ▼              ▼
   ┌────────────────────────────┐
   │ Log Resolution & Continue  │
   └────────────────────────────┘
```

---

## Logging Requirements for AI Agents

Every diagnostic action must log:
```python
log_entry = {
    'timestamp': datetime.now().isoformat(),
    'issue_id': 'ISSUE-XXX',
    'phase': 'phase_X',
    'diagnostic_step': 'step_description',
    'action_taken': 'what_was_done',
    'result': 'success|failure',
    'retry_count': N,
    'next_action': 'what_happens_next'
}
```

All logs go to:
- `logs/diagnostics.log` - All diagnostic actions
- `logs/errors.log` - Only failures and errors
- `logs/recovery.log` - Recovery attempts and results

---

## Human Intervention Triggers

Request human review when:
1. **3 consecutive failed recovery attempts**
2. **Unexpected system behavior not in this guide**
3. **Resource exhaustion cannot be resolved**
4. **Data corruption or security concern**
5. **Build time exceeds 2x expected duration**

When requesting intervention, provide:
- Issue ID and description
- All diagnostic steps taken
- Recovery procedures attempted
- Current system state
- Relevant log excerpts
- Recommended next steps

---

## Success Criteria Checklist

After resolving any issue:
- [ ] Diagnostic steps completed and logged
- [ ] Recovery procedure executed successfully
- [ ] Validation confirms issue resolved
- [ ] Checkpoint updated if needed
- [ ] Can proceed to next build step
- [ ] No new issues introduced

---

**Version:** 1.0.0
**Last Updated:** 2025-10-22
**Maintainer:** AI-First Build System
"""

with open("swarm_macos/docs/TROUBLESHOOTING.md", "w") as f:
    f.write(troubleshooting_guide)

print("✅ Created: docs/TROUBLESHOOTING.md")
print("   → Comprehensive troubleshooting guide for AI agents")
