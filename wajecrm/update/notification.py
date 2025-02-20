from django.shortcuts import render
from .models import *
from django.http import HttpResponse
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.http import Http404
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

class Notification:
      def emailNotification(self,firstname,randomnumber,emailaddress,subject,template_name,others):
         subject =subject
         template_name=template_name
         recipientemail=emailaddress.lower()
         from_email = settings.DEFAULT_FROM_EMAIL
         context = {'user':firstname,'code': randomnumber,'amount':others}
         text_content={}
         html_content = render_to_string(template_name, context)
         email = EmailMultiAlternatives(subject,text_content,from_email,[recipientemail])
         email.attach_alternative(html_content, "text/html")
         email.send()
