"""Card management router — add, list, update, remove cards from user wallet."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.db import get_db
from app.models import User, UserCard, CardProduct
from app.schemas import UserCardCreate, UserCardOut, UserCardDetail, CardProductDetail

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/", response_model=list[UserCardDetail])
def list_my_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all cards in the current user's wallet."""
    cards = (
        db.query(UserCard)
        .options(
            joinedload(UserCard.card_product)
            .joinedload(CardProduct.issuer)
        )
        .filter(UserCard.user_id == current_user.id, UserCard.is_active == True)
        .order_by(UserCard.added_at.desc())
        .all()
    )
    return [UserCardDetail.model_validate(c) for c in cards]


@router.post("/", response_model=UserCardOut, status_code=201)
def add_card(
    body: UserCardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a card to the user's wallet by selecting a known card product."""
    # Verify card product exists
    product = db.get(CardProduct, body.card_product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Card product not found")

    # A soft-deleted card can be restored. Reusing its record also preserves
    # the links from historical transactions and avoids the unique constraint.
    existing = (
        db.query(UserCard)
        .filter_by(
            user_id=current_user.id,
            card_product_id=body.card_product_id,
            last_four=body.last_four,
        )
        .first()
    )
    if existing and existing.is_active:
        raise HTTPException(status_code=409, detail="This card is already in your wallet")

    # If this is set as default, unset other defaults
    if body.is_default:
        db.query(UserCard).filter_by(
            user_id=current_user.id, is_default=True
        ).update({"is_default": False})

    if existing:
        existing.is_active = True
        existing.nickname = body.nickname or product.name
        existing.is_default = body.is_default
        db.commit()
        db.refresh(existing)
        return UserCardOut.model_validate(existing)

    card = UserCard(
        user_id=current_user.id,
        card_product_id=body.card_product_id,
        nickname=body.nickname or product.name,
        last_four=body.last_four,
        is_default=body.is_default,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return UserCardOut.model_validate(card)


@router.patch("/{card_id}", response_model=UserCardOut)
def update_card(
    card_id: int,
    nickname: str | None = None,
    is_default: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a card's nickname or default status."""
    card = db.query(UserCard).filter_by(id=card_id, user_id=current_user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if nickname is not None:
        card.nickname = nickname
    if is_default is not None:
        if is_default:
            db.query(UserCard).filter_by(
                user_id=current_user.id, is_default=True
            ).update({"is_default": False})
        card.is_default = is_default

    db.commit()
    db.refresh(card)
    return UserCardOut.model_validate(card)


@router.delete("/{card_id}", status_code=204)
def remove_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-delete a card from the user's wallet."""
    card = db.query(UserCard).filter_by(id=card_id, user_id=current_user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.is_active = False
    db.commit()
