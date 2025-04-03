from django.db import migrations
from django.db.models import F, Q

def forwards_func(apps, schema_editor):
    GiftCard = apps.get_model('wajecrm', 'giftCard')
    User = apps.get_model('wajecrm', 'user')
    Merchant = apps.get_model('wajecrm', 'merchant')
    
    # Build a merchant-to-user mapping dictionary
    merchant_user_map = {}
    for user in User.objects.all():
        if user.merchID_id not in merchant_user_map:
            merchant_user_map[user.merchID_id] = user.id
    
    # Process in batches
    batch_size = 1000
    total_count = GiftCard.objects.count()
    processed = 0
    
    # Process only gift cards with numeric createdby values
    while processed < total_count:
        # Get a batch of records
        batch = GiftCard.objects.all()[processed:processed+batch_size]
        
        # Process each record in the batch
        updates = []
        for gc in batch:
            if gc.createdby and str(gc.createdby).strip().isdigit():
                merchant_id = int(gc.createdby)
                user_id = merchant_user_map.get(merchant_id)
                if user_id:
                    gc.createdby_fk_id = user_id
                    updates.append(gc)
        
        # Bulk update if we have records to update
        if updates:
            # Use bulk_update for efficiency
            GiftCard.objects.bulk_update(updates, ['createdby_fk_id'])
        
        processed += batch_size
        print(f"Processed {min(processed, total_count)}/{total_count} gift cards")

class Migration(migrations.Migration):
    dependencies = [
        ('wajecrm', '0043_giftcard_createdby_fk'),  # Update with the correct previous migration name
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]