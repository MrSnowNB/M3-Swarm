
# Create Makefile for easy execution
makefile_content = '''# Phase 4 Parallelism Verification Makefile
# Usage: make verify-parallel

.PHONY: verify-parallel gate1 gate2 gate3 gate4 gate5 bundle clean

# Run all verification gates and generate bundle
verify-parallel: clean gate1 gate2 gate3 gate4 gate5 bundle
\t@echo ""
\t@echo "================================================================================"
\t@echo "✅ PHASE 4 VERIFICATION COMPLETE"
\t@echo "================================================================================"
\t@echo "Check results in .checkpoints/PHASE4_VERIFICATION_BUNDLE.json"

# Gate 1: Code Audit
gate1:
\t@echo ""
\t@echo "================================================================================"
\t@echo "Running Gate 1: Code Audit..."
\t@echo "================================================================================"
\t@python3 verify_code_audit.py

# Gate 2: Concurrency Proof (CRITICAL)
gate2:
\t@echo ""
\t@echo "================================================================================"
\t@echo "Running Gate 2: Concurrency Proof (CRITICAL)..."
\t@echo "================================================================================"
\t@python3 verify_concurrency_proof.py

# Gate 3: Thread Count
gate3:
\t@echo ""
\t@echo "================================================================================"
\t@echo "Running Gate 3: Thread Count..."
\t@echo "================================================================================"
\t@python3 verify_thread_count.py

# Gate 4: CPU Core Utilization
gate4:
\t@echo ""
\t@echo "================================================================================"
\t@echo "Running Gate 4: CPU Core Utilization..."
\t@echo "================================================================================"
\t@python3 verify_cpu_cores.py

# Gate 5: Baseline Comparison
gate5:
\t@echo ""
\t@echo "================================================================================"
\t@echo "Running Gate 5: Baseline Comparison..."
\t@echo "================================================================================"
\t@python3 verify_baseline_comparison.py

# Generate final bundle
bundle:
\t@echo ""
\t@echo "================================================================================"
\t@echo "Generating Verification Bundle..."
\t@echo "================================================================================"
\t@python3 generate_verification_bundle.py

# Clean previous results
clean:
\t@echo "🧹 Cleaning previous verification results..."
\t@rm -f .checkpoints/gate*_results.json
\t@rm -f .checkpoints/PHASE4_VERIFICATION_BUNDLE.json
\t@echo "✅ Clean complete"

# Quick test (Gates 1 & 2 only - fast verification)
quick:
\t@echo "⚡ Running quick verification (Gates 1 & 2)..."
\t@make gate1
\t@make gate2
\t@echo ""
\t@echo "✅ Quick verification complete"

# Help
help:
\t@echo "Phase 4 Parallelism Verification"
\t@echo ""
\t@echo "Targets:"
\t@echo "  make verify-parallel  - Run full verification (all 5 gates + bundle)"
\t@echo "  make quick            - Quick check (Gates 1 & 2 only)"
\t@echo "  make gate1            - Run Gate 1: Code Audit"
\t@echo "  make gate2            - Run Gate 2: Concurrency Proof (CRITICAL)"
\t@echo "  make gate3            - Run Gate 3: Thread Count"
\t@echo "  make gate4            - Run Gate 4: CPU Utilization"
\t@echo "  make gate5            - Run Gate 5: Baseline Comparison"
\t@echo "  make bundle           - Generate verification bundle"
\t@echo "  make clean            - Clean previous results"
\t@echo ""
\t@echo "Critical Gates:"
\t@echo "  Gate 2 MUST pass for verification success"
\t@echo "  Expected: < 3 seconds for 4 bots × 2s tasks (true parallelism)"
'''

with open("Makefile", "w") as f:
    f.write(makefile_content)

print("✅ Created: Makefile")
print("   → Execute with: make verify-parallel")
