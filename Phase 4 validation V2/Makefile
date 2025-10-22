# Phase 4 Parallelism Verification Makefile
# Usage: make verify-parallel

.PHONY: verify-parallel gate1 gate2 gate3 gate4 gate5 bundle clean

# Run all verification gates and generate bundle
verify-parallel: clean gate1 gate2 gate3 gate4 gate5 bundle
	@echo ""
	@echo "================================================================================"
	@echo "✅ PHASE 4 VERIFICATION COMPLETE"
	@echo "================================================================================"
	@echo "Check results in .checkpoints/PHASE4_VERIFICATION_BUNDLE.json"

# Gate 1: Code Audit
gate1:
	@echo ""
	@echo "================================================================================"
	@echo "Running Gate 1: Code Audit..."
	@echo "================================================================================"
	@python3 verify_code_audit.py

# Gate 2: Concurrency Proof (CRITICAL)
gate2:
	@echo ""
	@echo "================================================================================"
	@echo "Running Gate 2: Concurrency Proof (CRITICAL)..."
	@echo "================================================================================"
	@python3 verify_concurrency_proof.py

# Gate 3: Thread Count
gate3:
	@echo ""
	@echo "================================================================================"
	@echo "Running Gate 3: Thread Count..."
	@echo "================================================================================"
	@python3 verify_thread_count.py

# Gate 4: CPU Core Utilization
gate4:
	@echo ""
	@echo "================================================================================"
	@echo "Running Gate 4: CPU Core Utilization..."
	@echo "================================================================================"
	@python3 verify_cpu_cores.py

# Gate 5: Baseline Comparison
gate5:
	@echo ""
	@echo "================================================================================"
	@echo "Running Gate 5: Baseline Comparison..."
	@echo "================================================================================"
	@python3 verify_baseline_comparison.py

# Generate final bundle
bundle:
	@echo ""
	@echo "================================================================================"
	@echo "Generating Verification Bundle..."
	@echo "================================================================================"
	@python3 generate_verification_bundle.py

# Clean previous results
clean:
	@echo "🧹 Cleaning previous verification results..."
	@rm -f .checkpoints/gate*_results.json
	@rm -f .checkpoints/PHASE4_VERIFICATION_BUNDLE.json
	@echo "✅ Clean complete"

# Quick test (Gates 1 & 2 only - fast verification)
quick:
	@echo "⚡ Running quick verification (Gates 1 & 2)..."
	@make gate1
	@make gate2
	@echo ""
	@echo "✅ Quick verification complete"

# Help
help:
	@echo "Phase 4 Parallelism Verification"
	@echo ""
	@echo "Targets:"
	@echo "  make verify-parallel  - Run full verification (all 5 gates + bundle)"
	@echo "  make quick            - Quick check (Gates 1 & 2 only)"
	@echo "  make gate1            - Run Gate 1: Code Audit"
	@echo "  make gate2            - Run Gate 2: Concurrency Proof (CRITICAL)"
	@echo "  make gate3            - Run Gate 3: Thread Count"
	@echo "  make gate4            - Run Gate 4: CPU Utilization"
	@echo "  make gate5            - Run Gate 5: Baseline Comparison"
	@echo "  make bundle           - Generate verification bundle"
	@echo "  make clean            - Clean previous results"
	@echo ""
	@echo "Critical Gates:"
	@echo "  Gate 2 MUST pass for verification success"
	@echo "  Expected: < 3 seconds for 4 bots × 2s tasks (true parallelism)"
