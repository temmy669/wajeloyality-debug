from django.shortcuts import render
from .models import *
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from django.http import Http404
from rest_framework.response import Response
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from .serializers import *
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
import logging
from .logger import *
import base64
import json
from django.db.models import Count, Sum, F
from rest_framework.permissions import IsAuthenticated
from django.views import View
from datetime import datetime, timedelta
# from .product import *
import calendar
from django.db import connection
from drf_spectacular.utils import extend_schema
from .permissions import IsManager, IsMerchant
from django.db.models import Q, F


@extend_schema(tags=["Analytics"])
class merchantDashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):

        merchID = request.GET.get('merchID')
        branchID = request.GET.get('branchID')

        if merchID and branchID:
            todaydate = datetime.datetime.now().date()
            yesterdaydate = todaydate - timedelta(days=1)
            tomorrow = todaydate + timedelta(days=1)
            weekstartdate = todaydate - timedelta(days=todaydate.weekday())
            weekenddate = weekstartdate + timedelta(days=6)
            lastweekdate = weekstartdate - timedelta(days=-6)
            truncate_month = connection.ops.date_trunc_sql(
                'month', 'created_at')
            chartresult = list(order.objects.filter(merchID=merchID).filter(branchID=branchID).extra({'month': truncate_month}).values(
                'month').annotate(Sum('ordertotal')))
            todayorder = order.objects.filter(merchID=merchID).filter(branchID=branchID).filter(created_at__gte=todaydate).filter(
                created_at__lte=tomorrow).aggregate(number_of_entry=Count('id'))
            yesterdayorder = order.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                created_at__gte=yesterdaydate).filter(created_at__lte=todaydate).aggregate(number_of_entry=Count('id'))
            todayrevenue = order.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                created_at__gte=todaydate).filter(created_at__lte=tomorrow).aggregate(Sum('ordertotal'))
            yesterdayrevenue = order.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                created_at__gte=yesterdaydate).filter(created_at__lte=todaydate).aggregate(Sum('ordertotal'))
            currentweekorder = order.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                created_at__gte=weekstartdate).filter(created_at__lte=weekenddate).aggregate(number_of_entry=Count('id'))
            # print(currentweekorder)
            lastweekorder = order.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                created_at__gte=lastweekdate).filter(created_at__gte=weekstartdate).aggregate(number_of_entry=Count('id'))
            currentweekrevenue = order.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                created_at__gte=weekstartdate).filter(created_at__lte=weekenddate).aggregate(Sum('ordertotal'))
            lastweekrevenue = order.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                created_at__gte=lastweekdate).filter(created_at__lte=weekstartdate).aggregate(Sum('ordertotal'))
            totalcustomer = user.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                role='customer').aggregate(number_of_entry=Count('id'))
            currentweektotalcustomer = user.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                created_at__gte=weekstartdate).filter(created_at__lte=weekenddate).filter(
                role='customer').aggregate(number_of_entry=Count('id'))
            lastweektotalcustomer = user.objects.filter(merchID=merchID).filter(branchID=branchID).filter(
                created_at__gte=lastweekdate).filter(created_at__lte=weekstartdate).aggregate(number_of_entry=Count('id'))
            branchdetails = list(branch.objects.filter(merchID=merchID).filter(
                id=branchID).values('id', 'branchname'))
            ongoingorders = list(order.objects.filter(merchID=merchID).filter(orderstatus='PENDING').values('id', 'ordercode', 'deliveryID', 'ordertotal', 'branchID',
                                                                                                            'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'pickupID',
                                                                                                            'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordertype', 'merchID', 'created_at'))
        else:
            todaydate = datetime.datetime.now().date()
            yesterdaydate = todaydate - timedelta(days=1)
            tomorrow = todaydate + timedelta(days=1)
            weekstartdate = todaydate - timedelta(days=todaydate.weekday())
            weekenddate = weekstartdate + timedelta(days=6)
            lastweekdate = weekstartdate - timedelta(days=-6)
            # chartresult = order.objects.filter(merchID=merchID).extra(
            # {'month': "Extract(created_at)"}).values_list('month').annotate(Sum('ordertotal'))
            truncate_month = connection.ops.date_trunc_sql(
                'month', 'created_at')
            chartresult = list(order.objects.filter(merchID=merchID).extra({'month': truncate_month}).values(
                'month').annotate(Sum('ordertotal')))
            todayorder = order.objects.filter(merchID=merchID).filter(created_at__gte=todaydate).filter(
                created_at__lte=tomorrow).aggregate(number_of_entry=Count('id'))
            yesterdayorder = order.objects.filter(merchID=merchID).filter(
                created_at__gte=yesterdaydate).filter(created_at__lte=todaydate).aggregate(number_of_entry=Count('id'))
            todayrevenue = order.objects.filter(merchID=merchID).filter(
                created_at__gte=todaydate).filter(created_at__lte=tomorrow).aggregate(Sum('ordertotal'))
            yesterdayrevenue = order.objects.filter(merchID=merchID).filter(
                created_at__gte=yesterdaydate).filter(created_at__lte=todaydate).aggregate(Sum('ordertotal'))
            currentweekorder = order.objects.filter(merchID=merchID).filter(
                created_at__gte=weekstartdate).filter(created_at__lte=weekenddate).aggregate(number_of_entry=Count('id'))
            lastweekorder = order.objects.filter(merchID=merchID).filter(
                created_at__gte=lastweekdate).filter(created_at__gte=weekstartdate).aggregate(number_of_entry=Count('id'))
            currentweekrevenue = order.objects.filter(merchID=merchID).filter(
                created_at__gte=weekstartdate).filter(created_at__lte=weekenddate).aggregate(Sum('ordertotal'))
            lastweekrevenue = order.objects.filter(merchID=merchID).filter(
                created_at__gte=lastweekdate).filter(created_at__lte=weekstartdate).aggregate(Sum('ordertotal'))
            totalcustomer = user.objects.filter(merchID=merchID).filter(
                role='customer').aggregate(number_of_entry=Count('id'))
            currentweektotalcustomer = user.objects.filter(merchID=merchID).filter(
                created_at__gte=weekstartdate).filter(created_at__lte=weekenddate).filter(
                role='customer').aggregate(number_of_entry=Count('id'))
            lastweektotalcustomer = user.objects.filter(merchID=merchID).filter(
                created_at__gte=lastweekdate).filter(created_at__lte=weekstartdate).aggregate(number_of_entry=Count('id'))
            branchdetails = list(branch.objects.filter(
                merchID=merchID).values('id', 'branchname'))
            ongoingorders = list(order.objects.filter(merchID=merchID).filter(orderstatus='PENDING').values('id', 'ordercode', 'deliveryID', 'ordertotal', 'branchID',
                                                                                                            'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'pickupID',
                                                                                                            'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordertype', 'merchID', 'created_at'))
        orderdetails = getOrders(ongoingorders)
        branchorders = getBranchOrders(branchdetails)
        formattedchartresult = getFormattedChart(chartresult)
        return JsonResponse({'totalcustomer': totalcustomer['number_of_entry'], 'currentweektotalcustomer': currentweektotalcustomer['number_of_entry'], 'lastweektotalcustomer': lastweektotalcustomer['number_of_entry'], 'todayorder': todayorder['number_of_entry'], 'yesterdayorder': yesterdayorder['number_of_entry'], 'todayrevenue': todayrevenue['ordertotal__sum'],
                             'yesterdayrevenue': yesterdayrevenue['ordertotal__sum'], 'currentweekorder': currentweekorder['number_of_entry'], 'lastweekorder': lastweekorder['number_of_entry'], 'currentweekrevenue': currentweekrevenue['ordertotal__sum'],
                             'lastweekrevenue': lastweekrevenue['ordertotal__sum'], 'OngoingOrders': orderdetails, 'Orderdistributionamoungbranches': branchorders, 'chart': formattedchartresult,
                             'status': True})


"""Class to display sales summary for a customer that has done transaction for the past 24 hours  """


@extend_schema(tags=["Analytics"])
class listSaleSummaryView(APIView):
    permission_classes = [IsManager, IsMerchant]

    def get(self, request, format=None):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `merchant id` query parameter in the URL.
        """
        #password = self.request.query_params.get('password')
        merchID = getattr(request.user, 'merchID_from_token', None)
        todaydate = datetime.now().date()
        yesterdaydate =  todaydate - timedelta(days=1)
        tomorrowdate = todaydate + timedelta(days=1)
        customersale = customerSaleToday(merchID, todaydate, yesterdaydate)
        morrischartrecord = morrisChart(merchID)
        total_sales = totalSales(merchID, todaydate, yesterdaydate)
        Todaycustomersalesummary = ['Todaycustomersalesummary']
        finalresult = Todaycustomersalesummary.append(customersale)
        #finalresult= customersale+total_sales
        return JsonResponse({'data': {'Todaycustomersalesummary': customersale}, 'Totalsalesummary': total_sales, "morris_chart_data": morrischartrecord, 'status': 'True'})


"""Class to display Loyalty summary for a customer that has done transaction for the past 24 hours  """


@extend_schema(tags=["Analytics"])
class listLoyaltySummaryView(APIView):
    permission_classes =[IsManager, IsMerchant]
    def get(self, request, format=None):
        userID = getattr(request.user, 'id', None)
        startdate = request.GET.get('startdate')
        endate = request.GET.get('endate')
        customerpoint = customerAwardedPoint(userID, startdate, endate)
        totalaward = totalAward(userID)
        return JsonResponse({'data': {'customerawardedpoints': customerpoint}, 'loyaltysummary': totalaward, 'status': 'True'})

@extend_schema(tags=["Analytics"])
class listGiftCardSummaryView(APIView):
    permission_classes = [IsManager, IsMerchant]

    def get(self, request, format=None):
        user = request.user
        startdate = request.GET.get('startDate')
        endate = request.GET.get('endDate')

        redeemptionhistory = redeemptionHistory(user, startdate, endate)
        giftcreated = giftcardCreatedRecord(user, startdate, endate)
        statdata = giftCardStat(user)

        return JsonResponse({'data': {'stat': statdata, 'giftcardreport': giftcreated, 'redeemptionhistory': redeemptionhistory}, 'status': 'True'})



def giftcardCreatedRecord(user, startdate=None, endate=None):
    giftcard_ids = giftCard.objects.filter(createdby=user).values_list('id', flat=True)

    filters = Q(giftID__in=giftcard_ids)
    if startdate and endate:
        filters &= Q(created_at__date__gte=startdate) & Q(cyreated_at__date__lte=endate)

    giftcardtransactionrecords = list(
        giftcardtransaction.objects
        .filter(filters)
        .values('giftID', 'created_at', 'purchaseamount', 'redeemedamount')
        .annotate(balance=F('purchaseamount') - F('redeemedamount'))
    )

    for gifttransaction in giftcardtransactionrecords:
        giftID = gifttransaction['giftID']
        giftcard = giftCard.objects.filter(id=giftID).values(
            'cardname', 'recipient_phone', 'serialnumber', 'recipient_email', 'createddate', 'createdby__name', 'expiration_date',
        ).first()

        if giftcard:
            giftcard['createddate'] = str(giftcard['createddate'])  # convert date to string
            gifttransaction.update(giftcard)

    return giftcardtransactionrecords

def redeemptionHistory(user, startdate, endate):
    giftcard_ids = giftCard.objects.filter(createdby=user).values_list('id', flat=True)
    queryset = giftcardtransaction.objects.filter(giftID__in=giftcard_ids, purchaseamount=0.00)

    if startdate and endate:
        queryset = queryset.filter(created_at__gte=startdate, created_at__lte=endate)

    redeemedgiftcardtansaction = list(queryset.values(
        'id', 'giftID', 'redeemedamount', 'merchID', 'reference', 'created_at'
    ).order_by('-created_at'))

    dictList = []
    for element in redeemedgiftcardtansaction:
        element['transactiondate'] = element.pop('created_at')
        giftcard = giftCard.objects.filter(id=element['giftID']).values('cardname', 'recipient_phone').first()
        if giftcard:
            element.update(giftcard)
        dictList.append(element)

    return dictList

def giftCardStat(user):
    todaydate = datetime.now().date()
    totalgiftcard = giftCard.objects.filter(createdby=user, expiration_date__gte=todaydate).count()

    giftcard_ids = giftCard.objects.filter(createdby=user).values_list('id', flat=True)
    totalredeemedgiftcard = giftcardtransaction.objects.filter(
        giftID__in=giftcard_ids, purchaseamount=0.00
    ).count()

    return {
        'totalgiftcardcreated': totalgiftcard,
        'totalgiftcardredeemed': totalredeemedgiftcard
    }


''' function to query for customer sales record for the last 24 hours'''


def customerSaleToday(merchID, todaydate, yesterdaydate):
    queryset = customer.objects.all()
    customersAmount = queryset.filter(merchID=merchID).values(
        'id', 'firstname', 'lastname', 'customerIdentifier')
    element = []
    temp = []
    dictList = []
    for counter, element in enumerate(customersAmount):
        length = len(customersAmount)
        if length > counter:
            totalamount = loyaltytransaction.objects.filter(CustID=element['id']).filter(
                transactiondate=todaydate).aggregate(Sum('transactionamount'))
            if totalamount['transactionamount__sum'] is not None:
                if totalamount['transactionamount__sum'] != 0.00:
                    totalamount['totalamount'] = totalamount.pop(
                        'transactionamount__sum')
                    element.update(totalamount)
                    dictList.append(element)
    return dictList


""" function to get the total sale report for transactions done within 24hours """


def totalSales(merchID, todaydate, yesterdaydate):
    temp = []
    dictList = []
    totalamount = loyaltytransaction.objects.filter(merchID=merchID).filter(
        transactiondate=todaydate).aggregate(Sum('transactionamount'))
    if totalamount['transactionamount__sum'] is None:
        totalamount = {'transactionamount__sum': 0.00}
    totalamount['totalsalesamount'] = totalamount.pop('transactionamount__sum')
    totalcustomerfortoday = customer.objects.filter(
        merchID=merchID).filter(createddate=todaydate).count()
    totalcustomerforyesterday = customer.objects.filter(
        merchID=merchID).filter(createddate=yesterdaydate).count()
    formattotalcustomerfortoday = {
        'totalcustomerfortoday': totalcustomerfortoday}
    formattotalcustomerforyesterday = {
        'totalcustomerforyesterday': totalcustomerforyesterday}
    totalamount.update(formattotalcustomerfortoday)
    totalamount.update(formattotalcustomerforyesterday)
    return totalamount


'''function to spool historical customers loyalty award points '''

def customerAwardedPoint(merchID, startdate, endate):
    queryset = customer.objects.all()
    element = []
    dictList = []
    if startdate and endate:
        loyaltytransactions = loyaltytransaction.objects.filter(merchID=merchID).filter(transactiondate__gte=startdate).filter(transactiondate__lte=endate).values(
            'CustID', 'redeemedpoint', 'assignedpoint', 'transactiondate').order_by('-transactiondate')
        for counter, element in enumerate(loyaltytransactions):
            length = len(loyaltytransactions)
            if length > counter:
                customersrecord = queryset.filter(id=element['CustID']).values(
                    'firstname', 'lastname', 'customerIdentifier').first()
                element.update(customersrecord)
                dictList.append(element)
        return dictList
    else:
        loyaltytransactions = loyaltytransaction.objects.filter(merchID=merchID).values(
            'CustID', 'redeemedpoint', 'assignedpoint', 'transactiondate').order_by('-transactiondate')
        for counter, element in enumerate(loyaltytransactions):
            length = len(loyaltytransactions)
            if length > counter:
                customersrecord = queryset.filter(id=element['CustID']).values(
                    'firstname', 'lastname', 'customerIdentifier').first()
                element.update(customersrecord)
                dictList.append(element)
        return dictList


''' function to get the sum total of the customers awards for a particular merchants'''


def totalAward(merchID):
    temp = []
    dictList = []
    formattotalpointawarded = []
    formattotalpointredemeemed = []
    totalpointawarded = loyaltytransaction.objects.filter(
        merchID=merchID).aggregate(Sum('assignedpoint'))
    totalredeemed = loyaltytransaction.objects.filter(
        merchID=merchID).aggregate(Sum('redeemedpoint'))
    totalpointawarded['totalpointsassigned'] = totalpointawarded.pop(
        'assignedpoint__sum')
    totalredeemed['totalpointredeemed'] = totalredeemed.pop(
        'redeemedpoint__sum')
    formattotalpointawarded = totalpointawarded
    formattotalpointredemeemed = totalredeemed
    temp = [totalpointawarded]
    dictList.append(formattotalpointawarded)
    dictList.append(formattotalpointredemeemed)
    return dictList


def morrisChart(merchID):
    salerecord = []
    element = []
    temp = []
    dictList = []
    todaydate = datetime.now().date()
    yesterdaydate = todaydate -timedelta(days=1)
    twodaysagodate = todaydate - timedelta(days=2)
    threedaysagodate = todaydate - timedelta(days=3)
    fourdaysagodate = todaydate - timedelta(days=4)
    fivedaysagodate = todaydate - timedelta(days=5)
    sixdaysagodate = todaydate - timedelta(days=6)
    recordlist = [todaydate, yesterdaydate, twodaysagodate,
                  threedaysagodate, fourdaysagodate, fivedaysagodate, sixdaysagodate]
    for counter, element in enumerate(recordlist):
        totalamount = loyaltytransaction.objects.filter(merchID=merchID).filter(
            transactiondate=element).aggregate(Sum('transactionamount'))
        if totalamount['transactionamount__sum'] is None:
            totalamount = {'transactionamount__sum': 0.00}
        totalamount['totalsalesamount'] = totalamount.pop(
            'transactionamount__sum')
        dictList.append(float(totalamount['totalsalesamount']))

    return dictList


def getBranchOrders(branchdetails):

    for branchdetail in branchdetails:
        earning = order.objects.filter(
            branchID=branchdetail['id']).aggregate(Sum('ordertotal'))
        totalorders = order.objects.filter(
            branchID=branchdetail['id']) .aggregate(number_of_entry=Count('id'))
        branchdetail.update(earning)
        branchdetail.update(totalorders)

    return branchdetails


def getFormattedChart(chartresult):
    names = []
    values = []
    expectednames = ['January', 'February', 'March', 'April', 'May', 'June',
                     'July', 'August', 'September', 'October', 'November', 'December']
    expectedvalues = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for chart in chartresult:
        names.append(chart['month'].strftime('%B'))
        values.append(float(chart['ordertotal__sum']))
    firstresultset = {"values": values, "names": names}
    secondresultset = {"values": expectedvalues, "names": expectednames}
    resultset = secondresultset, firstresultset
    print(resultset)
    return firstresultset
