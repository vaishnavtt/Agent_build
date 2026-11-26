from typing import Dict, List, Optional

from app.schemas.reliability import (
    CategoryScoreDetail,
    ReliabilityCategory,
    ReliabilityScoreBreakdown,
    ScenarioResult,
)

CATEGORY_MAX_POINTS: Dict[ReliabilityCategory, float] = {
    "normal": 40.0,
    "robustness": 30.0,
    "edge": 30.0,
}

DEDUCTION_AMOUNTS = {
    "UNHANDLED_CRASH": 15.0,
    "TIMEOUT_VIOLATION": 10.0,
    "CORRUPTED_OUTPUT": 20.0,
}


class ReliabilityScorer:
    """Deterministic reliability scorer operating strictly on executed scenario results."""

    FORMULA_DESCRIPTION = (
        "Reliability Score = max(0, min(100, Normal(40) + Robustness(30) + Edge(30) - Deductions)). "
        "Each category is scored proportionally from completed scenarios that passed. "
        "Deductions: -15 per confirmed unhandled crash, -10 per timeout violation, -20 per corrupted output. "
        "NOT_RUN scenarios are excluded; returns None if zero scenarios have been executed."
    )

    def score(self, results: List[ScenarioResult]) -> ReliabilityScoreBreakdown:
        total_counts: Dict[ReliabilityCategory, int] = {"normal": 0, "robustness": 0, "edge": 0}
        completed_counts: Dict[ReliabilityCategory, int] = {"normal": 0, "robustness": 0, "edge": 0}
        passed_counts: Dict[ReliabilityCategory, int] = {"normal": 0, "robustness": 0, "edge": 0}
        failed_counts: Dict[ReliabilityCategory, int] = {"normal": 0, "robustness": 0, "edge": 0}

        unhandled_crashes = 0
        timeout_violations = 0
        corrupted_outputs = 0

        for res in results:
            cat = res.category
            total_counts[cat] += 1
            if res.status == "NOT_RUN":
                continue

            completed_counts[cat] += 1
            if res.status == "PASSED":
                passed_counts[cat] += 1
            elif res.status == "FAILED":
                failed_counts[cat] += 1
                if res.critical_defect == "UNHANDLED_CRASH":
                    unhandled_crashes += 1
                elif res.critical_defect == "TIMEOUT_VIOLATION":
                    timeout_violations += 1
                elif res.critical_defect == "CORRUPTED_OUTPUT":
                    corrupted_outputs += 1

        total_executed = sum(completed_counts.values())

        category_details: Dict[ReliabilityCategory, CategoryScoreDetail] = {}
        earned_sum = 0.0

        for cat in ("normal", "robustness", "edge"):
            max_pts = CATEGORY_MAX_POINTS[cat]
            comp = completed_counts[cat]
            pas = passed_counts[cat]
            fail = failed_counts[cat]
            tot = total_counts[cat]

            if total_executed == 0 or comp == 0:
                earned: Optional[float] = None
            else:
                earned = round(max_pts * (pas / comp), 2)
                earned_sum += earned

            category_details[cat] = CategoryScoreDetail(
                completed=comp,
                passed=pas,
                failed=fail,
                total=tot,
                max_points=max_pts,
                earned_points=earned,
            )

        total_deductions = (
            unhandled_crashes * DEDUCTION_AMOUNTS["UNHANDLED_CRASH"]
            + timeout_violations * DEDUCTION_AMOUNTS["TIMEOUT_VIOLATION"]
            + corrupted_outputs * DEDUCTION_AMOUNTS["CORRUPTED_OUTPUT"]
        )

        final_score: Optional[float] = None
        if total_executed > 0:
            final_score = round(max(0.0, min(100.0, earned_sum - total_deductions)), 2)

        return ReliabilityScoreBreakdown(
            normal=category_details["normal"],
            robustness=category_details["robustness"],
            edge=category_details["edge"],
            unhandled_crashes=unhandled_crashes,
            timeout_violations=timeout_violations,
            corrupted_outputs=corrupted_outputs,
            total_deductions=total_deductions,
            final_score=final_score,
            formula_description=self.FORMULA_DESCRIPTION,
        )
