import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wajeloyality.settings')
django.setup()

from wajecrm.models import listvouchertransactions, giftCard, giftcardtransaction, merchant

from django.db.models import Sum

# The two specific recno values from MetroPOS for the missing transactions

MISSING_RECNOS = [243650, 243651]  # <-- replace with actual recno values

merch_id = merchant.objects.filter(serviceID='351817683').values('id').first()['id']

for recno in MISSING_RECNOS:

    receiptno = f'giftcardredeemed-{recno}'

    # 1. Check it's not already in giftcardtransaction

    already_exists = giftcardtransaction.objects.filter(

        reference=receiptno, merchID=merch_id

    ).exists()

    if already_exists:

        print(f"[SKIP] {receiptno} already recorded")

        continue

    # 2. Pull the transaction from MetroPOS

    txn = listvouchertransactions.objects.filter(recno=recno).values(

        'ID', 'Debit', 'DateUsed'

    ).first()

    if not txn:

        print(f"[NOT FOUND] recno {recno} not in MetroPOS")

        continue

    # 3. Look up the gift card in your DB

    giftid = giftCard.objects.filter(serialnumber=txn['ID']).values('id', 'amount').first()

    if not giftid:

        print(f"[NO GIFT CARD] serial {txn['ID']} not found")

        continue

    # 4. Dry run — print what would be inserted

    print(f"[DRY RUN] Would insert: giftID={giftid['id']}, "

          f"redeemedamount={txn['Debit']}, reference={receiptno}")

    # 5. Uncomment when you're satisfied:

    gt = giftcardtransaction(

        giftID_id=giftid['id'],

        redeemedamount=txn['Debit'],

        merchID_id=merch_id,

        reference=receiptno

    )

    gt.save()

    print(f"[SAVED] {receiptno}")