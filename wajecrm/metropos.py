from django.shortcuts import render
from .models import *
import random
import ast
import uuid
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
from django.contrib.auth.hashers import make_password
from .logger import *
import requests
import base64
from .customer import *
from .loyalty import postAssignedPoint,checkForDupReceipt
from .notification import Notification
import json
import xmltodict
from rest_framework.permissions import IsAuthenticated
from django.views import View
import datetime
from dateutil.parser import parse
from django.db import connections

"""
service to get external  loyalty transactions from merchant through third party API
"""


def customerLoyaltyTransaction(format=None):
    serviceID = '351817683'
    logger = get_logger(serviceID)
    try:
        todaydate = str(datetime.datetime.now().date())
        # Query MetroPOS to get transaction for today
        r = list(pointtable.objects.filter(date=todaydate).values(
            'CardNumber', 'Invoicenumber', 'date', 'Amount', 'InvValue'))
        # loop through the transactions
        for counter, element in enumerate(r):
            logger.info("{0}{1}{2}".format(
                "Starting loyalty migration for", " ", element['CardNumber']))
            cardnumber = element['CardNumber']
            transactionamount = element['Amount']
            receiptno = element['Invoicenumber']
            transactiondate = element['date']
            # Get customer details from MetroPOS database
            metrocustomerrecord = loyaltyCustomer.objects.filter(CardNumber=cardnumber).values(
                'CardNumber', 'Customername', 'Address', 'Tel', 'branch').first()
            customerphonenumber = metrocustomerrecord['CardNumber']
            customername = metrocustomerrecord['Customername']
            customeremailaddress = metrocustomerrecord['Address']
            branchname ='HD'
            # Get branch record from MetroPOS Database
            #branchrecord = Branch.objects.filter(BranchNickName=metrocustomerrecord['branch']).values(
               #'BranchCode', 'BranchNickName', 'BRANCHID').first()
            #if branchrecord is None: 
               #branchname = 'HD'
            #branchname = branchrecord['BRANCHID']
            merchID = checkForServiceID(serviceID)
            if merchID is not False:
                args = (cardnumber, merchID['id'], transactionamount, customerphonenumber, receiptno,
                        transactiondate, customername, customeremailaddress, branchname, serviceID)
                # get the loyalty rule in WALEXX database
                loyaltyruleid = loyaltyrule.objects.filter(
                    merchID=args[1]).values('id').first()
                # function to get the customer record
                customerID = getCustomerRecord(*args)
                # function to check if the transaction already exist in WaLLEX database
                checkduptransaction = checkDuplicateTransaction(*args)
                print(checkduptransaction)
                if customerID is None:
                    # function to save customer records
                    customerID = saveCustomerRecord(*args)
                    logger.info("{0}{1}{2}".format(
                        "Saving customer details for customerIdentity", " ", element['CardNumber']))
                if checkduptransaction is None:
                    try:
                        loyaltyruleID = loyaltyruleid['id']
                        transactionamount = args[2]
                        transactiondate = args[5]
                        transactionref = args[4]
                        # confim is the voucher id already exist in MetroPOS this is a very important for partial redemption in MetroPOS
                        realtransactionamount = listvouchertransactions.objects.filter(
                            Credit='00.00').filter(Invoicenumber=receiptno).values('Invoicenumber', 'Debit').first()
                        if realtransactionamount is None:
                            assignedpoint = postAssignedPoint(loyaltyruleID, transactionamount)
                            Loyalitytransaction = loyaltytransaction(loyaltyruleID_id=loyaltyruleID, CustID_id=customerID['id'],
                                                                     merchID_id=args[1], receiptno=transactionref, transactionamount=transactionamount, assignedpoint=assignedpoint, transactiondate=transactiondate, description='metropos customer transaction')
                            logger.info("{0}{1}{2}".format(
                                "Saving loyalty transaction for customerIdentity", " ", element['CardNumber']))
                            Loyalitytransaction.save()
                            saveVoucherRecord(assignedpoint, transactionref, customerphonenumber, merchID)
                        else:
                            transactionamount = float(
                                transactionamount-realtransactionamount['Debit'])
                            print(transactionamount)
                            assignedpoint = postAssignedPoint(
                                loyaltyruleID, transactionamount)
                            Loyalitytransaction = loyaltytransaction(loyaltyruleID_id=loyaltyruleID, CustID_id=customerID['id'], merchID_id=args[
                                1], receiptno=transactionref, transactionamount=transactionamount, assignedpoint=assignedpoint, transactiondate=transactiondate, description='metropos customer transaction')
                            logger.info("{0}{1}{2}".format(
                                "Saving loyalty transaction for customerIdentity", " ", element['CardNumber']))
                            Loyalitytransaction.save()
                            saveVoucherRecord(
                                assignedpoint, transactionref, customerphonenumber, merchID)
                    except TypeError as e:
                        logger.info(
                            "error occurred"+str(e))
                logger.info("{0}{1}{2}".format(
                    "ending loyalty migration for customerIdentity", " ", element['CardNumber']))
                continue
            logger.info("No merchant id")
            break
    except Exception as e:
        logger.info("error"+str(e))
    logger.info("The migration has ended")
    return HttpResponse(None)


def checkDuplicateTransaction(*args):
    """ Function to check for duplicate transaction """
    transactionrecord = loyaltytransaction.objects.filter(
        merchID=args[1]).filter(receiptno=args[4])
    if transactionrecord:
        return True
    else:
        return None

def order3D2dict(input_ordered_dict):
    return loads(dumps(input_ordered_dict))


def saveCustomerRecord(*args):
    randomnumber = randomGenerate()
    emailaddress = args[7].lower()
    try:
        data = args[6].split(" ")
        firstname = data[0]
        lastname = data[1]
    except Exception:
        lastname = None
    customerpassword = uuid.uuid4().hex[:6].upper()
    encrytcustomerpassword = make_password(
        customerpassword, salt=None, hasher='default')
    customerrecord = customer(transactionpin=randomnumber, firstname=firstname, lastname=lastname,
                              emailaddress=emailaddress, customerIdentifier=args[0], merchID_id=args[1],
                              password=encrytcustomerpassword)
    customerrecord.save()
    merchID = args[1]
    notify = Notification()
    username = args[0]
    notify.newCustomerNotification(
        firstname, randomnumber, customerpassword, emailaddress, merchID, username)
    custID = customer.objects.values('id').last()
    return custID


def randomGenerate():
    for x in range(4):
        return random.randint(1, 10001)


def checkForServiceID(serviceID):
    checkserviceid = merchant.objects.filter(
        serviceID=serviceID).values('id').first()
    if not checkserviceid:
        return False
    else:
        return checkserviceid


def getCustomerRecord(*args):
    """ This function checks if the customer record is in WALEXX """
    custID = customer.objects.filter(merchID=args[1]).filter(
        customerIdentifier=args[3]).values('id').first()
    if custID:
        return custID
    else:
        return None


def getRedemptionTransaction(format=None):
    "Query MetroPOS dbserver to retrive redeemption transactions done on MetroPOS"
    #loyaltyruleid, *args
    serviceID ='351817683'
    logger = get_logger(serviceID)
    todaydate = datetime.datetime.now().date()
    tomorrowdate =todaydate + datetime.timedelta(days=1)
    merchantrecord = merchant.objects.filter(
        serviceID=serviceID).values('id').first()
    merchID = merchantrecord['id']
    loyaltyruleid = loyaltyrule.objects.filter(
        merchID=merchID).values('id').first()
    logger.info("{0}{1}{2}".format(
        "Starting redemption migration for merchant", " ", serviceID))
    record = list(listvouchertransactions.objects.filter(Credit='00.00').filter(ref__isnull=True).filter(DateUsed__gt=todaydate).filter(DateUsed__lt=tomorrowdate).values(
        'ID', 'DateUsed', 'Invoicenumber', 'recno', 'Particular', 'Debit'))
    """ A list of redemption transactions done in MetroPOS """
    for counter, element in enumerate(record):
        length = len(record)
        if length > counter:
            todaydate = str(datetime.datetime.now().date())
            transactiondate = str(element['DateUsed']).split(" ")[0]
        """ The redemption transaction for the day is captured """
        if transactiondate == todaydate:
            receiptno = str(element['Invoicenumber']) + 'redemption'
            description = 'Redeemption For'+'-'+element['ID']
            dupreceipt = checkForDupReceipt(receiptno, merchID)
            if dupreceipt is False:
                """Filter by metroPOS Loyalty customer"""
                print(element['ID'])
                customerid = customer.objects.filter(customerIdentifier=element['ID'],merchID_id=merchID).values('id').first()
                if customerid:
                    """Capture the redeemption transaction done on MetroPOS for the Loyalty customers"""
                    loyaltytransactionrecord = loyaltytransaction(loyaltyruleID_id=loyaltyruleid['id'], CustID_id=customerid['id'], merchID_id=merchID,
                                                                redeemedpoint=element['Debit'], transactiondate=transactiondate, receiptno=receiptno, description=description)
                    logger.info("{0}{1}{2}".format("ending redemption migration for", " ", serviceID))
    return HttpResponse(None)


# function to sink Walexx gift voucher for market square with MetroPOS
def saveGiftVoucherRecord(format=None):
    serviceID ='351817683'
    logger = get_logger(serviceID)
    logger.info("{0}{1}{2}".format("Starting gift card migration for", " ", serviceID))
    try:
        merchID = merchant.objects.filter(serviceID=serviceID).values('id').first()  # get the mech ID using the service ID
        voucherdetails = list(giftCard.objects.filter(merchID=merchID['id']).filter(
            recipient_phone__isnull=False).values('id', 'serialnumber', 'cardname', 'recipient_phone', 'amount').order_by('-createddate'))
        for counter, element in enumerate(voucherdetails):
            length = len(voucherdetails)
            if length > counter:
                metroposvoucherrecord = voucher.objects.filter(ID=element['serialnumber']).values(
                    'id').first()  # fetch the gift voucher from MetroPOS by serialnumber fom WALEXX
                if metroposvoucherrecord is None:  # Validate if the gift card already exist in MetroPOS
                    logger.info("{0}{1}{2}".format("save gift card  for", " ", element['serialnumber']))
                    print("save voucherID")
                    print(element['serialnumber'])
                    v = voucher(ID=str(element['serialnumber']),CUSTOMERCODE=str(
                        element['serialnumber']),Amount=element['amount'], SOLDOUT=True,Status=False,vouchertype="Regular",OtherInfo=str(element['recipient_phone']))
                    v.save()  # Save the gift card in MetroPOS if the gift card does not exit
        
        logger.info("{0}{1}{2}".format("end gift card migration ", " ", serviceID))
        # push the deactivated giftcard
    except Exception as e:
        logger.info("The merchant ID not found"+str(e))
    return HttpResponse(None)

def pushDeactivatedGiftVoucherRecord(format=None):
    serviceID = '351817683'
    logger = get_logger(serviceID)
    logger.info(f"Starting gift card migration for {serviceID}")
    try:
        # Get merchant ID
        merchID = merchant.objects.filter(serviceID=serviceID).values('id').first()
        if not merchID:
            logger.error("Merchant not found")
            return HttpResponse(None)
            
        # Get deleted gift cards from Walexx
        voucherdetails = list(giftCard.objects.all_with_deleted().filter(
            merchID=merchID['id'], 
            deleted__isnull=False
        ).values('id', 'serialnumber', 'cardname', 'recipient_phone', 'amount').order_by('-createddate'))

        for element in voucherdetails:
            # Safely check if voucher exists in MetroPOS
            metroposvoucherrecord = voucher.objects.filter(ID=element['serialnumber']).first()
            
            if metroposvoucherrecord:  # Only proceed if record exists
                logger.info(f"Deactivating gift card {element['serialnumber']}")
                
                # Update using raw SQL
                sql_update_query = """
                    UPDATE voucher
                    SET Status = 1,
                        SOLDOUT = 0
                    WHERE ID = %s
                """
                try:
                    with connections['loyalty'].cursor() as cursor:
                        cursor.execute(sql_update_query, [element['serialnumber']])
                    logger.info(f"Successfully deactivated {element['serialnumber']}")
                except Exception as e:
                    logger.error(f"Error updating voucher {element['serialnumber']}: {str(e)}")
            else:
                logger.info(f"Voucher {element['serialnumber']} not found in MetroPOS, skipping")

        logger.info(f"Completed gift card migration for {serviceID}")

    except Exception as e:
        logger.error(f"Error in pushDeactivatedGiftVoucherRecord: {str(e)}")
    
    return HttpResponse(None)


# function to pull redeem gift transaction from MetroPOS
def retrieveRedeemGiftCard(format=None):
    serviceID ='351817683'
    logger = get_logger(serviceID)
    logger.info("{0}{1}{2}".format(
        "Starting pull redeem gift transaction for", " ", serviceID))
    merchid = merchant.objects.filter(serviceID=serviceID).values('id').first()
    try:
        merchID = int(merchid['id'])
        logger = get_logger(serviceID)
        record = list(listvouchertransactions.objects.filter(Credit='00.00').filter(ref__isnull=True).values(
            'ID', 'DateUsed', 'recno', 'Particular', 'Debit'))  # pull giftcard transaction from metroPOS
        for counter, element in enumerate(record):
            length = len(record)
            if length > counter:
                todaydate = str(datetime.datetime.now().date())
                transactiondate = str(element['DateUsed']).split(" ")[0]
                if transactiondate == todaydate:  # get the giftcard transaction for today
                    receiptno = 'giftcardredeemed'+'-'+str(element['recno'])
                    dupreceipt = checkForTransaction(receiptno, merchID)
                    if dupreceipt is False:
                        giftid = giftCard.objects.filter(
                            serialnumber=element['ID']).values('id', 'recipient_email','amount').first()
                        if giftid:
                            """Capture the redeemption transaction done on MetroPOS for the Loyalty customers"""
                            giftcardtransactions = giftcardtransaction(
                                giftID_id=giftid['id'], redeemedamount=element['Debit'], merchID_id=merchID, reference=receiptno)
                            giftcardtransactions.save()
                            notify = Notification()
                            transactionvalue = element['Debit']
                            purchasevalue = giftid['amount']
                            remainingvalue = giftcardtransaction.objects.filter(merchID=merchID).filter(
                                giftID=element['ID']).aggregate(Sum('redeemedamount').filter())
                            if not(remainingvalue['redeemedamount__sum']):                    
                               remainingvalue['redeemedamount__sum'] =0.00
                            print('remaining value  is {}'.format(remainingvalue))
                            print('purchase value  is {}'.format(purchasevalue))
                            currentvalue = float(purchasevalue)-float(remainingvalue['redeemedamount__sum'])
                            firstname = 'customer'
                            randomnumber = element['ID']
                            emailaddress = giftid['recipient_email']
                            subject = 'Gift Card Transaction'
                            template_name = 'voucher_transaction.html'
                            merchantname = merchant.objects.filter(id=merchID).values(
                                'businessname', 'businesslogo').first()
                            notify.emailNotificationRedeemGiftcard(
                                firstname, randomnumber, emailaddress, subject, template_name, merchantname, currentvalue,transactionvalue)
        logger.info("{0}{1}{2}".format(
            "Ending redemption migration for", " ", serviceID))
    except Exception as e:
        logger.info("The merchant ID not found"+str(e))
    return HttpResponse(None)


def checkForTransaction(receiptno, merchID):
    receiptrecord = giftcardtransaction.objects.filter(
        reference=receiptno).filter(merchID=merchID)
    if not receiptrecord:
        return False
    else:
        return True


def customerInfoMarch(queryset):
    element = []
    dictList = []
    serviceID = {}
    for counter, element in enumerate(queryset):
        length = len(queryset)
        if length > counter:
            customerinfo = customer.objects.filter(id=element['CustID']).values(
                'firstname', 'lastname', 'customerIdentifier', 'emailaddress').first()
            element.update(customerinfo)
            dictList.append(element)
    return dictList


def Voucher(request):
    p = voucher(ID='08130639936', CUSTOMERCODE='08130639936',
                Amount='100', OtherInfo='245')
    p.save()  # (statement 1)
    return HttpResponse(None)


def saveVoucherRecord(assignedpoint, transactionref, customerphonenumber, merchID):
    customertransactionpin = list(customer.objects.filter(merchID=merchID['id']).filter(
        customerIdentifier=customerphonenumber).values('transactionpin'))
    customerecord = voucher.objects.filter(
        ID=customerphonenumber).values('ID').first()
    if not customerecord:
        """check if the customer exist on MetroPOS"""
        v = voucher(ID=str(customerphonenumber), CUSTOMERCODE=str(customerphonenumber), Amount=assignedpoint,
                    OtherInfo=str(customertransactionpin[0]['transactionpin']))
        v.save()
        """Create the customer and the transactions in MetroPOS if the customer deos not exist in Walexx"""
    else:
        vt = vouchertransactions(ID=str(customerphonenumber), Credit=assignedpoint,
                                 Debit='0.00', Particular='transaction', ref=transactionref)
        vt.save()
        """Voucher transaction saves for already existing customers """
    return HttpResponse(None)


def VoucherTransaction(request):
    p = vouchertransactions(ID='08130639935', Invoicenumber='1.00',
                            Credit='00.00', Debit='100.00', Particular='transaction')
    p.save()  # (statement 1)
    return HttpResponse(None)
