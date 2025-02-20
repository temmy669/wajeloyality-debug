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
from rest_framework.permissions import IsAuthenticated
from django.views import View
import datetime
from django.db.models import Sum

"""Class to display sales summary for a customer that has done transaction for the past 24 hours  """
class listSaleSummaryView(APIView):
    permission_classes =(IsAuthenticated,) 
    def get(self,request, format=None):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `merchant id` query parameter in the URL.
        """
        #password = self.request.query_params.get('password')
        merchID=request.GET.get('merchID')
        todaydate = datetime.date.today()
        yesterdaydate = todaydate - datetime.timedelta(days = 1)
        tomorrowdate = todaydate + datetime.timedelta(days = 1)
        customersale = customerSaleToday(merchID,todaydate,yesterdaydate)
        morrischartrecord = morrisChart(merchID)
        total_sales= totalSales(merchID,todaydate,yesterdaydate)
        Todaycustomersalesummary= ['Todaycustomersalesummary']
        finalresult = Todaycustomersalesummary.append(customersale)
        #finalresult= customersale+total_sales
        return JsonResponse({'data':{'Todaycustomersalesummary':customersale},'Totalsalesummary':total_sales,"morris_chart_data":morrischartrecord,'status':'True'})

"""Class to display Loyalty summary for a customer that has done transaction for the past 24 hours  """
class listLoyaltySummaryView(APIView):
    permission_classes =(IsAuthenticated,) 
    def get(self,request, format=None):
        merchID=request.GET.get('merchID')
        customerpoint = customerAwardedPoint(merchID)
        totalaward =totalAward(merchID)
        return JsonResponse({'data':{'customerawardedpoints':customerpoint},'loyaltysummary':totalaward,'status':'True'})

''' function to query for customer sales record for the last 24 hours'''
def customerSaleToday(merchID,todaydate,yesterdaydate):
    queryset = customer.objects.all()
    customersAmount = queryset.filter(merchID=merchID).values('id','firstname','lastname','customerIdentifier')
    element =[]
    temp = []
    dictList = []
    for counter,element in enumerate(customersAmount):
        length = len(customersAmount)
        if length > counter:
           totalamount=loyaltytransaction.objects.filter(CustID=element['id']).filter(transactiondate=todaydate).aggregate(Sum('transactionamount'))
           if totalamount['transactionamount__sum'] is None:
              totalamount = {'transactionamount__sum':0.00}
           else:
               totalamount['totalamount'] = totalamount.pop('transactionamount__sum') 
               element.update(totalamount)
               dictList.append(element)
    return dictList

""" function to get the total sale report for transactions done within 24hours """
def totalSales(merchID,todaydate,yesterdaydate):
    temp=[]
    dictList = []
    totalamount=loyaltytransaction.objects.filter(merchID=merchID).filter(transactiondate=todaydate).aggregate(Sum('transactionamount'))
    if totalamount['transactionamount__sum'] is None:
           totalamount = {'transactionamount__sum':0.00}
    totalamount['totalsalesamount'] = totalamount.pop('transactionamount__sum')
    totalcustomerfortoday= customer.objects.filter(merchID=merchID).filter(createddate=todaydate).count()
    totalcustomerforyesterday= customer.objects.filter(merchID=merchID).filter(createddate=yesterdaydate).count()
    formattotalcustomerfortoday={'totalcustomerfortoday':totalcustomerfortoday}
    formattotalcustomerforyesterday={'totalcustomerforyesterday':totalcustomerforyesterday}
    totalamount.update(formattotalcustomerfortoday)
    totalamount.update(formattotalcustomerforyesterday)
    return totalamount

'''function to spool historical customers loyalty award points '''
def customerAwardedPoint(merchID):
    queryset = customer.objects.all()
    totalaward=loyaltytransaction.objects.filter(merchID=merchID).values('CustID','assignedpoint','assignedpoint','transactiondate')
    element =[]
    temp = []
    dictList = []
    for counter,element in enumerate(totalaward):
        length = len(totalaward)
        if length > counter:
           customersAmount = queryset.filter(id=element['CustID']).values('firstname','lastname','customerIdentifier').first()
           element.update(customersAmount)
           dictList.append(element)
    return dictList

''' function to get the sum total of the customers awards for a particular merchants'''
def totalAward(merchID):
    temp=[]
    dictList = []
    formattotalpointawarded=[]
    totalpointawarded=loyaltytransaction.objects.filter(merchID=merchID).aggregate(Sum('assignedpoint'))
    totalpointawarded['totalpointsassigned'] = totalpointawarded.pop('assignedpoint__sum') 
    formattotalpointawarded=totalpointawarded
    temp = [totalpointawarded]
    dictList.append(formattotalpointawarded)
    return formattotalpointawarded

def morrisChart(merchID):
    salerecord =[]
    element =[]
    temp = []
    dictList = []
    todaydate = datetime.date.today()
    yesterdaydate=todaydate - datetime.timedelta(days = 1)
    twodaysagodate=todaydate -datetime.timedelta(days = 2)
    threedaysagodate=todaydate -datetime.timedelta(days = 3)
    fourdaysagodate=todaydate -datetime.timedelta(days = 4)
    fivedaysagodate=todaydate -datetime.timedelta(days = 5)
    sixdaysagodate=todaydate -datetime.timedelta(days = 6)
    recordlist = [todaydate,yesterdaydate,twodaysagodate,threedaysagodate,fourdaysagodate,fivedaysagodate,sixdaysagodate]
    for counter,element in enumerate(recordlist):
        totalamount=loyaltytransaction.objects.filter(merchID=merchID).filter(transactiondate=element).aggregate(Sum('transactionamount'))
        if totalamount['transactionamount__sum'] is None:
           totalamount = {'transactionamount__sum':0.00}
        totalamount['totalsalesamount'] = totalamount.pop('transactionamount__sum')
        dictList.append(float(totalamount['totalsalesamount']))

    return dictList

  