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
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
import logging
from .logger import *
import base64
import json
from django.core.files.base import ContentFile
from .permissions import IsManager, IsAccountant, IsAuditor, IsMerchant
from rest_framework.permissions import IsAuthenticated
from django.views import View
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
import datetime
from .notification import Notification, htmltopdf
from drf_spectacular.utils import extend_schema
from django.db.models import F
# Create your views here.
# View to create a merchant and save in the database.

@extend_schema(tags=['Role'])
class ListCreateRoleView(ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

@extend_schema(tags=['Role'])
class UpdateRoleView(RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

@extend_schema(tags=['Merchant'])
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
                    logo=request.data['businesslogo']
                    imgext = request.data['businessname']
                    recipientemail = request.data['merchantemailaddress']
                    businessdescription=request.data['businessdescription']
                    country = request.data['country']
                    processedimage = receiveImage(img_data,imgext)
                    serializer.save(serviceID=serviceID,merchantpassword=passwd,businesslogo=processedimage, merchantemailaddress=merchantemailaddress)
                    emailactivation(recipientemail,imgext,request)
                    merchid = merchant.objects.order_by('id').values('id').last()
                    print(merchid)
                    walexServiceDetails(imgext,serviceID,businessdescription,request,merchid,country,logo)
                    responseData ={'message':'Your registeration is sucessfully,an email account activation link is sent to your registered email address',
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
        merchantrecord = queryset.filter(active=status).values('id','serviceID','merchantphonenumber', 'businessaddress','merchantemailaddress','active','contactpersonfirstname','contactpersonlastname','businesslogo', 'settingsactivated', 'themecolor')
        return JsonResponse({'data': list(merchantrecord),'status':'True'})

@extend_schema(tags=['Merchant'])
class ListCreateMerchantStaffView(ListCreateAPIView):
    queryset = user.objects.all()
    serializer_class = merchantUserSerializer

@extend_schema(tags=['Merchant'])
class UpdateMerchantStaffView(RetrieveUpdateDestroyAPIView):
    queryset = user.objects.all()
    serializer_class = merchantUserSerializer

    
@extend_schema(tags=['Merchant'])
class merchantManagerView(APIView):
    serializer_class = merchantUserSerializer
    # permission_classes = [IsMerchant]  # Ensure this is defined in your permissions.py
    def post(self, request, format=None):
        try:
            serializer = merchantUserSerializer(data=request.data)

            username = request.data.get('username')
            merchID = request.data.get('merchID_id')

            # Improved duplicate check
            if merchID:
                if checkdupmanagerEmails(username, merchID):
                    return Response({
                        'message': 'The duplicate username',
                        'status': 'False'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                if user.objects.filter(username=username).exists():
                    return Response({
                        'message': 'The duplicate username',
                        'status': 'False'
                    }, status=status.HTTP_400_BAD_REQUEST)

            if serializer.is_valid():
                user_obj = serializer.save()

                # Optional: send notification
                notify = Notification()
                notify.newCustomerNotification(
                    user_obj.name,
                    None,  # randomnumber
                    request.data.get('userpassword'),
                    user_obj.username,
                    user_obj.merchID.id if user_obj.merchID else None,
                    user_obj.username
                )

                return Response({
                    'message': 'Record created',
                    'status': 'True'
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'message': f'An error occurred: {str(e)}',
                'status': 'False'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
    def get(self,request, format=None):
        merchID=request.GET.get('merchID')
        queryset = user.objects.all()
        branchmanagerecord = queryset.filter( merchID=merchID).annotate( role_name=F('role__name')).values('id', 'username', 'role_name', 'branchID', 'merchID' )
        dictList=[]
        for counter, element in enumerate(branchmanagerecord):
            print(element)
            length = len(branchmanagerecord)
            if length > counter:
                branchname = branch.objects.filter(
                    id=element['branchID']).values('branchname').first()
                if branchname:
                    element.update(branchname)
                dictList.append(element)       
        return JsonResponse({'data': dictList,'status':'True'})  

@extend_schema(tags=['Merchant'])
class merchantDeleteManagerView(APIView):  
    serializer_class = merchantUserSerializer
    
    def post(self, request, pk):
        #return JsonResponse({'test': 'Testing this'})
        merchID=request.GET.get('merchID')
        user.objects.get(id=pk, merchID=merchID).delete()
        return JsonResponse({'message':'The user account has been deleted','status':True})
    
@extend_schema(tags=['Merchant'])
class merchantBranchView(APIView):
    #permission_classes = (IsAuthenticated,)
    def post(self,request, format=None):
        try:       
            """Save the post data when creating a new merchant."""       
            serializer = branchSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                responseData ={'message':'Branch record created ',
                            'status':'True'}                                   
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
               responseData ={'message':'An error occur'+str(e),'status':'False'}
               return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self,request, format=None):
        merchID=request.GET.get('merchID')
        queryset = branch.objects.all()
        branchrecord = queryset.filter(merchID=merchID).values('id','branchname','branchaddress','branchstate','branchcity','branchofficeline')
        return JsonResponse({'data': list(branchrecord),'status':'True'})          


@extend_schema(tags=['Authentication'])
class merchantLoginView(APIView):
    def get(self, request, format=None):
        username = request.GET.get('username')
        password = request.GET.get('password')

        # Validate input
        if not username or not password:
            return JsonResponse({
                'data': [],
                'status': False,
                'message': 'Username and password are required.'
            }, status=400)

        # Check for active merchant
        active_merchant = merchant.objects.filter(merchantemailaddress=username, active=True).first()
        if active_merchant:
            if check_password(password, active_merchant.merchantpassword):
                resultset = merchant.objects.filter(merchantemailaddress=username, active=True).values(
                    'id', 'businessfacebook', 'serviceID', 'businessname', 'merchantphonenumber',
                    'businessaddress', 'merchantemailaddress', 'active', 'contactpersonfirstname',
                    'contactpersonlastname', 'contactpersonphone', 'businesslogo', 'settingsactivated',
                    'accountnumber', 'accountname', 'bankname', 'currency', 'businesstwitter', 'pointname', 'themecolor'
                )
                tokens = get_tokens_for_merchant(active_merchant)
                return JsonResponse({
                    'data': list(resultset),
                    'access': tokens['access'],
                    'refresh': tokens['refresh'],
                    'status': True
                })
            else:
                return JsonResponse({
                    'data': [],
                    'status': False,
                    'message': 'Invalid password.'
                }, status=400)


        # Check for user
        user_instance = user.objects.filter(username=username).first()
        if user_instance:
            if check_password(password, user_instance.userpassword):
                tokens = get_tokens_for_user(user_instance)
                user_serializer = merchantUserSerializer(user_instance)
                return JsonResponse({
                    'data': user_serializer.data,
                    'access': tokens['access'],
                    'refresh': tokens['refresh'],
                    'status': True
                })
            else:
                return JsonResponse({
                    'data': [],
                    'status': False,
                    'message': 'Invalid password.'
                }, status=400)

        return JsonResponse({
            'data': [],
            'status': False,
            'message': 'Account not found or inactive.'
        }, status=404)
        
class merchantGiftcardVerificationView(APIView):
    def get(self, request, format=None):
        confirmationCode = request.GET.get('confirmationCode')
        queryset = AccountantData.objects.all()
        amount = queryset.filter(confirmationCode=confirmationCode).values('amount')
        return JsonResponse({'data': list(amount), 'status': 'True'})



@extend_schema(tags=['Authentication'])
class branchManagerLoginView(APIView):
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
        queryset =branchmanager.objects.all()
        tokengenerator = tokenGenerator()
        token= tokengenerator['access']
        resultset = queryset.filter(managerusername=username).values('id', 'managername', 'managerusername', 'managerpassword', 'branchID', 'merchID')
        if username is not None:          
            passwordvalue = list(queryset.filter(managerusername=username).values_list('managerpassword', flat=True))
            if  passwordvalue:            
                b=passwordvalue[0]          
                passwordconfirm=check_password(password,b)
                if passwordconfirm is True:                              
                    return JsonResponse({'data':list(resultset),'token':token,'status':'True'})
                else:
                    resultset =[]
                    return JsonResponse({'data': list(resultset),'status':'False','message':'Invalid password'})
        resultset =[]
        return JsonResponse({'data': list(resultset),'status':'False','message':'Invalid username'})

@extend_schema(tags=['Settings'])
class createMerchantSettings(APIView):
    permission_classes =(IsAuthenticated,) 
    def post(self, request, format=None):
        merchantid = request.data['merchantid']
        print("merchantid",merchantid)
        #businessdescription = request.data['businessdescription']
        businessfacebook = request.data['businessfacebook']
        businesstwitter= request.data['businesstwitter']
        bankname =request.data['bankname']
        accountnumber= request.data['accountnumber']
        accountname = request.data['accountname']
        #walexupdate(merchantid,bankname,accountnumber,accountname)
        #contactpersonphone = request.data['contactpersonphone']
        #try:
             # try something
        #merchantupdate = merchant.objects.get(id=merchantid)
        #merchantupdate.businessfacebook = businessfacebook
        #merchantupdate.businessdescription = businessdescription
        #merchantupdate.businesstwitter = businesstwitter
        #merchantupdate.bankname = bankname
        #merchantupdate.accountnumber = accountnumber
        #merchantupdate.accountname = accountname
        #merchantupdate.settingsactivated= True
        #merchantupdate.pointname = request.data['pointname']
        #merchantupdate.themecolor = request.data['themecolor']
        #merchantupdate.save(update_fields=['businessfacebook','businesstwitter','bankname','accountnumber','accountname','settingsactivated','pointname','themecolor'])
        responseData ={'message':'The record is updated','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
        #except ObjectDoesNotExist:
                # do something
              #responseData ={'message':'The record is missing','status':'False'}
              #return HttpResponse(json.dumps(responseData), content_type="application/json")               

@extend_schema(tags=['Authentication'])
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


@extend_schema(tags=['Roles'])
class roleListView(APIView):
    serializer_class = RoleSerializer()

    def get(self, request, *args, **kwargs):
        queryset = Role.objects.all()
        serializer = RoleSerializer(queryset, many=True)
        return JsonResponse({'data': serializer.data,'status':'True'})
        

@extend_schema(tags=['Merchant'])
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
            merchantupdate.pointname = request.data['pointname']
            merchantupdate.businesstwitter=request.data['businesstwitter']
            merchantupdate.updateddate=todaydate
            merchantupdate.save(update_fields=['merchantphonenumber','businessaddress','merchantemailaddress','contactpersonfirstname','contactpersonlastname','contactpersonphone','businesslogo','bankname','accountnumber','accountname','pointname','businesstwitter','updateddate'])
            responseData ={'message':'The record is updated','status':'True'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except ObjectDoesNotExist:
            responseData ={'message':'The record missing','status':'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

@extend_schema(tags=['Authentication'])
class recoverMerchantPassword(APIView):
    def post(self, request, format=None): 
        emailaddress = request.data['emailaddress']
        passwordRecoveryEmail(emailaddress,request)
        responseData ={'message':'Please check your email','status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
        
@extend_schema(tags=['Authentication'])
class passwordRecovery(APIView):
    def post(self, request, format=None):                           
        userid = request.data['userid']
        uid = force_str(urlsafe_base64_decode(userid))      
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

@extend_schema(tags=['Settings'])
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


def walexServiceDetails(imgext, serviceID, businessdescription, request, merchid, country, logo):
    headers = {'content-type': "application/json"}
    #params ={"username":"wajesmart","password":"Admin$1234"}
    activate_url = "{0}://{1}/{2}/{3}/?{4}={5}".format(
        request.scheme, request.get_host(), 'API', 'merchantcustomer', 'merchID', merchid['id'])
    giftcard_url = "{0}://{1}/{2}/{3}/?{4}={5}".format(
        request.scheme, request.get_host(), 'API','merchantgiftcardapi','serviceid',serviceID)
    params={"title":serviceID,"description":imgext,"service_type":businessdescription,"country":country,"is_opened":True,"api_url":activate_url,"giftcard_url":giftcard_url,"logo":logo}
    r = requests.post('http://199.192.22.132/API/service/', data=params)
    #r = requests.post('http://localhost:8009/service/', data=params)
    record = r.json()
    print("respeonse{}".format(record))
    return



def walexupdate(merchantid,bankname,accountnumber,accountname):    
    headers = {'content-type': "application/json"}
    service = merchant.objects.filter(id=merchantid).values('serviceID').first()
    print(service)
    params = {"bankname": bankname, "bankname": bankname, "accountnumber": accountnumber,
              "accountname": accountname, "service": service['serviceID']}
    r = requests.put('http://199.192.22.132/API/service/', data=params)
    record = r.json()
    print(record)
    return

def checkdupmanagerEmails(managerusername,merchID):
    managerusername = user.objects.filter(merchID=merchID).filter(
        username=managerusername).values('username').first()
    print('email check is {}'.format(managerusername))
    if not managerusername:
      return False
    else:
        return True
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
            uid = force_str(urlsafe_base64_decode(uidb64))
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
            fullurl="{0}:/activate".format(url)
            responseData ={
                'message':'Your account is now activated',
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

'''function to check for duplicate email'''
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
    print(fullurl)
    print(record)
    return record

def get_tokens_for_user(user_instance):
    refresh = RefreshToken.for_user(user_instance)
    # Optionally add custom claims, e.g. role
    refresh['role'] = user_instance.role.name if user_instance.role else None
    refresh['merchID'] = user_instance.merchID.id if user_instance.merchID else None
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_tokens_for_merchant(merchant_instance):
    refresh = RefreshToken()
    # Add custom claims for merchant
    refresh['merchant_id'] = merchant_instance.id
    refresh['role'] = 'Merchant'
    refresh['email'] = merchant_instance.merchantemailaddress
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

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
    save_path =os.path.join(settings.BASE_DIR,'merchantlogo',imgext+'.png')
    databasepath= '/merchantlogo/'+imgext+'.png'
    with open(save_path, "wb") as fh:
          fh.write(img_data)
    return databasepath

def emailactivation(recipientemail,imgext,request):
    subject = 'Account Activation'
    template_name='acc_active_email.html'
    from_email = settings.DEFAULT_FROM_EMAIL
    context = {
               'user':request.data['firstname'],
               'username':request.data['username'],
               'password':request.data['password']
              }
    
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
    kwargs = {"uidb64":urlsafe_base64_encode(force_bytes(emailaddress))}
    text_content={}
    #activation_url = reverse("password_recovery", kwargs=kwargs)
    #activation_url = reverse(kwargs=kwargs) 
    activate_url = "{0}://{1}/{2}/{3}".format(request.scheme, request.get_host(),'passwordrecovery',urlsafe_base64_encode(force_bytes(emailaddress)))
    print(activate_url)
    context = {'activate_url': activate_url}
    html_content = render_to_string(template_name, context)
    email = EmailMultiAlternatives(subject,text_content,from_email,[emailaddress])
    email.attach_alternative(html_content, "text/html")
    email.send()

def ValuesQuerySetToDict(vqs):
    return [item for item in vqs]





    
