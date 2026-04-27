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
from django.db.models import Sum, Q
from django.utils import timezone
import datetime
import pytz
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
from decimal import Decimal, ROUND_HALF_UP
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .services.gift_card_service import GiftCardError, redeem_normal
from wajecrm.services.gift_card_service import deactivate_gift_card
from wajecrm.models import DeactivationReason




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
        giftcard_id = request.data['giftcardid']
        to_reactivate = request.data.get('reactivate', False)

        try:
            to_reactivate = bool(to_reactivate)
        except Exception:
            return HttpResponse(
                json.dumps({'message': 'Invalid value for reactivate.', 'status': False}),
                content_type='application/json'
            )

        card = giftCard.objects.get(id=giftcard_id)

        if to_reactivate:
            card.active = True
            # Clear audit fields on reactivation so next deactivation is clean
            card.deactivated_by = None
            card.deactivated_date = None
            card.deactivation_reason = None
            card.save(update_fields=['active', 'deactivated_by', 'deactivated_date',
                                     'deactivation_reason'])
            msg = 'Gift card reactivated successfully.'
        else:
            deactivate_gift_card(
                card,
                deactivated_by_user=request.user,
                reason=DeactivationReason.MANUAL_DEACTIVATION,
            )
            msg = 'Gift card deactivated successfully.'

        return HttpResponse(
            json.dumps({'message': msg, 'status': True}),
            content_type='application/json'
        )


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
            
            confirmationCode=request.data.get('confirmationCode', None)

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
                
            created_giftcards = giftCard.objects.filter(
                confirmationCode=confirmationCode,
                merchID_id=merchID
            )

            accountant_data = AccountantData.objects.filter(confirmationCode=confirmationCode)
            accountant_data.update(giftCard=created_giftcards.first())
           

        except Exception as e:
            return Response({'message': 'An error occurred: ' + str(e), 'status': 'False'}, status=400)

        return Response({'message': 'The giftcard record is created successfully', 'status': 'True'})


    def get(self, request, format=None):

        try:

            search = request.query_params.get('search')

            queryset = giftCard.objects.filter(
                createdby=request.user
            )

            if search:
                queryset = queryset.filter(
                    Q(serialnumber__icontains=search) |
                    Q(cardname__icontains=search) |
                    Q(recipient_phone__icontains=search)
                )

            queryset = queryset.annotate(
                redeemedvalue=Sum('giftcardtransaction__redeemedamount')
            ).values(
                'serialnumber',
                'id',
                'cardname',
                'amount',
                'recipient_phone',
                'expiration_date',
                'merchID',
                'active',
                'redeemedvalue'
            ).order_by('-createddate')

            paginator = PageNumberPagination()

            page = paginator.paginate_queryset(queryset, request)

            dictList = []

            for element in page:

                redeemedvalue = element['redeemedvalue'] or Decimal('0.0')
                purchasevalue = element['amount']

                element['amount'] = float(element['amount'])
                element['expiration_date'] = str(element['expiration_date'])
                element['currentvalue'] = float(purchasevalue - redeemedvalue)
                #add expired tag
                if element['expiration_date'] and element['expiration_date'] < str(datetime.date.today()):
                    element['is_expired'] = True
                else:
                    element['is_expired'] = False

                dictList.append(element)

            return paginator.get_paginated_response({
                "data": dictList,
                "status": True
            })

        except Exception as e:
            return Response({
                "message": "An error occurred: " + str(e),
                "status": False
            })   

@extend_schema(tags=['Gift Cards'])
class MerchantCustomerGiftcardVerificationView(APIView):
    #   permission_classes = [IsManager]
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
                    output_dir = os.path.join(settings.BASE_DIR, "voucherpdf")
                    os.makedirs(output_dir, exist_ok=True)

                    pdf_path = os.path.join(output_dir, f"voucher_report-{request.data['phonenumber']}.pdf")
                    pdfkit.from_string(notify_html, pdf_path)    
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
    def post(self, request, format=None):
        try:
            merch_id = int(request.data['merchID'])
            serialnumber = request.data['serialnumber']
            phonenumber = request.data['phonenumber']
            amount = Decimal(str(request.data['amount']))

            card = giftCard.objects.filter(
                serialnumber=serialnumber,
                merchID=merch_id
            ).first()

            if not card:
                return _json_response({'message': 'Voucher serial number does not exist.',
                                       'status': 'False'})

            # Verify phone assignment
            owner = giftCard.objects.filter(
                recipient_phone=phonenumber, merchID=merch_id
            ).exists()
            if not owner:
                return _json_response({'message': 'Phone number is not assigned to this voucher.',
                                       'status': 'False'})

            ref = str(generateReferenceNumber(merch_id))
            result = redeem_normal(
                card=card,
                amount=amount,
                merch_id=merch_id,
                redeemed_by_user=request.user,
                reference=ref,
            )
            notify.emailNotificationRedeemGiftcard(firstname,randomnumber,emailaddress,subject,template_name, merchantname,currentvalue,transactionvalue,balance)
            notify.emailNotification(
                firstname, randomnumber, emailaddress, subject, template_name, others, merchantname)
            
            return _json_response({'message': 'Transaction captured.', 'status': 'True'})

        except GiftCardError as e:
            return _json_response({'message': str(e), 'status': 'False'})
        except Exception as e:
            return _json_response({'message': f'An error occurred: {str(e)}', 'status': 'False'})


def _json_response(data):
    import json
    from django.http import HttpResponse
    return HttpResponse(json.dumps(data), content_type='application/json')


@extend_schema(tags=['Gift Cards'])
class bulkPurchaseMerchantGiftCardView(APIView):
    permission_classes = [IsManager]

    def post(self, request, format=None):
        try:
            merch_id = getattr(request.user, 'merchID_from_token', None)
            if merch_id is None:
                return HttpResponse(json.dumps({
                    'message': 'Merchant ID not found in token',
                    'status': 'False'
                }), content_type="application/json")

            createdby = request.user
            giftcardname = request.data['giftcardname']
            voucher_date = request.data['voucher_date']
            todaydate = str(datetime.datetime.now().date()) + '-' + str(random.randint(1, 1000000000001))

            # Read Excel
            try:
                wb_final = pd.read_excel(request.FILES['excel_file'])
            except Exception as e:
                return HttpResponse(json.dumps({
                    'message': f'Failed to read Excel file: {str(e)}',
                    'status': 'False'
                }), content_type="application/json")

            # Extract confirmation code from first row and sum total
            try:
                confirmation_code = wb_final['confirmationCode'].iloc[0]
                # print(wb_final['amount'])
                # Convert amount column to Decimal for precision and compatibility
                
                wb_final['amount'] = wb_final['amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                
                # print(wb_final['amount'])
                amount_to_be_created = wb_final['amount'].sum()
                
                # print("Total amount to be created: ", amount_to_be_created)
                try:
                    record = AccountantData.objects.get(
                            confirmationCode=confirmation_code,
                            # merchID_id=merch_id
                        )
                    print(record)
                    amount_paid = record.amount

                except AccountantData.DoesNotExist:
                    return JsonResponse({
                        "message": f"No record found for confirmation code {confirmation_code}.",
                        "status": False
                    }, status=404)

                # Sum of existing giftcards with same confirmation code in the giftcards table
                used_amount = giftCard.objects.filter(
                    confirmationCode=confirmation_code
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.0')

               # Calculate available balance
                available_balance = amount_paid - used_amount
                
                print("Available balance: ", available_balance, "Amount to be created: ", amount_to_be_created, "Total amount created so far: ", used_amount)

                if available_balance <= 0:
                    # No funds remaining
                    return HttpResponse(json.dumps({
                        'message': f"Confirmation code {confirmation_code} has already been fully used. No balance remains.",
                        'status': 'False'
                    }), content_type="application/json")

                    
                if amount_to_be_created > available_balance:
                    # print(amount_to_be_created > available_balance)
                    return HttpResponse(json.dumps({
                        'message': (
                            f"Only ₦{available_balance:,.2f} is available for confirmation code {confirmation_code}, "
                            f"but you're trying to use ₦{amount_to_be_created:,.2f}. Please use an appropriate amount."
                        ),
                        'status': 'False'
                    }), content_type="application/json")

                # Otherwise, you're good to proceed
                print(f"Proceeding with amount: {amount_to_be_created} | Available balance: {available_balance}")

                
                # print(f"Total to be used: {amount_to_be_created} | Already used: {used_amount}")
            except Exception as e:
                return HttpResponse(json.dumps({
                    'message': f'Error validating confirmation code usage: {str(e)}',
                    'status': 'False'
                }), content_type="application/json")

            finalhtmlcontext = ''
            for item in wb_final.itertuples():
                try:
                    phonenumber = item.phonenumber
                    emailaddress = item.emailaddress
                    amount = item.amount
                except Exception as e:
                    print("Missing column in row:", str(e))
                    continue

                ref = generateReferenceNumber(merch_id)
                serialnumber = generateSerialNumber(merch_id)

                # Save giftcard
                gf = giftCard(
                    serialnumber=serialnumber,
                    cardname=giftcardname,
                    amount=float(amount),
                    merchID_id=merch_id,
                    recipient_phone=phonenumber,
                    recipient_email=emailaddress,
                    expiration_date=voucher_date,
                    createdby=createdby,
                    confirmationCode=confirmation_code  # ✅ Set here
                )
                gf.save()

                finalid = gf.id
                gt = giftcardtransaction(
                    giftID_id=finalid,
                    purchaseamount=amount,
                    merchID_id=merch_id,
                    reference=ref
                )
                gt.save()

                merchantname = merchant.objects.filter(id=merch_id).values(
                    'businessname', 'businesslogo', 'serviceID').first()

                template_name = 'MarketSquareVoucher_details_x20_v3.html'
                if merchantname and merchantname['serviceID'] == '351817683':
                    if request.data.get('template') == 0:
                        template_name = 'MarketSquareVoucher_details.html'
                    elif request.data.get('template') in [6, 10, 20]:
                        template_name = 'MarketSquareVoucher_details_x20_v3.html'

                expiry_date_str = voucher_date.strftime('%d %b %Y') if isinstance(voucher_date, datetime.date) else voucher_date

                try:
                    notify_html = htmltopdf(
                        giftcardname,
                        serialnumber,
                        emailaddress,
                        'Voucher Details',
                        template_name,
                        expiry_date_str,
                        amount,
                        merchantname
                    )
                    finalhtmlcontext += notify_html
                except Exception as e:
                    print(f"Error in htmltopdf for {emailaddress}: {str(e)}")

            if not finalhtmlcontext:
                return HttpResponse(json.dumps({
                    'message': 'HTML generation failed for all records.',
                    'status': 'False'
                }), content_type="application/json")

            pdf_dir = os.path.join(settings.BASE_DIR, "voucherpdf")
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f'voucher_report-{todaydate}.pdf')

            try:
                pdfkit.from_string(finalhtmlcontext, pdf_path)
            except Exception as e:
                return HttpResponse(json.dumps({
                    'message': f'PDF generation failed: {str(e)}',
                    'status': 'False'
                }), content_type="application/json")

            # Save attachment
            at = attachment(
                body=f'voucherpdf/voucher_report-{todaydate}.pdf',
                merchID_id=merch_id,
                name=todaydate,
                userID_id=request.user.id
            )
            at.save()

        except Exception as e:
            return HttpResponse(json.dumps({
                'message': f'Unhandled error: {str(e)}',
                'status': 'False'
            }), content_type="application/json")

        return HttpResponse(json.dumps({
            'message': 'Transaction capture successful',
            'status': 'True',
        }), content_type="application/json")

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





