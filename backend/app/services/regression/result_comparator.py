from typing import Dict, List, Set

from app.schemas.regression import (
    BaselineScenarioEntry,
    BaselineSnapshot,
    RegressionDiff,
    ScenarioTransition,
    TransitionClassification,
)
from app.schemas.reliability import ScenarioResult


class RegressionComparisonError(ValueError):
    """Raised when baseline or post-repair inputs are invalid or incompatible."""


class ResultComparator:
    """Pure deterministic comparator for pre-repair vs post-repair scenario results."""

    def compare(
        self,
        baseline: BaselineSnapshot,
        post_repair_results: List[ScenarioResult],
    ) -> RegressionDiff:
        if not baseline.baseline_results:
            raise RegressionComparisonError("Baseline snapshot contains no scenarios to compare.")

        # 1. Index baseline scenarios and reject duplicate IDs
        baseline_map: Dict[str, BaselineScenarioEntry] = {}
        seen_baseline: Set[str] = set()
        for entry in baseline.baseline_results:
            if entry.scenario_id in seen_baseline:
                raise RegressionComparisonError(
                    f"Duplicate scenario_id '{entry.scenario_id}' in baseline snapshot."
                )
            seen_baseline.add(entry.scenario_id)
            baseline_map[entry.scenario_id] = entry

        # 2. Index post-repair scenarios, reject duplicates and unexpected IDs
        post_map: Dict[str, ScenarioResult] = {}
        seen_post: Set[str] = set()
        unexpected_ids: List[str] = []
        for res in post_repair_results:
            if res.scenario_id in seen_post:
                raise RegressionComparisonError(
                    f"Duplicate scenario_id '{res.scenario_id}' in post-repair results."
                )
            seen_post.add(res.scenario_id)
            if res.scenario_id not in baseline_map:
                unexpected_ids.append(res.scenario_id)
            else:
                post_map[res.scenario_id] = res

        if unexpected_ids:
            raise RegressionComparisonError(
                f"Unexpected post-repair scenario ID(s) not present in baseline: {', '.join(unexpected_ids)}."
            )

        # 3. Compare each baseline scenario against post-repair outcome
        transitions: List[ScenarioTransition] = []
        missing_ids: List[str] = []
        fixed_count = 0
        unresolved_count = 0
        stable_count = 0
        regression_count = 0
        incomplete_count = 0

        for entry in baseline.baseline_results:
            sid = entry.scenario_id
            post_res = post_map.get(sid)

            if post_res is None:
                missing_ids.append(sid)
                incomplete_count += 1
                transitions.append(
                    ScenarioTransition(
                        scenario_id=sid,
                        category=entry.category,
                        sample_input=entry.sample_input,
                        expected_handling=entry.expected_handling,
                        before_status=entry.status,
                        after_status="NOT_RUN",
                        classification="INCOMPLETE",
                        before_error=entry.error_message,
                        note="Missing post-repair result for baseline scenario.",
                    )
                )
                continue

            if post_res.category != entry.category or post_res.expected_handling != entry.expected_handling:
                raise RegressionComparisonError(
                    f"Incompatible metadata for scenario '{sid}': "
                    f"baseline ({entry.category}/{entry.expected_handling}) vs "
                    f"post-repair ({post_res.category}/{post_res.expected_handling})."
                )

            if entry.status == "NOT_RUN" or post_res.status == "NOT_RUN":
                incomplete_count += 1
                classification: TransitionClassification = (
                    "NOT_RUN" if (entry.status == "NOT_RUN" and post_res.status == "NOT_RUN") else "INCOMPLETE"
                )
                transitions.append(
                    ScenarioTransition(
                        scenario_id=sid,
                        category=entry.category,
                        sample_input=entry.sample_input,
                        expected_handling=entry.expected_handling,
                        before_status=entry.status,
                        after_status=post_res.status,
                        classification=classification,
                        before_error=entry.error_message,
                        after_error=post_res.error_message,
                        note="Scenario was not executed in baseline or post-repair run.",
                    )
                )
                continue

            if entry.status == "FAILED" and post_res.status == "PASSED":
                classification = "FIXED"
                fixed_count += 1
            elif entry.status == "FAILED" and post_res.status == "FAILED":
                classification = "UNRESOLVED"
                unresolved_count += 1
            elif entry.status == "PASSED" and post_res.status == "PASSED":
                classification = "STABLE"
                stable_count += 1
            else:
                # entry.status == "PASSED" and post_res.status == "FAILED"
                classification = "REGRESSION"
                regression_count += 1

            transitions.append(
                ScenarioTransition(
                    scenario_id=sid,
                    category=entry.category,
                    sample_input=entry.sample_input,
                    expected_handling=entry.expected_handling,
                    before_status=entry.status,
                    after_status=post_res.status,
                    classification=classification,
                    before_error=entry.error_message,
                    after_error=post_res.error_message,
                )
            )

        return RegressionDiff(
            total_scenarios=len(baseline.baseline_results),
            fixed_count=fixed_count,
            unresolved_count=unresolved_count,
            stable_count=stable_count,
            regression_count=regression_count,
            incomplete_count=incomplete_count,
            missing_post_repair_ids=missing_ids,
            unexpected_post_repair_ids=[],
            transitions=transitions,
        )
