from django.shortcuts import render
import random
from django.template.defaulttags import csrf_token
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
import requests
from random import randint
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
import requests
import base64
import json
from .loyalty import postAssignedPoint
from django.core.files.base import ContentFile
from rest_framework.permissions import IsAuthenticated
from sequences import get_next_value
from django.utils import timezone
from datetime import datetime, timedelta,date
from django.db.models import Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import pagination
from django.db.models import Count, Sum, F, Q
import pandas as pd
import xlrd
from django.db.models import Count, Sum
from pyfcm import FCMNotification


class productUploadView(APIView):
    def post(self, request, format=None):
        uploadedfile = pd.ExcelFile(request.data['file'])
        #cols = ['barcode', 'productname', 'productdescription','stockqty','sellingprice']
        df = pd.read_excel(uploadedfile)
        for row in df.itertuples():

            productrecord = product(productcode=row.PRODUCTCODE, productname=row.PRODUCTNAME, merchID_id=request.data['merchID'], producttype=request.data['producttype'], productdescription=row.PRODUCTDESCRIPTION,
                                    expiration_date=row.EXPIRYDATE, branchID_id=request.data['branchID'], sellingprice=row.SELLINGPRICE, categoryID_id=request.data['categoryID'])
            productrecord.save()
            stockrecord = stock(
                merchID_id=request.data['merchID'], branchID_id=request.data['branchID'], inwardqty=row.STOCKQTY, productID_id=productrecord.id)
            stockrecord.save()

        responseData = {'message': 'The product record is created sucessfully',
                        'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class LinkHeaderPagination(pagination.PageNumberPagination):
    page_size_query_param = '10'

    def get_paginated_response(self, data):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()
        if next_url is not None and previous_url is not None:
            nexturl = next_url
            previousurl = previous_url
            #link = '<{next_url}>; rel="next", <{previous_url}>; rel="prev"'
        elif next_url is not None:
            nexturl = next_url
            previousurl = ''
        elif previous_url is not None:
            previousurl = previous_url
            nexturl = ''
        else:
            nexturl = ''
            previousurl = ''
        headers = {'Next': nexturl, 'Prev': previousurl,
                   'Count': self.page.paginator.count}
        responseData = {'data': data, 'headers': headers, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")
        # return Response(data, headers=headers)

    def get_record(self,data,id):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()
        if next_url is not None and previous_url is not None:
            nexturl = next_url
            previousurl = previous_url
            #link = '<{next_url}>; rel="next", <{previous_url}>; rel="prev"'
        elif next_url is not None:
            nexturl = next_url
            previousurl = ''
        elif previous_url is not None:
            previousurl = previous_url
            nexturl = ''
        else:
            nexturl = ''
            previousurl = ''
        if self.page.has_next():
            pagenum = self.page.next_page_number()
            print(pagenum)
        else:
            pagenum = ''
        headers = {'Next': nexturl, 'Prev': previousurl, 'pagenum': pagenum,
                   'Count': self.page.paginator.count, 'data': data,'category':id}
        # print(headers)
        return headers


class purchaseorderView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            purchaseorderecord = purchaseorder(template=request.data['template'], merchID_id=request.data['merchID'],
                                               branchID_id=request.data['branchID'], vendorID_id=request.data['vendorID'],
                                               purchaseordercode=request.data['purchaseordercode'], paymentterms=request.data[
                                                   'paymentterms'], createdby=request.data['createdby'],
                                               description=request.data['description'], orderdate=request.data['orderdate'], duedate=request.data['duedate'], currency=request.data['currency'])
            purchaseorderecord.save()
            for purchaseorderitem in request.data['purchaseorderitems']:
                purchaseitemrecord = purchaseorderitems(
                    purchaseID_id=purchaseorderecord.id, productID_id=purchaseorderitem[
                        'productID'], quantity=purchaseorderitem['quantity'],
                    vendorproductcode=purchaseorderitem['vendorproductcode'], unitprice=purchaseorderitem['unitprice'],
                    discountprice=purchaseorderitem['discountprice'], totalprice=purchaseorderitem['totalprice'], merchID_id=purchaseorderitem['merchID'])
                purchaseitemrecord.save()
            responseData = {'message': 'The vendor record is created sucessfully',
                            'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        purchaseorderecords = list(purchaseorder.objects.filter(merchID=merchID).values(
            'id', 'template', 'merchID', 'branchID', 'vendorID', 'purchaseordercode', 'paymentterms', 'createdby', 'description', 'duedate', 'currency'))
        for purchaseorderecord in purchaseorderecords:

            purchaseorderecord['duedate'] = str(purchaseorderecord['duedate'])
            vendorinfo = vendor.objects.filter(id=purchaseorderecord['vendorID']).values(
                'vendorname', 'vendorcontactperson', 'vendoraddress', 'vendoremail', 'vendorcity', 'vendorstate').first()
            purchaseorderecord.update(vendorinfo)
            branchinfo = branch.objects.filter(id=purchaseorderecord['branchID']).values(
                'branchname', 'branchcity').first()
            purchaseorderecord.update(branchinfo)
            purchaseitems = getPurchaseItems(purchaseorderecord)
            receivenote = getReceiveNote(purchaseorderecord)
            goodsreturnnote = getGoodsReturnNote(purchaseorderecord)
            purchaseitems = {'purchaseorderitems': purchaseitems}
            receiveitems = {'receiveorderitems': receivenote}
            goodsitems = {'goodsreturnorderitems': goodsreturnnote}
            purchaseorderecord.update(purchaseitems)
            purchaseorderecord.update(receiveitems)
            purchaseorderecord.update(goodsitems)
        responseData = {'data': purchaseorderecords, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

    def put(self, request, format=None):

        purchaseorderupdate = purchaseorder.objects.get(id=request.data['id'])
        purchaseorderupdate.template = request.data['template']
        purchaseorderupdate.branchID_id = request.data['branchID']
        purchaseorderupdate.vendorID_id = request.data['vendorID']
        purchaseorderupdate.purchaseordercode = request.data['purchaseordercode']
        purchaseorderupdate.paymentterms = request.data['paymentterms']
        purchaseorderupdate.createdby = request.data['createdby']
        purchaseorderupdate.description = request.data['description']
        purchaseorderupdate.orderdate = request.data['orderdate']
        purchaseorderupdate.duedate = request.data['duedate']
        purchaseorderupdate.currency = request.data['currency']
        purchaseorderupdate.save(update_fields=['template', 'branchID_id', 'vendorID_id', 'purchaseordercode',
                                                'paymentterms', 'description', 'paymentterms', 'description', 'orderdate', 'duedate', 'currency'])
        for purchaseorderitem in request.data['purchaseorderitems']:
            purchaseorderitemupdate = purchaseorderitems.objects.get(
                id=purchaseorderitem['id'])
            purchaseorderitemupdate.productID_id = purchaseorderitem['productID']
            purchaseorderitemupdate.quantity = purchaseorderitem['quantity']
            purchaseorderitemupdate.vendorproductcode = purchaseorderitem['vendorproductcode']
            purchaseorderitemupdate.unitprice = purchaseorderitem['unitprice']
            purchaseorderitemupdate.discountprice = purchaseorderitem['discountprice']
            purchaseorderitemupdate.totalprice = purchaseorderitem['totalprice']
            purchaseorderitemupdate.save(
                update_fields=['productID_id', 'quantity', 'vendorproductcode', 'unitprice', 'discountprice', 'totalprice'])
        responseData = {
            'message': 'The record is updated', 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class vendorView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            vendorcode = randomId()
            serializer = vendorSerializer(data=request.data)
            responseData = {}
            if serializer.is_valid(vendorcode=vendorcode):
                serializer.save()
                responseData = {'message': 'The vendor record is created sucessfully',
                                'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            responseData = {'message': serializer.errors,
                            'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        vendorecords = list(vendor.objects.filter(merchID=merchID).values(
            'id', 'vendorname', 'vendorcontactperson', 'merchID', 'vendoremail', 'vendorcity', 'vendorstate', 'vendorcountry', 'paymentmethod', 'vendoraccountname', 'vendorbankname', 'paymentterms', 'productdetails', 'vendoraddress', 'active').order_by('-created_at'))

        return JsonResponse({'data': vendorecords, 'status': True})

    def delete(self, request, format=None):
        vendorrrecord = vendor.objects.get(id=request.GET.get('id'))
        if vendorrrecord:
            vendorrrecord.delete()
            responseData = {'message': 'Vendor deleted', 'status': True}
        else:
            responseData = {'message': 'Vendor not found', 'status': False}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

    def put(self, request, format=None):
        id = request.data['id']
        vendors = vendor.objects.get(pk=id)
        serializer = vendorSerializer(vendors, data=request.data)
        if serializer.is_valid():
            serializer.save()
            responseData = {'status': True,
                            'data': serializer.data, 'message': 'record updated'}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class createnoteView(APIView):

    def post(self, request, format=None):
        try:
            createnoterecord = receivenote(description=request.data['description'], merchID_id=request.data['merchID'],
                                           branchID_id=request.data['branchID'], vendorID_id=request.data['vendorID'],
                                           purchaseID_id=request.data['purchaseID'], orderdate=request.data['orderdate'])
            createnoterecord.save()
            for notedetail in request.data['notedetails']:
                receivenoteitemrecord = receivenoteitems(
                    receivenoteID_id=createnoterecord.id, productID_id=notedetail[
                        'productID'], quantity=notedetail['quantity'], vendorproductcode=notedetail['vendorproductcode'], unitprice=notedetail['unitprice'], totalprice=notedetail['totalprice'],
                    merchID_id=notedetail['merchID'], receivedate=notedetail['receivedate'])
                receivenoteitemrecord.save()
            responseData = {'message': 'The  record is created sucessfully',
                            'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def put(self, request, format=None):
        receivenoteupdate = receivenote.objects.get(id=request.data['id'])
        receivenoteupdate.description = request.data['description']
        receivenoteupdate.orderdate = request.data['orderdate']
        receivenoteupdate.save(update_fields=['description', 'orderdate'])
        for notedetail in request.data['notedetails']:
            notedetailsupdate = receivenoteitems.objects.get(
                id=notedetail['id'])
            notedetailsupdate.productID_id = notedetail['productID']
            notedetailsupdate.quantity = notedetail['quantity']
            notedetailsupdate.vendorproductcode = notedetail['vendorproductcode']
            notedetailsupdate.unitprice = notedetail['unitprice']
            notedetailsupdate.totalprice = notedetail['totalprice']
            notedetailsupdate.save(
                update_fields=['productID_id', 'quantity', 'vendorproductcode', 'unitprice', 'totalprice'])
        responseData = {
            'message': 'The record is updated', 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class goodsReturnNoteView(APIView):

    def post(self, request, format=None):
        try:
            creategoodreturnrecord = goodsreturnnote(description=request.data['description'], merchID_id=request.data['merchID'],
                                                     branchID_id=request.data['branchID'], vendorID_id=request.data['vendorID'],
                                                     purchaseID_id=request.data['purchaseID'], orderdate=request.data['orderdate'])
            creategoodreturnrecord.save()
            for notedetail in request.data['notedetails']:
                returnnoteitemrecord = goodsreturnnoteitems(
                    goodsreturnnoteID_id=creategoodreturnrecord.id, productID_id=notedetail[
                        'productID'], quantity=notedetail['quantity'], vendorproductcode=notedetail['vendorproductcode'], unitprice=notedetail['unitprice'], totalprice=notedetail['totalprice'],
                    merchID_id=notedetail['merchID'], receivedate=notedetail['receivedate'])
                returnnoteitemrecord.save()
            responseData = {'message': 'The  record is created sucessfully',
                            'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def put(self, request, format=None):
        goodreturnupdate = goodsreturnnote.objects.get(id=request.data['id'])
        goodreturnupdate.description = request.data['description']
        goodreturnupdate.orderdate = request.data['orderdate']
        goodreturnupdate.save(update_fields=['description', 'orderdate'])
        for notedetail in request.data['notedetails']:
            notedetailsupdate = goodsreturnnoteitems.objects.get(
                id=notedetail['id'])
            notedetailsupdate.productID_id = notedetail['productID']
            notedetailsupdate.quantity = notedetail['quantity']
            notedetailsupdate.vendorproductcode = notedetail['vendorproductcode']
            notedetailsupdate.unitprice = notedetail['unitprice']
            notedetailsupdate.totalprice = notedetail['totalprice']
            notedetailsupdate.save(
                update_fields=['productID_id', 'quantity', 'vendorproductcode', 'unitprice', 'totalprice'])
        responseData = {
            'message': 'The record is updated', 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class categoryView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            serializer = categorySerializer(data=request.data)
            responseData = {}
            if serializer.is_valid():
                serializer.save()
                responseData = {'message': 'The category record is created sucessfully',
                                'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            responseData = {'message': serializer.errors,
                            'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        categoryrecord = list(category.objects.filter(merchID=merchID).values(
            'id', 'categoryname', 'categorydescription', 'merchID').order_by('-created_at'))
        print(categoryrecord)
        return JsonResponse({'data': categoryrecord, 'status': True})

    def put(self, request, format=None):
        try:
            categoryupdate = category.objects.get(id=request.data['id'])
            categoryupdate.categoryname = request.data['categoryname']
            categoryupdate.categorydescription = request.data['categorydescription']
            categoryupdate.save(
                update_fields=['categoryname', 'categorydescription'])
            responseData = {
                'message': 'The record is updated', 'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def delete(self, request, format=None):
        categoryrrecord = category.objects.get(id=request.GET.get('id'))
        if categoryrrecord:
            categoryrrecord.delete()
            responseData = {'message': 'Category deleted', 'status': True}
        else:
            responseData = {'message': 'Category not found', 'status': False}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class priceView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            serializer = priceSerializer(data=request.data)
            responseData = {}
            if serializer.is_valid():
                serializer.save()
                responseData = {'message': 'The price record is created sucessfully',
                                'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            responseData = {'message': serializer.errors,
                            'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        pricerecord = list(price.objects.filter(merchID=merchID).values(
            'id', 'price', 'created_at', 'merchID').order_by('-created_at'))
        print(pricerecord)
        return JsonResponse({'data': pricerecord, 'status': True})

    def put(self, request, format=None):
        try:
            priceupdate = price.objects.get(id=request.data['id'])
            priceupdate.price = request.data['price']
            priceupdate.save(
                update_fields=['price'])
            responseData = {
                'message': 'The record is updated', 'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")


class productView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            serializer = productSerializer(data=request.data)
            responseData = {}
            if serializer.is_valid():
                #img_data = base64.b64decode(request.data['photo'])
                #imgext = request.data['productcode']
                #saveimage = receiveImage(img_data, imgext)
                serializer.save()
                print(serializer.data)
                stockrecord = stock(merchID_id=request.data['merchID'], branchID_id=request.data['branchID'], inwardqty=request.data['stockqty'],
                                    productID_id=serializer.data['id'])
                stockrecord.save()
                responseData = {'message': 'The product record is created sucessfully',
                                'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            responseData = {'message': serializer.errors,
                            'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        merchantproductrecords = list(product.objects.filter(merchID=merchID).values(
            'id', 'productcode', 'productname', 'merchID', 'producttype', 'branchID', 'sellingprice',
            'expiration_date', 'categoryID', 'photo', 'productdescription').order_by('-created_at'))
        for merchantproductrecord in merchantproductrecords:
            categoryinfo = category.objects.filter(
                id=merchantproductrecord['categoryID']).values('categoryname').first()
            branchinfo = branch.objects.filter(
                id=merchantproductrecord['branchID']).values('branchname', 'branchaddress').first()
            stockqtyinward = stock.objects.filter(merchID=merchantproductrecord['merchID']).filter(
                branchID=merchantproductrecord['branchID']).filter(productID=merchantproductrecord['id']).aggregate(Sum('inwardqty'))
            stockoutwardqty = stock.objects.filter(merchID=merchantproductrecord['merchID']).filter(
                branchID=merchantproductrecord['branchID']).filter(productID=merchantproductrecord['id']).aggregate(Sum('outwardqty'))
            if not stockoutwardqty['outwardqty__sum']:
                stockoutwardqty['outwardqty__sum'] = float('0.00')
            if not stockqtyinward['inwardqty__sum']:
                stockqtyinward['inwardqty__sum'] = float('0.00')
            stockqtys = float(
                stockqtyinward['inwardqty__sum']) - float(stockoutwardqty['outwardqty__sum'])
            stockqty = {'stockqty': stockqtys}
            merchantproductrecord.update(stockqty)
            if branchinfo:
                merchantproductrecord.update(branchinfo)
            if categoryinfo:
                merchantproductrecord.update(categoryinfo)
            merchantproductrecord['photo'] = "{0}{1}{2}".format(
                settings.APP_URL, '/media/', merchantproductrecord['photo'])
            productfeature = list(productfeatures.objects.filter(
                productID=merchantproductrecord['id']).values('productID', 'featureID', 'priceID'))
            productfeatureinfo = getFeatureProduct(productfeature)
            productfeatureinfos = {'productfeatureinfo': productfeatureinfo}
            merchantproductrecord.update(productfeatureinfos)
        return JsonResponse({'data': merchantproductrecords, 'status': True})

    def put(self, request, format=None):
        try:
            # ot visit and make it sync to stock items
            productrecord = product.objects.get(id=request.data['id'])
            serializer = productSerializer(productrecord, data=request.data)
            if serializer.is_valid():
                serializer.save()
                stockrecord = stock(merchID_id=request.data['merchID'], branchID_id=request.data['branchID'], inwardqty=request.data['stockqty'],
                                    productID_id=request.data['id'])
                stockrecord.save()
                stockqtyinward = stock.objects.filter(merchID=serializer.data['merchID']).filter(
                    branchID=serializer.data['branchID']).filter(productID=serializer.data['id']).aggregate(Sum('inwardqty'))
                stockoutwardqty = stock.objects.filter(merchID=serializer.data['merchID']).filter(
                    branchID=serializer.data['branchID']).filter(productID=serializer.data['id']).aggregate(Sum('outwardqty'))
                if not stockoutwardqty['outwardqty__sum']:
                    stockoutwardqty['outwardqty__sum'] = float('0.00')
                if not stockqtyinward['inwardqty__sum']:
                    stockqtyinward['inwardqty__sum'] = float('0.00')
                stockqtys = float(
                    stockqtyinward['inwardqty__sum']) - float(stockoutwardqty['outwardqty__sum'])
                stockqty = {'stockqty': stockqtys}
                result = {**stockqty, **serializer.data}
                print(result)
                responseData = {'data': result, 'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def delete(self, request, format=None):
        productrecord = product.objects.get(id=request.GET.get('id'))
        if productrecord:
            productrecord.delete()
            responseData = {'message': 'Product deleted', 'status': True}
        else:
            responseData = {'message': 'Product not found', 'status': False}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class featureView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            for feature in request.data['features']:
                featuresrecord = features(featuretype=feature['featuretype'], featurename=feature['featurename'], merchID_id=feature['merchID']
                                          )
                featuresrecord.save()
            responseData = {'message': 'The feature record is created sucessfully',
                            'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        featureproductrecords = list(features.objects.filter(merchID=merchID).values(
            'id', 'featuretype', 'featurename', 'merchID').order_by('-created_at'))
        responseData = {'data': featureproductrecords,
                        'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class productFeatureView(APIView):
    def post(self, request, format=None):
        productfeature = productfeatures(productID_id=request.data['productID'],
                                         featureID_id=request.data['featureID'], priceID_id=request.data['priceID'])
        productfeature.save()
        responseData = {'message': 'The record is created sucessfully',
                        'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class placeOrderView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        try:
            deliverypin = random_with_N_digits(4)
            merchId = request.data['merchID']
            ordercode = get_next_value("order", initial_value=1)
            formatedordercode = "{}{}".format('ON', str(ordercode).zfill(6))
            print(formatedordercode)
            print(request.data)
            delivery = deliveryaddress(area=request.data['area'], state=request.data['state'], longitude=request.data['longitude'], latitude=request.data['latitude'], address=request.data['address'],
                                       city=request.data['city'], landmark=request.data['landmark'], customerID_id=request.data['customerID'])
            delivery.save()
            orderrecord = order(ordercode=formatedordercode, customerID_id=request.data['customerID'], merchID_id=request.data['merchID'], deliveryID_id=delivery.id, ordertotal=request.data['ordertotal'], deliverycharge=request.data['deliverycharge'], ETA=request.data['ETA'],
                                deliverypin=deliverypin, branchID_id=request.data['branchID'],
                                orderstatus=request.data['orderstatus'], deliveryinstruction=request.data[
                                    'deliveryinstruction'], ordertype=request.data['ordertype'], paymentstatus=request.data['paymentstatus'],
                                discountpayment=request.data['discountpayment'], scheduletime=request.data['scheduletime'], ordermethod=request.data['ordermethod'], pickupinfo=request.data['pickupinfo'], ordercategory=request.data['ordercategory'])
            orderrecord.save()
            orderitems = request.data['orders']
            orderitems = saveOrderItems(
                orderitems, orderrecord)
            lastestorder = order.objects.filter(
                id=orderrecord.id).values('id', 'ordercode', 'customerID', 'ordertotal', 'discountpayment', 'merchID').first()
            print(lastestorder)
            # for lastestorderentry in lastestorder:
            print(lastestorder['ordertotal'])
            lastestorder['discountpayment'] = int(
                lastestorder['discountpayment'])
            lastestorder['ordertotal'] = float(
                lastestorder['ordertotal'])
            responseData = {
                'data': lastestorder, 'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        customerID = request.GET.get('customerID')
        orderstatus = request.GET.get('orderstatus')
        ordertype = request.GET.get('ordertype')
        if orderstatus=='assigned':
            status=['pending','assigned']
        elif orderstatus=='in_transit':
            status=['ready_for_dispatch','in_transit']
        elif orderstatus=='completed':
            status=['completed']
        if customerID and orderstatus:
            orderrecords = list(order.objects.filter(customerID=customerID).filter(paymentstatus='PAID').filter(orderstatus__in=status).values('id', 'ordercode', 'deliveryID', 'ordertotal', 'deliverypin', 'sendername', 'senderphone', 'receivername', 'receiverphonenumber', 'scheduletime', 'ETA', 'ordermethod',
                                                                                                             'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'branchID', 'pickupID',
                                                                                                             'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordercategory', 'ordertype', 'merchID', 'created_at').order_by('-created_at'))
         
        elif customerID:
            orderrecords = list(order.objects.filter(customerID=customerID).filter(paymentstatus='PAID').values('id', 'ordercode', 'deliveryID', 'ordertotal', 'deliverypin', 'sendername', 'senderphone', 'receivername', 'receiverphonenumber', 'scheduletime', 'ETA', 'ordermethod',
                                                                                   'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'branchID', 'pickupID',
                                                                                   'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordercategory', 'ordertype', 'merchID', 'created_at').order_by('-created_at'))
        elif orderstatus:
            orderrecords = list(order.objects.filter(merchID=merchID).filter(paymentstatus='PAID').filter(orderstatus=orderstatus).values('id', 'ordercode', 'deliveryID', 'ordertotal', 'deliverypin', 'sendername', 'senderphone', 'receivername', 'receiverphonenumber', 'scheduletime', 'ETA', 'ordermethod',
                                                                                                             'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'branchID', 'pickupID',
                                                                                                             'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordercategory', 'ordertype', 'merchID', 'created_at').order_by('-created_at'))
        elif ordertype:
             orderrecords = list(order.objects.filter(merchID=merchID).filter(paymentstatus='PAID').filter(ordertype=ordertype).values('id', 'ordercode', 'deliveryID', 'ordertotal', 'deliverypin', 'sendername', 'senderphone', 'receivername', 'receiverphonenumber', 'scheduletime', 'ETA', 'ordermethod',
                                                                                                         'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'branchID', 'pickupID',
                                                                                                         'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordercategory', 'ordertype', 'merchID', 'created_at').order_by('-created_at'))
        else:
            orderrecords = list(order.objects.filter(merchID=merchID).filter(paymentstatus='PAID').values('id', 'ordercode', 'deliveryID', 'ordertotal', 'deliverypin', 'sendername', 'senderphone', 'receivername', 'receiverphonenumber', 'scheduletime', 'ETA', 'ordermethod',
                                                                             'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'branchID', 'pickupID',
                                                                                   'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordercategory', 'ordertype', 'merchID', 'created_at').order_by('-created_at'))

        result = getOrders(orderrecords)
        '''
        paginator = LinkHeaderPagination()
        page = paginator.paginate_queryset(result, request)  
        if page is not None:
            return paginator.get_paginated_response(page)
        else:
        '''
        responseData = {'data': result, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class onlinePlaceOrderView(APIView):
    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        branchID = request.GET.get('branchID')
        orderstatus=request.GET.get('orderstatus')
        todaydate = datetime.now().date()
        tomorrow = todaydate + timedelta(days=1)
        currentstartmonth = date(todaydate.year, todaydate.month, 1)
        print(todaydate)
        print(currentstartmonth)
        # todo add sender and receiver as the the ordertype
        if orderstatus:
           orderrecords = list(order.objects.filter(merchID=merchID).filter(orderstatus=orderstatus).filter(created_at__gte=currentstartmonth).filter(created_at__lte=tomorrow).filter(paymentstatus='PAID').filter(branchID=branchID).filter(Q(ordertype='Sender') | Q(ordertype='online') | Q(ordertype='Receiver')).values('id', 'ordercode', 'deliveryID', 'ordertotal', 'deliverypin', 'sendername', 'senderphone', 'receivername', 'receiverphonenumber', 'scheduletime', 'ETA', 'ordermethod','customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'branchID', 'pickupID','debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction','ordercategory', 'ordertype', 'merchID', 'created_at').order_by('-created_at'))

        else:    
           orderrecords = list(order.objects.filter(merchID=merchID).filter(created_at__gte=currentstartmonth).filter(created_at__lte=tomorrow).filter(paymentstatus='PAID').filter(branchID=branchID).filter(Q(ordertype='Sender') | Q(ordertype='online') | Q(ordertype='Receiver')).values('id', 'ordercode', 'deliveryID', 'ordertotal', 'deliverypin', 'sendername', 'senderphone', 'receivername', 'receiverphonenumber', 'scheduletime', 'ETA', 'ordermethod',
                                                                                                                              'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'branchID', 'pickupID',
                                                                                                                              'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordercategory', 'ordertype', 'merchID', 'created_at').order_by('-created_at'))
       
        result = getOrders(orderrecords)

        #paginator = LinkHeaderPagination()
        #page = paginator.paginate_queryset(result, request)
        #if page is not None:
            #return paginator.get_paginated_response(page)
        #else:
        responseData = {'data': result, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class placeDeliveryOrderView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            deliverypin = random_with_N_digits(4)
            if request.data['ordertype'] == 'online':
                ordercode = get_next_value("order", initial_value=1)
                formatedordercode = "{}{}".format(
                    'ON', str(ordercode).zfill(6))
                staffID=None
            else:
                ordercode = get_next_value("order", initial_value=1)
                formatedordercode = "{}{}".format(
                    'WA', str(ordercode).zfill(6))
                staffID=request.data['staffID']
            delivery = deliveryaddress(longitude=request.data['deliverylongitude'], latitude=request.data['deliverylatitude'], address=request.data['deliveryaddress'],
                                       customerID_id=request.data['customerID'])
            delivery.save()
            pickup = pickupaddress(longitude=request.data['pickuplongitude'], latitude=request.data['pickuplatitude'], address=request.data['pickupaddress'],
                                   customerID_id=request.data['customerID'])
            pickup.save()
            try:
                
                orderrecord = order(ordercode=formatedordercode, customerID_id=request.data['customerID'], merchID_id=request.data['merchID'], deliveryID_id=delivery.id, branchID_id=request.data['branchID'], pickupID_id=pickup.id,
                                    ordertotal=request.data['ordertotal'], deliverycharge=request.data['deliverycharge'], ETA=request.data['ETA'], deliverypin=deliverypin, weight=request.data['weight'], itemname=request.data[
                                        'itemname'], itemquantity=request.data['itemquantity'], orderstatus=request.data['orderstatus'], deliveryinstruction=request.data['deliveryinstruction'], ordertype=request.data['ordertype'],
                                    paymentstatus=request.data['paymentstatus'],staffID=staffID,
                                    discountpayment=request.data['discountpayment'], ordermethod=request.data['ordermethod'], ordercategory=request.data['ordercategory'], sendername=request.data['sendername'], senderphone=request.data[
                                        'senderphone'], receivername=request.data['receivername'], receiverphonenumber=request.data['receiverphonenumber'], riderID_id=request.data['riderID'], vechicletype=request.data['vechicletype']
                                    )
                orderrecord.save()
            except KeyError:
                orderrecord = order(ordercode=formatedordercode, customerID_id=request.data['customerID'], merchID_id=request.data['merchID'], deliveryID_id=delivery.id, branchID_id=request.data['branchID'], pickupID_id=pickup.id,
                                    ordertotal=request.data['ordertotal'], deliverycharge=request.data['deliverycharge'], ETA=request.data['ETA'], deliverypin=deliverypin, weight=request.data['weight'], itemname=request.data[
                                        'itemname'], itemquantity=request.data['itemquantity'], orderstatus=request.data['orderstatus'], deliveryinstruction=request.data['deliveryinstruction'], ordertype=request.data['ordertype'],
                                    paymentstatus=request.data['paymentstatus'],staffID=staffID,
                                    discountpayment=request.data['discountpayment'], ordermethod=request.data['ordermethod'], ordercategory=request.data['ordercategory'], sendername=request.data[
                                        'sendername'], senderphone=request.data['senderphone'], receivername=request.data['receivername'], receiverphonenumber=request.data['receiverphonenumber']
                                    )
                orderrecord.save()
                pass
            lastestorder = order.objects.filter(
                id=orderrecord.id).values('id', 'ordercode', 'customerID', 'ordertotal', 'discountpayment', 'merchID','branchID').first()
            # for lastestorderentry in lastestorder:
            print(lastestorder['ordertotal'])
            lastestorder['discountpayment'] = int(
                lastestorder['discountpayment'])
            lastestorder['ordertotal'] = float(
                lastestorder['ordertotal'])
            responseData = {'data': lastestorder, 'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

class placeWebDeliveryOrderView(APIView):
    def post(self, request, format=None):
        #try:
            ordercode = get_next_value("order", initial_value=1)
            formatedordercode = "{}{}".format('WA', str(ordercode).zfill(6))
            staffID=request.data['staffID']
            delivery = deliveryaddress(longitude=request.data['deliverylongitude'], latitude=request.data['deliverylatitude'], address=request.data['deliveryaddress'],
                                       customerID_id=request.data['customerID'])
            delivery.save()
            pickup = pickupaddress(longitude=request.data['pickuplongitude'], latitude=request.data['pickuplatitude'], address=request.data['pickupaddress'],
                                   customerID_id=request.data['customerID'])
            pickup.save()
            try:
                orderrecord = order(ordercode=formatedordercode, customerID_id=request.data['customerID'], merchID_id=request.data['merchID'], deliveryID_id=delivery.id, branchID_id=request.data['branchID'], pickupID_id=pickup.id,
                                    ordertotal=request.data['ordertotal'], deliverycharge=request.data['deliverycharge'], ETA=request.data['ETA'], weight=request.data['weight'], itemname=request.data[
                                        'itemname'], itemquantity=request.data['itemquantity'], orderstatus=request.data['orderstatus'], deliveryinstruction=request.data['deliveryinstruction'], ordertype=request.data['ordertype'],
                                    paymentstatus=request.data['paymentstatus'],staffID=staffID,
                                    discountpayment=request.data['discountpayment'], ordermethod=request.data['ordermethod'], ordercategory=request.data['ordercategory'], sendername=request.data['sendername'], senderphone=request.data[
                                        'senderphone'], receivername=request.data['receivername'], receiverphonenumber=request.data['receiverphonenumber'], riderID_id=request.data['riderID'], vechicletype=request.data['vechicletype']
                                    )
                orderrecord.save()
            except KeyError:
                orderrecord = order(ordercode=formatedordercode, customerID_id=request.data['customerID'], merchID_id=request.data['merchID'], deliveryID_id=delivery.id, branchID_id=request.data['branchID'], pickupID_id=pickup.id,
                                    ordertotal=request.data['ordertotal'], deliverycharge=request.data['deliverycharge'], ETA=request.data['ETA'], weight=request.data['weight'], itemname=request.data[
                                        'itemname'], itemquantity=request.data['itemquantity'], orderstatus=request.data['orderstatus'], deliveryinstruction=request.data['deliveryinstruction'], ordertype=request.data['ordertype'],
                                    paymentstatus=request.data['paymentstatus'],staffID=staffID,
                                    discountpayment=request.data['discountpayment'], ordermethod=request.data['ordermethod'], ordercategory=request.data['ordercategory'], sendername=request.data[
                                        'sendername'], senderphone=request.data['senderphone'], receivername=request.data['receivername'], receiverphonenumber=request.data['receiverphonenumber']
                                    )
                orderrecord.save()
                pass
            lastestorder = order.objects.filter(
                id=orderrecord.id).values('id', 'ordercode', 'customerID', 'ordertotal', 'discountpayment', 'merchID','branchID').first()
            # for lastestorderentry in lastestorder:
            print(lastestorder['ordertotal'])
            lastestorder['discountpayment'] = int(
                lastestorder['discountpayment'])
            lastestorder['ordertotal'] = float(lastestorder['ordertotal'])
            #if request.data['paymentmethod'] == 'multiple':
            for multiple in request.data['multiple']:
                paymentrecord = payment(orderID_id=lastestorder['id'], transactionreference=formatedordercode, customerID_id=request.data['customerID'],
                                        paymentamount=request.data['ordertotal'], paymentmethod=multiple['paymentmethod'], merchID_id=request.data['merchID'], paymentreference=multiple['paymentreference'],paymentaccountname=multiple['paymentaccountname'], paymentaccountnumber=multiple['paymentaccountnumber'], paymentaccountbank=multiple['paymentaccountnumber'])
                paymentrecord.save()
            responseData = {'data': lastestorder, 'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        #except Exception as e:
            #responseData = {'message': 'An error occur' +str(e), 'status': False}
            #return HttpResponse(json.dumps(responseData), content_type="application/json")

class placeWebOrderView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            checkdup = order.objects.filter(ordercode=request.data['ordercode']).filter(merchID_id=request.data['merchID']).values(
                'id', 'ordercode', 'customerID', 'ordertotal', 'discountpayment', 'merchID').first()
            if not checkdup:
                ordercode = get_next_value("order", initial_value=1)
                formatedordercode = formatedordercode = "{}{}".format(
                    'WA', str(ordercode).zfill(6))
                print(formatedordercode)
                todaydate = datetime.now().date()
                if request.data['ordercategory'] == 'Food' or request.data['ordercategory'] == 'Fashion':
                    orderrecord = order(ordercode=formatedordercode, customerID_id=request.data['customerID'], merchID_id=request.data['merchID'], branchID_id=request.data['branchID'], ordertotal=request.data['ordertotal'],
                                        orderstatus=request.data['orderstatus'], ordertype=request.data[
                                            'ordertype'], paymentstatus=request.data['paymentstatus'],staffID=request.data['staffID'],
                                        discountpayment=request.data['discountpayment'], ordermethod=request.data['ordermethod'], ordercategory=request.data['ordercategory'])
                    orderrecord.save()
                    orderitems = request.data['orders']
                    orderitems = saveOrderItems(orderitems, orderrecord)
                    lastestorder = order.objects.filter(id=orderrecord.id).values('id', 'ordercode', 'customerID', 'ordertotal', 'merchID','created_at','branchID').first()                 
                    lastestorder['ordertotal'] = float(lastestorder['ordertotal'])
                    lastestorder['created_at'] = str(lastestorder['created_at'])
                    if request.data['paymentmethod'] == 'multiple':
                        for multiple in request.data['multiple']:
                            paymentrecord = payment(orderID_id=lastestorder['id'], transactionreference=request.data['ordercode'], customerID_id=request.data['customerID'],
                                                    paymentamount=request.data['ordertotal'], paymentmethod=multiple[
                                'paymentmethod'], merchID_id=request.data['merchID'], paymentreference=multiple['paymentreference'],
                                paymentaccountname=multiple['paymentaccountname'], paymentaccountnumber=multiple['paymentaccountnumber'], paymentaccountbank=multiple['paymentaccountnumber'])
                            paymentrecord.save()
                    else:
                        paymentrecord = payment(orderID_id=lastestorder['id'], transactionreference=request.data['ordercode'], customerID_id=request.data['customerID'],
                                                paymentamount=request.data['ordertotal'], paymentmethod=request.data[
                                                    'paymentmethod'], merchID_id=request.data['merchID'], paymentreference=request.data['paymentreference'],
                                                paymentaccountname=request.data['paymentaccountname'], paymentaccountnumber=request.data['paymentaccountnumber'], paymentaccountbank=request.data['paymentaccountnumber'])
                        paymentrecord.save()

                    loyaltyrules = loyaltyrule.objects.filter(merchID=request.data['merchID']).filter(endate__gte=todaydate).values(
                        'id').first()
                    if loyaltyrules:
                        loyaltyruleID = int(loyaltyrules['id'])
                        transactionamount = request.data['ordertotal']
                        receiptno = request.data['ordercode']
                        assignpoint = postAssignedPoint(
                            loyaltyruleID, transactionamount)
                        loyaltytransactionrecord = loyaltytransaction(loyaltyruleID_id=loyaltyruleID, userID_id=request.data['customerID'], merchID_id=request.data['merchID'],
                                                                      transactionamount=transactionamount, assignedpoint=assignpoint, transactiondate=todaydate, receiptno=receiptno)
                        loyaltytransactionrecord.save()
                    #emailnotifiction =eReceipt(lastestorder)
                    #if emailnotifiction:
                    responseData = {'data': lastestorder, 'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData = {'message': 'duplicate record', 'status': False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")


class makePayment(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        # try:
        url = "https://ravesandboxapi.flutterwave.com/flwv3-pug/getpaidx/api/v2/verify"
        #public_key = 'FLWPUBK-a90716eafed1ab1c2fc490448bc76e62-X'
        SEC_key = 'FLWSECK-18cf70d7d6ddbc4d9bbcda245fb18828-X'
        if request.data['paymentmethod'] == "card":
            resp = requests.post(url, json=dict(
                txref=request.data['ordercode'], SECKEY=SEC_key), verify=False,)
            data = resp.text
            data = json.loads(data)
            if data['status'] == "success":

                paymentrecord = payment(orderID_id=request.data['id'], transactionreference=request.data['ordercode'], commissionamount=request.data['commissionamount'],
                                        paymentamount=request.data['paymentamount'], merchID_id=request.data['merchID']
                                        )
                paymentrecord.save()
                orderupdate = order.objects.get(id=request.data['id'])
                orderupdate.paymentstatus = 'PAID' 
                orderupdate.debitcardpayment = request.data['paymentamount']
                orderupdate.save(
                    update_fields=['paymentstatus', 'debitcardpayment'])
                # postCommssion(request.data['id'],request.data['merchID'])
                responseData = {
                    'message':"record created", 'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            else:
                responseData = {
                    'message': data['message'], 'status': False}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
        elif request.data['paymentmethod'] == "giftcard":
            paymentrecord = payment(orderID_id=request.data['id'], transactionreference=request.data['ordercode'],
                                    paymentamount=request.data['paymentamount'], merchID_id=request.data['merchID']
                                    )
            paymentrecord.save()
            orderupdate = order.objects.get(id=request.data['id'])
            orderupdate.paymentstatus = 'PAID'
            orderupdate.giftcardpayment = request.data['paymentamount']
            orderupdate.save(
                update_fields=['paymentstatus', 'giftcardpayment'])
        elif request.data['paymentmethod'] == "points":
            paymentrecord = payment(orderID_id=request.data['id'], transactionreference=request.data['ordercode'],
                                    paymentamount=request.data['paymentamount'], merchID_id=request.data['merchID']
                                    )
            paymentrecord.save()
            orderupdate = order.objects.get(id=request.data['id'])
            orderupdate.paymentstatus = 'PAID'
            orderupdate.loyaltypayment = request.data['paymentamount']
            orderupdate.save(
                update_fields=['paymentstatus', 'loyaltypayment'])

        elif request.data['paymentmethod'] == "wallex":  
            creditvalue = wallextransaction.objects.filter(
                userID=request.data['customerID']).aggregate(Sum('creditamount'))
            debitvalue = wallextransaction.objects.filter(
                userID_id=request.data['customerID']).aggregate(Sum('debitamount'))
            if(creditvalue['creditamount__sum'] is None):
                creditvalue['creditamount__sum'] = float('0.0')
            balance = float(creditvalue['creditamount__sum']) - float(debitvalue['debitamount__sum'])
            if balance >= float(request.data['paymentamount']):
                paymentrecord = payment(orderID_id=request.data['id'], transactionreference=request.data['ordercode'], commissionamount=request.data['commissionamount'],
                                paymentamount=request.data['paymentamount'], merchID_id=request.data['merchID']
                                )
                paymentrecord.save()
                wallexrecord=wallextransaction(userID_id=request.data['customerID'],debitamount=request.data['paymentamount'],receiptno=request.data['ordercode'])
                wallexrecord.save()
                orderupdate = order.objects.get(id=request.data['id'])
                orderupdate.paymentstatus = 'PAID'
                orderupdate.walletpayment = request.data['paymentamount']
                orderupdate.save(
                    update_fields=['paymentstatus', 'walletpayment'])
                responseData = {'message': 'record created',
                                'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            responseData = {'message': 'insufficent balance',
                                'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        # except Exception as e:
        #responseData = {'message': 'An error occur' +str(e), 'status': False}
        # return HttpResponse(json.dumps(responseData), content_type="application/json")


class assignOrder(APIView):
    def post(self, request, format=None):
        #try:

            orderupdate = order.objects.get(id=request.data['orderID'])
            orderupdate.riderID_id = request.data['riderID']
            orderupdate.orderstatus = 'assigned'
            orderupdate.save(update_fields=['riderID', 'orderstatus'])
            orderrecords = list(order.objects.filter(merchID=request.data['merchID']).filter(id=request.data['orderID']).values('id', 'ordercode', 'deliveryID', 'ordertotal','customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'pickupID',
                                                                                                 'debitcardpayment','branchID','paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordertype', 'merchID', 'created_at'))

            result = getOrders(orderrecords)
            data_message = {
                "title" : "New Order",
                "body" : result
            }
            push_service = FCMNotification(api_key="AAAAqJqYUqs:APA91bGAECv7YLwqm9zrK_NPs2VGViNcmTKsl9i3ytTOJWVrxKG8r722v1B2nfTqKCXzyAaPV_U1-k3c8fZJX7_3JJz4Sxbj1eHpY99swoWno09QjKmfLI1sI3OmmRZNUoGhvRHcr0lD")
            riderrecord= rider.objects.filter(id=request.data['riderID']).values('notificationtoken').first()
            if riderrecord:
                df = push_service.single_device_data_message(
                registration_id=riderrecord['notificationtoken'], data_message=data_message)
                print(df)
            responseData = {'message': 'record created', 'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        #except Exception as e:
            #responseData = {'message': 'An error occur' +
                            #str(e), 'status': False}
            #return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        riderID = request.GET.get('riderID')
        customerID = request.GET.get('customerID')

        orderrecords = list(order.objects.filter(merchID=merchID).filter(riderID=riderID).values('id', 'ordercode', 'deliveryID', 'ordertotal','branchID'
                                                                                                 'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'pickupID'
                                                                                                 'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordertype', 'merchID', 'created_at'))
        
        
        
        result = getOrders(orderrecords)
        responseData = {'data': result, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class menuItems(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        branchID = request.GET.get('branchID')
        categoryID = request.GET.get('categoryID')
        
        categorylist= list(category.objects.filter(merchID=merchID).values('categoryname', 'categorydescription', 'id').distinct())  
        if categoryID:
           print("working")
           results = list(category.objects.filter(merchID=merchID).filter(id=categoryID).values('categoryname', 'categorydescription', 'id'))        
        else:
            print("working2")
            results = list(category.objects.filter(merchID=merchID).values(
                'categoryname', 'categorydescription', 'id').distinct())
        finalrecords = []
        for result in results:
            print(result)
            productrecords = list(product.objects.filter(categoryID=result['id']).filter(merchID=merchID).filter(branchID=branchID).values(
                'id', 'productcode', 'productname', 'photo', 'promoID', 'sellingprice', 'branchID', 'productdescription', 'photo2', 'photo3', 'photo4'))
            for counter, productrecord in enumerate(productrecords):
                productrecord['photo'] = "{0}{1}{2}".format(
                    settings.APP_URL, '/media/', productrecord['photo'])
                productrecord['photo2'] = "{0}{1}{2}".format(
                    settings.APP_URL, '/media/', productrecord['photo2'])
                productrecord['photo3'] = "{0}{1}{2}".format(
                    settings.APP_URL, '/media/', productrecord['photo3'])
                productrecord['photo4'] = "{0}{1}{2}".format(
                    settings.APP_URL, '/media/', productrecord['photo4'])
                stockqtyinward = stock.objects.filter(merchID=merchID).filter(
                    branchID=branchID).filter(productID=productrecord['id']).aggregate(Sum('inwardqty'))
                stockoutwardqty = stock.objects.filter(merchID=merchID).filter(
                    branchID=branchID).filter(productID=productrecord['id']).aggregate(Sum('outwardqty'))
                if not stockoutwardqty['outwardqty__sum']:
                    stockoutwardqty['outwardqty__sum'] = float('0.00')
                if not stockqtyinward['inwardqty__sum']:
                    stockqtyinward['inwardqty__sum'] = float('0.00')
                stockqtys = float(
                    stockqtyinward['inwardqty__sum']) - float(stockoutwardqty['outwardqty__sum'])
                stockqty = {'stockqty': stockqtys}
                productrecord.update(stockqty)
                productfeature = list(productfeatures.objects.filter(
                    productID=productrecord['id']).values('id', 'productID', 'featureID', 'priceID'))
                productfeatureinfo = getFeatureProduct(productfeature)
                productfeaturerecord = {"productfeatures": productfeatureinfo}
                productrecord.update(productfeaturerecord)
            paginator = LinkHeaderPagination()
            page = paginator.paginate_queryset(productrecords, request)
            rec = paginator.get_record(page,result['id'])
            finalrecord = {"category": result['categoryname'], 'header': rec,'categorylist':categorylist}
            finalrecords.append(finalrecord)
        for finalrecord in finalrecords:
            for counter, productinfo in enumerate(finalrecord['header']['data']):
                productinfo['sellingprice'] = float(
                    productinfo['sellingprice'])
                featuredescription = getfeatureDescrtipion(
                    productinfo, counter)
                featuredescriptioninfo = {
                    "featuredescriptions": featuredescription}
                productinfo.update(featuredescriptioninfo)
        #paginator = LinkHeaderPagination()
        #page = paginator.paginate_queryset(finalrecords, request)
        # if page is not None:
            # return paginator.get_paginated_response(page)
        responseData = {'data': finalrecords, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class promotionView(APIView):
    def post(self, request, format=None):
        try:
            serializer = promoSerializer(data=request.data)
            responseData = {}
            if serializer.is_valid():
                serializer.save()
                responseData = {'message': 'The promo record is created sucessfully',
                                'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            responseData = {'message': serializer.errors,
                            'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        todaydate = datetime.datetime.now().date()
        print(todaydate)
        promorecord = list(promo.objects.filter(merchID=merchID).filter(enddate__gte=todaydate).values(
            'id', 'promoname', 'promotype', 'merchID', 'promovalue', 'startdate', 'enddate').order_by('-created_at'))
        return JsonResponse({'data': promorecord, 'status': True})

    def put(self, request, format=None):
        try:
            promoupdate = promo.objects.get(id=request.data['id'])
            promoupdate.promotype = request.data['promotype']
            promoupdate.promovalue = request.data['promovalue']
            promoupdate.startdate = request.data['startdate']
            promoupdate.enddate = request.data['enddate']
            promoupdate.save(
                update_fields=['promoname', 'promotype', 'promovalue', 'startdate', 'enddate'])
            responseData = {
                'message': 'The record is updated', 'status': True}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")


class assignProductPromotion(APIView):
    def post(self, request, format=None):
        product.objects.filter(
            id__in=request.data['product']).update(promoID=request.data['promoID'])
        responseData = {'message': 'record updated', 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class reviewView(APIView):
    def post(self, request, format=None):
        try:
            serializer = reviewSerializer(data=request.data)
            responseData = {}
            if serializer.is_valid():
                serializer.save()
                responseData = {'message': 'The review record is created sucessfully',
                                'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            responseData = {'message': serializer.errors,
                            'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        review = list(reviews.objects.filter(merchID=merchID).values(
            'review', 'ratings', 'merchID', 'customername'))
        responseData = {'message': review, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class commissionRateView(APIView):
    def post(self, request, format=None):
        try:
            serializer = commissionSerializer(data=request.data)
            responseData = {}
            if serializer.is_valid():
                serializer.save()
                responseData = {'message': 'The commission record is created sucessfully',
                                'status': True}
                return HttpResponse(json.dumps(responseData), content_type="application/json")
            responseData = {'message': serializer.errors,
                            'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")
        except Exception as e:
            responseData = {'message': 'An error occur' +
                            str(e), 'status': False}
            return HttpResponse(json.dumps(responseData), content_type="application/json")

    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        commissionrecord = list(commission.objects.filter(merchID=merchID).values(
            'riderrate', 'adminrate', 'merchID', 'merchantrate'))
        responseData = {'message': commissionrecord, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class commissionTransactionView(APIView):
    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        commssionrecords = list(commissiontransaction.objects.filter(merchID=merchID).values(
            'ridercommissionamount', 'merchantcomissionamount', 'merchID', 'admincommissionamount', 'receiptno', 'created_at', 'riderID'))
        for commssionrecord in commssionrecords:
            commssionrecord['ridercommissionamount'] = float(
                commssionrecord['ridercommissionamount'])
            commssionrecord['merchantcomissionamount'] = float(
                commssionrecord['merchantcomissionamount'])
            commssionrecord['admincommissionamount'] = float(
                commssionrecord['admincommissionamount'])
            commssionrecord['created_at'] = str(
                commssionrecord['created_at'])
            commssionrecord['riderecord'] = rider.objects.filter(id=commssionrecord['riderID']).values(
                'ridername', 'riderphonenumber', 'riderusername').first()
        responseData = {'message': commssionrecord, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class addstocksViews(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        stocks = stock(branchID_id=request.data['branchID'], merchID_id=request.data['merchID'],
                       productID_id=request.data['productID'], inwardqty=request.data['inwardqty'])
        stocks.save()
        responseData = {'message': 'The record is created sucessfully',
                        'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class barcodesearchView(APIView):
    def get(self, request, format=None):
        merchID = request.GET.get('merchID')
        barcode = request.GET.get('barcode')
        branchID = request.GET.get('branchID')
        print(merchID)
        print(barcode)
        print(branchID)
        productrecord = product.objects.filter(productcode=str(barcode)).filter(merchID=merchID).filter(branchID=branchID).values(
            'id', 'productcode', 'productname', 'photo', 'promoID', 'sellingprice', 'outofstock', 'branchID', 'productdescription', 'photo', 'photo2', 'photo3', 'photo4').first()
        print(productrecord)
        if productrecord:
            productrecord['sellingprice'] = float(
                productrecord['sellingprice'])
            productrecord['photo'] = "{0}{1}{2}".format(
                settings.APP_URL, '/media/', productrecord['photo'])
            productrecord['photo2'] = "{0}{1}{2}".format(
                settings.APP_URL, '/media/', productrecord['photo2'])
            productrecord['photo3'] = "{0}{1}{2}".format(
                settings.APP_URL, '/media/', productrecord['photo3'])
            productrecord['photo4'] = "{0}{1}{2}".format(
                settings.APP_URL, '/media/', productrecord['photo4'])
            stockqtyinward = stock.objects.filter(merchID=merchID).filter(
                branchID=branchID).filter(productID=productrecord['id']).aggregate(Sum('inwardqty'))
            stockoutwardqty = stock.objects.filter(merchID=merchID).filter(
                branchID=branchID).filter(productID=productrecord['id']).aggregate(Sum('outwardqty'))
            if not stockoutwardqty['outwardqty__sum']:
                stockoutwardqty['outwardqty__sum'] = float('0.00')
            if not stockqtyinward['inwardqty__sum']:
                stockqtyinward['inwardqty__sum'] = float('0.00')
            stockqtys = float(
                stockqtyinward['inwardqty__sum']) - float(stockoutwardqty['outwardqty__sum'])
            stockqty = {'stockqty': stockqtys}
            productrecord.update(stockqty)
            productfeature = list(productfeatures.objects.filter(
                productID=productrecord['id']).values('id', 'productID', 'featureID', 'priceID'))
            productfeatureinfo = getFeatureProduct(productfeature)
            productfeaturerecord = {"productfeatures": productfeatureinfo}
            productrecord.update(productfeaturerecord)
            responseData = {'data': productrecord, 'status': True}
        else:
            responseData = {'message': 'product not found', 'status': False}
        return HttpResponse(json.dumps(responseData), content_type="application/json")



class setProductOutStock(APIView):
    def post(self, request, format=None):
        productupdate = product.objects.get(id=request.data['id'])
        productupdate.outofstock = request.data['outofstock']
        productupdate.save(
            update_fields=['outofstock'])
        responseData = {
            'message': 'The record is updated', 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")


class emailReceipt(APIView):
    def post(self, request, format=None):
        template_name = 'ntisa-receipt.html'
        subject='E-Receipt'
        merchantname=merchant.objects.filter(id=request.data['merchID']).values('businessname').first()
        orderrecord = order.objects.filter(id=request.data['orderID']).filter(merchID=request.data['merchID']).filter(branchID=request.data['branchID']).values('id', 'ordercode', 'customerID','ordertotal','created_at').first()
        orderitems=getOrderItems(orderrecord['id'])
        recipientemail =user.objects.filter(id=orderrecord['customerID']).values('emailaddress').first()
        print(recipientemail['emailaddress'])
        from_email = "{0}{1}".format(
            merchantname['businessname'], settings.DEFAULT_FROM_EMAIL)
        context = {'orderdate': orderrecord['created_at'], 'ordercode': orderrecord['ordercode'], 'totalamount': orderrecord['ordertotal'], 'orderitems': orderitems}
        text_content = {}
        html_content = render_to_string(template_name, context)
        #print('Html content {}'.format(html_content))
        email = EmailMultiAlternatives(subject,text_content, from_email,[recipientemail['emailaddress']])
        email.attach_alternative(html_content, "text/html")
        email.send()
        responseData = {
            'message': orderitems, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")



class UserOrders(APIView):
     def get(self, request, format=None):
        username = request.GET.get('username')
        ordercode= request.GET.get('ordercode')
        customerID= user.objects.filter(username=username).values('id').first()
        print(customerID)
        if customerID['id'] and ordercode:                   
            orderrecord = order.objects.filter(customerID=customerID['id']).filter(paymentstatus='PAID').filter(ordercode=ordercode).values('id', 'ordercode', 'deliveryID', 'ordertotal', 'deliverypin', 'sendername', 'senderphone', 'receivername', 'receiverphonenumber', 'scheduletime', 'ETA', 'ordermethod',
                                                                                                                   'customerID', 'deliverycharge', 'discountpayment', 'loyaltypayment', 'giftcardpayment', 'branchID', 'pickupID',
                                                                                                                   'debitcardpayment', 'paymentstatus', 'riderID', 'orderstatus', 'deliveryinstruction', 'ordercategory', 'ordertype', 'merchID', 'created_at').first()
           
            orderitemsrecords = list(orderitems.objects.filter(orderID_id=orderrecord['id']).values('productID', 'id', 'quantity', 'unitprice', 'totalprice', 'productfeatureID'))
            for orderitemsrecord in orderitemsrecords:
                productdetail = product.objects.filter(id=orderitemsrecord['productID']).values('productcode', 'productname','productdescription', 'photo').first()
                if productdetail:
                    productdetail['photo'] = "{0}{1}{2}".format(settings.APP_URL, '/media/', productdetail['photo'])
                    orderitemsrecord.update(productdetail)
                orderitemsrecord['quantity'] = float(orderitemsrecord['quantity'])
                orderitemsrecord['unitprice'] = float(orderitemsrecord['unitprice'])
                orderitemsrecord['totalprice'] = float(orderitemsrecord['totalprice'])
                if orderitemsrecord['productfeatureID']:
                    productfeaturesinfo = productfeatures.objects.filter(
                        id=orderitemsrecord['productfeatureID']).values('featureID', 'priceID').first()
                    featureinfo = features.objects.filter(id=productfeaturesinfo['featureID']).values(
                        'featurename', 'featuretype').first()
                    orderitemsrecord.update(featureinfo)
            merchantdetails = merchant.objects.filter(id=orderrecord['merchID']).values('businessname', 'businessaddress').first()
            if merchantdetails:
               orderrecord.update(merchantdetails)
            customerinfo = user.objects.filter(id=orderrecord['customerID']).values('firstname', 'lastname', 'emailaddress', 'username', 'profilelink', 'phonenumber').first()
            if customerinfo:
                orderrecord.update(customerinfo)
            else:
                orderrecord['firstname'] = ''
                orderrecord['lastname'] = ''
                orderrecord['emailaddress'] = ''
                orderrecord['username'] = ''
                orderrecord['profilelink'] = ''
                orderrecord['phonenumber'] = ''
                # orderrecord.update(customerinfo)
            deliveryinfo = deliveryaddress.objects.filter(
                id=orderrecord['deliveryID']).values('address', 'latitude', 'longitude').first()
            if deliveryinfo:
                deliveryinfo['deliveryaddress'] = deliveryinfo['address']
                deliveryinfo['deliverylatitude'] = deliveryinfo['latitude']
                deliveryinfo['deliverylongitude'] = deliveryinfo['longitude']
                orderrecord.update(deliveryinfo)
            pickupinfo = pickupaddress.objects.filter(id=orderrecord['pickupID']).values(
                'address', 'latitude', 'longitude').first()
            if pickupinfo:
                pickupinfo['pickupaddress'] = pickupinfo['address']
                pickupinfo['pickuplatitude'] = pickupinfo['latitude']
                pickupinfo['pickuplongitude'] = pickupinfo['longitude']
                orderrecord.update(pickupinfo)
            if orderrecord['branchID']:
                branchinfo = branch.objects.filter(id=orderrecord['branchID']).values(
                    'branchname', 'branchaddress', 'branchaddress', 'branchcity').first()
                if branchinfo:
                    orderrecord.update(branchinfo)
            if orderrecord['riderID']:
                riderinfo = rider.objects.filter(id=orderrecord['riderID']).values(
                    'registrationnumber', 'riderfirstname', 'riderlastname', 'riderphonenumber', 'riderphoto',).first()
                riderinfo['riderphoto'] = "{0}{1}".format(
                    settings.APP_URL, riderinfo['riderphoto'])
                ridertrans = ratetransaction.objects.filter(
                    riderID=orderrecord['riderID']).aggregate(Sum('rate'))
                if not ridertrans['rate__sum']:
                    ridertrans['rate__sum'] = float(0.00)
                ridertrans['rate__sum'] = float(ridertrans['rate__sum'])
                orderrecord.update(riderinfo)
                orderrecord.update(ridertrans)
            else:
                orderrecord['rate__sum'] = float(0.00)
                orderrecord['riderfirstname'] = ''
                orderrecord['riderlastname'] = ''
                orderrecord['riderphonenumber'] = ''
                orderrecord['riderphoto'] = "{0}{1}".format(settings.APP_URL, '')
            orderrecord['ordertotal'] = float(orderrecord['ordertotal'])
            orderrecord['deliverycharge'] = float(
                orderrecord['deliverycharge'])
            orderrecord['discountpayment'] = float(
                orderrecord['discountpayment'])
            orderrecord['debitcardpayment'] = float(
                orderrecord['debitcardpayment'])
            orderrecord['loyaltypayment'] = float(
                orderrecord['loyaltypayment'])
            orderrecord['giftcardpayment'] = float(
                orderrecord['giftcardpayment'])
            orderrecord['created_at'] = str(
                orderrecord['created_at'].date())
            orderrecord['orderitems'] = orderitemsrecords
            orderrecord['paymentdetails'] = getPaymentdetails(orderrecord['id']) 
 
        responseData = {
            'data':orderrecord, 'status': True}
        return HttpResponse(json.dumps(responseData), content_type="application/json")

def eReceipt(lastestorder):
        try:
            template_name = 'ntisa-receipt.html'
            subject='E-Receipt'
            print(lastestorder)
            merchantname=merchant.objects.filter(id=lastestorder['merchID']).values('businessname').first()
            orderitems=getOrderItems(lastestorder['id'])
            recipientemail =user.objects.filter(id=lastestorder['customerID']).values('emailaddress').first()
            if recipientemail:
                print(recipientemail['emailaddress'])
                from_email = "{0}{1}".format(
                    merchantname['businessname'], settings.DEFAULT_FROM_EMAIL)
                context = {'orderdate':lastestorder['created_at'], 'ordercode':lastestorder['ordercode'], 'totalamount': lastestorder['ordertotal'], 'orderitems': orderitems}
                text_content = {}
                html_content = render_to_string(template_name, context)
                #print('Html content {}'.format(html_content))
                email = EmailMultiAlternatives(subject,text_content, from_email,[recipientemail['emailaddress']])
                email.attach_alternative(html_content, "text/html")
                email.send()
                return True
            else:
                return True
        except Exception as e:
            return True


def postCommssion(id, merchid):
    commissionrecord = commission.objects.filter(merchID=merchid).values(
        'riderrate', 'adminrate', 'merchantrate').first()
    if commissionrecord['merchantrate']:
        orderrecord = order.objects.filter(id=id).filter(
            merchID=merchid).values('ordertotal', 'ordercode', 'riderID').first()
        rideramount = (
            float(orderrecord['ordertotal'])*float(commissionrecord['riderrate']))/100
        merchantamount = (
            float(orderrecord['ordertotal'])*float(commissionrecord['merchantrate']))/100
        adminamount = (
            float(orderrecord['ordertotal'])*float(commissionrecord['adminrate']))/100
        commtransaction = commissiontransaction(riderID_id=orderrecord['riderID'], ridercommissionamount=rideramount, merchantcomissionamount=merchantamount,
                                                admincommissionamount=adminamount, merchID_id=merchid, receiptno=orderrecord['ordercode'])
        commtransaction.save()
    return True


def getbusinessinfo(businessdescription):
    results = list(merchant.objects.filter(
        businessdescription=businessdescription).values('id', 'businessname',
                                                        'merchantphonenumber', 'businessaddress', 'businesslogo'))
    for result in results:
        result['category'] = getProductCategories(result['id'])
        result['rank'] = reviews.objects.filter(
            merchID=result['id']).aggregate(Avg('ratings'))
        result['feedbacks'] = list(reviews.objects.filter(
            merchID=result['id']).values('review', 'customername'))
    return results


def getProductCategories(id):
    categories = list(category.objects.filter(merchID=id).values('id',
                                                                 'categoryname', 'categorydescription', 'merchID'))
    todaydate = datetime.datetime.now().date()
    for categoryrecord in categories:
        productrecords = list(product.objects.filter(categoryID=categoryrecord['id']).values(
            'productcode', 'productname', 'sellingprice', 'photo', 'promoID'))
        for productrecord in productrecords:
            productrecord['sellingprice'] = float(
                productrecord['sellingprice'])
            productrecord['photo'] = "{0}{1}".format(
                settings.APP_URL, productrecord['photo'])
            if productrecord['promoID']:
                productrecord['promo'] = promo.objects.filter(id=productrecord['promoID']).filter(
                    enddate__gte=todaydate).values('promoname', 'promotype', 'promovalue').first()
            else:
                productrecord['promo'] = {}
        categoryrecord['products'] = productrecords
    return categories


def getOrders(orderrecords):
    for orderrecord in orderrecords:
        merchantdetails = merchant.objects.filter(id=orderrecord['merchID']).values(
            'businessname', 'businessaddress').first()
        if merchantdetails:
            orderrecord.update(merchantdetails)
        customerinfo = user.objects.filter(id=orderrecord['customerID']).values(
            'firstname', 'lastname', 'emailaddress', 'username', 'profilelink', 'phonenumber').first()
        print(orderrecord['customerID'])
        print(customerinfo)
        if customerinfo:
            orderrecord.update(customerinfo)
        else:
            orderrecord['firstname'] = ''
            orderrecord['lastname'] = ''
            orderrecord['emailaddress'] = ''
            orderrecord['username'] = ''
            orderrecord['profilelink'] = ''
            orderrecord['phonenumber'] = ''
            # orderrecord.update(customerinfo)
        deliveryinfo = deliveryaddress.objects.filter(
            id=orderrecord['deliveryID']).values('address', 'latitude', 'longitude').first()
        if deliveryinfo:
            deliveryinfo['deliveryaddress'] = deliveryinfo['address']
            deliveryinfo['deliverylatitude'] = deliveryinfo['latitude']
            deliveryinfo['deliverylongitude'] = deliveryinfo['longitude']
            orderrecord.update(deliveryinfo)
        pickupinfo = pickupaddress.objects.filter(id=orderrecord['pickupID']).values(
            'address', 'latitude', 'longitude').first()
        if pickupinfo:
            pickupinfo['pickupaddress'] = pickupinfo['address']
            pickupinfo['pickuplatitude'] = pickupinfo['latitude']
            pickupinfo['pickuplongitude'] = pickupinfo['longitude']
            orderrecord.update(pickupinfo)
        if orderrecord['branchID']:
            branchinfo = branch.objects.filter(id=orderrecord['branchID']).values(
                'branchname', 'branchaddress', 'branchaddress', 'branchcity').first()
            if branchinfo:
                orderrecord.update(branchinfo)
        if orderrecord['riderID']:
            riderinfo = rider.objects.filter(id=orderrecord['riderID']).values(
                'registrationnumber', 'riderfirstname', 'riderlastname', 'riderphonenumber', 'riderphoto',).first()
            riderinfo['riderphoto'] = "{0}{1}".format(
                settings.APP_URL, riderinfo['riderphoto'])
            ridertrans = ratetransaction.objects.filter(
                riderID=orderrecord['riderID']).aggregate(Sum('rate'))
            if not ridertrans['rate__sum']:
                ridertrans['rate__sum'] = float(0.00)
            ridertrans['rate__sum'] = float(ridertrans['rate__sum'])
            orderrecord.update(riderinfo)
            orderrecord.update(ridertrans)
        else:
            orderrecord['rate__sum'] = float(0.00)
            orderrecord['riderfirstname'] = ''
            orderrecord['riderlastname'] = ''
            orderrecord['riderphonenumber'] = ''
            orderrecord['riderphoto'] = "{0}{1}".format(settings.APP_URL, '')
        orderitems = getOrderItems(orderrecord['id'])
        orderrecord['ordertotal'] = float(orderrecord['ordertotal'])
        orderrecord['deliverycharge'] = float(
            orderrecord['deliverycharge'])
        orderrecord['discountpayment'] = float(
            orderrecord['discountpayment'])
        orderrecord['debitcardpayment'] = float(
            orderrecord['debitcardpayment'])
        orderrecord['loyaltypayment'] = float(
            orderrecord['loyaltypayment'])
        orderrecord['giftcardpayment'] = float(
            orderrecord['giftcardpayment'])
        orderrecord['created_at'] = str(
            orderrecord['created_at'].date())
        orderrecord['orderitems'] = orderitems
        orderrecord['paymentdetails'] = getPaymentdetails(orderrecord['id'])
    return orderrecords


def getOrderItems(id):
    orderitemsrecords = list(orderitems.objects.filter(orderID_id=id).values(
        'productID', 'id', 'quantity', 'unitprice', 'totalprice', 'productfeatureID'))
    for orderitemsrecord in orderitemsrecords:
        productdetail = product.objects.filter(
            id=orderitemsrecord['productID']).values('productcode', 'productname','productdescription', 'photo').first()
        if productdetail:
            productdetail['photo'] = "{0}{1}{2}".format(
                settings.APP_URL, '/media/', productdetail['photo'])
            orderitemsrecord.update(productdetail)
        orderitemsrecord['quantity'] = float(orderitemsrecord['quantity'])
        orderitemsrecord['unitprice'] = float(orderitemsrecord['unitprice'])
        orderitemsrecord['totalprice'] = float(orderitemsrecord['totalprice'])
        if orderitemsrecord['productfeatureID']:
            productfeaturesinfo = productfeatures.objects.filter(
                id=orderitemsrecord['productfeatureID']).values('featureID', 'priceID').first()
            featureinfo = features.objects.filter(id=productfeaturesinfo['featureID']).values(
                'featurename', 'featuretype').first()
            orderitemsrecord.update(featureinfo)

    return orderitemsrecords


def getPaymentdetails(id):
    paymentrecords = list(payment.objects.filter(orderID_id=id).values('id',
                                                                       'transactionreference', 'paymentamount', 'paymentmethod'))
    for paymentrecord in paymentrecords:
        paymentrecord['paymentamount'] = float(paymentrecord['paymentamount'])
    return paymentrecords


def saveOrderItems(orderitemrecords, order):
    for orderitem in orderitemrecords:
        if ('productfeatureID' in orderitem):
            orderitems.objects.create(orderID_id=order.id,
                                      productID_id=orderitem['productid'], quantity=orderitem['quantity'],
                                      unitprice=orderitem['price'], productfeatureID_id=orderitem['productfeatureID'],
                                      totalprice=orderitem['totalamount'])
        else:
            orderitems.objects.create(orderID_id=order.id,
                                      productID_id=orderitem['productid'], quantity=orderitem['quantity'],
                                      unitprice=orderitem['price'],
                                      totalprice=orderitem['totalamount'])
        stockrecord = stock(merchID_id=order.merchID_id, branchID_id=order.branchID_id, outwardqty=orderitem['quantity'],
                            productID_id=orderitem['productid'])
        stockrecord.save()
    return True


def getFeatureProduct(productfeature):
    for feature in productfeature:
        featureinfo = features.objects.filter(id=feature['featureID']).values(
            'featuretype', 'featurename').first()
        if featureinfo:
            priceinfo = price.objects.filter(
                id=feature['priceID']).values('price').first()
        if priceinfo:
            priceinfo['price'] = float(priceinfo['price'])
            feature.update(featureinfo)
            feature.update(priceinfo)
    return productfeature


def receiveImage(img_data, imgext):
    save_path = os.path.join(settings.BASE_DIR, 'productimage', imgext+'.png')
    databasepath = '/productimage/'+imgext+'.png'
    print(databasepath)
    with open(save_path, "wb") as fh:
        fh.write(img_data)
    return databasepath


def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1

    return randint(range_start, range_end)


def getPurchaseItems(purchaseorderecord):
    print(purchaseorderecord)
    purchaseorderitemsrecords = list(purchaseorderitems.objects.filter(
        purchaseID=purchaseorderecord['id']).values('id', 'productID', 'quantity', 'vendorproductcode', 'unitprice', 'discountprice', 'totalprice', 'merchID'))

    for purchaseorderitemsrecord in purchaseorderitemsrecords:
        productinfo = product.objects.filter(id=purchaseorderitemsrecord['productID']).values(
            'productname', 'productcode').first()
        purchaseorderitemsrecord.update(productinfo)
        purchaseorderitemsrecord['quantity'] = float(
            purchaseorderitemsrecord['quantity'])
        purchaseorderitemsrecord['unitprice'] = float(
            purchaseorderitemsrecord['unitprice'])
        purchaseorderitemsrecord['discountprice'] = float(
            purchaseorderitemsrecord['discountprice'])
        purchaseorderitemsrecord['totalprice'] = float(
            purchaseorderitemsrecord['totalprice'])
    return purchaseorderitemsrecords


def getReceiveNote(purchaseorderecord):
    receivenoterecords = list(receivenote.objects.filter(
        purchaseID=purchaseorderecord['id']).values('id', 'description', 'vendorID', 'orderdate'))
    for receivenoterecord in receivenoterecords:
        receivenoterecord['orderdate'] = str(receivenoterecord['orderdate'])
        receivenoteiteminfos = list(receivenoteitems.objects.filter(
            receivenoteID=receivenoterecord['id']).values('id', 'productID', 'quantity', 'vendorproductcode', 'unitprice', 'totalprice', 'receivedate'))
        for receivenoteiteminfo in receivenoteiteminfos:
            productinfo = product.objects.filter(id=receivenoteiteminfo['productID']).values(
                'productname', 'productcode').first()
            receivenoteiteminfo['quantity'] = float(
                receivenoteiteminfo['quantity'])
            receivenoteiteminfo['unitprice'] = float(
                receivenoteiteminfo['unitprice'])
            receivenoteiteminfo['totalprice'] = float(
                receivenoteiteminfo['totalprice'])
            receivenoteiteminfo['receivedate'] = str(
                receivenoteiteminfo['receivedate'])
            receivenoteiteminfo.update(productinfo)
        result = {'receivenoteitems': receivenoteiteminfos}
        receivenoterecord.update(result)
    return receivenoterecords


def getGoodsReturnNote(purchaseorderecord):
    goodsreturnnoterecords = list(goodsreturnnote.objects.filter(
        purchaseID=purchaseorderecord['id']).values('id', 'description', 'vendorID', 'orderdate'))
    for goodsreturnnoterecord in goodsreturnnoterecords:
        goodsreturnnoterecord['orderdate'] = str(
            goodsreturnnoterecord['orderdate'])
        goodsreturnnoteitemrecord = list(goodsreturnnoteitems.objects.filter(
            goodsreturnnoteID=goodsreturnnoterecord['id']).values('id', 'productID', 'quantity', 'vendorproductcode', 'unitprice', 'totalprice', 'receivedate'))
        for goodsreturnnoterecordinfo in goodsreturnnoteitemrecord:
            productinfo = product.objects.filter(id=goodsreturnnoterecordinfo['productID']).values(
                'productname', 'productcode').first()
            goodsreturnnoterecordinfo['quantity'] = float(
                goodsreturnnoterecordinfo['quantity'])
            goodsreturnnoterecordinfo['unitprice'] = float(
                goodsreturnnoterecordinfo['unitprice'])
            goodsreturnnoterecordinfo['totalprice'] = float(
                goodsreturnnoterecordinfo['totalprice'])
            goodsreturnnoterecordinfo['receivedate'] = str(
                goodsreturnnoterecordinfo['receivedate'])
            goodsreturnnoterecordinfo.update(productinfo)
        result = {'goodsreturnnoteitems': goodsreturnnoteitemrecord}
        goodsreturnnoterecord.update(result)
    return goodsreturnnoterecords


def getfeatureDescrtipion(productinfo, counter):
    for productdetails in productinfo['productfeatures']:
        try:
            if productdetails['featuretype'] == 'size' or productdetails['featuretype'] == 'weight' or productdetails['color'] == 'weight':
                finaldicrecord = {
                    "feature": productdetails['featurename'], "price": productdetails['price']}
            productdetails.update(finaldicrecord)
        except KeyError:
            pass
    return productinfo['productfeatures']


def randomId():
    for x in range(10):
        randomnumber = str(random.randint(1, 10000000001))
        confirmrandomnumber = vendor.objects.filter(
            vendorcode=randomnumber).values('vendorcode')
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
            randomnumber = str(random.randint(1, 10000001))
            confirmrandomnumber = vendor.objects.filter(
                vendorcode=randomnumber).values('vendorcode')
            return randomnumber


def orderCode(merchID, O):
    for x in range(10):
        randomnumber = str(random.randint(1, 10000000001))
        confirmrandomnumber = order.objects.filter(
            merchID=merchID).values('ordercode').first()
        if not confirmrandomnumber:
            return randomnumber
        else:
            randomnumber = str(random.randint(1, 10000001))
            confirmrandomnumber = merchant.objects.filter(
                serviceID=randomnumber).values('serviceID')
            return randomnumber



    
def validateMerchantRider(merchID):
    #merchID=77
    merchlicense = ntisamerchantlicensetransaction.objects.filter(merchID=merchID).values(
        'id', 'licenseID', 'startdate', 'duration', 'created_at', 'merchID', 'addtionalrider', 'addtionalorder', 'addtionalusers', 'istrial').last()
    startdate=merchlicense['created_at']
    duration = merchlicense['duration']
    licenserider=ntisalicense.objects.filter(id=merchlicense['licenseID']).values('nosofriders').first()
    addtionalrider=merchlicense['addtionalrider']
    if not(addtionalrider):
        addtionalrider=int(0)
    else:
        addtionalrider = int(merchlicense['addtionalrider'])
    if duration =='monthly':
        expirationdate = startdate + timedelta(days=30)   
        numberofriders=addtionalrider.objects.filter(merchID=merchID).filter(created_at__gte=startdate).filter(created_at__lte=expirationdate).aggregate(number_of_entry=Count('id'))
        if int(numberofriders['number_of_entry']) <= (int(licenserider['nosofriders']) + int(addtionalrider)):
           print("working")
           return True
        else:
            print("not working")
            return False
    return HttpResponse(None)


