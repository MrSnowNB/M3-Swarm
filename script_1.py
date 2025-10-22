
# 1. MASTER AI-FIRST BUILD YAML - The primary directive for coding agents
build_yaml = """---
# ============================================================================
# AI-FIRST SWARM-100 MACOS BUILD SPECIFICATION
# ============================================================================
# Version: 1.0.0
# Platform: macOS M3 Max 36GB (adaptable to other Apple Silicon)
# Baseline: Swarm-100 Z8 Linux (working reference)
# Build Agent: Autonomous AI coding agent with stepwise validation
# ============================================================================

metadata:
  project_name: "Swarm-100-MacOS"
  baseline_repo: "https://github.com/MrSnowNB/Swarm-100"
  target_platform: "macOS_ARM64_M3_Max"
  build_type: "autonomous_stepwise_gated"
  validation_level: "strict"
  recovery_protocol: "auto_with_human_fallback"
  
hardware_profile:
  cpu_cores: 14
  performance_cores: 10
  efficiency_cores: 4
  gpu_cores: 30
  neural_engine_cores: 16
  unified_memory_gb: 36
  memory_bandwidth_gbps: 200
  hyperthreading: true
  architecture: "ARM64"

# ============================================================================
# PHASE 0: PRE-BUILD VALIDATION
# ============================================================================
# CRITICAL: Coding agent must complete ALL validations before proceeding
# ============================================================================

phase_0_prerequisites:
  name: "Environment Validation"
  checkpoint: ".checkpoints/phase_0_complete.json"
  
  validations:
    - id: "VAL_001"
      name: "Python Version Check"
      command: "python3 --version"
      expected: "Python 3.10 or higher"
      validation_test: "version >= 3.10"
      failure_action: "ABORT_BUILD"
      
    - id: "VAL_002"
      name: "Ollama Installation"
      command: "which ollama"
      expected: "/usr/local/bin/ollama or /opt/homebrew/bin/ollama"
      validation_test: "path exists"
      failure_action: "RUN_RECOVERY_001"
      
    - id: "VAL_003"
      name: "Ollama Service Check"
      command: "ollama list"
      expected: "Command executes without error"
      validation_test: "exit code 0"
      failure_action: "RUN_RECOVERY_002"
      
    - id: "VAL_004"
      name: "Model Availability"
      command: "ollama list | grep gemma3:270m"
      expected: "gemma3:270m present in list"
      validation_test: "model found"
      failure_action: "RUN_RECOVERY_003"
      
    - id: "VAL_005"
      name: "System Resources"
      script: "utils/check_resources.py"
      expected: "Available memory > 10GB, CPU accessible"
      validation_test: "resources sufficient"
      failure_action: "LOG_WARNING_CONTINUE"

  recovery_procedures:
    RUN_RECOVERY_001:
      description: "Install Ollama"
      steps:
        - "brew install ollama"
        - "Wait 5 seconds for installation"
        - "Retry VAL_002"
      max_retries: 2
      
    RUN_RECOVERY_002:
      description: "Start Ollama Service"
      steps:
        - "ollama serve &"
        - "sleep 3"
        - "Retry VAL_003"
      max_retries: 3
      
    RUN_RECOVERY_003:
      description: "Pull Required Model"
      steps:
        - "ollama pull gemma3:270m"
        - "Verify with ollama list"
        - "Retry VAL_004"
      max_retries: 2

  success_criteria:
    - "All validations pass OR recover successfully"
    - "Checkpoint file written to .checkpoints/phase_0_complete.json"
    - "Log all results to logs/phase_0_validation.log"

# ============================================================================
# PHASE 1: DEPENDENCY INSTALLATION
# ============================================================================
# GATE: Phase 0 must be complete before proceeding
# ============================================================================

phase_1_dependencies:
  name: "Install Python Dependencies"
  checkpoint: ".checkpoints/phase_1_complete.json"
  requires: ".checkpoints/phase_0_complete.json"
  
  pre_validation:
    - name: "Check Phase 0 Complete"
      test: "file_exists(.checkpoints/phase_0_complete.json)"
      failure_action: "ABORT_WITH_MESSAGE: Phase 0 not complete"
  
  steps:
    - id: "DEP_001"
      name: "Install Core Dependencies"
      command: "pip install -r requirements.txt"
      validation: "pip list shows all required packages"
      failure_action: "RUN_RECOVERY_DEP_001"
      timeout_seconds: 120
      
    - id: "DEP_002"
      name: "Verify Imports"
      script: "python -c 'import ollama, asyncio, psutil, yaml; print(\"OK\")'"
      expected_output: "OK"
      failure_action: "RUN_RECOVERY_DEP_002"
      
    - id: "DEP_003"
      name: "Test Ollama Python Client"
      script: "tests/test_ollama_connection.py"
      expected: "Connection successful"
      failure_action: "LOG_ERROR_AND_ABORT"

  recovery_procedures:
    RUN_RECOVERY_DEP_001:
      description: "Clean install dependencies"
      steps:
        - "pip install --upgrade pip"
        - "pip install --no-cache-dir -r requirements.txt"
        - "Retry DEP_001"
      max_retries: 2
      
    RUN_RECOVERY_DEP_002:
      description: "Install missing packages individually"
      steps:
        - "pip install ollama asyncio psutil pyyaml --force-reinstall"
        - "Retry DEP_002"
      max_retries: 1

  success_criteria:
    - "All dependencies installed and importable"
    - "Ollama Python client connects successfully"
    - "Checkpoint written"

# ============================================================================
# PHASE 2: CORE IMPLEMENTATION
# ============================================================================
# GATE: Phase 1 must be complete
# AI AGENT: Implement core bot and swarm manager classes
# ============================================================================

phase_2_core_implementation:
  name: "Build Core Swarm Components"
  checkpoint: ".checkpoints/phase_2_complete.json"
  requires: ".checkpoints/phase_1_complete.json"
  
  implementation_order:
    - id: "IMPL_001"
      file: "core/bot_agent.py"
      template: "templates/bot_agent_template.py"
      description: "Single bot agent with async execution"
      validation_test: "tests/test_bot_agent.py"
      success_criteria:
        - "Bot can execute single prompt"
        - "Bot handles errors gracefully"
        - "Response time logged"
      failure_action: "RUN_RECOVERY_IMPL_001"
      
    - id: "IMPL_002"
      file: "core/task_router.py"
      template: "templates/task_router_template.py"
      description: "Routes tasks to available bots"
      validation_test: "tests/test_task_router.py"
      success_criteria:
        - "Can distribute 10 tasks to 2 bots"
        - "Load balancing works"
        - "Queue management functional"
      failure_action: "RUN_RECOVERY_IMPL_002"
      
    - id: "IMPL_003"
      file: "core/swarm_manager.py"
      template: "templates/swarm_manager_template.py"
      description: "Orchestrates entire swarm lifecycle"
      validation_test: "tests/test_swarm_manager.py"
      success_criteria:
        - "Can spawn 2 bots successfully"
        - "Can spawn 4 bots successfully"
        - "Resource monitoring active"
        - "Graceful shutdown works"
      failure_action: "RUN_RECOVERY_IMPL_003"
      
    - id: "IMPL_004"
      file: "utils/diagnostics.py"
      template: "templates/diagnostics_template.py"
      description: "Error detection and recovery utilities"
      validation_test: "tests/test_diagnostics.py"
      success_criteria:
        - "Can detect memory pressure"
        - "Can detect high error rates"
        - "Auto-scaling recommendations work"
      failure_action: "RUN_RECOVERY_IMPL_004"

  recovery_procedures:
    RUN_RECOVERY_IMPL_001:
      description: "Debug bot agent implementation"
      steps:
        - "Run tests/test_bot_agent.py with verbose logging"
        - "Check logs/implementation_debug.log for errors"
        - "Compare implementation against templates/bot_agent_template.py"
        - "Fix identified issues"
        - "Retry IMPL_001 validation"
      max_retries: 3
      human_intervention_threshold: 2
      
    RUN_RECOVERY_IMPL_002:
      description: "Debug task router"
      steps:
        - "Verify bot_agent.py is working first"
        - "Run task router with 1 bot as sanity check"
        - "Check for async/await issues"
        - "Review logs/task_router_debug.log"
        - "Retry IMPL_002 validation"
      max_retries: 3
      
    RUN_RECOVERY_IMPL_003:
      description: "Debug swarm manager"
      steps:
        - "Verify IMPL_001 and IMPL_002 are complete"
        - "Test with minimal configuration (2 bots, simple tasks)"
        - "Check for resource exhaustion"
        - "Review logs/swarm_manager_debug.log"
        - "Retry with reduced concurrency"
      max_retries: 3
      
    RUN_RECOVERY_IMPL_004:
      description: "Fix diagnostics utilities"
      steps:
        - "Ensure psutil is working correctly on macOS"
        - "Test each diagnostic function individually"
        - "Review logs/diagnostics_debug.log"
      max_retries: 2

  ai_agent_notes:
    - "CRITICAL: Test each component individually before integration"
    - "CRITICAL: Never proceed if previous component fails validation"
    - "If stuck after 3 retries, log detailed error and request human review"
    - "Use templates as baseline but adapt for macOS-specific requirements"
    - "All logging must go to logs/ directory with timestamps"

# ============================================================================
# PHASE 3: PROGRESSIVE LOAD TESTING
# ============================================================================
# GATE: Phase 2 complete, all core components validated
# CRITICAL: Must pass each stage before advancing
# ============================================================================

phase_3_progressive_testing:
  name: "Stepwise Swarm Scaling Tests"
  checkpoint: ".checkpoints/phase_3_complete.json"
  requires: ".checkpoints/phase_2_complete.json"
  
  test_stages:
    - stage: 1
      name: "Minimal Swarm (2 bots)"
      bot_count: 2
      duration_seconds: 30
      success_threshold: 95
      validation_script: "tests/test_swarm_load.py --bots 2 --duration 30"
      expected_metrics:
        success_rate_min: 95
        avg_response_time_max: 2.0
        memory_increase_max_gb: 2
      failure_action: "ABORT_TEST_SEQUENCE"
      
    - stage: 2
      name: "Small Swarm (6 bots)"
      bot_count: 6
      duration_seconds: 30
      success_threshold: 90
      validation_script: "tests/test_swarm_load.py --bots 6 --duration 30"
      expected_metrics:
        success_rate_min: 90
        avg_response_time_max: 3.0
        memory_increase_max_gb: 4
      failure_action: "RUN_RECOVERY_STAGE"
      
    - stage: 3
      name: "Medium Swarm (12 bots)"
      bot_count: 12
      duration_seconds: 30
      success_threshold: 85
      validation_script: "tests/test_swarm_load.py --bots 12 --duration 30"
      expected_metrics:
        success_rate_min: 85
        avg_response_time_max: 4.0
        memory_increase_max_gb: 6
      failure_action: "RUN_RECOVERY_STAGE"
      
    - stage: 4
      name: "Large Swarm (24 bots)"
      bot_count: 24
      duration_seconds: 30
      success_threshold: 80
      validation_script: "tests/test_swarm_load.py --bots 24 --duration 30"
      expected_metrics:
        success_rate_min: 80
        avg_response_time_max: 5.0
        memory_increase_max_gb: 10
      failure_action: "RUN_RECOVERY_STAGE"

  recovery_procedures:
    ABORT_TEST_SEQUENCE:
      description: "Critical failure at minimal scale"
      steps:
        - "Log complete failure details to logs/critical_failure.log"
        - "Run diagnostics.py to identify bottleneck"
        - "Review Phase 2 implementation for bugs"
        - "REQUEST HUMAN INTERVENTION"
      
    RUN_RECOVERY_STAGE:
      description: "Test stage failed, attempt recovery"
      steps:
        - "Analyze logs/test_results.json for failure patterns"
        - "Check if memory/cpu limits reached"
        - "Reduce OLLAMA_NUM_PARALLEL by 25%"
        - "Retry stage once with adjusted parameters"
        - "If retry fails, mark as max capacity and continue to next stage"
      max_retries: 1

  success_criteria:
    - "All stages pass OR maximum capacity identified"
    - "Performance metrics logged for each stage"
    - "Resource utilization tracked"
    - "Recommendations generated for optimal configuration"

# ============================================================================
# PHASE 4: FULL SWARM VALIDATION
# ============================================================================
# GATE: Phase 3 complete with at least stage 3 (12 bots) passing
# TARGET: Test full 100-bot swarm OR maximum validated capacity
# ============================================================================

phase_4_full_swarm:
  name: "Full Swarm Stress Test"
  checkpoint: ".checkpoints/phase_4_complete.json"
  requires: ".checkpoints/phase_3_complete.json"
  
  pre_validation:
    - name: "Check Phase 3 Results"
      script: "utils/analyze_phase3.py"
      decision_logic:
        - "If stage 4 (24 bots) passed: Target 100 bots"
        - "If stage 3 (12 bots) passed: Target 50 bots"
        - "If only stage 2 (6 bots) passed: Target 24 bots"
  
  test_configuration:
    target_bot_count: "AUTO_FROM_PHASE_3"
    test_duration_seconds: 60
    batch_mode: true
    batch_size: 12
    validation_script: "tests/test_full_swarm.py"
    
  success_criteria:
    - "Success rate >= 75%"
    - "No system crashes or hangs"
    - "Graceful degradation if capacity exceeded"
    - "Complete test metrics exported to JSON"
    
  failure_recovery:
    - "If success rate < 75%, reduce target by 25% and retry"
    - "If system becomes unresponsive, force shutdown and reduce by 50%"
    - "Maximum 2 retries before marking as capacity limit"

# ============================================================================
# PHASE 5: DOCUMENTATION & DEPLOYMENT
# ============================================================================
# Generate final reports and deployment configurations
# ============================================================================

phase_5_finalization:
  name: "Generate Reports and Deployment Configs"
  checkpoint: ".checkpoints/phase_5_complete.json"
  requires: ".checkpoints/phase_4_complete.json"
  
  outputs:
    - file: "docs/BUILD_REPORT.md"
      description: "Complete build process documentation"
      includes:
        - "All validation results"
        - "Performance metrics"
        - "Identified bottlenecks"
        - "Optimal configuration recommendations"
        
    - file: "docs/DEPLOYMENT_GUIDE.md"
      description: "Production deployment instructions"
      includes:
        - "Recommended bot count"
        - "Ollama configuration"
        - "Resource requirements"
        - "Monitoring recommendations"
        
    - file: "config/production_config.yaml"
      description: "Validated production configuration"
      includes:
        - "Optimal bot count"
        - "Tested model settings"
        - "Resource limits"
        - "Error handling parameters"

# ============================================================================
# AI AGENT PROTOCOLS
# ============================================================================

ai_agent_protocols:
  hallucination_detection:
    - "After each implementation, compare output against template"
    - "If validation fails 2+ times, flag for human review"
    - "Never invent success - all validations must actually pass"
    
  error_logging:
    - "Every error must be logged with timestamp, phase, step_id"
    - "Include full stack trace and system state"
    - "Log to both console and logs/errors.log"
    
  checkpoint_management:
    - "Write checkpoint JSON after each phase completes"
    - "Include phase_name, completion_time, validation_results"
    - "Never proceed without valid checkpoint from previous phase"
    
  human_intervention:
    - "Request human review after 3 failed retry attempts"
    - "Request human review if system behavior is unexpected"
    - "Provide clear summary of issue and attempted fixes"
    
  testing_discipline:
    - "NEVER skip validation steps"
    - "NEVER mock or simulate test results"
    - "ALWAYS run actual tests and log real results"
    - "If test infrastructure is broken, fix it first"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging:
  level: "DEBUG"
  format: "[{timestamp}] [{phase}] [{level}] {message}"
  files:
    main: "logs/build.log"
    errors: "logs/errors.log"
    validations: "logs/validations.log"
    performance: "logs/performance.log"
    diagnostics: "logs/diagnostics.log"
  
  retention:
    days: 30
    max_size_mb: 100

# ============================================================================
# SUCCESS CRITERIA - OVERALL BUILD
# ============================================================================

overall_success_criteria:
  required:
    - "All phases 0-3 complete with passing validations"
    - "At least 12-bot swarm validated"
    - "All checkpoints written"
    - "No critical errors in logs"
    
  optional:
    - "Phase 4 (full swarm) complete"
    - "100-bot capacity achieved"
    - "All performance targets met"
    
  build_complete_when:
    - "Phase 5 finalization complete OR"
    - "Maximum capacity identified and documented OR"
    - "Critical failure requiring human intervention"
"""

with open("swarm_macos/AI_FIRST_BUILD.yaml", "w") as f:
    f.write(build_yaml)

print("✅ Created: AI_FIRST_BUILD.yaml")
print("   → Master build specification with gated phases and validation")
