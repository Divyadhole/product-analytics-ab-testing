"""Frequentist A/B-test calculations implemented without external packages."""

from __future__ import annotations

import math
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExperimentResult:
    control_users: int
    treatment_users: int
    control_conversions: int
    treatment_conversions: int
    control_rate: float
    treatment_rate: float
    absolute_lift: float
    relative_lift: float
    z_score: float
    p_value: float
    ci_low: float
    ci_high: float
    significant: bool


def normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def sample_ratio_mismatch(control: int, treatment: int) -> dict:
    """Test observed allocation against the planned 50/50 split."""
    total = control + treatment
    if total <= 0:
        raise ValueError("Experiment must contain assigned users")
    expected = total / 2
    chi_square = ((control - expected) ** 2 + (treatment - expected) ** 2) / expected
    # Chi-square with one degree of freedom equals a squared standard normal.
    p_value = math.erfc(math.sqrt(chi_square / 2))
    return {"chi_square": chi_square, "p_value": p_value, "passed": p_value >= 0.01}


def required_sample_size(baseline: float, minimum_detectable_effect: float,
                         alpha: float = 0.05, power: float = 0.80) -> int:
    """Approximate required users per variant for two independent proportions."""
    if not 0 < baseline < 1 or minimum_detectable_effect <= 0:
        raise ValueError("Baseline must be a probability and MDE must be positive")
    target = baseline + minimum_detectable_effect
    if target >= 1:
        raise ValueError("Baseline plus MDE must be below one")
    # Constants for the common 95% confidence / 80% power design.
    if alpha != 0.05 or power != 0.80:
        raise ValueError("This dependency-free implementation supports alpha=.05 and power=.80")
    z_alpha, z_beta = 1.959963984540054, 0.8416212335729143
    pooled = (baseline + target) / 2
    numerator = (
        z_alpha * math.sqrt(2 * pooled * (1 - pooled))
        + z_beta * math.sqrt(baseline * (1 - baseline) + target * (1 - target))
    ) ** 2
    return math.ceil(numerator / minimum_detectable_effect ** 2)


def two_proportion_test(c_success: int, c_total: int, t_success: int, t_total: int) -> ExperimentResult:
    if min(c_total, t_total) <= 0:
        raise ValueError("Both variants must contain users")
    pc, pt = c_success / c_total, t_success / t_total
    diff = pt - pc
    pooled = (c_success + t_success) / (c_total + t_total)
    pooled_se = math.sqrt(pooled * (1 - pooled) * (1 / c_total + 1 / t_total))
    z_score = diff / pooled_se if pooled_se else 0.0
    p_value = math.erfc(abs(z_score) / math.sqrt(2))
    unpooled_se = math.sqrt(pc * (1 - pc) / c_total + pt * (1 - pt) / t_total)
    return ExperimentResult(
        control_users=c_total, treatment_users=t_total,
        control_conversions=c_success, treatment_conversions=t_success,
        control_rate=pc, treatment_rate=pt, absolute_lift=diff,
        relative_lift=(diff / pc if pc else 0), z_score=z_score, p_value=p_value,
        ci_low=diff - 1.96 * unpooled_se, ci_high=diff + 1.96 * unpooled_se,
        significant=p_value < 0.05,
    )


def analyze(db_path: Path) -> dict:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT variant, users, purchasers FROM experiment_summary ORDER BY variant"
        ).fetchall()
    values = {variant: (purchasers, users) for variant, users, purchasers in rows}
    result = two_proportion_test(*values["control"], *values["treatment"])
    payload = asdict(result)
    srm = sample_ratio_mismatch(result.control_users, result.treatment_users)
    payload["sample_ratio_mismatch"] = srm
    payload["planned_mde"] = 0.025
    payload["required_users_per_variant"] = required_sample_size(
        result.control_rate, payload["planned_mde"]
    )
    payload["adequately_powered"] = min(result.control_users, result.treatment_users) >= payload["required_users_per_variant"]
    payload["recommendation"] = (
        "Ship treatment" if (
            result.significant and result.absolute_lift > 0
            and srm["passed"] and payload["adequately_powered"]
        )
        else "Do not ship; collect more evidence"
    )
    return payload
