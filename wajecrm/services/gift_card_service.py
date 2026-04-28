"""
Central gift card redemption and deactivation service.
All endpoints delegate here — no business logic lives in views.
"""

import datetime
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from wajecrm.models import giftCard, giftcardtransaction, DeactivationReason


class GiftCardError(Exception):
    """Raised for any expected business-rule violation."""
    pass


def get_card_balance(card: giftCard) -> Decimal:
    """Return the remaining balance for a card."""
    redeemed = giftcardtransaction.objects.filter(
        giftID=card,
        redeemedamount__gt=0
    ).aggregate(total=Sum('redeemedamount'))['total'] or Decimal('0')
    return card.amount - redeemed


def validate_card_for_redemption(card: giftCard, amount: Decimal) -> Decimal:
    """
    Run all pre-redemption guards. Returns remaining balance.
    Raises GiftCardError with a user-facing message on any failure.
    """
    if card.expiration_date and card.expiration_date < datetime.date.today():
        raise GiftCardError('Voucher has expired.')

    if not card.active:
        raise GiftCardError('Voucher is inactive or has already been fully used.')

    balance = get_card_balance(card)

    if amount <= 0:
        raise GiftCardError('Redemption amount must be positive.')

    if amount > balance:
        raise GiftCardError(
            f'Redemption amount (₦{amount:,.2f}) exceeds '
            f'available balance (₦{balance:,.2f}).'
        )

    return balance


def deactivate_gift_card(
    card: giftCard,
    deactivated_by_user,          # user instance or None
    reason: str,                   # DeactivationReason value
):
    """
    Single shared deactivation function. Populates all audit fields.
    Always call this instead of setting card.active = False directly.
    """
    card.active = False
    card.deactivated_by = deactivated_by_user
    card.deactivated_date = timezone.now()
    card.deactivation_reason = reason
    card.save(update_fields=['active', 'deactivated_by', 'deactivated_date', 'deactivation_reason'])


@transaction.atomic
def redeem_normal(
    card: giftCard,
    amount: Decimal,
    merch_id: int,
    redeemed_by_user,              # user instance (for audit)
    reference: str = None,
) -> dict:
    """
    Normal (multi-use) redemption. Deactivates automatically when balance hits zero.
    Returns a result dict consumed by the calling view.
    """
    card = giftCard.objects.select_for_update().get(id=card.id)
    balance = validate_card_for_redemption(card, amount)

    giftcardtransaction.objects.create(
        giftID=card,
        redeemedamount=amount,
        merchID_id=merch_id,
        reference=reference,
        createdby=getattr(redeemed_by_user, 'username', str(redeemed_by_user)),
    )


    remaining = balance - amount

    if remaining <= 0:
        deactivate_gift_card(
            card,
            deactivated_by_user=redeemed_by_user,
            reason=DeactivationReason.BALANCE_EXHAUSTED,
        )

    return {
        'redeemed_amount': float(amount),
        'remaining_balance': float(max(remaining, Decimal('0'))),
        'active': card.active,
    }


@transaction.atomic
def redeem_full_and_deactivate(
    card: giftCard,
    amount: Decimal,
    merch_id: int,
    redeemed_by_user,
    reference: str = None,
) -> dict:
    """
    Full redemption + immediate deactivation path (checkout manager option 1).

    Only allows redemption if the provided amount fully clears the voucher
    balance (remaining balance must be zero). Also rejects if any prior
    redemption already exists.
    """

    # Re-check for prior redemptions — single-use enforcement
    card = giftCard.objects.select_for_update().get(id=card.id)

    prior = giftcardtransaction.objects.filter(
        giftID=card,
        redeemedamount__gt=0
    ).exists()

    if prior:
        # Defensively sync the active flag if it drifted
        if card.active:
            deactivate_gift_card(
                card,
                deactivated_by_user=redeemed_by_user,
                reason=DeactivationReason.MANAGER_FULL_REDEEM,
            )

        raise GiftCardError(
            "Voucher has already been redeemed and cannot be reused in full-redeem mode."
        )

    # Validate card and get current balance
    balance = validate_card_for_redemption(card, amount)

    remaining = balance - amount

    # Enforce FULL redemption only
    if remaining > Decimal("0"):
        raise GiftCardError(
            f"Full redemption required. Voucher balance is {balance}, "
            f"but attempted redemption is {amount}. Remaining balance would be {remaining}."
        )

    giftcardtransaction.objects.create(
        giftID=card,
        redeemedamount=amount,
        merchID_id=merch_id,
        reference=reference,
        createdby=getattr(
            redeemed_by_user,
            "username",
            str(redeemed_by_user),
        ),
    )

    deactivate_gift_card(
        card,
        deactivated_by_user=redeemed_by_user,
        reason=DeactivationReason.MANAGER_FULL_REDEEM,
    )

    return {
        "redeemed_amount": float(amount),
        "remaining_balance": 0.0,
        "active": False,
    }