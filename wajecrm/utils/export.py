from openpyxl import Workbook
from django.http import HttpResponse
from rest_framework.views import APIView
from wajecrm.models import giftCard  # Adjust import if your model is elsewhere
from ..permissions import IsManager

class ExportGiftCardReportExcelView(APIView):
    permission_classes = [IsManager]  # Ensure only managers can access this view
    """Export gift card report to Excel format"""
    def get(self, request, format=None):
        userID = getattr(request.user,'id', None)
        startdate = request.GET.get('startDate')
        enddate = request.GET.get('endDate')

        queryset = giftCard.objects.filter(createdby=userID)
        if startdate and enddate:
            queryset = queryset.filter(expiration_date__range=[startdate, enddate])

        wb = Workbook()
        wb.create_sheet(title="Gift Card Report", index=0)
        ws = wb["Gift Card Report"]
        ws.append(['Serial Number', 'Card Name', 'Amount', 'Expiration Date'])

        for card in queryset:
            ws.append([
                card.serialnumber,
                card.cardname,
                card.amount,
                card.expiration_date.strftime('%Y-%m-%d') if card.expiration_date else ''
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=giftcard_report.xlsx'
        wb.save(response)
        return response