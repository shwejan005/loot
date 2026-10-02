"""Loot Wallet routing engine.

Given a user, a merchant, and an amount, returns the card from the user's
wallet that earns the highest reward value for that purchase.
"""

from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models import UserCard, CardProduct, RewardRule


# ── Spending categories recognised by Loot Wallet ───────────────────────

CATEGORIES = [
    "dining",
    "grocery",
    "fuel",
    "travel",
    "online",
    "utilities",
    "entertainment",
    "healthcare",
    "education",
    "insurance",
    "government",
    "rent",
    "international",
    "department_store",
    "other",
]


def get_applicable_rules(
    card_product_id: int,
    category: str,
    db: Session,
    now: datetime | None = None,
) -> list[RewardRule]:
    """Return all reward rules for a card product + category that are
    currently valid (within date range or permanent)."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    query = (
        db.query(RewardRule)
        .filter(RewardRule.card_product_id == card_product_id)
        .filter(RewardRule.category == category)
    )
    rules = query.all()
    # Filter to active rules (permanent or within date window)
    def in_range(value: datetime | None, compare_before: bool) -> bool:
        if value is None:
            return True
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value <= now if compare_before else value >= now

    return [r for r in rules if in_range(r.valid_from, True) and in_range(r.valid_to, False)]


def _apply_rule_caps(reward: Decimal, rule: RewardRule) -> Decimal:
    caps = [cap for cap in (rule.monthly_cap, rule.quarterly_cap) if cap is not None]
    return max(min(reward, *caps) if caps else reward, Decimal("0"))


def calculate_reward_value(
    amount: Decimal,
    rule: RewardRule,
    card: CardProduct,
) -> Decimal:
    """Calculate the INR reward value for a single transaction + rule."""
    if rule.min_spend is not None and amount < rule.min_spend:
        # Transaction too small for bonus — fall back to base rate
        return _apply_rule_caps(amount * card.base_earn_rate * card.point_value, rule)

    if rule.earn_type == "cashback_pct":
        # Cashback percentage: 5% of ₹500 = ₹25
        return _apply_rule_caps(amount * (rule.earn_rate / Decimal("100")), rule)
    else:
        # Multiplier: 5x means 5 points per ₹100 (or per ₹150, depends on card)
        # Simplified: earn_rate * base_rate * point_value * amount
        points_earned = amount * rule.earn_rate * card.base_earn_rate
        return _apply_rule_caps(points_earned * card.point_value, rule)


def calculate_base_reward(amount: Decimal, card: CardProduct) -> Decimal:
    """Fallback: reward value when no category-specific rule matches."""
    points = amount * card.base_earn_rate
    return points * card.point_value


def rank_cards(
    user_id: int,
    category: str,
    amount: Decimal,
    db: Session,
) -> list[dict]:
    """Rank all of a user's active cards by expected reward value.

    Returns a list of dicts:
      [{"user_card": UserCard, "card_product": CardProduct,
        "reward_value": Decimal, "earn_rate": Decimal,
        "rule": RewardRule | None, "reasoning": str}, ...]
    sorted descending by reward_value.
    """
    user_cards = (
        db.query(UserCard)
        .options(joinedload(UserCard.card_product).joinedload(CardProduct.issuer))
        .filter(UserCard.user_id == user_id, UserCard.is_active == True)
        .all()
    )

    rankings = []
    for uc in user_cards:
        cp = uc.card_product
        rules = get_applicable_rules(cp.id, category, db)

        if rules:
            # Pick the best rule for this category
            best_rule = max(rules, key=lambda r: calculate_reward_value(amount, r, cp))
            reward_val = calculate_reward_value(amount, best_rule, cp)
            effective_rate = best_rule.earn_rate
            reasoning = (
                f"{cp.issuer.name} {cp.name} earns {best_rule.earn_rate}x "
                f"on {category} (≈₹{reward_val:.0f} back)"
            )
        else:
            reward_val = calculate_base_reward(amount, cp)
            effective_rate = cp.base_earn_rate
            best_rule = None
            reasoning = (
                f"{cp.issuer.name} {cp.name} earns base rate "
                f"({cp.base_earn_rate}x) on {category} (≈₹{reward_val:.0f} back)"
            )

        rankings.append({
            "user_card": uc,
            "card_product": cp,
            "reward_value": reward_val,
            "earn_rate": effective_rate,
            "rule": best_rule,
            "reasoning": reasoning,
        })

    rankings.sort(key=lambda r: r["reward_value"], reverse=True)
    return rankings


def get_best_card(
    user_id: int,
    category: str,
    amount: Decimal,
    db: Session,
) -> dict | None:
    """Return the single best card for a purchase, or None if the user has no cards."""
    rankings = rank_cards(user_id, category, amount, db)
    return rankings[0] if rankings else None
