import django
import os
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wajeloyality.settings')
django.setup()

from wajecrm.models import listvouchertransactions, giftCard, giftcardtransaction, merchant

def run(json_file='recnos.json'):
    # Load recnos from json file
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            recnos = data['recnos']
    except FileNotFoundError:
        print(f"[ERROR] {json_file} not found")
        return
    except KeyError:
        print("[ERROR] JSON file must have a 'recnos' key")
        return

    if not recnos:
        print("[ERROR] No recnos provided in JSON file")
        return

    print(f"[INFO] Processing {len(recnos)} transaction(s): {recnos}")

    merch_id = merchant.objects.filter(serviceID='351817683').values('id').first()
    if not merch_id:
        print("[ERROR] Merchant not found")
        return
    merch_id = merch_id['id']

    for recno in recnos:
        print(f"\n--- Processing recno: {recno} ---")
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

        # 5. Uncomment when satisfied:
        gt = giftcardtransaction(
            giftID_id=giftid['id'],
            redeemedamount=txn['Debit'],
            merchID_id=merch_id,
            reference=receiptno
        )
        gt.save()
        print(f"[SAVED] {receiptno}")

if __name__ == '__main__':
    run()