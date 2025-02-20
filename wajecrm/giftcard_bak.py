from django.shortcuts import render
from .models import giftCard,giftcardtransaction,merchant,attachment,voucher
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
from django.db.models import Sum, Q
from decimal import *
import openpyxl
from collections import OrderedDict
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import pagination


        
class LinkHeaderPagination(pagination.PageNumberPagination):
    page_size_query_param = '500' 
    def get_paginated_response(self, data):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()
        if next_url is not None and previous_url is not None:
            nexturl=next_url
            previousurl=previous_url
            #link = '<{next_url}>; rel="next", <{previous_url}>; rel="prev"'
        elif next_url is not None:
            nexturl=next_url
            previousurl=''
        elif previous_url is not None:
            previousurl=previous_url
            nexturl=''
        else:
            nexturl = ''
            previousurl = ''
        headers = {'Next': nexturl,'Prev':previousurl,'Count': self.page.paginator.count}
        responseData = {'data': data,'headers': headers,'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
        #return Response(data, headers=headers)

    def get_record(self,data):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()
        if next_url is not None and previous_url is not None:
            nexturl=next_url
            previousurl=previous_url
            #link = '<{next_url}>; rel="next", <{previous_url}>; rel="prev"'
        elif next_url is not None:
            nexturl=next_url
            previousurl=''
        elif previous_url is not None:
            previousurl=previous_url
            nexturl=''
        else:
            nexturl = ''
            previousurl = ''
        if self.page.has_next():
           pagenum = self.page.next_page_number()
           print(pagenum)
        else:
           pagenum=''
        headers = {'Next': nexturl,'Prev':previousurl,'pagenum':pagenum,'Count': self.page.paginator.count,'data':data}
        #print(headers)
        return headers


class MerchantGiftCardView(APIView):  
    permission_classes = (IsAuthenticated,)
    """ Function to create gift card of a merchants  """
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant."""       
        count=request.data['count']
        merchID=request.data['merchID']
        createdby = request.data['createdby']
        try:
            for i in range(0,count):      
                serialnumber=generateSerialNumber(merchID)
                gf=giftCard(serialnumber=serialnumber,cardname=request.data['name'],amount=float(request.data['amount']),merchID_id=merchID,expiration_date=request.data['voucher_date'],
                createdby=createdby)      
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
        search = request.GET.get('search')
        try:
            if search :
               giftcardrecord = list(giftCard.objects.filter(merchID=merchID).filter(Q(cardname__icontains=search) | Q(serialnumber__icontains=search)).values(
                       'serialnumber', 'id', 'cardname', 'amount', 'recipient_phone', 'expiration_date', 'merchID', 'active').order_by('-createddate')) 
            else:
                giftcardrecord = list(giftCard.objects.filter(merchID=merchID).values(
                'serialnumber', 'id', 'cardname', 'amount', 'recipient_phone', 'expiration_date', 'merchID','active').order_by('-createddate'))
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
            paginator = LinkHeaderPagination()
            page = paginator.paginate_queryset(dictList, request)  
            if page is not None:
               return paginator.get_paginated_response(page)             
        except Exception as e:
               responseData ={'message':'An error occur'+str(e),'status':'False'}
               return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'data':dictList,'status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
    def put(self, request, format=None):
        merchID= request.data['merchid']
        serialnumber = giftCard.objects.filter(
            id=request.data['giftcardid']).values('serialnumber').first()
        serviceid = merchant.objects.filter(id=merchID).values('serviceID').first()
        giftcard = giftCard.objects.get(id=request.data['giftcardid'])
        giftcard.active = request.data['status']
        giftcard.save(update_fields=['active'])
        if serviceid['serviceID']=='351817683':
           #update Metro Pos database
           voucherdetail=voucher.objects.get(ID=serialnumber['serialnumber'])
           voucherdetail.SOLDOUT = request.data['status']
           voucherdetail.save(update_fields=['SOLDOUT'])
        responseData ={'message':'record updated','status':True}
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
            code = str(datetime.datetime.now().date())+'-' + \
                str(random.randint(1, 1000000000001))
            giftcardrecord=giftCard.objects.filter(id=request.data['id']).filter(merchID=request.data['merchID']).values('recipient_phone','id','serialnumber','amount','cardname').first()
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
                    beneficiary = giftcardrecord['cardname']
                    emailaddress=request.data['emailaddress']
                    subject='Voucher Details'
                    template_name='voucher_details.html'
                    if merchantname['serviceID'] =='351817683':
                        template_name = 'MarketSquareVoucher_details.html'
                    others=request.data['amount']
                    notify.emailNotification(firstname,randomnumber,emailaddress,subject,template_name,others,merchantname,beneficiary) 
                    pdfconverter=htmltopdf(firstname,randomnumber,emailaddress,subject,template_name,others,merchantname,beneficiary)  
                    pdfkit.from_string(pdfconverter, os.path.join(
                        settings.BASE_DIR,"voucherpdf",'voucher_report-%s.pdf' % (code)))
                    at = attachment(
                        body='/voucherpdf/'+'voucher_report-%s.pdf' % (code), merchID_id=request.data['merchID'], name=code)
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
                        merchantname = merchant.objects.filter(id=request.data['merchID']).values('businessname', 'businesslogo').first()
                        notify.emailNotificationRedeemGiftcard(firstname,randomnumber,emailaddress,subject,template_name,merchantname,currentvalue,transactionvalue)
                        notify = emailNotification(
                            firstname, randomnumber, emailaddress, subject, template_name, others, merchantname)
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
        createdby=request.data['createdby']
        giftcardname=request.data['giftcardname']
        voucher_date=request.data['voucher_date']
        beneficiary = request.data['giftcardname']
        todaydate = str(datetime.datetime.now().date())+'-'+str(random.randint(1,1000000000001))
        wb = request.FILES['excel_file'].get_records()
        wb_final=loads(dumps(wb))
        # getting a particular sheet by name out of many sheets
        #excel_data = list()
        # iterating over the rows and
        # getting value from each cell in row
        finalhtmlcontext=''
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
            print(finalid)
            gt = giftcardtransaction(
                giftID_id=finalid, purchaseamount=amount, merchID_id=merchID, reference=ref)
            gt.save()
            merchantname = merchant.objects.filter(id=merchID).values(
                'businessname', 'businesslogo', 'serviceID').first()
            if merchantname['serviceID'] =='351817683':
               template_name='MarketSquareVoucher_details.html'
            else:
               template_name='voucher_details.html'                
            firstname = 'customer'
            randomnumber = serialnumber
            emailaddress = emailaddress
            subject='Voucher Details'   
            others = amount
            notify=htmltopdf(firstname,randomnumber,emailaddress,subject,template_name,others,merchantname,beneficiary)
            finalhtmlcontext += "{}<p style='page-break-before:always'></p>".format(
                notify)
        pdfkit.from_string(finalhtmlcontext, os.path.join(
            settings.BASE_DIR, "voucherpdf", 'voucher_report-%s.pdf' % (todaydate)))
        at = attachment(body='/voucherpdf/'+'voucher_report-%s.pdf'%(todaydate),
                        merchID_id=merchID, name=todaydate)
        at.save()
        responseData = {'message': 'Transaction capture', 'status': 'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

class documentattachment(APIView):
    def get(self,request, format=None):
        merchID=request.GET.get('merchID')
        records = list(attachment.objects.filter(
            merchID=merchID).values('body', 'name','createddate'))
        for record in records:
            record['createddate']=str(record['createddate'])       
        responseData = {'data': records, 'status': 'True'}
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


        
