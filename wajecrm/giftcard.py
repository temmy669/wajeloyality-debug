from django.shortcuts import render
from .models import giftCard,giftcardtransaction,merchant,attachment
import random
import os
import pdfkit
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from django.http import Http404
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
import base64
import json
from json import loads, dumps
from .notification import Notification, htmltopdf
from rest_framework.permissions import IsAuthenticated
from django.views import View
from django.db.models import Sum
from django.utils import timezone
import datetime
import pytz
from django.db.models import Sum
from decimal import *
import openpyxl
import pandas as pd
from collections import OrderedDict
from django.conf import settings
from .permissions import (
    IsAdmin, IsAccountant, IsAuditor)

from .filters import GiftCardStatFilter, GiftCardFilter
from .serializers import GiftCardSerializer
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView






class GiftCardView(ListAPIView):
    queryset = giftCard.objects.all()
    serializer_class = GiftCardSerializer
    filter_class = GiftCardStatFilter

    def get_queryset(self):
        """Fetch the giftcards belonging to a particular merchant
        using the merchant's service ID.
        """
        
        service_id = self.kwargs['merchant_service_id']
        queryset = self.queryset.filter(merchID__serviceID__iexact = service_id)
        return queryset



class UpdateGiftCardView(RetrieveUpdateDestroyAPIView):
    queryset = giftCard.objects.all()
    serializer_class = GiftCardSerializer


class deactivateGiftCard(APIView):   
    def post(self, request, format=None):     
        giftcardid=request.data['giftcardid']
        to_reactivate=request.data.get('reactivate', False)
        try:
            to_reactivate = bool(to_reactivate)
        except:
            responseData ={'message':'Read the docs!','status':False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
            
        giftcardrecord=giftCard.objects.get(id=giftcardid)
        giftcardrecord.active = to_reactivate
        giftcardrecord.save()
        responseData ={'message':f'The giftcard record has been {"re-" if to_reactivate else "de-"}activated sucessfully','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
        

class MerchantGiftCardView(APIView):   
    """ Function to create gift card of a merchants  """
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant."""       
        count=request.data['count']
        merchID=request.data['merchID']
        createdby = request.data['createdby']
        try:
            for i in range(0,count):      
                serialnumber=generateSerialNumber(merchID)
                gf=giftCard(serialnumber=serialnumber,cardname=request.data['name'],amount=float(request.data['amount']),merchID_id=merchID,expiration_date=request.data['voucher_date'],createdby=createdby)      
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
            giftcardrecord = list(giftCard.objects.filter(merchID=merchID).values(
                'serialnumber', 'id', 'cardname', 'amount', 'recipient_phone', 'expiration_date', 'merchID').order_by('-createddate')[:1000])
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

class MerchantCustomerGiftcardVerificationView(APIView):
      def get(self, request, format=None):     
          """Save the post data when creating a new merchant.""" 
          serviceid = request.GET.get('serviceid')
          serialnumber = request.GET.get('serialnumber')
          merchid = merchant.objects.filter(
              serviceID=serviceid).values('id').first()
          record = list(giftCard.objects.filter(serialnumber=serialnumber).filter(merchID=merchid['id']).values('id', 'amount'))
          if merchid:   
            if record:
                redeemedamount = giftcardtransaction.objects.filter(merchID=merchid['id']).filter(
                    giftID=record[0]['id']).aggregate(Sum('redeemedamount'))
                if redeemedamount['redeemedamount__sum'] is None:
                    balance = float(0.00)
                else: 
                    balance = float(record[0]['amount']) - float(redeemedamount['redeemedamount__sum'])                
                responseData = {'data': balance, 'status': True}
            else:
                responseData ={'message':'giftcard is not found','status':False}
          else:
              responseData ={'message':'merchant is not found','status':False}
          return HttpResponse(json.dumps(responseData), content_type="application/json")        

class purchaseMerchantGiftCardView(APIView):
    def post(self, request, format=None):     
        """Class to purchase gift cards.""" 
        try: 
            """ Logic to get the giftcard """          
            giftcardrecord=giftCard.objects.filter(id=request.data['id']).filter(merchID=request.data['merchID']).values('recipient_phone','id','serialnumber','amount').first()
            if giftcardrecord['recipient_phone'] is None:
                """ Check to confim if the gift card has not be purchased """
                if giftcardrecord['amount']==float(request.data['amount']):
                    """ Check to confim if gift card has not be purchase """
                    gt =giftcardtransaction(
                        giftID_id=giftcardrecord['id'], purchaseamount=request.data['amount'], merchID_id=request.data['merchID'])
                    gt.save()
                    giftcard = giftCard.objects.get(id=request.data['id'])
                    giftcard.recipient_phone = request.data['phonenumber']
                    giftcard.recipient_email = request.data['emailaddress']
                    giftcard.save(update_fields=['recipient_phone','recipient_email'])#assign the gift card to the owner
                    notify = Notification()
                    merchantname = merchant.objects.filter(id=request.data['merchID']).values('businessname', 'businesslogo','serviceID').first()
                    firstname='customer'
                    randomnumber=giftcardrecord['serialnumber']
                    emailaddress=request.data['emailaddress']
                    subject='Voucher Details'
                    template_name='MarketSquareVoucher_details_bak.html'
                    if merchantname['serviceID'] =='351817683':
                        template_name = 'MarketSquareVoucher_details.html'
                    others=request.data['amount']
                    notify.emailNotification(firstname,randomnumber,emailaddress,subject,template_name,others,merchantname) 
                    notify=htmltopdf(firstname,randomnumber,emailaddress,subject,template_name,others,merchantname)  
                    pdfkit.from_string(notify,os.path.join(
                        settings.BASE_DIR, "voucherpdf", 'voucher_report-%s.pdf' %
                        (request.data['phonenumber'])))
                    at = attachment(
                        body='/voucherpdf/voucher_report-'+str(request.data['phonenumber'])+'.pdf', merchID_id=request.data['merchID'], name=request.data['phonenumber'])
                    at.save()
                else:
                    responseData ={'message':'amount does not match','status':'False'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")            
            else:
                responseData ={'message':'The voucher has been bought by another customer','status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
              responseData ={'message':'An error occur'+str(e),'status':'False'}
              return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'message':'Transaction capture','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

class redeemMerchantGiftCardView(APIView):
    def post(self, request, format=None):     
        """function to redeem gift cards from a merchant.""" 
        try: 
            try:
                record = giftCard.objects.filter(serialnumber=request.data['serialnumber']).filter(
                    merchID=request.data['merchID']).values('serialnumber', 'recipient_email', 'id', 'amount','expiration_date').first()
                    #retrieve giftcards from a merchant with a particular serialnumber """
            except TypeError:
                record = None  #to catch error when the record is none 
            todaydate = datetime.datetime.now().date()   
            #if record['expiration_date'] > todaydate:              
            if not(record is None):
                try:
                    #retrieve the owner of the giftcard 
                    verifyphone=giftCard.objects.filter(recipient_phone=request.data['phonenumber']).filter(merchID=request.data['merchID']).values('recipient_phone').first()
                except TypeError:
                    verifyphone = None  # to catch error when the record is none
                if not(verifyphone is None):
                    transactionvalue =float(request.data['amount'])
                    purchasevalue=record['amount'] 
                    remainingvalue = giftcardtransaction.objects.filter(merchID=request.data['merchID']).filter(
                        giftID=record['id']).aggregate(Sum('redeemedamount'))
                    #get the remaininging giftcard value
                    currentvalue = purchasevalue-remainingvalue['redeemedamount__sum']
                    #get the balance giftcard value
                    if currentvalue >= float(request.data['amount']):
                        gt=giftcardtransaction(giftID_id=record['id'],redeemedamount=request.data['amount'],merchID_id=request.data['merchID'])
                        gt.save() #capture the gift transaction
                        notify = Notification()
                        remainingvalue = giftcardtransaction.objects.filter(merchID=request.data['merchID']).filter(
                            giftID=record['id']).aggregate(Sum('redeemedamount'))
                        currentvalue = purchasevalue - remainingvalue['redeemedamount__sum']
                        firstname = 'customer'
                        randomnumber = request.data['serialnumber']
                        emailaddress = record['recipient_email']
                        subject = 'Gift Card Transaction'
                        template_name = 'voucher_transaction.html'
                        others = request.data['amount']
                        merchantname = merchant.objects.filter(id=request.data['merchID']).values('businessname', 'businesslogo').first()
                        notify.emailNotificationRedeemGiftcard(firstname,randomnumber,emailaddress,subject,template_name,merchantname,currentvalue,transactionvalue)
                        notify = htmltopdf(firstname, randomnumber, emailaddress, subject, template_name, others, merchantname)
                    else:
                        responseData ={'message':'Insufficent amount','status':'False'}
                        return HttpResponse(json.dumps(responseData), content_type="application/json")
                else:
                    responseData ={'message':'The phone number is not assigned to the voucher','status':'False'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData ={'message':'The voucher serial number does not exist','status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            #else:
                #responseData ={'message':'The voucher card has expired','status':'False'}
                #return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
               responseData ={'message':'An error occur'+str(e),'status':'False'}
               return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'message':'Transaction capture','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class bulkPurchaseMerchantGiftCardView(APIView):
    def post(self, request, format=None):       
        # you may put validations here to check extension or file size
        merchID = request.data['merchID']
        print(merchID)
        createdby=request.data['createdby']
        giftcardname=request.data['giftcardname']
        voucher_date=request.data['voucher_date']
        todaydate = str(datetime.datetime.now().date())+'-'+str(random.randint(1,1000000000001))
        wb_final=pd.read_excel(request.FILES['excel_file'])
        print(wb_final)
        #wb = request.FILES['excel_file'].get_records()
        #print(wb)
        #wb_final=loads(dumps(wb))
        # getting a particular sheet by name out of many sheets
        #excel_data = list()
        # iterating over the rows and
        # getting value from each cell in row
        finalhtmlcontext=''
        for item in wb_final.itertuples():
            phonenumber =item.phonenumber
            emailaddress=item.emailaddress
            amount = item.amount
            ref=generateReferenceNumber(merchID)
            serialnumber=generateSerialNumber(merchID)
            gf = giftCard(serialnumber=serialnumber, cardname=giftcardname, amount=float(
                amount),merchID_id=merchID, recipient_phone=phonenumber, recipient_email=emailaddress,
                expiration_date=voucher_date, createdby=createdby)
            gf.save()
            '''
            for item in wb_final.itertuples():
                phonenumber =item['phonenumber']
                emailaddress=item['emailaddress']
                amount = item['amount']
                ref=generateReferenceNumber(merchID)
                serialnumber=generateSerialNumber(merchID)
                gf = giftCard(serialnumber=serialnumber, cardname=giftcardname, amount=float(
                    amount),merchID_id=merchID, recipient_phone=phonenumber, recipient_email=emailaddress,
                    expiration_date=voucher_date, createdby=createdby)
                gf.save()
            '''
            lastestid = giftCard.objects.latest('id')
            finalid=lastestid.id
            gt = giftcardtransaction(
                giftID_id=finalid, purchaseamount=amount, merchID_id=merchID, reference=ref)
            gt.save()
            template_name='MarketSquareVoucher_details_x20_v3.html'
            merchantname = merchant.objects.filter(id=merchID).values(
                'businessname', 'businesslogo', 'serviceID').first()
            if merchantname['serviceID'] =='351817683':
               #template_name='MarketSquareVoucher_details.html'
               #template_name='MarketSquareVoucher_details_x20_v3.html'
                print(request.data['template'])
                if request.data['template']==0:
                   template_name='MarketSquareVoucher_details.html'
                elif request.data['template']==6:
                   template_name='MarketSquareVoucher_details_x20_v3.html'
                elif request.data['template']==10:
                   template_name='MarketSquareVoucher_details_x20_v3.html'
                elif request.data['template']==20:
                   template_name='MarketSquareVoucher_details_x20_v3.html'
            firstname = giftcardname
            randomnumber = serialnumber
            emailaddress = emailaddress
            subject='Voucher Details'   
            others = amount
            notify=htmltopdf(firstname,randomnumber,emailaddress,subject,template_name,others,merchantname)
            #finalhtmlcontext += "<div class='container'><div class='row'><div class='col-md'>{}</div></div></div>".format(notify)
            #print(finalhtmlcontext)
            finalhtmlcontext +='{}'.format(notify)
        pdfkit.from_string(finalhtmlcontext, os.path.join(settings.BASE_DIR, "voucherpdf", 'voucher_report-%s.pdf' % (todaydate)))
        at = attachment(body='/voucherpdf/voucher_report-'+todaydate+'.pdf',
                        merchID_id=merchID, name=todaydate)
        at.save()
        responseData = {'message': 'Transaction capture', 'status': 'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class bulkMerchantGiftCardView(APIView):
    def post(self, request, format=None):       
        # you may put validations here to check extension or file size
        merchID = request.data['merchID']
        createdby=request.data['createdby']
        giftcardname=request.data['giftcardname']
        voucher_date=request.data['voucher_date']
        todaydate = str(datetime.datetime.now().date())+'-'+str(random.randint(1,1000000000001))
        wb = request.FILES['excel_file'].get_records()
        wb_final=loads(dumps(wb))
        # getting a particular sheet by name out of many sheets
        #excel_data = list()
        # iterating over the rows and
        # getting value from each cell in row
        finalhtmlcontext=''
        htmldata={}
        for item in wb_final:
            phonenumber =item['phonenumber']
            emailaddress=item['emailaddress']
            amount = item['amount']
            ref=generateReferenceNumber(merchID)
            serialnumber=generateSerialNumber(merchID)
            gf = giftCard(serialnumber=serialnumber, cardname=giftcardname, amount=float(
                amount),merchID_id=merchID, recipient_phone=phonenumber, recipient_email=emailaddress,
                expiration_date=voucher_date, createdby=createdby)
            gf.save()
            lastestid = giftCard.objects.latest('id')
            finalid=lastestid.id
            #print(finalid)
            gt = giftcardtransaction(
                giftID_id=finalid, purchaseamount=amount, merchID_id=merchID, reference=ref)
            gt.save()
            htmldata.update({'serialnumber':serialnumber,'cardname':cardname,'amount':float(
                amount),'recipient_phone':phonenumber,'recipient_email':emailaddress, 'expiration_date':str(voucher_date)})
            #template_name='voucher_details.html'
            merchantname = merchant.objects.filter(id=merchID).values(
                'businessname', 'businesslogo', 'serviceID').first()
            '''
            if merchantname['serviceID'] =='351817683':
               template_name='MarketSquareVoucher_details.html'
            firstname = 'customer'
            randomnumber = serialnumber
            emailaddress = emailaddress
            subject='Voucher Details'   
            others = amount
            notify=htmltopdf(firstname,randomnumber,emailaddress,subject,template_name,others,merchantname)
            finalhtmlcontext += "{}<p style='page-break-before:always'></p>".format(
                notify)
        pdfkit.from_string(finalhtmlcontext, os.path.join(
            settings.BASE_DIR, "voucherpdf", 'voucher_report-%s.pdf' % (todaydate)))
        at = attachment(body='/voucherpdf/'+todaydate+'.pdf',
                        merchID_id=merchID, name=todaydate)
        at.save()
        '''
        responseData = {'message': htmldata, 'status': 'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

class documentattachment(APIView):
    def get(self,request, format=None):
        merchID=request.GET.get('merchID')
        records = list(attachment.objects.filter(
            merchID=merchID).values('body', 'name','createddate').order_by('-createddate'))
        for record in records:
            record['createddate']=str(record['createddate'])       
        responseData = {'data': records,'status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


def generateSerialNumber(merchID):
    x=random.randint(1,1000000000001)
    serialnum= giftCard.objects.filter(serialnumber=x).filter(merchID=merchID).values('serialnumber').first()
    while(serialnum != None):
        x=random.randint(1,1000000000001)
        serialnum= giftCard.objects.filter(serialnumber=x).filter(merchID=merchID).values('serialnumber').first()
    return x 


def generateReferenceNumber(merchID):
    x = random.randint(1, 1000000000001)
    refnum = giftcardtransaction.objects.filter(reference=x).filter(
        merchID=merchID).values('reference').first()
    while(refnum != None):
        x = random.randint(1, 1000000000001)
        refnum = giftcardtransaction.objects.filter(reference=x).filter(
            merchID=merchID).values('reference').first()
    return x



        
