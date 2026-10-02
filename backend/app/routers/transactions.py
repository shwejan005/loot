"""Transaction router — add transactions (manual / SMS), list, and view analysis."""

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.db import get_db
from app.models import User, UserCard, Transaction, Merchant, CardProduct
from app.schemas import (
    TransactionCreate,
    TransactionOut,
    TransactionDetail,
    SMSTransactionCreate,
    PaginatedResponse,
)
from app.services.sms_parser import parse_sms
from app.ai.classifier import classify_merchant
from app.services.routing_engine import rank_cards

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _enrich_transaction(txn: Transaction, user_id: int, db: Session):
    """After creating a transaction, classify the merchant and compute routing."""
    # 1. Classify merchant category
    merchant_name = txn.merchant_raw or ""
    if merchant_name and not txn.category:
        txn.category = classify_merchant(merchant_name)

    # 2. Resolve or create merchant
    if merchant_name and not txn.merchant_id:
        normalized = merchant_name.strip().lower()
        merchant = db.query(Merchant).filter_by(normalized_name=normalized).first()
        if not merchant:
            merchant = Merchant(
                raw_name=merchant_name,
                normalized_name=normalized,
                display_name=merchant_name.title(),
                category=txn.category or "other",
            )
            db.add(merchant)
            db.flush()
        txn.merchant_id = merchant.id

    # 3. Calculate reward on the card actually used
    if txn.card_id:
        card = db.get(
            UserCard,
            txn.card_id,
            options=[joinedload(UserCard.card_product)],
        )
        if card:
            from app.services.routing_engine import (
                get_applicable_rules,
                calculate_reward_value,
                calculate_base_reward,
            )
            rules = get_applicable_rules(card.card_product_id, txn.category or "other", db)
            if rules:
                best_rule = max(rules, key=lambda r: calculate_reward_value(txn.amount, r, card.card_product))
                txn.reward_earned = calculate_reward_value(txn.amount, best_rule, card.card_product)
            else:
                txn.reward_earned = calculate_base_reward(txn.amount, card.card_product)

    # 4. Find optimal card via routing engine
    if txn.category:
        rankings = rank_cards(user_id, txn.category, txn.amount, db)
        if rankings:
            best = rankings[0]
            txn.optimal_card_id = best["user_card"].id
            txn.optimal_reward = best["reward_value"]
            txn.reward_missed = max(Decimal("0"), txn.optimal_reward - (txn.reward_earned or Decimal("0")))

    db.commit()


@router.post("/", response_model=TransactionOut, status_code=201)
def add_transaction(
    body: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually add a transaction."""
    # Validate card belongs to user
    if body.card_id:
        card = db.query(UserCard).filter_by(id=body.card_id, user_id=current_user.id).first()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found in your wallet")

    txn = Transaction(
        user_id=current_user.id,
        card_id=body.card_id,
        merchant_raw=body.merchant_raw,
        amount=body.amount,
        currency=body.currency,
        category=body.category,
        source=body.source,
        transacted_at=body.transacted_at or datetime.now(timezone.utc),
    )
    db.add(txn)
    db.flush()

    _enrich_transaction(txn, current_user.id, db)
    db.refresh(txn)
    return TransactionOut.model_validate(txn)


@router.post("/sms", response_model=TransactionOut, status_code=201)
def add_transaction_from_sms(
    body: SMSTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Parse a raw bank SMS and create a transaction from it."""
    parsed = parse_sms(body.sms_body)
    if not parsed:
        raise HTTPException(
            status_code=422,
            detail="Could not parse a transaction from this SMS. Is it a bank debit/credit alert?",
        )
    if parsed.is_credit:
        raise HTTPException(status_code=422, detail="Refund and credit alerts cannot be imported as purchases yet.")
    if parsed.amount <= 0:
        raise HTTPException(status_code=422, detail="The alert must contain a positive purchase amount.")

    # Try to match card by last-four digits
    card_id = None
    if parsed.last_four:
        card = (
            db.query(UserCard)
            .filter_by(user_id=current_user.id, last_four=parsed.last_four, is_active=True)
            .first()
        )
        if card:
            card_id = card.id

    txn = Transaction(
        user_id=current_user.id,
        card_id=card_id,
        merchant_raw=parsed.merchant,
        amount=parsed.amount,
        currency="INR",
        source="sms",
        transacted_at=parsed.timestamp or datetime.now(timezone.utc),
    )
    db.add(txn)
    db.flush()

    _enrich_transaction(txn, current_user.id, db)
    db.refresh(txn)
    return TransactionOut.model_validate(txn)


@router.get("/", response_model=PaginatedResponse[TransactionOut])
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    card_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the current user's transactions with pagination and filters."""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if category:
        query = query.filter(Transaction.category == category)
    if card_id:
        query = query.filter(Transaction.card_id == card_id)

    total = query.count()
    items = (
        query.order_by(Transaction.transacted_at.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        items=[TransactionOut.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{txn_id}", response_model=TransactionDetail)
def get_transaction(
    txn_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single transaction with card and merchant details."""
    txn = (
        db.query(Transaction)
        .options(
            joinedload(Transaction.card_used).joinedload(UserCard.card_product).joinedload(CardProduct.issuer),
            joinedload(Transaction.optimal_card).joinedload(UserCard.card_product).joinedload(CardProduct.issuer),
            joinedload(Transaction.merchant),
        )
        .filter(Transaction.id == txn_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionDetail.model_validate(txn)
