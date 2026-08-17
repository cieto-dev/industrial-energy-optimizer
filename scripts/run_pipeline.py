"""
run_pipeline.py — Full pipeline orchestrator (Sprint 3.5).

NOTE: When Sprint 3.5 is implemented, this script must call PolicyEngine.evaluate()
and ensure the total_benefit_verified flag and disclaimer propagate through
the pipeline output. The pipeline output must include:

1. The total_benefit_verified flag from PolicyEvaluationResult
2. The disclaimer text when total_benefit_verified is False:
   "Estimated combined benefit — subject to manual verification against
   scheme-specific convergence rules; individual scheme benefits are
   independently sourced, their combined stackability is not."

This flag and disclaimer must not be silently dropped — they must appear
in the pipeline's human-readable output and any machine-readable output
that surfaces the estimated_total_benefit_inr figure.
"""