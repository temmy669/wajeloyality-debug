from django.shortcuts import render
from .models import giftCard,giftcardtransaction,merchant,attachment, AccountantData,user
import random
import os
import pdfkit
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
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
    IsManager, IsAccountant, IsAuditor)
from .serializers import AccountantDataSerializer
from .filters import GiftCardStatFilter, GiftCardFilter
from .serializers import GiftCardSerializer
from .utils.auth import get_authenticated_user_from_request
from drf_spectacular.utils import extend_schema



@extend_schema(tags=['Gift Cards'])
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


@extend_schema(tags=['Gift Cards'])
class UpdateGiftCardView(ListAPIView):
    queryset = giftCard.objects.all()
    serializer_class = GiftCardSerializer

@extend_schema(tags=['Gift Cards'])
class deactivateGiftCard(APIView):
    permission_classes = [IsManager] 

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


@extend_schema(tags=['Finance'])  
class AccountDataView(ListAPIView):
    queryset = AccountantData.objects.all()
    serializer_class = AccountantDataSerializer
    # permission_classes = [IsAccountant, IsAdmin]
    filter_class = GiftCardFilter


@extend_schema(tags=['Finance'])
class UpdateAccountantDataView(RetrieveUpdateDestroyAPIView):
    queryset = AccountantData.objects.all()
    serializer_class = AccountantDataSerializer
    # permission_classes = [IsAdmin, IsAccountant]

@extend_schema(tags=['Gift Cards'])
class MerchantGiftCardView(APIView):
    permission_classes = [IsManager]
    """Class to create gift cards for a particular merchant."""

    def post(self, request, format=None):
        try:
            count = int(request.data['count'])
            merchID = int(request.data['merchID'])
            
            confirmationCode=request.data.get('confirmationCode', None),

            giftcards = [
                giftCard(
                    serialnumber=generateSerialNumber(merchID),
                    cardname=request.data['name'],
                    amount=float(request.data['amount']),
                    merchID_id=merchID,
                    expiration_date=request.data['voucher_date'],
                    createdby=request.user,
                    confirmationCode=confirmationCode
                )
                for _ in range(count)
            ]
            giftCard.objects.bulk_create(giftcards)
                
            created_giftcard = giftCard.objects.get(
                confirmationCode=confirmationCode,
                merchID_id=merchID
            )

            AccountantData.objects.filter(confirmationCode=confirmationCode).update(giftCard=created_giftcard)

        except Exception as e:
            return Response({'message': 'An error occurred: ' + str(e), 'status': 'False'}, status=400)

        return Response({'message': 'The giftcard record is created successfully', 'status': 'True'})

    def get(self, request, format=None):
        """List gift cards for a particular user with role manager."""
        try:
            giftcardrecord = list(
                giftCard.objects.filter(createdby=request.user)
                .values('serialnumber', 'id', 'cardname', 'amount', 'recipient_phone', 'expiration_date', 'merchID', 'active')
                .order_by('-createddate')[:1000]
            )
            dictList = []

            for counter, element in enumerate(giftcardrecord):
                length = len(giftcardrecord)
                if length > counter:
                    purchasevalue = element['amount']
                    redeemedvalue = giftcardtransaction.objects.filter(
                        merchID=element['merchID'], giftID=element['id']
                    ).aggregate(Sum('redeemedamount'))['redeemedamount__sum']

                    if redeemedvalue is None:
                        redeemedvalue = Decimal('0.0')

                    currentvalue = float(purchasevalue - redeemedvalue)
                    currentvalue_dict = {'currentvalue': currentvalue}

                    element['amount'] = float(element['amount'])
                    element['expiration_date'] = str(element['expiration_date'])
                    element.update(currentvalue_dict)
                    dictList.append(element)

        except Exception as e:
            responseData = {
                'message': 'An error occurred: ' + str(e),
                'status': 'False'
            }
            return HttpResponse(json.dumps(responseData), content_type="application/json")

        responseData = {
            'data': dictList,
            'status': 'True'
        }
        return HttpResponse(json.dumps(responseData), content_type="application/json")
   

@extend_schema(tags=['Gift Cards'])
class MerchantCustomerGiftcardVerificationView(APIView):
      permission_classes = [IsManager]
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


@extend_schema(tags=['Gift Cards'])
class purchaseMerchantGiftCardView(APIView):
    permission_classes = [IsManager]
    def post(self, request, format=None):     
        """Class to purchase gift cards.""" 
        try:
            # Get merchant ID from token (set by custom authentication)
            merch_id = getattr(request.user, 'merchID_from_token', None)
            if merch_id is None:
                responseData = {'message': 'Merchant ID not found in token', 'status': 'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        
            # Fetch the gift card record
            giftcardrecord = giftCard.objects.filter(
                id=request.data['id'],
                merchID=merch_id
            ).values('recipient_phone', 'id', 'serialnumber', 'amount', 'cardname').first()
        
            # Check if the gift card exists
            if not giftcardrecord:
                responseData = {'message': 'Gift card not found', 'status': 'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
    
            # Check if the gift card has not been purchased
            if giftcardrecord['recipient_phone'] is None:
                # Check if the amount matches
                if giftcardrecord['amount'] == float(request.data['amount']):
                    gt = giftcardtransaction(
                        giftID_id=giftcardrecord['id'],
                        purchaseamount=request.data['amount'],
                        merchID_id=merch_id,  # Use the merchID from the token
                    )
                    gt.save()
                    giftcard = giftCard.objects.get(id=request.data['id'])
                    giftcard.recipient_phone = request.data['phonenumber']
                    giftcard.recipient_email = request.data['emailaddress']
                    giftcard.save(update_fields=['recipient_phone','recipient_email'])  # assign the gift card to the owner
                    notify = Notification()
                    merchantname = merchant.objects.filter(id=merch_id).values('businessname', 'businesslogo','serviceID').first()
                    if not merchantname:
                        responseData = {'message': 'Merchant not found', 'status': 'False'}
                        return HttpResponse(json.dumps(responseData), content_type="application/json")
                    name = giftcardrecord['cardname']
                    randomnumber = giftcardrecord['serialnumber']
                    emailaddress = request.data['emailaddress']
                    subject = 'Voucher Details'
                    template_name = 'MarketSquareVoucher_details_x20_v3.html'
                    if merchantname['serviceID'] == '351817683':
                        template_name = 'MarketSquareVoucher_details_x20_v3.html'
                    others = request.data['amount']
                    # Get the expiry date from the giftcard record
                    expiry = str(giftCard.objects.get(id=request.data['id']).expiration_date)
                    notify.emailNotification(name, randomnumber, emailaddress, subject, template_name, others, merchantname)
                    notify_html = htmltopdf(name, randomnumber, emailaddress, subject, template_name, expiry, others, merchantname)
                    config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
                    pdf_path = os.path.join(settings.MEDIA_ROOT, "voucherpdf", 'voucher_report-%s.pdf' % request.data['phonenumber'])
                    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                    pdfkit.from_string(notify_html, pdf_path, configuration=config)
                    
                    at = attachment(
                        body='voucherpdf/voucher_report-%s.pdf' % request.data['phonenumber'],
                        merchID_id=merch_id,
                        name=request.data['phonenumber'],
                        userID_id=request.user.id
                    )
                    at.save()
                else:
                    responseData = {'message': 'amount does not match', 'status': 'False'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")            
            else:
                responseData = {'message': 'The voucher has been bought by another customer', 'status': 'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur: ' + str(e), 'status': 'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData = {'message': 'Transaction capture', 'status': 'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


@extend_schema(tags=['Gift Cards'])
class redeemMerchantGiftCardView(APIView):
    permission_classes = [IsManager]
    def post(self, request, format=None):     
        """function to redeem gift cards from a merchant.""" 
        try: 
            try:
                record = giftCard.objects.filter(serialnumber=request.data['serialnumber']).filter(
                    merchID=request.data['merchID']).values('serialnumber', 'recipient_email', 'id', 'amount','expiration_date', 'active').first()
                    #retrieve giftcards from a merchant with a particular serialnumber """
            except TypeError:
                record = None  #to catch error when the record is none 
            todaydate = datetime.datetime.now().date()   
            #if record['expiration_date'] > todaydate:              
            if not(record is None):
                #check if the giftcard is active
                if record['active'] == False:
                    responseData ={'message':'The voucher card is inactive','status':'False'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
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
                        notify.emailNotificationRedeemGiftcard(firstname,randomnumber,emailaddress,subject,template_name, others, merchantname,currentvalue,transactionvalue)
                        notify.emailNotification(
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


@extend_schema(tags=['Gift Cards'])
class bulkPurchaseMerchantGiftCardView(APIView):
    permission_classes = [IsManager]
    def post(self, request, format=None):
        try:
            # Get merchant ID from token (set by custom authentication)
            merch_id = getattr(request.user, 'merchID_from_token', None)
            if merch_id is None:
                responseData = {'message': 'Merchant ID not found in token', 'status': 'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")

            createdby = request.user
            giftcardname = request.data['giftcardname']
            voucher_date = request.data['voucher_date']
            todaydate = str(datetime.datetime.now().date()) + '-' + str(random.randint(1, 1000000000001))
            wb_final = pd.read_excel(request.FILES['excel_file'])

            finalhtmlcontext = ''
            for item in wb_final.itertuples():
                phonenumber = item.phonenumber
                emailaddress = item.emailaddress
                amount = item.amount
                ref = generateReferenceNumber(merch_id)
                serialnumber = generateSerialNumber(merch_id)
                gf = giftCard(
                    serialnumber=serialnumber,
                    cardname=giftcardname,
                    amount=float(amount),
                    merchID_id=merch_id,
                    recipient_phone=phonenumber,
                    recipient_email=emailaddress,
                    expiration_date=voucher_date,
                    createdby=createdby
                )
                gf.save()
                lastestid = giftCard.objects.latest('id')
                finalid = lastestid.id
                gt = giftcardtransaction(
                    giftID_id=finalid, purchaseamount=amount, merchID_id=merch_id, reference=ref)
                gt.save()
                template_name = 'MarketSquareVoucher_details_x20_v3.html'
                merchantname = merchant.objects.filter(id=merch_id).values(
                    'businessname', 'businesslogo', 'serviceID').first()
                if merchantname and merchantname['serviceID'] == '351817683':
                    if request.data.get('template') == 0:
                        template_name = 'MarketSquareVoucher_details.html'
                    elif request.data.get('template') in [6, 10, 20]:
                        template_name = 'MarketSquareVoucher_details_x20_v3.html'
                firstname = giftcardname
                randomnumber = serialnumber
                subject = 'Voucher Details'
                others = amount
                expiry_date_str = voucher_date.strftime('%d %b %Y') if isinstance(voucher_date, datetime.date) else voucher_date

                notify = htmltopdf(
                    firstname,
                    randomnumber,
                    emailaddress,
                    subject,
                    template_name,
                    expiry_date_str,
                    others,
                    merchantname
                )
                finalhtmlcontext += '{}'.format(notify)

            pdfkit.from_string(finalhtmlcontext, os.path.join(settings.BASE_DIR, "voucherpdf", 'voucher_report-%s.pdf' % (todaydate)))
            at = attachment(body='/voucherpdf/voucher_report-' + todaydate + '.pdf',
                            merchID_id=merch_id, name=todaydate)
            at.save()
            responseData = {'message': 'Transaction capture', 'status': 'True'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur: ' + str(e), 'status': 'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

@extend_schema(tags=['Gift Cards'])
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
            cardname=""
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


@extend_schema(tags=['Attachment'])
class documentattachment(APIView):
    permission_classes = [IsManager]
    def get(self,request, format=None):
        userID = getattr(request.user, 'id', None)
        records = list(attachment.objects.filter(
            userID_id=userID,).values('body', 'name','createddate').order_by('-createddate'))
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





