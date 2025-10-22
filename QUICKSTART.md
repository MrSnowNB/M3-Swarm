# 🚀 Quick Start Guide

## For Human Developers

### 1. Setup Environment (5 minutes)
```bash
# Install Ollama
brew install ollama

# Start Ollama in background
ollama serve &

# Wait for startup
sleep 3

# Pull model
ollama pull gemma3:270m

# Install Python dependencies
cd swarm_macos
pip install -r requirements.txt
```

### 2. Validate Setup (2 minutes)
```bash
# Check system resources
python3 utils/check_resources.py

# Test Ollama connection
python3 tests/test_ollama_connection.py
```

### 3. Implement Core (30-60 minutes)
```bash
# Copy templates
cp core/bot_agent_template.py core/bot_agent.py
cp core/swarm_manager_template.py core/swarm_manager.py

# Edit bot_agent.py
# - Replace TODOs with actual Ollama API calls
# - Implement execute() method
# - Implement health_check() method

# Edit swarm_manager.py  
# - Implement spawn_bot() method
# - Implement execute_task_batch() method
# - Integrate with BotAgent

# Test implementation
python3 tests/test_bot_agent.py
python3 tests/test_swarm_manager.py
```

### 4. Run Load Tests (10-15 minutes)
```bash
# Progressive scaling
python3 tests/test_swarm_load.py --bots 2 --duration 30
python3 tests/test_swarm_load.py --bots 6 --duration 30
python3 tests/test_swarm_load.py --bots 12 --duration 30
python3 tests/test_swarm_load.py --bots 24 --duration 30

# Check results
cat .checkpoints/load_test_*bots.json
```

### 5. Review Results
```bash
# Check logs
tail -100 logs/validations.log

# Review performance
cat .checkpoints/phase_3_complete.json
```

---

## For AI Coding Agents

### 1. Read Specifications
```bash
# Primary directive
cat AI_FIRST_BUILD.yaml

# Execution guide  
cat docs/AI_AGENT_GUIDE.md

# Troubleshooting reference
cat docs/TROUBLESHOOTING.md
```

### 2. Execute Phase 0
```bash
# Run validations
python3 --version
which ollama
ollama list
python3 utils/check_resources.py
python3 tests/test_ollama_connection.py

# Write checkpoint
python3 -c "
import json, time
checkpoint = {
    'phase': 'phase_0',
    'timestamp': time.time(),
    'status': 'complete',
    'validations': ['VAL_001', 'VAL_002', 'VAL_003', 'VAL_004', 'VAL_005']
}
with open('.checkpoints/phase_0_complete.json', 'w') as f:
    json.dump(checkpoint, f, indent=2)
print('✅ Phase 0 checkpoint written')
"
```

### 3. Execute Phase 1
```bash
# Install dependencies
pip install -r requirements.txt

# Validate
python3 -c "import ollama, asyncio, psutil, yaml; print('✅ All imports OK')"

# Write checkpoint
# [Same pattern as Phase 0]
```

### 4. Execute Phase 2
```bash
# Implement bot_agent.py from template
# Implement swarm_manager.py from template

# Validate
python3 tests/test_bot_agent.py
python3 tests/test_swarm_manager.py

# Write checkpoint
# [Same pattern]
```

### 5. Execute Phase 3
```bash
# Run staged tests
for bots in 2 6 12 24; do
    python3 tests/test_swarm_load.py --bots $bots --duration 30
    if [ $? -ne 0 ]; then
        echo "⚠️  Test failed at $bots bots"
        # Check TROUBLESHOOTING.md
        # Attempt recovery
        # Retry once
    fi
done

# Write checkpoint with results
```

### 6. Complete Build
```bash
# Phase 4 & 5 as needed
# Generate BUILD_REPORT.md
# Create production_config.yaml
```

---

## Troubleshooting Quick Reference

### Ollama Issues
```bash
# Not running
ollama serve

# Model missing
ollama pull gemma3:270m

# Check status
ollama ps
```

### Python Issues
```bash
# Update pip
pip install --upgrade pip

# Reinstall dependencies
pip install --no-cache-dir -r requirements.txt

# Test imports
python3 -c "import ollama; print('OK')"
```

### Test Failures
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python3 tests/test_bot_agent.py -v

# Check error logs
tail -50 logs/errors.log
```

### Resource Issues
```bash
# Check memory
python3 -c "import psutil; m = psutil.virtual_memory(); print(f'{m.available/1e9:.1f}GB available')"

# Reduce concurrency
# Edit config/swarm_config.yaml:
# max_concurrent_bots: 6  # Down from 12
```

---

## Common Commands

```bash
# Start fresh build
rm -rf .checkpoints/* logs/*

# Check build status
ls -la .checkpoints/

# View recent logs
tail -f logs/build.log

# Run diagnostics
python3 -c "from utils.diagnostics import SystemDiagnostics; import yaml; config = yaml.safe_load(open('config/swarm_config.yaml')); diag = SystemDiagnostics(config); print(diag.get_health_summary())"

# Clean up
pkill ollama
rm -rf logs/* .checkpoints/*
```

---

## Expected Timeline

### Human Developer:
- Setup: 5-10 minutes
- Implementation: 30-60 minutes  
- Testing: 15-30 minutes
- **Total: ~1-2 hours**

### AI Coding Agent:
- Phase 0-1: 5-10 minutes
- Phase 2: 10-30 minutes (implementation + iteration)
- Phase 3: 10-15 minutes (testing)
- Phase 4-5: 5-10 minutes
- **Total: ~30-60 minutes** (with optimal performance)

---

## Success Indicators

✅ All checkpoints in `.checkpoints/` directory  
✅ No errors in `logs/errors.log`  
✅ At least 12-bot capacity validated  
✅ Success rates >80% in load tests  
✅ System remains stable during tests

---

## Next Steps After Build

1. **Review BUILD_REPORT.md** (generated in Phase 5)
2. **Adjust config** based on validated capacity
3. **Deploy to production** with recommended settings
4. **Monitor performance** in real workloads
5. **Iterate and optimize** as needed

---

## Help & Support

- **Troubleshooting:** `docs/TROUBLESHOOTING.md`
- **AI Agent Guide:** `docs/AI_AGENT_GUIDE.md`
- **Configuration:** `config/swarm_config.yaml`
- **Issue Tracker:** Create issue in Swarm-100 repo

---

**Quick Start Version:** 1.0.0  
**Last Updated:** 2025-10-22
