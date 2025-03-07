from django_filters import (
    FilterSet, AllValuesFilter, DateTimeFilter, NumberFilter, DateFilter)
from .models import AccountantData

class GiftCardFilter(FilterSet):
    from_payment_date = DateFilter(field_name='datePayment', lookup_expr='gt')
    to_payment_date = DateFilter(field_name='datePayment', lookup_expr='lt')
    from_confirmation_date = DateFilter(field_name='datePayment', lookup_expr='gt')
    to_confirmation_date = DateFilter(field_name='datePayment', lookup_expr='lt')
    from_amount = NumberFilter(field_name='amount', lookup_expr='gt')
    to_amount = NumberFilter(field_name='amount', lookup_expr='lt')
    confirmation_code = AllValuesFilter(field_name='confirmationCode')
    transaction_reference = AllValuesFilter(field_name='transactionRef')
    customer = AllValuesFilter(field_name='customer')
    """
    amount = models.DecimalField(max_digits=16, decimal_places=2)  
    cardName = models.CharField(max_length=200) 
    confirmationCode = models.CharField(max_length=20, unique=True)  
    transactionRef = models.CharField(max_length=255, unique=True)  
    dateConfirmed = models.DateField(default=timezone.now,null=False)
    customer = models.CharField(max_length=200, null=False)
    datePayment = models.DateField(default=timezone.now,null=False)
    """
    class Meta:
        model = AccountantData
        fields = "__all__"