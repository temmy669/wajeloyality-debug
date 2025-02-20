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
import json
import xmltodict
from rest_framework.permissions import IsAuthenticated
from django.views import View
import datetime
from dateutil.parser import parse

class merchantLoyaltyRuleView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        try:
            serializer = merchantLoyaltyRuleSerializer(data=request.data)
            rulename=request.data['loyaltyrule']
            checkloyaltyrulenamedup= duplicateLoyaltyRuleName(rulename)
            if checkloyaltyrulenamedup is True:
                if serializer.is_valid():
                    serializer.save()
                    responseData ={
                        'message':'The loyalty rule record is created sucessfully',
                        'status':'True'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
            else:
                responseData ={
                'message':'The loyalty record cannot be created because of duplicate rulename',
                'status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData ={'message':'An error occur'+str(e),'status':'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json") 
    def get(self,request, format=None):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        #password = self.request.query_params.get('password')
        merchID=request.GET.get('merchID')
        queryset = loyaltyrule.objects.all()
        todaydate =datetime.datetime.now().date()
        resultset = queryset.filter(merchID=merchID).filter(endate__gte=todaydate).values('id','loyaltyrule','rewardpoint','amountspent','status','endate')
        return JsonResponse({'data': list(resultset),'status':'True'})

class merchantLoyaltyTransactionView(APIView):
    #permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        try:
            loyaltyruleID = int(request.data['loyaltyruleID'])
            transactionamount = request.data['transactionamount']
            assignpoint = postAssignedPoint(loyaltyruleID,transactionamount)
            custID = request.data['CustID']
            merchID= request.data['merchID']
            receiptno =request.data['receiptno']
            dupreciptcheck=checkForDupReceipt(receiptno,merchID)
            if dupreciptcheck is True:
                loyaltytransactionrecord =loyaltytransaction(loyaltyruleID_id=loyaltyruleID,CustID_id=custID,merchID_id=merchID,transactionamount=transactionamount,assignedpoint=assignpoint,transactiondate=request.data['transactiondate'],receiptno=receiptno)
                loyaltytransactionrecord.save()
                responseData ={
                            'message':'The loyalty transaction record is created sucessfully',
                            'status':'True'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData ={
                            'message':'Duplicate Reciept',
                            'status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData ={'message':'An error occur'+str(e),'status':'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json") 
    
    def get(self,request, format=None):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        #password = self.request.query_params.get('password')
        merchID=request.GET.get('merchID')
        startDate =request.GET.get('startDate')
        endDate =request.GET.get('endDate')
        formattedstartdate = dateFormat(startDate)
        formattedendate= dateFormat(endDate)
        queryset = loyaltytransaction.objects.filter(merchID=merchID).filter(transactiondate__gte=formattedstartdate).filter(transactiondate__lte=formattedendate).values('CustID','merchID','receiptno','transactionamount','assignedpoint','transactiondate')
        finalrecord=customerInfoMarch(queryset)
        #resultset = queryset.filter(merchID=merchID).filter(endate__gte=todaydate).values('id','loyaltyrule','status','endate')
        return JsonResponse({'data': list(finalrecord),'status':'True'})
 
"""
service to get external  loyalty transactions from merchant through third party API
"""
def customerLoyaltyTransaction(format=None):
        headers = {'content-type': "text/xml"}
        """activate_url = "{0}://{1}/{2}/{3}/?{4}={5}".format(request.scheme, request.get_host(),'API','listmerchantcustomer','merchID',merchid['id'])"""
        activate_url='http://metropos.biz/MSQ.asmx/GETROYALTYTRANSACTIONSjson'
        """params={"title":serviceID,"description":imgext,"service_type":businessdescription,"country":country,"is_opened":'True',"api_url":activate_url}"""
        r = requests.get(activate_url,headers)
        try:
            if r.ok: 
                #print(r.text)         
                r = xmltodict.parse(r.text)['string']['#text']
                try:
                    r=ast.literal_eval(r) 
                    for counter, element in enumerate(r['admintable']):
                        logger=get_logger(element['SERVICEID'])                        
                        logger.info("{0}{1}{2}".format("Starting loyalty migration for"," ",element['TEL']))
                        serviceID=element['SERVICEID']
                        cardnumber=element['CARDNUMBER']             
                        transactionamount= element['AMOUNT']
                        customerphonenumber= element['TEL']
                        receiptno =element['INVOICENUMBER']
                        transactiondate=element['DATE']
                        customername=element['CUSTOMERNAME']
                        customeremailaddress= element['ADDRESS']
                        branchname= element['BRANCH']
                        merchID =checkForServiceID(serviceID)
                        if merchID  is not False:
                            args=(cardnumber,merchID['id'],transactionamount,customerphonenumber,receiptno,transactiondate,customername,customeremailaddress,branchname,serviceID)
                            loyaltyruleid = loyaltyrule.objects.filter(merchID=args[1]).values('id').first()
                            customerID = getCustomerRecord(*args)
                            checkduptransaction=checkDuplicateTransaction(*args)
                            getRedemptionTransaction(loyaltyruleid,*args)                    
                            if customerID is None:
                                customerID =saveCustomerRecord(*args)
                                logger.info("{0}{1}{2}".format("Saving customer details for customerIdentity"," ",element['TEL']))
                            if checkduptransaction is None:     
                                try:
                                    loyaltyruleID=loyaltyruleid['id']
                                    transactionamount=args[2]
                                    transactiondate=args[5]
                                    formatteddate = parse(transactiondate)
                                    transactionref=args[8]+args[4]
                                    assignedpoint=postAssignedPoint(loyaltyruleID,transactionamount)
                                    saveVoucherRecord(assignedpoint,*args)                
                                    Loyalitytransaction=loyaltytransaction(loyaltyruleID_id=loyaltyruleID,CustID_id=customerID['id'],merchID_id=args[1],receiptno=transactionref,transactionamount=transactionamount,assignedpoint=assignedpoint,transactiondate=formatteddate,description='metropos customer transaction')
                                    logger.info("{0}{1}{2}".format("Saving loyalty transaction for customerIdentity"," ",element['TEL']))       
                                    Loyalitytransaction.save()     
                                except TypeError as e:
                                    logger.info("oooops no loyalty rule was created"+str(e))
                            logger.info("{0}{1}{2}".format("ending loyalty migration for customerIdentity"," ",element['TEL']))
                            continue 
                        logger.info("No merchant id")
                        break 
                except Exception as e:
                    logger.info("The key error"+str(e))           
        except (ConnectionError,requests.exceptions.TooManyRedirects,requests.Timeout, requests.exceptions.HTTPError,requests.exceptions.ConnectTimeout) as e:              
            logger.info("The key error"+str(e)) 
            logger.info("The migration has ended")
        return HttpResponse(None)

def checkDuplicateTransaction(*args):
    transactionref=args[8]+args[4]
    transactionrecord =loyaltytransaction.objects.filter(merchID=args[1]).filter(receiptno=transactionref)
    if  transactionrecord:
       return True

def order3D2dict(input_ordered_dict):
    return loads(dumps(input_ordered_dict))
     
def saveCustomerRecord(*args):
    data = args[6].split(" ")
    firstname= data[0]
    lastname=data[1]
    emailaddress=args[7].lower()
    randomnumber= randomGenerate() 
    customerrecord =customer(transactionpin=randomnumber,firstname=firstname,lastname=lastname,emailaddress=emailaddress,customerIdentifier=args[3],merchID_id=args[1])
    customerrecord.save()
    notification=Notification(firstname,randomnumber,emailaddress)  
    custID= customer.objects.values('id').last()
    return custID
    

def randomGenerate():
    for x in range(4):
        return random.randint(1,10001)
   

def checkForServiceID(serviceID):
    checkserviceid = merchant.objects.filter(serviceID=serviceID).values('id').first()
    if not checkserviceid:
        return False
    else:
        return checkserviceid

def getCustomerRecord(*args):
    custID= customer.objects.filter(merchID=args[1]).filter(customerIdentifier=args[3]).values('id').first()
    if custID:
        return custID
    else:
        return None


def postAssignedPoint(loyaltyruleID,transactionamount):
    loyaltyruleresult = loyaltyrule.objects.filter(id=loyaltyruleID).values('id','rewardpoint','amountspent')
    list_loyaltyruleresult = [entry for entry in loyaltyruleresult] 
    amountspent= float(list_loyaltyruleresult[0]['amountspent'])
    loyaltypoint= int(list_loyaltyruleresult[0]['rewardpoint'])
    pointrewarded = (float(transactionamount)* loyaltypoint)/amountspent
    return pointrewarded

def duplicateLoyaltyRuleName(rulename):
    rulenamerecord = loyaltyrule.objects.filter(loyaltyrule=rulename) 
    if not rulenamerecord:
       return True
    else:
        return False

def checkForDupReceipt(receiptno,merchID):
    receiptrecord = loyaltytransaction.objects.filter(receiptno=receiptno).filter(merchID=merchID) 
    if not receiptrecord:
       return True
    else:
        return False

def expiredLoyaltyRule(resultset):
    list_result = [entry for entry in resultset]  # converts ValuesQuerySet into Python list
    expirydate =list_result[0]['endate']
    todaydate =datetime.datetime.now().date()
    if todaydate > expirydate:     
        return True
    else:
        return False

def dateFormat(unformatteddate):
    formatteddate= datetime.datetime.strptime(unformatteddate, "%d/%m/%Y").strftime("%Y-%m-%d")
    return formatteddate

def customerInfoMarch(queryset):
    element =[]
    dictList = []
    serviceID ={}
    for counter,element in enumerate(queryset):
        length = len(queryset)
        if length > counter:
           customerinfo=customer.objects.filter(id=element['CustID']).values('firstname','lastname','customerIdentifier','emailaddress').first()
           element.update(customerinfo)
           dictList.append(element)          
    return dictList

def Notification(firstname,randomnumber,emailaddress):
    subject ='Transaction Code'
    template_name='transaction_pin.html'
    recipientemail=emailaddress.lower()
    from_email = settings.DEFAULT_FROM_EMAIL
    context = {'user':firstname,'code': randomnumber}
    text_content={}
    html_content = render_to_string(template_name, context)
    email = EmailMultiAlternatives(subject,text_content,from_email,[recipientemail])
    email.attach_alternative(html_content, "text/html")
    email.send()

def Voucher(request):
    p = voucher(ID='08130639936',CUSTOMERCODE='08130639936',Amount='100',OtherInfo='245')
    p.save(using='loyalty')  # (statement 1) 
    return HttpResponse(None)

def saveVoucherRecord(assignedpoint,*args):
    customerid=args[3]
    merchantid=args[1]
    receiptno=args[4]
    customertransactionpin=list(customer.objects.filter(merchID=merchantid).filter(customerIdentifier=customerid).values('transactionpin'))
    customerecord =list(voucher.objects.using('loyalty').filter(ID=customerid).values('ID'))
    if  not customerecord:
        v = voucher(ID=str(customerid),CUSTOMERCODE=str(customerid),Amount=assignedpoint,OtherInfo=str(customertransactionpin[0]['transactionpin']))
        v.save(using='loyalty')   
    else:
        vt = vouchertransactions(ID=str(customerid),Invoicenumber=receiptno,Credit=assignedpoint,Debit='0.00',Particular='transaction')
        vt.save(using='loyalty')
    return HttpResponse(None)

def VoucherTransaction(request):
    p = vouchertransactions(ID='08130639935',Invoicenumber='1.00',Credit='00.00',Debit='100.00',Particular='transaction')
    p.save(using='loyalty')  # (statement 1) 
    return HttpResponse(None)

def getRedemptionTransaction(loyaltyruleid,*args):
    logger=get_logger(args[9])
    logger.info("{0}{1}{2}".format("Starting redemption migration for"," ",args[3]))
    record =list(listvouchertransactions.objects.using('loyalty').filter(Credit='00.00').values('ID','DateUsed','recno','Particular','Debit'))
    for counter,element in enumerate(record):
        length=len(record)
        if length >counter:
            todaydate =str(datetime.datetime.now().date())
            transactiondate= str(element['DateUsed']).split(" ")[0]
            merchID=args[1]
        if transactiondate == todaydate:
           receiptno='MetroPOSRedem'+'-'+str(element['recno'])
           description='Redeemption For'+'-'+element['ID']
           dupreceipt=checkForDupReceipt(receiptno,merchID)
           if dupreceipt is True:
            customerid=customer.objects.filter(customerIdentifier=element['ID']).values('id').first()     
            loyaltytransactionrecord =loyaltytransaction(loyaltyruleID_id=loyaltyruleid['id'],CustID_id=customerid['id'],merchID_id=merchID,redeemedpoint=element['Debit'],transactiondate=transactiondate,receiptno=receiptno,description=description)
            loyaltytransactionrecord.save()
        logger.info("{0}{1}{2}".format("ending redemption migration for"," ",args[3]))         
    return HttpResponse(None)
    
    

    

    
