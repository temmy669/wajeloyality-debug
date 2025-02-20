from django.shortcuts import render
from .models import *
import random
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from django.http import Http404
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from .serializers import *
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.forms.models import model_to_dict
import logging
from .notification import Notification
from .customer import *
from .loyalty import *
from .logger import *
from .giftcard import generateReferenceNumber
import base64
import json
from django.views import View
from django.db.models import Sum
from django.utils import timezone
import datetime

''' Class to create merchant customers '''
class MerchantCustomerRegistrationView(APIView):
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant."""
        try:       
            serviceid=request.data['serviceid']
            checkserviceid= checkServiceId(serviceid)        
            if checkserviceid:
                merchID=checkserviceid['id']
                customerphonenumber = request.data['phonenumber']           
                checkdupcustomer=duplicateCustomerID(customerphonenumber,merchID)           
                #checkdupmetrocustomer = duplicateMetroCustomer(customerphonenumber,serviceid)
                if checkdupcustomer:
                    passwd = make_password(request.data['password'],salt=None,hasher='default')
                    c=customer(title=request.data['title'],firstname=request.data['firstname'],
                            lastname=request.data['lastname'],emailaddress=request.data['emailaddress'],
                            customerIdentifier=request.data['phonenumber'],
                            merchID_id=merchID, password=passwd, gender=request.data['emailaddress'],
                            DOB=request.data['dob'])
                    c.save()
                    '''
                    ct = loyaltyCustomer(Loyaltycode='POINT',CardNumber=request.data['phonenumber'], Customername=request.data['firstname']+' '+request.data['lastname'], Address=request.data['emailaddress'], Tel=request.data['phonenumber'])
                    ct.save()
                    '''
                    responseData ={'message':'record created','status':True}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                else:
                    responseData ={'message':'loyalty record already exist, please login with your loyalty number','status':False}
                    return HttpResponse(json.dumps(responseData), content_type="application/json") 
            else:
                responseData ={'message':'serviceID cannot be found','status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")

class MerchantCustomerLoginView(APIView):
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant."""
        print('request')
        print(request.data)
        try:       
            serviceid=request.data['serviceid']
            password=request.data['password']
            print('request')
            print(request.data)
            checkserviceid= checkServiceId(serviceid)
            if checkserviceid:
                username=customer.objects.filter(customerIdentifier=request.data['phonenumber']).values('id','firstname','lastname','customerIdentifier','emailaddress','gender','DOB','title').first()
                if username is not None:                                               
                    passwordvalue =list(customer.objects.filter(customerIdentifier=request.data['phonenumber']).values_list('password',flat=True))                   
                    b=passwordvalue[0]          
                    passwordconfirm=check_password(password,b)
                    if passwordconfirm:
                       return JsonResponse({'data':username,'status':True})
                    else:
                     responseData ={'message':'password is invalid','status':False}
                     return HttpResponse(json.dumps(responseData), content_type="application/json")
                else:
                    responseData ={'message':'username does not exist','status':False}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData ={'message':'serviceID cannot be found','status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
    
    def put(self, request, format=None):
        serviceid=request.data['serviceid']
        password=request.data['password']
        phonenumber=request.data['phonenumber']
        merchid= merchant.objects.filter(serviceID=serviceid).values('id').first()
        userid=customer.objects.filter(customerIdentifier=phonenumber).filter(merchID=merchid['id']).values('id').first()
        print(userid['id'])
        if userid:
            customerupdate = customer.objects.get(id=str(userid['id']))
            customerupdate.password= make_password(password,salt=None,hasher='default')
            customerupdate.save(update_fields=['password'])
            print('working')
            responseData ={'message':'password changed','status':True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        else:
            responseData ={'message':'password not changed','status':False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
           
class MerchantCustomerEarnPointsView(APIView):
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant."""
        try:       
            serviceid=request.data['serviceid']
            checkserviceid= checkServiceId(serviceid)        
            if checkserviceid:
                merchID=checkserviceid['id']
                customerphonenumber=request.data['phonenumber']
                receiptno= request.data['ref']
                checkduplicatereceipt=checkForDupReceipt(receiptno,merchID)
                if checkduplicatereceipt is False:
                    custID = customer.objects.filter(merchID=merchID).filter(
                        customerIdentifier=customerphonenumber).values('id', 'transactionpin').first()
                    merchloyaltyrule=loyaltyrule.objects.filter(merchID=merchID).values('id').first() 
                    loyaltyruleID= merchloyaltyrule['id']
                    transactionamount =request.data['transactionamount']
                    assignpoint=postAssignedPoint(loyaltyruleID,transactionamount)
                    loyaltytransactionrecord =loyaltytransaction(loyaltyruleID_id=loyaltyruleID,CustID_id=custID['id'],merchID_id=merchID,transactionamount=transactionamount,assignedpoint=assignpoint,transactiondate=request.data['transactiondate'],receiptno=receiptno)
                    loyaltytransactionrecord.save()
                    if serviceid =='351817683':
                        customerecord = list(voucher.objects.filter(
                            ID=customerphonenumber).values('ID'))
                        if  not customerecord:
                            """check if the customer exist on MetroPOS"""
                            v = voucher(ID=str(customerphonenumber),CUSTOMERCODE=str(customerphonenumber),Amount=assignpoint,OtherInfo=str(custID['transactionpin']))
                            v.save()
                            """Create the customer and the transactions in MetroPOS if the customer deos not exist in Walexx"""
                        else:
                            vt = vouchertransactions(ID=str(
                                customerphonenumber), Credit=assignpoint, Debit='0.00', Particular='transaction', ref=receiptno)
                            vt.save()
                            """Voucher transaction saves for already existing customers """             
                    responseData ={'message':'earned point is captured','status':True}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                else:
                    responseData ={'message':'record aleady exist','status':False}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData ={'message':'serviceID cannot be found','status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")

class MerchantCustomerRedeemPointsView(APIView):
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant."""
        try:       
            serviceid=request.data['serviceid']
            checkserviceid= checkServiceId(serviceid)        
            if checkserviceid:
                merchID=checkserviceid['id']
                customerphonenumber=str(request.data['phonenumber'])
                receiptno = generateReceiptNo(merchID)
                custID=customer.objects.filter(merchID=merchID).filter(customerIdentifier=customerphonenumber).values('id').first()
                assignedvalue=loyaltytransaction.objects.filter(merchID=merchID).filter(CustID=custID['id']).aggregate(Sum('assignedpoint'))
                redeemedpoint=loyaltytransaction.objects.filter(merchID=merchID).filter(CustID=custID['id']).aggregate(Sum('redeemedpoint'))
                if assignedvalue['assignedpoint__sum'] is not None:
                   currentvalue=assignedvalue['assignedpoint__sum'] -redeemedpoint['redeemedpoint__sum']
                   amountredeem=request.data['point']
                   if currentvalue > Decimal(amountredeem):
                      l=loyaltytransaction(CustID_id=custID['id'],merchID_id=merchID,redeemedpoint=request.data['point'],transactiondate=timezone.now(),
                      receiptno=receiptno,description=request.data['description'])
                      l.save()
                      if serviceid =='351817683':
                         vt = vouchertransactions(ID=str(customerphonenumber),Debit=request.data['point'],Credit='0.00', Particular='transaction',ref=receiptno)
                         vt.save()
                      responseData ={'message':'Successful redemption','data':receiptno,'status':True}
                      return HttpResponse(json.dumps(responseData), content_type="application/json")
                   else:
                    responseData ={'message':'insufficent balance','status':False}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                else:
                    responseData ={'message':'insufficent balance','status':False}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData ={'message':'serviceID cannot be found','status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")

class MerchantCustomerPointsView(APIView):
    def get(self, request, format=None):     
        """Save the post data when creating a new merchant."""
        try:       
            serviceid=request.GET.get('serviceid')
            customerphone=request.GET.get('phone')
            checkserviceid= checkServiceId(serviceid)      
            if checkserviceid:
                merchID=checkserviceid['id']
                custID=customer.objects.filter(merchID=merchID).filter(customerIdentifier=customerphone).values('id').first()
                if custID is None:
                   responseData ={'message':'user does not exist','status':False}
                   return HttpResponse(json.dumps(responseData), content_type="application/json")     
                else:
                    assignedvalue=loyaltytransaction.objects.filter(merchID=merchID).filter(CustID=custID['id']).aggregate(Sum('assignedpoint'))
                    print(assignedvalue)
                    redeemedpoint=loyaltytransaction.objects.filter(merchID=merchID).filter(CustID=custID['id']).aggregate(Sum('redeemedpoint'))
                    print(redeemedpoint)
                    if assignedvalue['assignedpoint__sum'] is None:
                        currentvalue = 0.00
                    else:
                        currentvalue=assignedvalue['assignedpoint__sum'] - redeemedpoint['redeemedpoint__sum']
                    responseData ={'data':round(currentvalue),'status':True}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData ={'message':'serviceID cannot be found','status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")


class MerchantCustomerGiftcardView(APIView):
    def post(self, request, format=None):
        """Save the post data when creating a new merchant."""
        try:
            serviceid = request.data['serviceid']
            customerphone = request.data['phonenumber']
            serialnumber = request.data['serialnumber']
            amount = request.data['amount']
            checkserviceid = checkServiceId(serviceid)
            if checkserviceid:
                merchID = checkserviceid['id']
                ref = generateReferenceNumber(merchID)
                giftcardserialnumber = giftCard.objects.filter(merchID=merchID).filter(serialnumber=serialnumber).values('id', 'amount', 'serialnumber', 'recipient_email', 'expiration_date').first()
                todaydate = datetime.datetime.now().date()   
                #if giftcardserialnumber['expiration_date'] > todaydate:
                if giftcardserialnumber is None:
                    responseData = {
                        'message': 'Invalid serial number', 'status': False}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                '''    
                custID = giftCard.objects.filter(merchID=merchID).filter(
                    recipient_phone=customerphone).values('recipient_phone').first()
                if custID is None:
                    responseData = {
                        'message': 'Invalid phone number', 'status': False}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
              
                else:
                '''
                remainingvalue = giftcardtransaction.objects.filter(merchID=merchID).filter(
                    giftID=giftcardserialnumber['id']).aggregate(Sum('redeemedamount'))
                #get the remaininging giftcard value
                purchasevalue = giftcardserialnumber['amount']
                currentvalue = purchasevalue-remainingvalue['redeemedamount__sum']
                #get the balance giftcard value
                print(purchasevalue)
                print(currentvalue)
                if currentvalue >= float(amount) and float(amount)!=0:
                    gt = giftcardtransaction(
                        giftID_id=giftcardserialnumber['id'], redeemedamount=amount, merchID_id=merchID,reference=ref)
                    gt.save() #capture the gift transaction
                    notify = Notification()
                    remainingvalue = giftcardtransaction.objects.filter(merchID=merchID).filter(
                        giftID=giftcardserialnumber['id']).aggregate(Sum('redeemedamount'))
                    currentvalue = purchasevalue - remainingvalue['redeemedamount__sum']
                    firstname = 'customer'
                    randomnumber = request.data['serialnumber']
                    emailaddress = giftcardserialnumber['recipient_email']
                    subject = 'Gift Card Transaction'
                    template_name = 'voucher_transaction.html'
                    merchantname = merchant.objects.filter(id=merchID).values(
                        'businessname', 'businesslogo').first()
                    notify.emailNotificationRedeemGiftcard(firstname,randomnumber,emailaddress,subject,template_name,merchantname,currentvalue,purchasevalue)
                else:
                    responseData ={'message':'Insufficent amount','status':False}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData = {
                    'message': 'serviceID cannot be found', 'status': False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData = {'message': 'An error occur' +
                                str(e), 'status': False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'message':'Transaction capture','data':ref,'status':True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
      
class MerchantGiftcard(APIView):
        def post(self, request, format=None):
            """Save the post data when creating a new merchant."""
            try:
                serviceid = request.data['serviceid']
                customerphone = request.data['customerphone']
                serialnumber = request.data['serialnumber']
                amount = request.data['amount']
                customeremail = request.data['customeremail']
                reference =request.data['reference']
                checkserviceid = checkServiceId(serviceid)
                if checkserviceid:
                    merchID = checkserviceid['id']
                    giftcardrecord = giftCard.objects.filter(merchID=merchID).filter(
                        serialnumber=serialnumber).values('id', 'amount', 'serialnumber', 'recipient_phone', 'recipient_email').first()
                    if giftcardrecord:
                        print(giftcardrecord)
                        if not (giftcardrecord['recipient_phone']):
                            """ Check to confim if the gift card has not be purchased """
                            if giftcardrecord['amount'] == float(request.data['amount']):
                                """ Check to confim if gift card has not be purchase """
                                gt = giftcardtransaction(
                                    giftID_id=giftcardrecord['id'], purchaseamount=amount, merchID_id=merchID,reference=reference)
                                gt.save()
                                giftcard = giftCard.objects.get(
                                    id=giftcardrecord['id'])
                                giftcard.recipient_phone = customerphone
                                giftcard.recipient_email = customeremail
                                # assign the gift card to the owner
                                giftcard.save(
                                    update_fields=['recipient_phone', 'recipient_email'])
                                notify = Notification()
                                merchantname = merchant.objects.filter(id=merchID).values(
                                    'businessname', 'businesslogo').first()
                                firstname = 'customer'
                                randomnumber = serialnumber
                                emailaddress = customeremail
                                subject = 'Voucher Details'
                                template_name = 'voucher_details.html'
                                others = amount
                                notify.emailNotification(
                                    firstname, randomnumber, emailaddress, subject, template_name, others, merchantname)
                                responseData  = {'message': 'Transaction capture', 'status': True}
                                return HttpResponse(json.dumps(responseData), content_type="application/json")
                            else:
                                responseData = {
                                    'message': 'amount does not match', 'status': False}
                        else:
                            responseData = {
                             'message': 'The voucher has been bought by another customer', 'status': False}                                                           
                    else:
                        responseData = {
                            'message': 'Invalid serial number', 'status': False}                 
                else:
                    responseData = {
                        'message': 'serviceID cannot be found', 'status': False}
            except Exception as e:
                    responseData = {'message': 'An error occur' +
                                    str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

        def get(self, request, format=None):
            serviceid = request.GET.get('serviceid')
            todaydate = datetime.datetime.now().date()
            merchID= merchant.objects.filter(serviceID=serviceid).values('id').first()
            if merchID:
               giftcardrecords=list(giftCard.objects.filter(merchID=merchID['id']).filter(recipient_phone__isnull=True).values('id', 'amount', 'serialnumber', 'recipient_email', 'cardname', 'expiration_date', 'recipient_phone'))
               for giftcardrecord in giftcardrecords:
                        giftcardrecord['amount'] = float(giftcardrecord['amount'])
                        giftcardrecord['expiration_date'] = str(giftcardrecord['expiration_date'])
               responseData = {'data': giftcardrecords, 'status': True}
            else:
                responseData = {'data':[], 'status': True} 
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        
def checkServiceId(serviceid):
    serivcerecord = merchant.objects.filter(serviceID=serviceid).values('id').first()
    print(serivcerecord)
    if serivcerecord:
       return serivcerecord
    else:
        return False


def duplicateMetroCustomer(customerphonenumber,serviceid):
     if serviceid == '351817683':
        customerecord = loyaltyCustomer.objects.filter(
            CardNumber=customerphonenumber).values('CardNumber')
        if not customerecord:
            return True
        else:
            return False
     else:
        return True
