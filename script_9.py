
# 9. Create AI Agent execution guide and main README

agent_guide = """# 🤖 AI Coding Agent Execution Guide

## Purpose
This document provides step-by-step instructions for an autonomous AI coding agent to build, test, and validate the Swarm-100 MacOS system.

## AI Agent Requirements
- Ability to read YAML specifications
- Ability to execute shell commands and Python scripts
- Ability to write and modify Python code
- Ability to validate test results
- Ability to log all actions and decisions

## Critical Rules

### 1. NEVER Skip Validations
Every phase has validation gates. You MUST pass validation before proceeding.

### 2. NEVER Invent Success
Run actual tests and use real results. Do not mock or simulate passing tests.

### 3. ALWAYS Log Everything
Every action, decision, error, and result must be logged with timestamps.

### 4. Request Human Help
After 3 failed attempts at any step, request human intervention with detailed context.

### 5. Checkpoint Discipline
Write checkpoint files after completing each phase. Never proceed without valid checkpoint.

---

## Phase-by-Phase Execution

### Phase 0: Pre-Build Validation

**Objective:** Ensure environment is ready for build

**Steps:**
1. Read `AI_FIRST_BUILD.yaml` Phase 0 section
2. Execute validations in order:
   ```bash
   python3 --version  # Should be 3.10+
   which ollama       # Should return path
   ollama list        # Should execute without error
   ollama list | grep gemma3:270m  # Check model
   python3 utils/check_resources.py  # System resources
   ```

3. For each failed validation:
   - Check recovery procedure in YAML
   - Execute recovery steps
   - Retry validation
   - Log outcome

4. Write checkpoint:
   ```python
   import json, time
   checkpoint = {
       'phase': 'phase_0',
       'timestamp': time.time(),
       'status': 'complete',
       'validations': ['VAL_001', 'VAL_002', ...]
   }
   with open('.checkpoints/phase_0_complete.json', 'w') as f:
       json.dump(checkpoint, f, indent=2)
   ```

**Success Criteria:**
- All validations pass OR recover successfully
- Checkpoint file written
- logs/phase_0_validation.log contains all actions

---

### Phase 1: Dependency Installation

**Objective:** Install and validate Python dependencies

**Gate:** Phase 0 checkpoint must exist

**Steps:**
1. Verify Phase 0 checkpoint exists:
   ```python
   import os
   assert os.path.exists('.checkpoints/phase_0_complete.json')
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Validate imports:
   ```bash
   python3 tests/test_ollama_connection.py
   ```

4. If failures occur, check `docs/TROUBLESHOOTING.md` for ISSUE-004

5. Write Phase 1 checkpoint

**Success Criteria:**
- All packages installed
- test_ollama_connection.py passes
- Checkpoint written

---

### Phase 2: Core Implementation

**Objective:** Implement bot_agent.py and swarm_manager.py

**Gate:** Phase 1 checkpoint must exist

**This is the critical implementation phase. Follow carefully.**

#### Step 2.1: Implement bot_agent.py

1. Copy template to implementation:
   ```bash
   cp core/bot_agent_template.py core/bot_agent.py
   ```

2. Replace TODOs with working code:
   - Initialize `ollama.AsyncClient`
   - Implement `execute()` method with actual API call
   - Implement `health_check()` method

3. Run validation test:
   ```bash
   python3 tests/test_bot_agent.py
   ```

4. If test fails:
   - Review error logs
   - Compare against template
   - Check TROUBLESHOOTING.md ISSUE-005
   - Fix and retry (max 3 attempts)

5. Log completion:
   ```python
   log_entry = {
       'step': 'IMPL_001',
       'file': 'core/bot_agent.py',
       'status': 'complete',
       'test_result': 'pass',
       'timestamp': time.time()
   }
   # Append to logs/implementation.log
   ```

#### Step 2.2: Implement swarm_manager.py

1. Copy template:
   ```bash
   cp core/swarm_manager_template.py core/swarm_manager.py
   ```

2. Implement TODOs:
   - Complete `spawn_bot()` method
   - Complete `execute_task_batch()` method
   - Integrate with BotAgent class

3. Run validation:
   ```bash
   python3 tests/test_swarm_manager.py
   ```

4. Iterate until tests pass

5. Log completion

**Success Criteria:**
- bot_agent.py fully implemented
- swarm_manager.py fully implemented
- All unit tests pass
- Phase 2 checkpoint written

---

### Phase 3: Progressive Load Testing

**Objective:** Validate swarm scales from 2 to 24 bots

**Gate:** Phase 2 checkpoint must exist

**This phase tests real performance. Cannot be simulated.**

#### Test Sequence

**Stage 1: 2 Bots**
```bash
python3 tests/test_swarm_load.py --bots 2 --duration 30
```
- Expected: 95%+ success rate
- If fail: Critical error, review Phase 2 implementation

**Stage 2: 6 Bots**
```bash
python3 tests/test_swarm_load.py --bots 6 --duration 30
```
- Expected: 90%+ success rate
- If fail: Check TROUBLESHOOTING.md ISSUE-006

**Stage 3: 12 Bots**
```bash
python3 tests/test_swarm_load.py --bots 12 --duration 30
```
- Expected: 85%+ success rate
- If fail: May need to reduce concurrency

**Stage 4: 24 Bots**
```bash
python3 tests/test_swarm_load.py --bots 24 --duration 30
```
- Expected: 80%+ success rate
- If fail: Document as max capacity

**After Each Stage:**
1. Check `.checkpoints/load_test_Nbots.json` for results
2. If below threshold, run diagnostics:
   ```python
   from utils.diagnostics import SystemDiagnostics
   diag = SystemDiagnostics(config)
   health = diag.get_health_summary()
   # Log health status
   ```

3. Decide: continue, recover, or stop

**Success Criteria:**
- At least Stage 3 (12 bots) passes
- All results logged
- Phase 3 checkpoint written with max validated capacity

---

### Phase 4: Full Swarm Validation (Optional)

**Objective:** Test at full 100-bot capacity OR max validated capacity

**Gate:** Phase 3 checkpoint, at least 12 bots validated

**Steps:**
1. Determine target based on Phase 3 results:
   - If 24 bots passed: Try 50 bots
   - If 12 bots passed: Try 24 bots
   - If 6 bots passed: Skip this phase

2. Run extended test:
   ```bash
   python3 tests/test_swarm_load.py --bots N --duration 60
   ```

3. Evaluate results:
   - Success rate >= 75%: PASS
   - Success rate < 75%: Reduce and retry once

4. Document maximum capacity

**Success Criteria:**
- Full swarm test attempted
- Results documented
- Phase 4 checkpoint written

---

### Phase 5: Finalization

**Objective:** Generate documentation and deployment configs

**Steps:**
1. Aggregate all test results
2. Generate BUILD_REPORT.md with:
   - All validation results
   - Performance metrics
   - Maximum validated capacity
   - Recommendations

3. Create production_config.yaml with optimal settings

4. Write Phase 5 checkpoint

---

## Error Handling Protocol

### When Test Fails:

1. **Identify Issue:**
   - Check logs/errors.log
   - Note error type and phase

2. **Consult Troubleshooting:**
   - Open docs/TROUBLESHOOTING.md
   - Find matching ISSUE-XXX
   - Follow diagnostic steps

3. **Attempt Recovery:**
   - Execute recovery procedure
   - Log all actions
   - Retry validation

4. **Track Attempts:**
   - Increment retry counter
   - If retry >= 3: STOP

5. **Request Human Help:**
   ```
   ERROR REPORT:
   Phase: phase_X
   Step: STEP_ID
   Issue: ISSUE-XXX
   Attempts: 3
   Last Error: [error message]
   Diagnostic Results: [results]
   Suggested Action: [recommendation]
   ```

---

## Logging Requirements

### Every action must log:
```python
import logging, datetime

logging.basicConfig(
    filename='logs/agent_actions.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logging.info(f"Phase: {phase}, Step: {step}, Action: {action}, Result: {result}")
```

### Critical events to log:
- Phase transitions
- Validation attempts and results
- Recovery procedures
- Test executions
- Errors and exceptions
- Checkpoint writes
- Human intervention requests

---

## Decision Tree

```
Start → Read AI_FIRST_BUILD.yaml
  ↓
Phase 0: Validate environment
  ↓ (checkpoint)
Phase 1: Install dependencies
  ↓ (checkpoint)
Phase 2: Implement core
  ↓ (checkpoint)
Phase 3: Progressive testing
  ├─ Stage 1 (2 bots)
  │   ├─ Pass → Continue
  │   └─ Fail → ABORT (critical)
  ├─ Stage 2 (6 bots)
  │   ├─ Pass → Continue
  │   └─ Fail → Recover & Retry
  ├─ Stage 3 (12 bots)
  │   ├─ Pass → Continue
  │   └─ Fail → Recover & Retry
  └─ Stage 4 (24 bots)
      ├─ Pass → Phase 4
      └─ Fail → Document & Phase 5
  ↓ (checkpoint)
Phase 4: Full swarm (optional)
  ↓ (checkpoint)
Phase 5: Finalization
  ↓
Complete!
```

---

## Validation Checklist

Before marking any phase complete:

- [ ] All required steps executed
- [ ] All validations passed OR recovered
- [ ] All results logged
- [ ] Checkpoint file written
- [ ] No critical errors remain
- [ ] Ready for next phase

---

## File Reference

**Configuration:**
- `AI_FIRST_BUILD.yaml` - Master build spec
- `config/swarm_config.yaml` - Runtime config
- `config/models.yaml` - Model config

**Templates:**
- `core/bot_agent_template.py` - Bot implementation guide
- `core/swarm_manager_template.py` - Swarm implementation guide

**Tests:**
- `tests/test_bot_agent.py` - Bot unit tests
- `tests/test_swarm_manager.py` - Swarm unit tests
- `tests/test_swarm_load.py` - Load testing

**Utilities:**
- `utils/check_resources.py` - System validation
- `utils/diagnostics.py` - Error detection

**Documentation:**
- `docs/TROUBLESHOOTING.md` - Issue resolution
- `docs/AI_AGENT_GUIDE.md` - This file

**Logs:**
- `logs/build.log` - Main build log
- `logs/errors.log` - Errors only
- `logs/validations.log` - Test results

**Checkpoints:**
- `.checkpoints/phase_X_complete.json` - Phase completion markers

---

## Success Indicators

**Build Successful If:**
- Phases 0-3 complete
- At least 12-bot capacity validated
- All checkpoints written
- Documentation generated

**Build Failed If:**
- Phase 0 or 1 cannot be completed
- Phase 2 implementation fails after 3 attempts
- Phase 3 Stage 1 (2 bots) fails
- Critical system errors occur

---

## Final Notes for AI Agents

1. **Be methodical:** Follow phases in order
2. **Be honest:** Report real results, not simulated
3. **Be thorough:** Log everything
4. **Be cautious:** Don't skip validations
5. **Be collaborative:** Request help when stuck

This build system is designed to catch mistakes early and provide clear recovery paths. Trust the process.

---

**Version:** 1.0.0
**For:** Autonomous AI Coding Agents
**Project:** Swarm-100 MacOS Build
"""

with open("swarm_macos/docs/AI_AGENT_GUIDE.md", "w") as f:
    f.write(agent_guide)

created_files.append("docs/AI_AGENT_GUIDE.md")
print("✅ Created: docs/AI_AGENT_GUIDE.md")
print("   → Complete execution guide for AI coding agents")
