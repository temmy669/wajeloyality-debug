from django.shortcuts import render
from .models import *
import random
import ast
from django.http import HttpResponse
from django.http import JsonResponse
from django.template.loader import render_to_string
from rest_framework.views import APIView
from json import loads, dumps
from rest_framework import status
from django.http import Http404
from rest_framework.response import Response
from django.core.mail import send_mail
from .serializers import *
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from .logger import *
import requests
import base64
from .customer import *
import json
import xmltodict
from rest_framework.permissions import IsAuthenticated
from django.views import View
import datetime
from dateutil.parser import parse
from drf_spectacular.utils import extend_schema

@extend_schema(tags=["Reward Program"])
class merchantLoyaltyRuleView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            serializer = merchantLoyaltyRuleSerializer(data=request.data)
            rulename = request.data['loyaltyrule']
            merchID = request.data['merchID']
            checkloyaltyrulenamedup = duplicateLoyaltyRuleName(
                rulename, merchID)
            if checkloyaltyrulenamedup is True:
                if serializer.is_valid():
                    serializer.save()
                    responseData = {
                        'message': 'The loyalty rule record is created sucessfully',
                        'status': 'True'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                responseData = {
                    'message': 'The loyalty record cannot be created because of duplicate rulename',
                    'status': 'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': 'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        #password = self.request.query_params.get('password')
        merchID = request.GET.get('merchID')
        queryset = loyaltyrule.objects.all()
        todaydate = datetime.datetime.now().date()
        resultset = queryset.filter(merchID=merchID).filter(endate__gte=todaydate).values(
            'id', 'loyaltyrule', 'rewardpoint', 'amountspent', 'status', 'endate')
        return JsonResponse({'data': list(resultset), 'status': 'True'})


@extend_schema(tags=["Reward Program"])
class merchantCrossPromotionRuleView(APIView):
    #permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        try:
            serializer = merchantCrossCampaignRuleSerializer(data=request.data)
            campaignrulename = request.data['campaignrulename']
            merchID = request.data['merchID']
            checkcampaignrulenamedup = CheckDuplicateCampaignRuleName(
                campaignrulename, merchID)
            if checkcampaignrulenamedup is True:
                if serializer.is_valid():
                    img_data = base64.b64decode(request.data['item'])
                    imgext = request.data['campaignrulename']
                    processedimage = receiveImage(img_data, imgext)
                    serializer.save(item=processedimage)
                    responseData = {
                        'message': 'The campaignpromotion rule record is created sucessfully',
                        'status': 'True'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                responseData = {
                    'message': 'The loyalty record cannot be created because of duplicate rulename',
                    'status': 'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': 'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        #password = self.request.query_params.get('password')
        merchID = request.GET.get('merchID')
        queryset = crosscampaignrule.objects.all()
        todaydate = datetime.datetime.now().date()
        resultset = queryset.filter(merchID=merchID).filter(endate__gte=todaydate).values(
            'id', 'campaignrulename', 'item', 'amountspent', 'status', 'endate')
        return JsonResponse({'data': list(resultset), 'status': 'True'})

@extend_schema(tags=["Reward Program"])
class merchantLoyaltyTransactionView(APIView):
    #permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        try:
            loyaltyruleID = int(request.data['loyaltyruleID'])
            transactionamount = request.data['transactionamount']
            assignpoint = postAssignedPoint(loyaltyruleID, transactionamount)
            custID = request.data['CustID']
            merchID = request.data['merchID']
            receiptno = request.data['receiptno']
            dupreciptcheck = checkForDupReceipt(receiptno, merchID)
            if dupreciptcheck is False:
                loyaltytransactionrecord = loyaltytransaction(loyaltyruleID_id=loyaltyruleID, CustID_id=custID, merchID_id=merchID,
                                                              transactionamount=transactionamount, assignedpoint=assignpoint, transactiondate=request.data['transactiondate'], receiptno=receiptno)
                loyaltytransactionrecord.save()
                responseData = {
                    'message': 'The loyalty transaction record is created sucessfully',
                    'status': 'True'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData = {
                    'message': 'Duplicate Reciept',
                    'status': 'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': 'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        #password = self.request.query_params.get('password')
        merchID = request.GET.get('merchID')
        startDate = request.GET.get('startDate')
        endDate = request.GET.get('endDate')
        formattedstartdate = dateFormat(startDate)
        formattedendate = dateFormat(endDate)
        queryset = loyaltytransaction.objects.filter(merchID=merchID).filter(transactiondate__gte=formattedstartdate).filter(
            transactiondate__lte=formattedendate).values('CustID', 'merchID', 'receiptno', 'transactionamount', 'assignedpoint', 'transactiondate')
        finalrecord = customerInfoMarch(queryset)
        #resultset = queryset.filter(merchID=merchID).filter(endate__gte=todaydate).values('id','loyaltyrule','status','endate')
        return JsonResponse({'data': list(finalrecord), 'status': 'True'})
        
def duplicateLoyaltyRuleName(rulename, merchID):
    rulenamerecord = loyaltyrule.objects.filter(
        loyaltyrule=rulename).filter(merchID=merchID)
    if not rulenamerecord:
       return True
    else:
        return False


def CheckDuplicateCampaignRuleName(campaignrulename, merchID):
    campaignnamerecord = crosscampaignrule.objects.filter(
        campaignrulename=campaignrulename).filter(merchID=merchID)
    if not campaignnamerecord:
       return True
    else:
        return False


def postAssignedPoint(loyaltyruleID, transactionamount):
    loyaltyruleresult = loyaltyrule.objects.filter(id=loyaltyruleID).values('id', 'rewardpoint', 'amountspent')
    list_loyaltyruleresult = [entry for entry in loyaltyruleresult]
    amountspent = float(list_loyaltyruleresult[0]['amountspent'])
    loyaltypoint = int(list_loyaltyruleresult[0]['rewardpoint'])
    pointrewarded = (float(transactionamount) * loyaltypoint)/amountspent
    return pointrewarded


def checkForDupReceipt(receiptno, merchID):
    """ Test for duplicate record """
    receiptrecord = loyaltytransaction.objects.filter(receiptno=receiptno).filter(merchID=merchID)
    if not receiptrecord:
       return False
    else:
        return True


def expiredLoyaltyRule(resultset):
    # converts ValuesQuerySet into Python list
    list_result = [entry for entry in resultset]
    expirydate = list_result[0]['endate']
    todaydate = datetime.datetime.now().date()
    if todaydate > expirydate:
        return True
    else:
        return False


def receiveImage(img_data, imgext):
    save_path = os.path.join(
        settings.BASE_DIR, 'crosspromotion', imgext+'.png')
    databasepath = '/crosspromotion/'+imgext+'.png'
    with open(save_path, "wb") as fh:
          fh.write(img_data)
    return databasepath

def dateFormat(unformatteddate):
    formatteddate = datetime.datetime.strptime(
        unformatteddate, "%d/%m/%Y").strftime("%Y-%m-%d")
    return formatteddate

def crossCampaign(request):
    merchID = request.GET.get('merchID')
    todaydate = datetime.datetime.now().date()
    record = list(crosscampaignrule.objects.filter(merchID=merchID).filter(
        endate__gte=todaydate).values('id', 'campaignrulename', 'item', 'amountspent', 'status'))
    for counter, element in enumerate(record):
        length = len(record)
        if length > counter:
           amount = element['amountspent']
           logo = element['item']
    return HttpResponse(None)

