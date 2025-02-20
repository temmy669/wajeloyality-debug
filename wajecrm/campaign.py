from django.shortcuts import render
from .models import *
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from .serializers import *
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
import logging
from .logger import *
import base64
import json
from rest_framework.permissions import IsAuthenticated
from django.views import View
import datetime
from django.db.models import Sum
from django.template.loader import render_to_string

class CampaignTemplate(APIView):
    #permission_classes =(IsAuthenticated,) 
    def post(self,request, format=None):
        serializer = campaignTemplates(data=request.data)
        imgext = request.data['title']
        merchID =request.data['merchID']
        checkduptemplatename =duplicateTemplatename(imgext,merchID)
        try:
            if checkduptemplatename is False:
                if serializer.is_valid():
                    html_data =  base64.b64decode(request.data['body'])
                    img_data =  base64.b64decode(request.data['body_preview'])
                    imgext = str(request.data['title'].replace(" ", ""))
                    print(imgext)
                    processedhtml =receiveImage(html_data,imgext,ext_img='html')
                    processedimage = receiveImage(img_data,imgext,ext_img='png')
                    serializer.save(body=processedhtml,preview_body=processedimage)
                    responseData ={
                                    'message':'Campaign template created',
                                    'status':'True'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            responseData={
                        'message':'The duplicate campaign template name',
                        'status':'False'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json") 
        
    
    def get(self,request,format=None):
        merchID=request.GET.get('merchID')
        queryset = campaigntemplate.objects.all()
        campaigntemplaterecord = queryset.filter(merchID=merchID).filter(active=True).values('id','title','body','preview_body','active')
        return JsonResponse({'data': list(campaigntemplaterecord),'status':'True'})

    def put(self,request,format=None):
            html_data =  base64.b64decode(request.data['body'])
            img_data =  base64.b64decode(request.data['body_preview'])
            imgext = str(request.data['title'].replace(" ", ""))
            processedhtml =receiveImage(html_data,imgext,ext_img='html')
            processedimage = receiveImage(img_data,imgext,ext_img='png')
            try:
                # try something
                todaydate = datetime.date.today()
                campaigntempateid =request.data['campaigntempalateid']
                campaigntemplateupdate = campaigntemplate.objects.get(id=campaigntempateid)
                campaigntemplateupdate.title = request.data['title']
                campaigntemplateupdate.active =request.data['active']
                campaigntemplateupdate.body =processedhtml
                campaigntemplateupdate.body_preview =processedimage
                campaigntemplateupdate.updateddate=todaydate
                campaigntemplateupdate.save(update_fields=['title','active','body','updateddate'])
            except Exception as e:
                    responseData ={'message':'An error occur'+str(e),'status':'False'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")  
            responseData ={'message':'The record is updated','status':'True'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

class Campaign(APIView):
    permission_classes =(IsAuthenticated,) 
    def post(self,request, format=None):
        try:
            serializer = createCampaigns(data=request.data)
            if serializer.is_valid(): 
                    serializer.save()
                    responseData ={'message':'Campaign record created','status':'True'}
                    return HttpResponse(json.dumps(responseData), content_type="application/json")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json") 
    def put(self,request,format=None):
        try:
             # try something
            todaydate = datetime.date.today()
            campaignid =request.data['campaignid']
            campaignupdate = campaigns.objects.get(id=campaignid)
            campaignupdate.title = request.data['title']
            campaignupdate.campaigntype =request.data['campaigntype'] 
            campaignupdate.interval = request.data['interval'] 
            campaignupdate.startdate = request.data['startdate']  
            campaignupdate.enddate = request.data['enddate'] 
            campaignupdate.tempateID_id =request.data['tempateID']  
            campaignupdate.active= request.data['active']  
            campaignupdate.updateddate=todaydate
            campaignupdate.save(update_fields=['title','campaigntype','interval','startdate','enddate','tempateID','active','updateddate'])
            responseData ={'message':'The record is updated','status':'True'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
                responseData ={'message':'An error occur'+str(e),'status':'False'}
                return HttpResponse(json.dumps(responseData), content_type="application/json") 

    def get(self,request,format=None):
        merchID=request.GET.get('merchID')
        queryset = campaigns.objects.all()
        campaignrecord = queryset.filter(merchID=merchID).values('id','title','campaigntype', 'interval','startdate','enddate','tempateID','active')
        element=[]
        dictList=[]
        for counter,element in enumerate(campaignrecord):
            template_name = campaigntemplate.objects.filter(id=element['tempateID']).values('title').first()
            template_name['template name'] = template_name.pop('title') 
            element.update(template_name)
            dictList.append(element)
        return JsonResponse({'data': list(campaignrecord),'status':'True'})

class campaignHistoryView(APIView):
    def get(self,request,format=None):
        merchID=request.GET.get('merchID')
        queryset = campaignhistory.objects.all()
        campaignrecord = queryset.filter(merchID=merchID).values('id','merchantname','customeremail','campaigntype', 'templatename','campaign_channel','subject','createddate')
        return JsonResponse({'data': list(campaignrecord),'status':'True'})   


def processTwentyhoursCampaign():
    todaydate = datetime.date.today()
    activecampaign=list(campaigns.objects.filter(enddate__gte=todaydate).filter(active=True).filter(interval='daily').values('title','merchID','campaigntype','interval','tempateID'))
    activeCampaign(activecampaign)
    return HttpResponse(None)

def processweeklyCampaign():
    todaydate = datetime.date.today()
    activecampaign=list(campaigns.objects.filter(enddate__gte=todaydate).filter(active=True).filter(interval='weekly').values('title','merchID','campaigntype','interval','tempateID'))
    activeCampaign(activecampaign)
    return HttpResponse(None)

def processtestCampaign(request):
    todaydate = datetime.date.today()
    activecampaign=list(campaigns.objects.filter(enddate__gte=todaydate).filter(active=True).filter(interval='daily').values('title','merchID','campaigntype','interval','tempateID'))
    activeCampaign(activecampaign)
    return HttpResponse(None)

def processmonthlyCampaign():
    todaydate = datetime.date.today()
    activecampaign=list(campaigns.objects.filter(enddate__gte=todaydate).filter(active=True).filter(interval='monthly').values('title','merchID','campaigntype','interval','tempateID'))
    activeCampaign(activecampaign)
    return HttpResponse(None)

def activeCampaign(activecampaign):
    for counter,element in enumerate(activecampaign):
        todaydate = datetime.date.today()
        print(todaydate.month)
        print(todaydate.day)
        subject=element['title']
        campaigntype=element['campaigntype']
        merchID= element['merchID']
        print(campaigntype)
        if campaigntype !='birthday':
           merchantname = merchant.objects.filter(id=element['merchID']).values('serviceID').first()
           templatename=campaigntemplate.objects.filter(merchID=element['merchID']).filter(id=element['tempateID']).filter(active=True).values('title','body').first()
           customerrecord= list(customer.objects.filter(merchID=element['merchID']).values('firstname','lastname','emailaddress'))
           CampaignNotification(customerrecord,templatename,subject,merchantname,campaigntype,merchID)     
        else:
           merchantname = merchant.objects.filter(id=element['merchID']).values('serviceID').first()
           templatename=campaigntemplate.objects.filter(merchID=element['merchID']).filter(id=element['tempateID']).filter(active=True).values('title','body').first()
           customerrecord= list(customer.objects.filter(merchID=element['merchID']).filter(DOB__month=todaydate.month).filter(DOB__day=todaydate.day).values('firstname','lastname','emailaddress'))
           print(customerrecord)
           CampaignNotification(customerrecord,templatename,subject,merchantname,campaigntype,merchID)   
          
def CampaignNotification(customerrecord,templatename,subject,merchantname,campaigntype,merchID):
    for counter,element in enumerate(customerrecord):
        customerfullname = element['firstname']+' '+ element['lastname']
        customeremail = element['emailaddress']
        templatesample=templatename['body']
        templatetitle=templatename['title']
        emailNotification(customerfullname,templatesample,customeremail,subject,merchantname,campaigntype,templatetitle,merchID)
    
def emailNotification(customerfullname,templatesample,customeremail,subject,merchantname,campaigntype,templatetitle,merchID):
    subject =subject
    template_name = os.path.join(settings.BASE_DIR,templatesample)
    f = open(template_name, 'r')
    file_content = f.read()
    f.close()
    recipientemail=customeremail
    from_email =str(merchantname['serviceID'])+' '+settings.DEFAULT_FROM_EMAIL
    text_content ={}
    email = EmailMultiAlternatives(subject,text_content,from_email,[recipientemail])
    email.attach_alternative(file_content, "text/html")
    emailHistory(merchantname,subject,customeremail,campaigntype,templatetitle,merchID)
    email.send()

def emailHistory(merchantname,subject,customeremail,campaigntype,templatetitle,merchID):
    c= campaignhistory(merchID_id=merchID,merchantname=merchantname['serviceID'],subject=subject,customeremail=customeremail,campaigntype=campaigntype,templatename=templatetitle,campaign_channel='email')
    c.save()
   
def receiveImage(img_data,imgext,ext_img):
    save_path= os.path.join(settings.BASE_DIR,'campaigntemplates',imgext+'.'+ext_img)
    databasepath="{0}{1}.{2}".format("campaigntemplates/",imgext,ext_img) 
    with open(save_path, "wb") as fh:
          fh.write(img_data)
    return databasepath


def duplicateTemplatename(imgext,merchID):
    templatename = campaigntemplate.objects.filter(title=imgext).filter(merchID=merchID)
    if not templatename:
      return False
    else:
        return True
