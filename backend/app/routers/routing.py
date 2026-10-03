"""Routing endpoint for comparing cards in the user's wallet."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.ai.classifier import classify_merchant
from app.services.routing_engine import rank_cards
from app.schemas import (
    RoutingRequest,
    RoutingResponse,
    CardRanking,
    UserCardDetail,
)

router = APIRouter(prefix="/route", tags=["routing"])


@router.post("/", response_model=RoutingResponse)
def get_recommendation(
    body: RoutingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compare the user's cards for a merchant and purchase amount.

    Given a merchant name and amount, returns the best card from the user's
    wallet with reasoning, plus ranked alternatives.
    """
    # 1. Classify merchant into spending category
    category = classify_merchant(body.merchant_name)

    # 2. Rank all user's cards
    rankings = rank_cards(
        current_user.id,
        category,
        body.amount,
        db,
        apple_pay_india=body.apple_pay_india,
    )

    if not rankings:
        return RoutingResponse(
            recommended=CardRanking(
                card=UserCardDetail(
                    id=0, user_id=current_user.id, card_product_id=0,
                    added_at="2026-01-01T00:00:00Z",
                ),
                reward_value=Decimal("0"),
                earn_rate=Decimal("0"),
                reasoning=(
                    "No eligible Axis Bank Visa or Mastercard is saved yet."
                    if body.apple_pay_india
                    else "No cards in your wallet yet. Add a card to get started!"
                ),
            ),
            category_detected=category,
        )

    # Build response
    def _to_ranking(r: dict) -> CardRanking:
        uc = r["user_card"]
        # Eagerly load card_product with issuer and reward_rules for detail
        return CardRanking(
            card=UserCardDetail.model_validate(uc),
            reward_value=r["reward_value"],
            earn_rate=r["earn_rate"],
            reasoning=r["reasoning"],
        )

    best = _to_ranking(rankings[0])
    alternatives = [_to_ranking(r) for r in rankings[1:4]]  # top 3 alternatives

    savings = Decimal("0")
    if len(rankings) > 1:
        savings = rankings[0]["reward_value"] - rankings[-1]["reward_value"]

    return RoutingResponse(
        recommended=best,
        alternatives=alternatives,
        category_detected=category,
        savings_vs_worst=max(savings, Decimal("0")),
    )
