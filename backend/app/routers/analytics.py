"""Analytics router — spending insights, monthly reports, card utilisation."""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.db import get_db
from app.models import User, UserCard, Transaction, CardProduct
from app.schemas import (
    SpendingByCategoryItem,
    MonthlyReportOut,
    CardUtilizationItem,
    UserCardDetail,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/spending-by-category", response_model=list[SpendingByCategoryItem])
def spending_by_category(
    months: int = Query(1, ge=1, le=24, description="Number of past months to analyse"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Breakdown of spending by category with reward earned vs. missed."""
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)

    results = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total_spent"),
            func.sum(Transaction.reward_earned).label("reward_earned"),
            func.sum(Transaction.reward_missed).label("reward_missed"),
            func.count(Transaction.id).label("txn_count"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transacted_at >= cutoff,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    return [
        SpendingByCategoryItem(
            category=r.category or "uncategorized",
            total_spent=r.total_spent or Decimal("0"),
            reward_earned=r.reward_earned or Decimal("0"),
            reward_missed=r.reward_missed or Decimal("0"),
            transaction_count=r.txn_count,
        )
        for r in results
    ]


@router.get("/card-utilization", response_model=list[CardUtilizationItem])
def card_utilization(
    months: int = Query(1, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """How well is each card being used? Shows times used vs. times optimal."""
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)

    cards = (
        db.query(UserCard)
        .options(joinedload(UserCard.card_product).joinedload(CardProduct.issuer))
        .filter(UserCard.user_id == current_user.id, UserCard.is_active == True)
        .all()
    )

    items = []
    for card in cards:
        used_count = (
            db.query(func.count(Transaction.id))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.card_id == card.id,
                Transaction.transacted_at >= cutoff,
            )
            .scalar() or 0
        )

        total_spent = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.card_id == card.id,
                Transaction.transacted_at >= cutoff,
            )
            .scalar() or Decimal("0")
        )

        reward_earned = (
            db.query(func.sum(Transaction.reward_earned))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.card_id == card.id,
                Transaction.transacted_at >= cutoff,
            )
            .scalar() or Decimal("0")
        )

        optimal_count = (
            db.query(func.count(Transaction.id))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.optimal_card_id == card.id,
                Transaction.transacted_at >= cutoff,
            )
            .scalar() or 0
        )

        utilization_pct = 0.0
        if optimal_count > 0:
            used_when_optimal = (
                db.query(func.count(Transaction.id))
                .filter(
                    Transaction.user_id == current_user.id,
                    Transaction.card_id == card.id,
                    Transaction.optimal_card_id == card.id,
                    Transaction.transacted_at >= cutoff,
                )
                .scalar() or 0
            )
            utilization_pct = round(used_when_optimal / optimal_count * 100, 1)

        items.append(CardUtilizationItem(
            card=UserCardDetail.model_validate(card),
            transaction_count=used_count,
            total_spent=total_spent,
            reward_earned=reward_earned,
            times_was_optimal=optimal_count,
            times_was_used=used_count,
            utilization_pct=utilization_pct,
        ))

    items.sort(key=lambda x: x.total_spent, reverse=True)
    return items


@router.get("/monthly-report", response_model=MonthlyReportOut)
def monthly_report(
    month: str = Query(..., description="Month in YYYY-MM format", pattern=r"^\d{4}-\d{2}$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a monthly spending + rewards report."""
    from datetime import datetime, timezone
    year, mon = map(int, month.split("-"))
    start = datetime(year, mon, 1, tzinfo=timezone.utc)
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)

    txns = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transacted_at >= start,
            Transaction.transacted_at < end,
        )
        .all()
    )

    total_spent = sum(t.amount for t in txns) if txns else Decimal("0")
    total_earned = sum(t.reward_earned or Decimal("0") for t in txns)
    total_missed = sum(t.reward_missed or Decimal("0") for t in txns)

    category_totals: dict[str, Decimal] = {}
    for t in txns:
        cat = t.category or "other"
        category_totals[cat] = category_totals.get(cat, Decimal("0")) + t.amount
    top_cat = max(category_totals, key=category_totals.get, default="none") if category_totals else "none"

    return MonthlyReportOut(
        month=month,
        total_spent=total_spent,
        total_reward_earned=total_earned,
        total_reward_missed=total_missed,
        top_category=top_cat,
    )


@router.get("/summary")
def quick_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Quick stats for the dashboard header."""
    total_txns = db.query(func.count(Transaction.id)).filter(
        Transaction.user_id == current_user.id
    ).scalar() or 0

    total_earned = db.query(func.sum(Transaction.reward_earned)).filter(
        Transaction.user_id == current_user.id
    ).scalar() or Decimal("0")

    total_missed = db.query(func.sum(Transaction.reward_missed)).filter(
        Transaction.user_id == current_user.id
    ).scalar() or Decimal("0")

    card_count = db.query(func.count(UserCard.id)).filter(
        UserCard.user_id == current_user.id, UserCard.is_active == True
    ).scalar() or 0

    return {
        "total_transactions": total_txns,
        "total_reward_earned": float(total_earned),
        "total_reward_missed": float(total_missed),
        "card_count": card_count,
        "money_left_on_table": float(total_missed),
    }
