"""
Step 10 -- QA/QC and load test triggers.

Purpose
-------
Determine when full-scale load testing per ASTM D1143/D3689/D3966 is
required, and enumerate baseline QA items. Reference: Design Procedure
doc, Section 10. This module is a rule engine, not a calculation --
it consumes flags/results produced by the other steps.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LoadTestTriggerInputs:
    kt_established_by_ac358: bool
    frost_uplift_relies_on_assumed_values: bool
    py_params_from_lab_or_cpt: bool          # False -> SPT-correlation only
    predicted_y_over_limit_ratio: float      # y_gl_service / y_limit
    n_production_piles: int
    variable_or_unfamiliar_soils: bool
    owner_or_code_official_requires_test: bool = False


@dataclass
class LoadTestTriggerResult:
    triggered_tests: set[str] = field(default_factory=set)
    reasons: list[str] = field(default_factory=list)

    def add(self, test: str, reason: str) -> None:
        self.triggered_tests.add(test)
        self.reasons.append(f"{test}: {reason}")


def evaluate_load_test_triggers(inputs: LoadTestTriggerInputs) -> LoadTestTriggerResult:
    """Doc Section 10.2 trigger table, evaluated programmatically."""
    result = LoadTestTriggerResult()

    if not inputs.kt_established_by_ac358:
        result.add("D1143/D3689",
                    "Kt not established by AC358 report for this exact shaft/helix product")

    if inputs.frost_uplift_relies_on_assumed_values:
        result.add("D3689",
                    "Frost-uplift design relies on assumed tau_ad or sleeve performance")

    lateral_margin_low = inputs.predicted_y_over_limit_ratio > 0.75
    if lateral_margin_low or not inputs.py_params_from_lab_or_cpt:
        reason = []
        if lateral_margin_low:
            reason.append("lateral serviceability margin < 25%")
        if not inputs.py_params_from_lab_or_cpt:
            reason.append("p-y parameters assumed without lab/CPT data")
        result.add("D3966", " and ".join(reason))

    if inputs.n_production_piles > 50 or inputs.variable_or_unfamiliar_soils:
        result.add("D3689+D3966",
                    "> 50 production piles, or unfamiliar/variable soils across site "
                    "-- one pre-production test pile per soil regime")

    if inputs.owner_or_code_official_requires_test:
        result.add("as directed",
                    "Owner or code-official requirement (e.g. IBC 2021 Sec.1810.3.3.1.9) [verify]")

    return result


BASELINE_QA_ITEMS = [
    "Mill certs for shaft/helix steel and HDG on file",
    "AC358 evaluation report (or equivalent product data) on file",
    "Calibrated torque indicator certificate <= 12 months old",
    "Installation logs (torque-vs-depth, per pile) reviewed and signed by the engineer",
    "Anchor-bolt template verification completed before pole delivery",
]
