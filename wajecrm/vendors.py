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
from .loyalty import *
import requests
import base64
import json
import xmltodict
from rest_framework.permissions import IsAuthenticated
from django.views import View
import datetime
from dateutil.parser import parse

def vendorCustomerTransaction(format=None):
    try:
        merchantrecord=list(merchant.objects.values('serviceID','businessname','id'))
        """ Loop through the merchant records to fetch merchant details"""
        for counter,element in enumerate(merchantrecord):
            length = len(merchantrecord)
            if length > counter:
                merchID=element['id']
                """ Loop through vendor customer records"""
                if (element['serviceID']=="2777545579"):
                    customerrecord=list(tblCustomer.objects.values('CustomerAccNo','Forename','Surname','EMail','Title'))
                    customertransactionrecord=list(tblTicket.objects.filter(TicketDate__gte="2019-01-01").values('TicketID','TicketDate','CustomerAccNo','TicketTotal'))
                    loyaltyruleID = loyaltyrule.objects.filter(merchID=merchID).values('id').first()
                    loyaltyruleID=loyaltyruleID['id']
                    for counter, details in enumerate(customerrecord):
                        phone_number=details['CustomerAccNo']
                        validity=validNumber(phone_number)
                        if validity is True:
                           duplicaterecord =checkCustomerRecord(merchID,phone_number)
                           if duplicaterecord is False:
                              customerrecord =customer(firstname=details['Forename'],title=details['Title'],lastname=details['Surname'],emailaddress=details['EMail'],customerIdentifier=details['CustomerAccNo'],merchID_id=merchID)                             
                              customerrecord.save()
                    for counter,transactions in enumerate(customertransactionrecord):
                         ticketid=transactions['TicketID']
                         receiptno='MIDAS'+'-'+str(transactions['TicketDate'])
                         checkduptransaction=checkForDupReceipt(receiptno,merchID)
                         if checkduptransaction is True:
                            transactionamount=transactions['TicketTotal']
                            loyaltypoint=postAssignedPoint(loyaltyruleID,transactionamount)
                            description='migration@'+str(receiptno)
                            customerid=customer.objects.filter(customerIdentifier=transactions['CustomerAccNo']).values('id').first()
                            print(customerid)
                            if customerid is not None:
                                loyaltytransactionrecord =loyaltytransaction(loyaltyruleID_id=loyaltyruleID,assignedpoint=loyaltypoint,transactionamount=transactions['TicketTotal'],CustID_id=customerid['id'],merchID_id=merchID,transactiondate=transactions['TicketDate'],receiptno=receiptno,description=description)
                                loyaltytransactionrecord.save()               
    except Exception as e:
        print(str(e))
    return HttpResponse(None)

def validNumber(phone_number):
    if len(phone_number) != 11:
        return False
    for i in range(11):
        if not phone_number[i].isalnum():
           return False
    return True

def checkCustomerRecord(merchID,phone_number):
    custID= customer.objects.filter(merchID=merchID).filter(customerIdentifier=phone_number).values('id').first()
    if custID:
        return True
    else:
        return False