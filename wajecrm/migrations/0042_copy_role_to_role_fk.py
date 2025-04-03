from django.db import migrations

def forwards_func(apps, schema_editor):
    User = apps.get_model('wajecrm', 'user')
    Role = apps.get_model('wajecrm', 'Role')

    for user in User.objects.all():
        if user.role:  # Ensure role is not None
            try:
                # Case-insensitive lookup for robustness
                role_instance = Role.objects.get(name__iexact=user.role)
                user.role_fk = role_instance
                user.save()
            except Role.DoesNotExist:
                # Handle cases where role name doesn't match any Role entry
                pass

class Migration(migrations.Migration):
    dependencies = [
        ('wajecrm', '0041_user_role_fk'),  # Previous migration
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
