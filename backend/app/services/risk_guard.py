"""
Risk Guard — prevents catastrophic AI decisions.
Runs AFTER every agent output before execution.
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("shangtanai.risk_guard")


@dataclass
class RiskResult:
    allowed: bool
    violations: list[str] = field(default_factory=list)
    action: str = "proceed"  # proceed / pause_and_notify / block


# System-wide hard limits that can NEVER be exceeded
HARD_LIMITS = {
    "max_single_product_cost": 10000,       # Never source >10k RMB
    "max_daily_ad_spend_per_store": 5000,   # Never spend >5k/day on ads
    "max_single_ad_bid": 50,                # Never bid >50 RMB per click
    "min_gross_margin": 0.15,               # Never list with <15% margin
    "max_discount_percent": 0.50,           # Never discount >50%
    "max_content_publish_per_day": 10,      # Never publish >10 pieces/day per platform
    "max_price_change_percent": 0.20,       # Never change price >20% in one step
    "max_new_pipelines_per_day": 3,         # Never start >3 new product pipelines per day
}


class RiskGuard:
    """Validates AI decisions against hard limits and store-specific thresholds."""

    async def check(
        self,
        decision_type: str,
        decision: dict,
        store_thresholds: dict | None = None,
    ) -> RiskResult:
        violations = []

        # Check system hard limits
        for key, limit in HARD_LIMITS.items():
            value = decision.get(key)
            if value is not None and value > limit:
                violations.append(
                    f"超出系统限制 {key}: {value} > {limit}"
                )

        # Check store-specific thresholds
        if store_thresholds:
            for key, limit in store_thresholds.items():
                value = decision.get(key)
                if value is not None and value > limit:
                    violations.append(
                        f"超出店铺限制 {key}: {value} > {limit}"
                    )

        # Decision-type specific checks
        if decision_type == "product_select":
            violations.extend(self._check_product_selection(decision))
        elif decision_type == "ad_bid":
            violations.extend(self._check_ad_decision(decision))
        elif decision_type == "content_publish":
            violations.extend(self._check_content_publish(decision))

        if violations:
            logger.warning("Risk guard blocked: %s — %s", decision_type, violations)
            return RiskResult(
                allowed=False,
                violations=violations,
                action="pause_and_notify",
            )

        return RiskResult(allowed=True)

    def _check_product_selection(self, decision: dict) -> list[str]:
        violations = []
        margin = decision.get("estimated_gross_margin", 0)
        if margin < HARD_LIMITS["min_gross_margin"]:
            violations.append(f"毛利率过低: {margin:.1%} < {HARD_LIMITS['min_gross_margin']:.0%}")

        # Check for categories requiring special qualifications
        risky_categories = {"食品", "化妆品", "医疗器械", "保健品", "母婴", "药品"}
        category = decision.get("category", "")
        if any(rc in category for rc in risky_categories):
            if not decision.get("has_qualification", False):
                violations.append(f"品类 '{category}' 需要特殊资质")
        return violations

    def _check_ad_decision(self, decision: dict) -> list[str]:
        violations = []
        daily_budget = decision.get("daily_budget", 0)
        if daily_budget > HARD_LIMITS["max_daily_ad_spend_per_store"]:
            violations.append(f"日广告预算过高: ¥{daily_budget}")

        bid = decision.get("bid_amount", 0)
        if bid > HARD_LIMITS["max_single_ad_bid"]:
            violations.append(f"单次出价过高: ¥{bid}")
        return violations

    def _check_content_publish(self, decision: dict) -> list[str]:
        violations = []
        violation_level = decision.get("violation_level", "green")
        if violation_level == "red":
            violations.append("内容违规检测: 红色（阻断发布）")
        return violations


risk_guard = RiskGuard()
