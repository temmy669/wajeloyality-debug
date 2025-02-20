from django.shortcuts import render
from .models import *
import random
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
from django.forms.models import model_to_dict
import logging
from .logger import *
import base64
import json
from  .loyalty import *
from rest_framework.permissions import IsAuthenticated
from django.views import View
from django.db.models import Sum
from django.utils import timezone
from decimal import *

''' Class to create merchant customers '''
class MerchantCustomerView(APIView):
    #permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):     
        """Save the post data when creating a new merchant."""
        try:       
            serializer = merchantCustomerSerializer(data=request.data)
            customerphonenumber=request.data['customerIdentifier']
            merchID=request.data['merchID']
            checkcustomerphonedup= duplicateCustomerID(customerphonenumber,merchID)
            if checkcustomerphonedup:
                if serializer.is_valid():
                    serializer.save()
                    responseData ={
                        'message':'The customer record is created sucessfully',
                        'status':'True'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
            else:
                responseData ={
                'message':'The customer record cannot be created because of duplicate phonenumber',
                'status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
    
    def get(self,request, format=None): 
        c=merchantCustomerRedemptionView().get(request) 
        merchID=request.GET.get('merchID')
        merchantcustomerrecord = customer.objects.filter(merchID=merchID).values(
            'id', 'firstname', 'lastname', 'emailaddress', 'customerIdentifier', 'facebooklink', 'twitterlink', 'instagramlink', 'DOB', 'merchID').order_by('-createddate')
        args=(merchantcustomerrecord,None,None)
        customermergedrecord = customerMergeRecord(*args)
        return JsonResponse({'data':customermergedrecord,'redemptionstatus':c,'status':'True'})
    
    def put(self, request, format=None):
        customerid = request.data['customerid']
        todaydate = datetime.date.today()
        dob= request.data['DOB'] or None
        try:
            customerupdate = customer.objects.get(id=customerid)
            customerupdate.firstname = request.data['firstname']
            customerupdate.lastname = request.data['lastname']
            customerupdate.emailaddress = request.data['emailaddress']
            customerupdate.addressdetails= request.data['addressdetails']
            customerupdate.facebooklink =request.data['facebooklink']
            customerupdate.twitterlink= request.data['twitterlink']
            customerupdate.instagramlink = request.data['instagramlink']
            customerupdate.DOB =dob
            customerupdate.updateddate=todaydate
            customerupdate.save(update_fields=['firstname','lastname','emailaddress','addressdetails','facebooklink','twitterlink','instagramlink','DOB','updateddate'])
            responseData ={'message':'The record is updated','status':'True'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
    
class listCustomersPoint(APIView):
    permission_classes =(IsAuthenticated,) 
    def get(self,request, format=None):
        merchID=request.GET.get('merchID')
        startDate =request.GET.get('startDate')
        endDate =request.GET.get('endDate')
        merchantcustomerrecord =customer.objects.filter(merchID=merchID).values('id','firstname','lastname','emailaddress','customerIdentifier','facebooklink','twitterlink','instagramlink','DOB','merchID')
        args=(merchantcustomerrecord,startDate,endDate)
        customermergedrecord = customerMergeRecord(*args)       
        return JsonResponse({'data':customermergedrecord,'status':'True'})

class merchantCustomerRedemptionView(APIView):
    def get(self,request,format=None):
        #customerIdentifier=request.data['customerIdentifier']
        customerIdentifier=request.GET.get('customerIdentifier')
        serviceID =request.GET.get('serviceID')
        merchID=request.GET.get('merchID')
        reference=request.GET.get('reference')
        description=request.GET.get('description')
        CustID= list(customer.objects.filter(customerIdentifier=customerIdentifier).filter(merchID=merchID).values('id'))
        amount = request.GET.get('amount') 
        if amount is not None:
            amount = float(amount)
            rate= list(merchant.objects.filter(id=merchID).values('rate'))
            try:
                ratevalue = float(rate[0]['rate'])
                CustIDs= CustID[0]['id']
            except IndexError:
                ratevalue =0
                CustIDs = ''    
            if  ratevalue != 0:
                deductpoint = amount/ratevalue
                receiptno = generateReceiptNo(merchID)
                l=loyaltytransaction(CustID_id=CustIDs,merchID_id=merchID,redeemedpoint=deductpoint,transactiondate=timezone.now(),receiptno=reference,description=description)
                l.save()
                data={"serviceID":serviceID,"customerIdentifier":customerIdentifier}
                responseData ={
                        'message':'The points has being deducted',
                        'data':data,
                        'status':'True'}
                return 'resetpoint'
            else:
                data={"amount":"0","serviceID":serviceID,"customerIdentifier":customerIdentifier}
                responseData ={
                        'message':'There is no points to be deducted',
                        'data':data,
                        'status':'False'}
                return  'noresetpoint'
            return HttpResponse(None)
        else:      
            return   'noresetpoint'

class merchantCustomerUpload(APIView):
    def post(self,request,format=None):
        csv_file = request.FILES["csv_file"]
        merchID=request.data["merchID"]
        if csv_file.multiple_chunks() is False:
          file_data = csv_file.read().decode("utf-8")
          lines = file_data.split("\n")
		  #loop over the lines and save them in db. If error , store as string and then display
          for counter,line in enumerate(lines):
              length = len(lines)
              #if length > counter:						
                 #fields = file_data.split(",")
                 #print(fields)
                 #data_dict = {} 
                 #data_dict["firstname"]=fields[0]
                 #print(data_dict["firstname"])      			
          return JsonResponse({'status':'True'}) 
        else:
            return JsonResponse({'status':'False'})

class redeemCustomerPoint(APIView):
    def post(self,request,format=None):
        try: 
            try:
                customerecord=customer.objects.filter(customerIdentifier=request.data['identifier']).filter(merchID=request.data['merchID']).values('customerIdentifier','id').first()
            except TypeError:
                customerecord = None                 
            if not(customerecord is None):
                try:
                    verifytransactionpin=customer.objects.filter(transactionpin=request.data['secret']).filter(merchID=request.data['merchID']).values('transactionpin').first()
                except TypeError:
                        verifytransactionpin = None 
                if not(verifytransactionpin is None):
                    merchID=request.data['merchID']
                    receiptno = generateReceiptNo(merchID)
                    assignedvalue=loyaltytransaction.objects.filter(merchID=merchID).filter(CustID=customerecord['id']).aggregate(Sum('assignedpoint'))
                    redeemedpoint=loyaltytransaction.objects.filter(merchID=merchID).filter(CustID=customerecord['id']).aggregate(Sum('redeemedpoint'))
                    currentvalue=assignedvalue['assignedpoint__sum'] -redeemedpoint['redeemedpoint__sum']
                    amountredeem=request.data['amount']
                    if currentvalue > Decimal(amountredeem):
                        l=loyaltytransaction(CustID_id=customerecord['id'],merchID_id=request.data['merchID'],redeemedpoint=request.data['amount'],transactiondate=timezone.now(),receiptno=receiptno,description=request.data['description'])
                        l.save()
                    else:
                        responseData ={'message':'insufficent balance','status':'False'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                else:
                 responseData ={'message':'The transaction pin deos not match','status':'False'}
                 return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                 responseData ={'message':'The customer record does not exist','status':'False'}
                 return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
               responseData ={'message':'An error occur'+str(e),'status':'False'}
               return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'message':'Successful redeemption ','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
 
def customerMergeRecord(*args):
    #list_merchantcustomerrecord = [entry for entry in merchantcustomerrecord]
    element =[]
    dictList = []
    serviceID ={}
    for counter,element in enumerate(args[0]):
        length = len(args[0])
        if length > counter:
           if args[1] and args[2] is not None:
                formattedstartdate = dateFormat(args[1])
                formattedendate= dateFormat(args[2]) 
                totalamount = loyaltytransaction.objects.filter(CustID=element['id']).aggregate(Sum('transactionamount'))
                assignedpoint=loyaltytransaction.objects.filter(CustID=element['id']).filter(transactiondate__gte=formattedstartdate).filter(transactiondate__lte=formattedendate).aggregate(Sum('assignedpoint'))
                redeempoint=loyaltytransaction.objects.filter(CustID=element['id']).filter(transactiondate__gte=formattedstartdate).filter(transactiondate__lte=formattedendate).aggregate(Sum('redeemedpoint'))
                if assignedpoint['assignedpoint__sum'] is not None:        
                   serviceID =list(merchant.objects.filter(id=element['merchID']).values('serviceID','rate'))
                   pointbalance=assignedpoint['assignedpoint__sum']-redeempoint['redeemedpoint__sum']
                   assignedpoint['points']=assignedpoint.pop('assignedpoint__sum')
                   assignedpoint['points'] = pointbalance
                   totalamount['totalamount']=totalamount.pop('transactionamount__sum')          
                   element.update(assignedpoint)
                   element.update(totalamount)
                   element.update(serviceID[0])
                   dictList.append(element)
           else:
                assignedpoint=loyaltytransaction.objects.filter(CustID=element['id']).aggregate(Sum('assignedpoint'))
                totalamount = loyaltytransaction.objects.filter(CustID=element['id']).aggregate(Sum('transactionamount'))
                redeempoint=loyaltytransaction.objects.filter(CustID=element['id']).aggregate(Sum('redeemedpoint'))
                if redeempoint['redeemedpoint__sum'] is None:
                    redeempoint={'redeemedpoint__sum':0.00} 
                if assignedpoint['assignedpoint__sum'] is None:
                    assignedpoint = {'assignedpoint__sum':0.00}
                    totalamount ={'transactionamount__sum':0.00}        
                serviceID =list(merchant.objects.filter(id=element['merchID']).values('serviceID','rate'))
                pointbalance=assignedpoint['assignedpoint__sum']-redeempoint['redeemedpoint__sum']
                assignedpoint['points']=assignedpoint.pop('assignedpoint__sum')
                assignedpoint['points'] = pointbalance
                totalamount['totalamount']=totalamount.pop('transactionamount__sum')
                element.update(assignedpoint)
                element.update(totalamount)
                element.update(serviceID[0])
                dictList.append(element)
    return dictList


def duplicateCustomerID(customerphonenumber, merchID):
    phonenumber = customer.objects.filter(customerIdentifier=customerphonenumber).filter(merchID=merchID)
    if not phonenumber:
       return True
    else:
        return False

def ValuesQuerySetToDict(vqs):
    return [item for item in vqs]

def generateReceiptNo(merchID):
    transactiontime = timezone.now()
    finaltransactiontime=timezone.localtime(transactiontime).strftime('%H:%M:%S')
    random_values = str(random.randint(1,10000000000000001))+finaltransactiontime
    refno =loyaltytransaction.objects.filter(receiptno=random_values).filter(merchID=merchID).values('receiptno').first()
    while(refno != None):
        random_values = str(random.randint(1,10000000000000001))+finaltransactiontime
        refno =loyaltytransaction.objects.filter(receiptno=random_values).filter(merchID=merchID).values('receiptno').first()
    return random_values
    
