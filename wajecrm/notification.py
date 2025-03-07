from django.shortcuts import render
import os
from .models import *
from django.http import HttpResponse
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.http import Http404
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import pdfkit


class Notification:
    def emailNotification(self, firstname, randomnumber, emailaddress, subject, template_name, others, merchantname):
        subject = subject
        template_name = template_name
        recipientemail = emailaddress.lower()
        from_email = "{0}{1}".format(
            merchantname['businessname'], settings.DEFAULT_FROM_EMAIL)
        barcode = "{0}{1}.{2}".format(
            'http://barcodes4.me/barcode/c128b/', randomnumber, 'png')
        logo = "{0}{1}".format('http://199.192.28.167',
                               merchantname['businesslogo'])
        print(from_email)
        othersformatted = '{:,.2f}'.format(float(others))
        print('formatted voucher{}'.format(othersformatted))
        context = {'user': firstname, 'code': randomnumber, 'amount': othersformatted,
                   'barcode': barcode, 'merchantname': merchantname['businessname'], logo: logo}
        #context1 = {'user': firstname, 'code': randomnumber, 'amount': othersformatted,
                   #'barcode': barcode, 'merchantname': merchantname['businessname'], logo: logo}
        text_content = {}
        html_content = render_to_string(template_name, context)
        #print('Html content {}'.format(html_content))
        email = EmailMultiAlternatives(subject,text_content, from_email, [recipientemail])
        email.attach_alternative(html_content, "text/html")
        email.send()
        #return html_content

    def emailNotificationRedeemGiftcard(self, firstname, randomnumber, emailaddress, subject, template_name, merchantname, currentvalue, transactionvalue):
        subject = subject
        template_name = template_name
        recipientemail = emailaddress.lower()
        from_email = "{0}{1}".format(
            merchantname['businessname'], settings.DEFAULT_FROM_EMAIL)
        #barcode="{0}{1}{2}{3}.{4}{5}{6}{7}{8}".format('<img src=','"','http://barcodes4.me/barcode/c128b/',randomnumber,'png','"',' ','"','style=height:80px;width:120px;>','"')
        #barcode = "{0}{1}.{2}".format( 'http://barcodes4.me/barcode/c128b/', randomnumber, 'png')
        barcode={}
        logo = "{0}{1}".format('http://199.192.28.167',
                               merchantname['businesslogo'])
        print("email working")

        context = {'user': firstname, 'code': randomnumber, 'amount': format(round(transactionvalue, 2)), 'balance': format(round(currentvalue, 2)),
                   'barcode': barcode, 'merchantname': merchantname['businessname'], logo: logo}
        text_content = {}
        html_content = render_to_string(template_name, context)
        email = EmailMultiAlternatives(
            subject, text_content, from_email, [recipientemail])
        email.attach_alternative(html_content, "text/html")
        email.send()

    def newCustomerNotification(self, firstname, randomnumber, customerpassword, emailaddress, merchID, username):
        subject = 'Welcome'
        template_name = 'welcome.html'
        recipientemail = emailaddress.lower()
        from_email = settings.DEFAULT_FROM_EMAIL
        merchantrecord = merchant.objects.filter(id=merchID).values(
            'businesslogo', 'businessname').first()
        logo = "{0}{1}".format('http://199.192.28.167',
                               merchantrecord['businesslogo'])
        print(logo)
        context = {'firstname': firstname, 'pin': randomnumber,
                   'password': customerpassword, 'logo': logo,
                   'businessname': merchantrecord['businessname'], 'username': username}
        text_content = {}
        html_content = render_to_string(template_name, context)
        email = EmailMultiAlternatives(
            subject, text_content, from_email, [recipientemail])
        email.attach_alternative(html_content, "text/html")
        email.send()


def testNotification(self):
    subject = 'Welcome'
    template_name = 'welcome.html'
    recipientemail = 'ozigbochidozie@gmail.com'
    from_email = "Market Square{0}".format(settings.DEFAULT_FROM_EMAIL)
    #from_name = settings.DEFAULT_FROM_NAME
    #print('from emailaddress {}'.format(from_email))
    text_content = {}
    html_content = render_to_string(template_name)
    email = EmailMultiAlternatives(
        subject, text_content, from_email, [recipientemail])
    email.attach_alternative(html_content, "text/html")
    email.send()
    return HttpResponse(None)


def htmltopdf(firstname, randomnumber, emailaddress, subject, template_name, expiry, others, merchantname):
    """Render the html template to a string that can be download as pdf.
    :firstname: name of customer
    :randomnumber: randomly generated integers
    :emailaddress: address of customer
    :subject: title of card
    :template_name: the template to be rendered
    :expirty: expiring date of giftcard
    :others: None
    :merchantname: merchat details 
    """
    subject = subject
    template_name = template_name
    recipientemail = emailaddress.lower()
    from_email = "{0}{1}".format(
        merchantname['businessname'], settings.DEFAULT_FROM_EMAIL)
    barcode = "{0}{1}{2}".format('https://barcode.tec-it.com/barcode.ashx?data=',randomnumber,'%0A&code=Code128&multiplebarcodes=true&translate-esc=true&unit=Fit&dpi=96&imagetype=Gif&rotation=0&color=%23000000&bgcolor=%23ffffff&codepage=Default&qunit=Mm&quiet=0&hidehrt=False')
    print(barcode)
    #logo = "{0}{1}".format('http://199.192.28.167',merchantname['businesslogo'])

    print(from_email)
    othersformatted = '{:,.2f}'.format(float(others))
    print('formatted voucher{}'.format(othersformatted))
    context = {'beneficiary': firstname, 'code': randomnumber, 'amount': othersformatted,
                'barcode': barcode, 'merchantname': merchantname['businessname'], 'expiry': expiry}
    #context1 = {'user': firstname, 'code': randomnumber, 'amount': othersformatted,
                #'barcode': barcode, 'merchantname': merchantname['businessname'], logo: logo}
    #text_content = {}
    html_content = render_to_string(template_name, context)
    return html_content
