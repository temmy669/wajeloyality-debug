"""
Checkout Manager Voucher Validation
------------------------------------
Stopgap solution for branches where LS Retail has been deployed.
Allows checkout managers to:
  1. Check a voucher's available balance (GET)
  2. Redeem and immediately deactivate a voucher in one step (POST)

Single-use enforcement: once a voucher is redeemed, it is permanently
deactivated and cannot be used again.
"""

import json
import datetime
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from drf_spectacular.utils import extend_schema

from .models import giftCard, giftcardtransaction, merchant, user


# ---------------------------------------------------------------------------
# 1.  Balance Check  (GET)
# ---------------------------------------------------------------------------

@extend_schema(tags=['Checkout Manager'])
class CheckoutVoucherBalanceView(APIView):
    """
    GET /checkout/voucher-balance/?serialnumber=XXX&serviceid=YYY

    Returns the current balance of a voucher for a given merchant.
    Does NOT modify any data — safe to call multiple times.

    Query params:
        serialnumber  – the voucher number printed on the card
        serviceid     – the merchant's service ID

    Response (success):
        { "status": true, "serialnumber": "...", "balance": 5000.00, "active": true }

    Response (failure):
        { "status": false, "message": "..." }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        serialnumber = request.GET.get('serialnumber', '').strip()
        userID = request.user

        if not serialnumber:
            return _json({'status': False,
                          'message': 'voucher number is required.'})
        
       

        # Fetch the voucher
        card = giftCard.objects.filter(
            serialnumber=serialnumber,
        ).values('id', 'amount', 'active', 'expiration_date', 'cardname').first()

        if not card:
            return _json({'status': False, 'message': 'Voucher not found.'})

        # Check expiry
        if card['expiration_date'] and card['expiration_date'] < datetime.date.today():
            return _json({'status': False, 'message': 'Voucher has expired.'})

        # Check active flag
        if not card['active']:
            return _json({'status': False,
                          'message': 'Voucher is inactive (already used or deactivated).'})

        # Calculate remaining balance
        redeemed = giftcardtransaction.objects.filter(
            giftID=card['id'],
        ).aggregate(total=Sum('redeemedamount'))['total'] or 0

        balance = float(card['amount']) - float(redeemed)

        return _json({
            'status':       True,
            'serialnumber': serialnumber,
            'balance':      round(balance, 2),
            'active':       card['active'],
            'cardname':     card['cardname'],
            'expiration_date': card['expiration_date'],
        })


# ---------------------------------------------------------------------------
# 2.  Redeem & Deactivate  (POST)
# ---------------------------------------------------------------------------

@extend_schema(tags=['Checkout Manager'])
class CheckoutVoucherRedeemView(APIView):
    """
    POST /checkout/voucher-redeem/

    Validates, redeems, and permanently deactivates a voucher in one step.
    Enforces single-use: if the voucher has ANY prior redemption transaction,
    or is already inactive, the request is rejected.

    Request body (JSON):
        {
            "serialnumber": "123456789",
            "serviceid":    "351817683",
            "amount":       5000.00       ← amount being redeemed at the till
        }

    Response (success):
        { "status": true, "message": "Voucher redeemed and deactivated successfully.",
          "redeemed_amount": 5000.00, "remaining_balance": 0.00 }

    Response (failure):
        { "status": false, "message": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serialnumber = str(request.data.get('serialnumber', '')).strip()
        amount_raw   = request.data.get('amount')

        # --- basic validation ---
        if not serialnumber or amount_raw is None:
            return _json({'status': False,
                          'message': 'serialnumber, and amount are required.'})

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return _json({'status': False, 'message': 'amount must be a positive number.'})

        # --- resolve merchant from user's branch ---
        user = request.user

        merch_id = request.user.merchID_id

        if not merch_id:
            return _json({'status': False, 'message': 'Merchant not found for user.'})

        print(merch_id)
                
                

        # --- fetch voucher ---
        card = giftCard.objects.filter(
            serialnumber=serialnumber,
            # merchID=merch_id
        ).first()

        if not card:
            return _json({'status': False, 'message': 'Voucher not found.'})

        # --- expiry check ---
        if card.expiration_date and card.expiration_date < datetime.date.today():
            return _json({'status': False, 'message': 'Voucher has expired.'})

        # --- single-use enforcement: reject if already inactive ---
        if not card.active:
            return _json({'status': False,
                          'message': 'Voucher has already been used or deactivated.'})

        # --- single-use enforcement: reject if any prior redemption exists ---
        prior_redemptions = giftcardtransaction.objects.filter(
            giftID=card,
            redeemedamount__gt=0          # only rows that are actual redemptions
        ).exists()

        if prior_redemptions:
            # Deactivate defensively in case active flag drifted out of sync
            card.active = False
            card.save(update_fields=['active'])
            return _json({'status': False,
                          'message': 'Voucher has already been redeemed and cannot be reused.'})

        # --- check sufficient balance ---
        voucher_value = float(card.amount)
        if amount > voucher_value:
            return _json({'status': False,
                          'message': f'Redemption amount (₦{amount:,.2f}) exceeds '
                                     f'voucher value (₦{voucher_value:,.2f}).'})

        # --- record the redemption transaction ---
        # Use the authenticated checkout manager's username as audit trail
        redeemed_by = getattr(user, 'username', 'checkout_manager')
        print(f"Redeeming voucher {serialnumber} for merchant {merch_id} by user {redeemed_by} for amount {amount}")

        giftcardtransaction.objects.create(
            giftID=card,
            redeemedamount=amount,
            merchID_id=merch_id,
            createdby=redeemed_by,       # stored for audit
        )

        # --- DEACTIVATE immediately (single-use) ---
        card.active = False
        card.save(update_fields=['active'])

        remaining = round(voucher_value - amount, 2)

        return _json({
            'status':            True,
            'message':           'Voucher redeemed and deactivated successfully.',
            'redeemed_amount':   round(amount, 2),
            'remaining_balance': remaining,   # will be 0 for full redemptions
        })


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _json(data, status_code=200):
    return HttpResponse(json.dumps(data), content_type="application/json", status=status_code)