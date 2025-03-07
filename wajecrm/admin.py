from django.contrib import admin
from .models import merchant, branch, giftCard, AccountantData, user, Role
# Register your models here.
admin.site.register(merchant)
admin.site.register(branch)
admin.site.register(giftCard)
admin.site.register(user)
admin.site.register(AccountantData)
admin.site.register(Role)