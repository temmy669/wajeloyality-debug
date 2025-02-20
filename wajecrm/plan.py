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
import datetime

class managePlan(APIView): 
    def post(self,request, format=None):
        serializer = planSerializer(data=request.data)
        if serializer.is_valid(): 
                serializer.save()
                responseData ={'message':'plan record created','status':'True'}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        responseData ={'message':serializer.errors,'status':'False'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
    def get(self,request,format=None):
        plans = plan.objects.all()
        serializer = planSerializer(plans,many=True)      
        responseData ={'data':serializer.data,'status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

class planSubscription(APIView): 
    def post(self,request, format=None):
        planid=int(request.data['planid'])
        print(planid)
        merchantid=request.data['merchantid']
        contract_start_date=request.data['contract_start_date']
        plan_details=list(plan.objects.filter(id=planid).values('id','initial_minimum_user','price','subsequent_minimum','number_of_days','billing_interval'))
        mini_user=plan_details[0]['initial_minimum_user']
        price=plan_details[0]['price']
        number_of_days=plan_details[0]['number_of_days']
        amount=float(mini_user)*float(price)
        date_1 = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d")
        contract_end_date=date_1 + datetime.timedelta(days=int(number_of_days))
        c=contract(planID_id=planid,merchID_id=merchantid,contract_start_date=date_1,contract_end_date=contract_end_date,number_of_license=mini_user)
        c.save()
        contract_id = contract.objects.values('id').last()
        responseData ={'data':{'contract_id':contract_id['id'],'amount':amount},
                      'status':'True'}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

class upgradeSubscription(APIView): 
    def post(self,request, format=None):
        contract_id=int(request.data['contract_id'])
        numberofusers=request.data['numberofusers']
        renewdate=request.data['renewdate']
        date_1 = datetime.datetime.strptime(renewdate,"%Y-%m-%d")
        contract_details=list(contract.objects.filter(id=contract_id).values('id','contract_end_date'))
        print(renewdate)
        remainingdate=contract_details[0]['contract_end_date']
        print(remainingdate)   
        return HttpResponse(None)


