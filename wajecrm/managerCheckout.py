import json
import datetime
from decimal import Decimal
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from wajecrm.models import giftCard
from wajecrm.services.gift_card_service import (
    GiftCardError,
    get_card_balance,
    redeem_normal,
    redeem_full_and_deactivate,
)


REDEMPTION_TYPE_NORMAL = 'normal'
REDEMPTION_TYPE_FULL = 'full_deactivate'


@extend_schema(tags=['Checkout Manager'])
class CheckoutVoucherBalanceView(APIView):
    """
    GET /checkout/voucher-balance/?serialnumber=XXX
    Read-only balance check — no changes made.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        serialnumber = request.GET.get('serialnumber', '').strip()
        if not serialnumber:
            return _json({'status': False, 'message': 'serialnumber is required.'})

        card = giftCard.objects.filter(serialnumber=serialnumber).first()
        if not card:
            return _json({'status': False, 'message': 'Voucher not found.'})

        if card.expiration_date and card.expiration_date < datetime.date.today():
            return _json({'status': False, 'message': 'Voucher has expired.'})

        if not card.active:
            return _json({'status': False,
                          'message': 'Voucher is inactive (already used or deactivated).'})

        balance = get_card_balance(card)

        return _json({
            'status': True,
            'serialnumber': serialnumber,
            'balance': float(balance),
            'active': card.active,
            'cardname': card.cardname,
        })


@extend_schema(tags=['Checkout Manager'])
class CheckoutVoucherRedeemView(APIView):
    """
    POST /checkout/voucher-redeem/

    Body:
        {
            "serialnumber": "...",
            "amount": 5000.00,
            "redemption_type": "normal" | "full_deactivate"
        }

    redemption_type:
      - "normal"           — allows partial use; deactivates only when balance hits zero
      - "full_deactivate"  — redeems and immediately deactivates (single-use enforcement)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serialnumber = str(request.data.get('serialnumber', '')).strip()
        amount_raw = request.data.get('amount')
        redemption_type = request.data.get('redemption_type', REDEMPTION_TYPE_NORMAL)

        # --- validation ---
        if not serialnumber or amount_raw is None:
            return _json({'status': False,
                          'message': 'serialnumber and amount are required.'})

        if redemption_type not in (REDEMPTION_TYPE_NORMAL, REDEMPTION_TYPE_FULL):
            return _json({'status': False,
                          'message': f'redemption_type must be "{REDEMPTION_TYPE_NORMAL}" '
                                     f'or "{REDEMPTION_TYPE_FULL}".'})

        try:
            amount = Decimal(str(amount_raw))
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return _json({'status': False,
                          'message': 'amount must be a positive number.'})

        merch_id = getattr(request.user, 'merchID_id', None)
        if not merch_id:
            return _json({'status': False, 'message': 'Merchant not found for this user.'})

        card = giftCard.objects.filter(serialnumber=serialnumber).first()
        if not card:
            return _json({'status': False, 'message': 'Voucher not found.'})

        try:
            if redemption_type == REDEMPTION_TYPE_FULL:
                result = redeem_full_and_deactivate(
                    card=card,
                    amount=amount,
                    merch_id=merch_id,
                    redeemed_by_user=request.user,
                )
                message = 'Voucher redeemed and deactivated successfully.'
            else:
                result = redeem_normal(
                    card=card,
                    amount=amount,
                    merch_id=merch_id,
                    redeemed_by_user=request.user,
                )
                message = (
                    'Voucher redeemed. Card deactivated — balance exhausted.'
                    if result['deactivated']
                    else f'Voucher redeemed. Remaining balance: ₦{result["remaining_balance"]:,.2f}'
                )

        except GiftCardError as e:
            return _json({'status': False, 'message': str(e)})

        return _json({
            'status': True,
            'message': message,
            'redeemed_amount': result['redeemed_amount'],
            'remaining_balance': result['remaining_balance'],
            'deactivated': result['deactivated'],
            'active': result.get('active', card.active),
        })


def _json(data, status_code=200):
    return HttpResponse(json.dumps(data), content_type='application/json', status=status_code)