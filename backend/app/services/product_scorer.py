"""
Product Scorer — deterministic scoring before AI evaluation.
Filters out obviously bad products before spending AI tokens.
"""
from dataclasses import dataclass, field


WEIGHTS = {
    "demand_heat": 0.25,
    "profit_margin": 0.25,
    "competition_gap": 0.20,
    "trend_momentum": 0.15,
    "supply_accessibility": 0.15,
}

# Platform-specific minimum margin requirements
MIN_MARGINS = {
    "douyin": 0.40,
    "taobao": 0.30,
    "pinduoduo": 0.25,
    "xiaohongshu": 0.35,
    "default": 0.25,
}


@dataclass
class ScoredProduct:
    keyword: str
    scores: dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    go_decision: str = "no_go"  # go / conditional / no_go
    confidence: float = 0.0
    rejection_reasons: list[str] = field(default_factory=list)


class ProductScorer:
    """Five-dimension deterministic product scoring."""

    def score(
        self,
        keyword: str,
        market_data: dict,
        supply_data: dict | None = None,
        target_platform: str = "default",
    ) -> ScoredProduct:
        result = ScoredProduct(keyword=keyword)

        # Hard filters (instant NO-GO)
        hard_reject = self._hard_filter(market_data, supply_data, target_platform)
        if hard_reject:
            result.rejection_reasons = hard_reject
            result.go_decision = "no_go"
            result.confidence = 0.9  # High confidence it's bad
            return result

        # Five-dimension scoring
        result.scores["demand_heat"] = self._score_demand(market_data)
        result.scores["profit_margin"] = self._score_margin(market_data, target_platform)
        result.scores["competition_gap"] = self._score_competition(market_data)
        result.scores["trend_momentum"] = self._score_trend(market_data)
        result.scores["supply_accessibility"] = self._score_supply(supply_data or {})

        result.total_score = sum(
            result.scores[k] * WEIGHTS[k] for k in WEIGHTS
        )
        result.total_score = round(result.total_score, 2)

        # Determine decision
        if result.total_score >= 3.5:
            result.go_decision = "go"
            result.confidence = min(0.7 + (result.total_score - 3.5) * 0.2, 0.95)
        elif result.total_score >= 2.5:
            result.go_decision = "conditional"
            result.confidence = 0.5 + (result.total_score - 2.5) * 0.2
        else:
            result.go_decision = "no_go"
            result.confidence = 0.7 + (2.5 - result.total_score) * 0.1

        result.confidence = round(result.confidence, 2)
        return result

    def _hard_filter(
        self, market_data: dict, supply_data: dict | None, platform: str
    ) -> list[str]:
        """Hard reject reasons. Any one = instant NO-GO."""
        reasons = []

        # Net margin too low
        estimated_margin = market_data.get("estimated_net_margin", 0)
        min_margin = MIN_MARGINS.get(platform, MIN_MARGINS["default"])
        if estimated_margin > 0 and estimated_margin < 0.15:
            reasons.append(f"净利率过低: {estimated_margin:.0%} < 15%")

        # Monthly search volume too low
        monthly_searches = market_data.get("monthly_searches", 0)
        if 0 < monthly_searches < 100:
            reasons.append(f"月搜索量过低: {monthly_searches}")

        # Market monopoly
        top3_share = market_data.get("top3_market_share", 0)
        if top3_share > 0.80:
            reasons.append(f"市场垄断: Top3占{top3_share:.0%}市场份额")

        # High IP risk
        if market_data.get("ip_risk", False):
            reasons.append("高侵权风险")

        # No suppliers at all
        if supply_data and supply_data.get("supplier_count", -1) == 0:
            reasons.append("1688无供应商")

        return reasons

    def _score_demand(self, data: dict) -> float:
        """Score 1-5 based on search volume trend."""
        trend = data.get("search_trend", "stable")  # rising/stable/declining
        volume = data.get("monthly_searches", 0)

        base = {"rising": 4.0, "stable": 3.0, "declining": 1.5}.get(trend, 3.0)
        # Volume bonus
        if volume > 50000:
            base = min(base + 0.5, 5.0)
        elif volume > 10000:
            base = min(base + 0.3, 5.0)
        return round(base, 1)

    def _score_margin(self, data: dict, platform: str) -> float:
        """Score 1-5 based on estimated net margin."""
        margin = data.get("estimated_net_margin", 0)
        if margin <= 0:
            return 1.0
        if margin >= 0.50:
            return 5.0
        if margin >= 0.40:
            return 4.0
        if margin >= 0.30:
            return 3.0
        if margin >= 0.20:
            return 2.0
        return 1.0

    def _score_competition(self, data: dict) -> float:
        """Score 1-5 based on number of sellers."""
        sellers = data.get("seller_count", 0)
        if sellers <= 0:
            return 3.0  # Unknown
        if sellers < 50:
            return 5.0
        if sellers < 200:
            return 3.5
        if sellers < 500:
            return 2.0
        return 1.0

    def _score_trend(self, data: dict) -> float:
        """Score 1-5 based on week-over-week search growth."""
        wow_growth = data.get("wow_growth", 0)  # percentage
        if wow_growth > 20:
            return 5.0
        if wow_growth > 10:
            return 4.0
        if wow_growth > 0:
            return 3.0
        return 1.0

    def _score_supply(self, data: dict) -> float:
        """Score 1-5 based on 1688 supplier availability."""
        count = data.get("supplier_count", 0)
        has_dropship = data.get("has_dropship_suppliers", False)

        if count == 0:
            return 1.0
        if has_dropship and count >= 10:
            return 5.0
        if has_dropship and count >= 3:
            return 4.0
        if count >= 3:
            return 3.0
        return 2.0


product_scorer = ProductScorer()
