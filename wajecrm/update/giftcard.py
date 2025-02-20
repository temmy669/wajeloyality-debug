from django.shortcuts import render
from .models import giftCard,giftcardtransaction
import random
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from django.http import Http404
from twilio.rest import Client
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
import base64
import json
from .notification import Notification
from rest_framework.permissions import IsAuthenticated
from django.views import View
from django.db.models import Sum
from django.utils import timezone
import datetime
from django.db.models import Sum
from decimal import *

class MerchantGiftCardView(APIView):   
    """ Function to create gift card of a merchants  """
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant."""       
        giftcardrecord=request.data['giftcards']
        merchID=request.data['merchID']
        try:
            for counter,element in enumerate(giftcardrecord):
                if counter >0:
                    serialnumber=generateSerialNumber(merchID)
                    gf=giftCard(serialnumber=serialnumber,cardname=element['name'],amount=float(element['amount']),merchID_id=merchID,expiration_date=element['voucher_date'])      
                    gf.save()
        except Exception as e:
               responseData ={'message':'An error occur'+str(e),'status':'False'}
               return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'message':'The giftcard record is created sucessfully','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
   
    """ Function to list gift card of various merchants  """
    def get(self, request, format=None):     
        """Save the post data when creating a new merchant.""" 
        merchID=request.GET.get('merchID')
        try:
            giftcardrecord=list(giftCard.objects.filter(merchID=merchID).values('serialnumber','id','cardname','amount','recipient_phone','expiration_date','merchID'))
            dictList=[]
            for counter,element in enumerate(giftcardrecord):
                length=len(giftcardrecord)
                if length > counter:                                                                                                                                                                                                        
                    purchasevalue=element['amount']
                    redeemedvalue=giftcardtransaction.objects.filter(merchID=element['merchID']).filter(giftID=element['id']).aggregate(Sum('redeemedamount'))
                    redeemedvalue=redeemedvalue['redeemedamount__sum']
                    if(redeemedvalue is None):
                       redeemedvalue= Decimal('0.0')                
                    currentvalue=float(purchasevalue-redeemedvalue)
                    currentvalue={'currentvalue':currentvalue}
                    element['amount']=float(element['amount'])
                    element['expiration_date']=str(element['expiration_date'])
                    element.update(currentvalue)
                    dictList.append(element)               
        except Exception as e:
               responseData ={'message':'An error occur'+str(e),'status':'False'}
               return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'data':dictList,'status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

class purchaseMerchantGiftCardView(APIView):
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant.""" 
        try:           
            account_sid = "ACd64533b5d4bdff90d408bee126fe6680"
            auth_token = "a0f88a25b9151a08030cd3389dcdcf67"
            client = Client(account_sid, auth_token)
            from_whatsapp_number='whatsapp:+14155238886'
            # replace this number with your own WhatsApp Messaging number
            to_whatsapp_number='whatsapp:+2348131361241'
            client.messages.create(body='Ahoy, world!',
                                from_=from_whatsapp_number,
                                to=to_whatsapp_number)
            giftcardrecord=giftCard.objects.filter(serialnumber=request.data['serialnumber']).filter(merchID=request.data['merchID']).values('recipient_phone','id').first()
            if giftcardrecord['recipient_phone'] is None:
               giftcard = giftCard.objects.get(serialnumber=request.data['serialnumber'])
               giftcard.recipient_phone = request.data['phonenumber']
               gt=giftcardtransaction(giftID_id=giftcardrecord['id'],purchaseamount=request.data['amount'],merchID_id=request.data['merchID'])
               gt.save()
               giftcard.save(update_fields=['recipient_phone'])
               notify = Notification()
               firstname='customer'
               randomnumber=request.data['serialnumber']
               emailaddress=request.data['emailaddress']
               subject='Voucher Details'
               template_name='voucher_details.html'
               others=request.data['amount']
               notify.emailNotification(firstname,randomnumber,emailaddress,subject,template_name,others)
            else:
                 responseData ={'message':'The voucher has been bought by another customer','status':'False'}
                 return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
               responseData ={'message':'An error occur'+str(e),'status':'False'}
               return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'message':'The transaction capture','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

class redeemMerchantGiftCardView(APIView):
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant.""" 
        try: 
            try:
                record=giftCard.objects.filter(serialnumber=request.data['serialnumber']).filter(merchID=request.data['merchID']).values('serialnumber','id').first()
            except TypeError:
                record = None                 
            if not(record is None):
               try:
                  verifyphone=giftCard.objects.filter(recipient_phone=request.data['phonenumber']).filter(merchID=request.data['merchID']).values('recipient_phone').first()
               except TypeError:
                    verifyphone = None 
               if not(verifyphone is None):
                    gt=giftcardtransaction(giftID_id=record['id'],redeemedamount=request.data['amount'],merchID_id=request.data['merchID'])
                    gt.save()
               else:
                 responseData ={'message':'The phone number is not assigned to the voucher','status':'False'}
                 return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                 responseData ={'message':'The voucher serial number does not exist','status':'False'}
                 return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
               responseData ={'message':'An error occur'+str(e),'status':'False'}
               return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'message':'The transaction capture','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

def generateSerialNumber(merchID):
    x=random.randint(1,1000000000001)
    serialnum= giftCard.objects.filter(serialnumber=x).filter(merchID=merchID).values('serialnumber').first()
    while(serialnum != None):
        x=random.randint(1,1000000000001)
        serialnum= giftCard.objects.filter(serialnumber=x).filter(merchID=merchID).values('serialnumber').first()
    return x 


        
