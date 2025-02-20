from django.shortcuts import render
import random
from django.template.defaulttags import csrf_token
from django.core.exceptions import ObjectDoesNotExist
from .models import *
import requests
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from django.http import Http404
from rest_framework.response import Response
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from .serializers import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.conf import settings
from django.shortcuts import redirect
import logging
from .logger import *
import base64
import json
from django.core.files.base import ContentFile
from rest_framework.permissions import IsAuthenticated
from django.views import View
from django.utils import timezone
import datetime

# Create your views here.
# View to create a merchant and save in the database.
class merchantView(APIView):
    #permission_classes = (IsAuthenticated,)
    def post(self,request, format=None):
        try:       
            """Save the post data when creating a new merchant."""       
            serializer = merchantSerializer(data=request.data)
            merchantemailaddress=request.data['merchantemailaddress']
            serviceID =randomId()
            checkemaildup = duplicateEmails(merchantemailaddress)
            if checkemaildup is False:
                if serializer.is_valid():
                    passwd = make_password(request.data['merchantpassword'],salt=None,hasher='default')
                    img_data =  base64.b64decode(request.data['businesslogo'])
                    imgext = request.data['businessname']
                    recipientemail = request.data['merchantemailaddress']
                    businessdescription=request.data['businessdescription']
                    country = request.data['country']
                    processedimage = receiveImage(img_data,imgext)
                    serializer.save(serviceID=serviceID,merchantpassword=passwd,businesslogo=processedimage)
                    emailactivation(recipientemail,imgext,request)
                    merchid = merchant.objects.values('id').last()
                    walexServiceDetails(imgext,serviceID,businessdescription,request,merchid,country)
                    responseData ={'message':'The Merchant is registerated sucessfully,an email account activation link is sent to your registered email address',
                                'status':'True'}                           
                    covertJsonString(responseData)         
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            responseData={'message':'The duplicate merchant emailaddresses','status':'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
               responseData ={'message':'An error occur'+str(e),'status':'False'}
               return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'data':dictList,'status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
    
    def get(self,request, format=None):
        status=request.GET.get('status')
        queryset = merchant.objects.all()
        merchantrecord = queryset.filter(active=status).values('id','serviceID','merchantphonenumber', 'businessaddress','merchantemailaddress','active','contactpersonfirstname','contactpersonlastname','businesslogo')
        return JsonResponse({'data': list(merchantrecord),'status':'True'})         
        
'''Class to grant access to an authenticated Merchant '''
class merchantLoginView(APIView):
    #permission_classes =(IsAuthenticated,)  
    def get(self,request, format=None):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        #password = self.request.query_params.get('password')
        password=request.GET.get('password')
        #username= self.request.query_params.get('username')
        username=request.GET.get('username')
        queryset = merchant.objects.all()
        tokengenerator = tokenGenerator()
        token= tokengenerator['access']
        checkactivemerchant = queryset.filter(merchantemailaddress=username).filter(active=True)
        if  checkactivemerchant:
            resultset = queryset.filter(merchantemailaddress=username).filter(active=True).values('id','serviceID','businessname','merchantphonenumber', 'businessaddress','merchantemailaddress','active','contactpersonfirstname','contactpersonlastname','contactpersonphone','businesslogo','settingsactivated','accountnumber','accountname','bankname','currency') 
            if username is not None:           
                passwordvalue =list(queryset.filter(merchantemailaddress=username).values_list('merchantpassword',flat=True))
                if  passwordvalue:            
                    b=passwordvalue[0]          
                    passwordconfirm=check_password(password,b)
                    if passwordconfirm is True:                              
                       return JsonResponse({'data': list(resultset),'token':token,'status':'True'})
                    else:
                        resultset =[]
                        return JsonResponse({'data': list(resultset),'status':'False','Message':'Invalid password'})
            resultset =[]
            return JsonResponse({'data': list(resultset),'status':'False','Message':'Invalid username'})
        else:
            resultset =[]
            return JsonResponse({'data': list(resultset),'status':'False','Message':'Account is inactive'})

class createMerchantSettings(APIView):
    permission_classes =(IsAuthenticated,) 
    def post(self, request, format=None):
        merchantid = request.data['merchantid']
        #businessdescription = request.data['businessdescription']
        businessfacebook = request.data['businessfacebook']
        businesstwitter= request.data['businesstwitter']
        bankname =request.data['bankname']
        accountnumber= request.data['accountnumber']
        accountname = request.data['accountname']
        #contactpersonphone = request.data['contactpersonphone']
        try:
             # try something
            merchantupdate = merchant.objects.get(id=merchantid)
            merchantupdate.businessfacebook = businessfacebook
            merchantupdate.businesstwitter = businesstwitter
            merchantupdate.bankname = bankname
            merchantupdate.accountnumber = accountnumber
            merchantupdate.accountname = accountname
            merchantupdate.settingsactivated= True
            merchantupdate.save(update_fields=['businessfacebook','businesstwitter','bankname','accountnumber','accountname','settingsactivated'])
            responseData ={'message':'The record is updated','status':'True'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except ObjectDoesNotExist:
                # do something
              responseData ={'message':'The record is missing','status':'False'}
              return HttpResponse(json.dumps(responseData), content_type="application/json")               

class merchantChangePassword(APIView):
    def post(self,request,format=None):
        merchantid = request.data['merchantid']
        todaydate =datetime.date.today()
        try:
            merchantupdate = merchant.objects.get(id=merchantid)       
            merchantupdate.merchantpassword= make_password(request.data['merchantpassword'],salt=None,hasher='default')
            merchantupdate.updateddate=todaydate
            merchantupdate.save(update_fields=['merchantpassword','updateddate'])
            responseData ={'message':'The record is updated','status':'True'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except ObjectDoesNotExist:
            responseData ={'message':'The record missing','status':'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

        return
class editMerchantRecord(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        merchantid = request.data['merchantid']
        todaydate =datetime.date.today()
        img_data =  base64.b64decode(request.data['businesslogo'])
        imgext = request.data['serviceID']
        processedimage = receiveImage(img_data,imgext)
        try:
            merchantupdate = merchant.objects.get(id=merchantid)
            merchantupdate.merchantphonenumber = request.data['merchantphonenumber']
            merchantupdate.businessaddress = request.data['businessaddress']
            merchantupdate.merchantemailaddress = request.data['merchantemailaddress']
            #merchantupdate.merchantpassword= make_password(request.data['merchantpassword'],salt=None,hasher='default')
            merchantupdate.contactpersonfirstname =request.data['contactpersonfirstname']
            merchantupdate.contactpersonlastname= request.data['contactpersonlastname']
            merchantupdate.contactpersonphone= request.data['contactpersonphone']
            merchantupdate.businesslogo = request.data['businesslogo']
            merchantupdate.bankname = request.data['bankname']
            merchantupdate.accountnumber = request.data['accountnumber']
            merchantupdate.accountname = request.data['accountname']
            merchantupdate.updateddate=todaydate
            merchantupdate.save(update_fields=['merchantphonenumber','businessaddress','merchantemailaddress','contactpersonfirstname','contactpersonlastname','contactpersonphone','businesslogo','bankname','accountnumber','accountname','updateddate'])
            responseData ={'message':'The record is updated','status':'True'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except ObjectDoesNotExist:
            responseData ={'message':'The record missing','status':'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

class recoverMerchantPassword(APIView):
    def post(self, request, format=None): 
        emailaddress = request.data['emailaddress']
        passwordRecoveryEmail(emailaddress,request)
        responseData ={'message':'Please check your email','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
        
class passwordRecovery(APIView):
    def post(self, request, format=None):                           
        userid = request.data['userid']
        uid = force_text(urlsafe_base64_decode(userid))      
        try:
            user = merchant.objects.get(merchantemailaddress=uid)            
            password =make_password(request.data['password'],salt=None,hasher='default')
            user.merchantpassword = password
            user.save()
            responseData ={
                'message':'Password changed',
                'status':'True'
            }
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except merchant.DoesNotExist: 
               user = None    
               responseData ={
                        'message':'The record cannot be found',
                        'status':'False'
                }
               return HttpResponse(json.dumps(responseData), content_type="application/json")

class themeColorsDetails(APIView):
    #permission_classes = (IsAuthenticated,)
    def get_object(self,pk,format=None):
        try:
            return merchant.objects.get(pk=pk)
        except merchant.DoesNotExist:
            raise Http404

    def get(self, request,pk, format=None):
        merchantthemecolor = self.get_object(pk)
        serializer = themeColorSerializer(merchantthemecolor)
        responseData ={'status':'True','data':serializer.data}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
        #return Response(serializer.data)

    def put(self, request, pk, format=None):
        merchantthemecolor = self.get_object(pk)
        serializer = themeColorSerializer(merchantthemecolor, data=request.data)
        if serializer.is_valid():
            serializer.save()
            responseData={'status':'True','data':serializer.data,'message':'record updated'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        merchantthemecolor = self.get_object(pk)
        merchantthemecolor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

def walexServiceDetails(imgext,serviceID,businessdescription,request,merchid,country):
    headers = {'content-type': "application/json"}
    #params ={"username":"wajesmart","password":"Admin$1234"}
    print(merchid)
    activate_url = "{0}://{1}/{2}/{3}/?{4}={5}".format(request.scheme, request.get_host(),'API','listmerchantcustomer','merchID',merchid['id'])
    print(activate_url)
    params={"title":serviceID,"description":imgext,"service_type":businessdescription,"country":country,"is_opened":'True',"api_url":activate_url}
    r = requests.post('http://199.192.22.132/service/', data=params)
    record = r.json()
    print(record)
    return
    
def randomId():
    for x in range(10):
        randomnumber = str(random.randint(1,10000000001)) 
        confirmrandomnumber = merchant.objects.filter(serviceID=randomnumber).values('serviceID')
        ''' check for empty queryset 
        while confirmrandomnumber:
           print("working2")
           randomnumber = random.randint(1,100000001)
           confirmrandomnumber = merchant.objects.filter(serviceID=randomnumber).values('serviceID')
        else:
            return confirmrandomnumber '''
        if not confirmrandomnumber:
            return randomnumber
        else:
            randomnumber = str(random.randint(1,10000001)) 
            confirmrandomnumber = merchant.objects.filter(serviceID=randomnumber).values('serviceID')
            return randomnumber 

''' account verifiction function '''
def activate_user_account(request,uidb64=None):            
        try:           
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = merchant.objects.get(merchantemailaddress=uid)
        except user.DoesNotExist:
            user = None
            responseData ={
                'message':'merchant not found',
                'status':'False'
            }
            return HttpResponse(json.dumps(responseData), content_type="application/json")                  
        if user :
            user.active = True
            user.save()
            url = settings.APP_URL
            fullurl="{0}:/#/activate".format(url)
            responseData ={
                'message':'The Merchant is now activated',
                'status':'True'
            }
            #return HttpResponse(json.dumps(responseData), content_type="application/json")
            return redirect(fullurl)
        else:
            responseData ={
                'message':'Activation link has expired',
                'status':'False'
            }
            return HttpResponse(json.dumps(responseData), content_type="application/json")
            
'''function to convert json key to string value '''
def covertJsonString(responseData):
    for key in responseData.keys():
        if type(key) is not str:
            try:
              responseData[str(key)] = responseData[key]
            except:
             try:
                responseData[repr(key)] = responseData[key]
             except:
                pass
            del responseData[key]
            return responseData[key]

'''function to check for duplicate email '''
def duplicateEmails(merchantemailaddress):
    logger=get_logger('merchant record')
    email = merchant.objects.filter(merchantemailaddress=merchantemailaddress)
    if not email:
      return False
    else:
        return True
def tokenGenerator():
    headers = {'content-type': "application/json"}
    params ={"username":"wajesmart","password":"Admin$1234"}
    url = settings.APP_URL
    fullurl="{0}:/API/api/token/".format(url)
    r = requests.post(fullurl, data=params,verify=False)
    record = r.json()
    print(record)
    return record

''' function to check for duplicate merchant name '''
def duplicateServiceID(serviceID):
    logger=get_logger('merchant record')
    serviceID = merchant.objects.filter(serviceID=serviceID)
    print("working1")
    print(serviceID)
    if not serviceID:
      return False
    else:
        return True
        
'''function to process images'''
def receiveImage(img_data,imgext):
    save_path = os.path.join(settings.BASE_DIR,'merchantlogo',imgext+'.png')
    databasepath= '/merchantlogo/'+imgext+'.png'
    with open(save_path, "wb") as fh:
          fh.write(img_data)
    return databasepath

def emailactivation(recipientemail,imgext,request):
    subject = 'Account Activation'
    template_name='acc_active_email.html'
    from_email = settings.DEFAULT_FROM_EMAIL
    '''context = {
               'user':request.data['firstname'],
               'username':request.data['username'],
               'password':request.data['password']
              }
    '''  
    kwargs = {"uidb64":urlsafe_base64_encode(force_bytes(recipientemail)).decode()}
    print(kwargs)
    text_content={}
    activation_url = reverse("activate_user_account", kwargs=kwargs) 
    activate_url = "{0}://{1}{2}".format(request.scheme, request.get_host(), activation_url)
    context = {'user':imgext,'activate_url': activate_url}
    html_content = render_to_string(template_name, context)
    email = EmailMultiAlternatives(subject,text_content,from_email,[recipientemail])
    email.attach_alternative(html_content, "text/html")
    email.send()

def passwordRecoveryEmail(emailaddress,request):
    subject = 'Password Recovery'
    template_name='password_recovery.html'
    from_email = settings.DEFAULT_FROM_EMAIL  
    kwargs = {"uidb64":urlsafe_base64_encode(force_bytes(emailaddress)).decode()}
    text_content={}
    #activation_url = reverse("password_recovery", kwargs=kwargs)
    #activation_url = reverse(kwargs=kwargs) 
    activate_url = "{0}://{1}/#/{2}/{3}".format(request.scheme, request.get_host(),'passwordrecovery',urlsafe_base64_encode(force_bytes(emailaddress)).decode())
    print(activate_url)
    context = {'activate_url': activate_url}
    html_content = render_to_string(template_name, context)
    email = EmailMultiAlternatives(subject,text_content,from_email,[emailaddress])
    email.attach_alternative(html_content, "text/html")
    email.send()

def ValuesQuerySetToDict(vqs):
    return [item for item in vqs]





    
