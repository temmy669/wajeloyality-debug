from django_filters import (
    FilterSet, AllValuesFilter, DateTimeFilter, NumberFilter, DateFilter)
from .models import AccountantData, giftCard

class GiftCardFilter(FilterSet):
    amount = NumberFilter(field_name='amount', lookup_expr='gt')
    card_name = AllValuesFilter(field_name='cardName')
    confirmation_code = AllValuesFilter(field_name='confirmationCode')
    transaction_reference = AllValuesFilter(field_name='transactionRef')
    customer = AllValuesFilter(field_name='customer')
    
    class Meta:
        model = AccountantData
        fields = "__all__"
    
class GiftCardStatFilter(FilterSet):
    start_date = DateTimeFilter(field_name='createddate', lookup_expr='gt')
    end_date = DateTimeFilter(field_name='createddate', lookup_expr='lt')
    merchant = AllValuesFilter(field_name='merchID__businessname')
 
    class Meta:
        model = giftCard
        fields = "__all__"
