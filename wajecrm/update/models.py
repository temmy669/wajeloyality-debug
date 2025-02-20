# Create your models here.
from __future__ import unicode_literals

from django.db import models

from datetime import datetime 
# Create your models here.

class merchant(models.Model):
    serviceID =  models.CharField(max_length=255,null=True)
    businessname = models.CharField(max_length=45,null=True)
    merchantphonenumber = models.CharField(max_length=45,null=True)
    businessaddress = models.CharField(max_length=45,null=True)
    merchantemailaddress = models.CharField(max_length=45,null=True)
    merchantpassword= models.CharField(max_length=255,null=True)
    contactpersonfirstname = models.CharField(max_length=255,null=True)
    country = models.CharField(max_length=255,null=True)
    currency = models.CharField(max_length=255,null=True)
    contactpersonlastname = models.CharField(max_length=255,null=True)
    contactpersonphone= models.CharField(max_length=255,null=True)
    themecolor = models.CharField(max_length=255,null=True)
    themecolorlight = models.CharField(max_length=255,null=True)
    themetextcolor = models.CharField(max_length=255,null=True)
    themetitlecolor = models.CharField(max_length=255,null=True)
    themebordercolor = models.CharField(max_length=255,null=True)
    businesslogo = models.ImageField(upload_to="merchantlogo/")
    active = models.BooleanField(default=0)
    rate = models.DecimalField(max_digits=10,decimal_places=2,null=False,default=1)
    settingsactivated = models.BooleanField(default=0)
    businessdescription = models.CharField(max_length=255,null=True)
    businessfacebook = models.CharField(max_length=45,null=True)
    businesstwitter = models.CharField(max_length=45,null=True)
    bankname= models.CharField(max_length=255,null=False)
    accountnumber = models.CharField(max_length=255,null=False)
    accountname =models.CharField(max_length=255,null=False)
    createddate = models.DateField(auto_now_add=True)
    updateddate = models.DateField('updateddate',null=True)
    class Meta:
          ordering = ['serviceID']

class customer(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=45)
    firstname = models.CharField(max_length=45)
    lastname = models.CharField(max_length=45)
    emailaddress = models.CharField(max_length=45)
    gender = models.CharField(max_length=45)
    customerIdentifier = models.CharField(max_length=45)
    addressdetails = models.CharField(max_length=45)
    facebooklink = models.CharField(max_length=45,null=True)
    twitterlink = models.CharField(max_length=45,null=True)
    instagramlink = models.CharField(max_length=45,null=True)
    transactionpin = models.CharField(max_length=45,null=True)   
    DOB = models.DateField('date_of_birth',null=True)
    active = models.BooleanField(default=1)
    merchID = models.ForeignKey(merchant, on_delete=models.CASCADE)
    createddate = models.DateField('createddate',auto_now_add=True)
    updateddate = models.DateField('updateddate',null=True)

class loyaltyrule(models.Model):
    loyaltyrule= models.CharField(max_length=45)
    rewardpoint = models.CharField(max_length=45,null=True)
    amountspent = models.DecimalField(max_digits=10,decimal_places=2,null=True)
    startdate = models.DateField('createddate',null=True)
    endate = models.DateField('updateddate',null=True)
    merchID = models.ForeignKey(merchant, on_delete=models.CASCADE)
    status = models.BooleanField(default=1)
    createddate = models.DateField('createddate',auto_now_add=True)
    updateddate = models.DateField('updateddate',null=True)

class loyaltytransaction(models.Model):
    loyaltyruleID =models.ForeignKey(loyaltyrule,on_delete=models.CASCADE,null=True)
    CustID = models.ForeignKey(customer, on_delete=models.CASCADE,null=True)
    merchID = models.ForeignKey(merchant, on_delete=models.CASCADE)
    receiptno = models.CharField(max_length=100,unique=True)
    description = models.TextField(max_length=400,null=True)
    transactionamount=models.DecimalField(max_digits=10,decimal_places=2,null=True)
    assignedpoint=models.DecimalField(default=0,max_digits=10,decimal_places=2)
    redeemedpoint=models.DecimalField(default=0,max_digits=10,decimal_places=2)
    transactiondate = models.DateField('transctiondate',null=True)
    createddate = models.DateField('createddate',auto_now_add=True) 
    updateddate = models.DateField('updateddate',null=True)

class campaigntemplate(models.Model):
    title = models.CharField(max_length=45)
    body = models.CharField(max_length=255,null=True)
    preview_body = models.CharField(max_length=255,null=True)
    active = models.BooleanField(default=1)
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    createddate = models.DateField('createddate',auto_now_add=True, null=True)
    updateddate = models.DateField('updateddate',null=True)

class campaigns(models.Model):
    title = models.CharField(max_length=45)
    merchID = models.ForeignKey(merchant, on_delete=models.CASCADE)
    campaigntype=models.CharField(max_length=45)
    interval = models.CharField(max_length=100)
    startdate = models.DateField(null=True)
    enddate= models.DateField(null=True)
    tempateID=models.ForeignKey(campaigntemplate,on_delete=models.CASCADE,null=True)
    active = models.BooleanField(default=1)
    createddate = models.DateField('createddate',auto_now_add=True, null=True)
    updateddate = models.DateField('updateddate',null=True)

class campaignhistory(models.Model):
    merchantname = models.CharField(max_length=45)
    customeremail = models.CharField(max_length=255,null=True)
    campaigntype = models.CharField(max_length=255,null=True)
    templatename=models.CharField(max_length=45,null=True)
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    subject=models.CharField(max_length=45,null=True)
    createddate = models.DateField('createddate',auto_now_add=True,null= True)
    updateddate = models.DateField('updateddate',null=True)

class giftCard(models.Model):
    serialnumber =models.CharField(null=True,max_length=200,unique=True)
    cardname = models.CharField(null=True,max_length=200)
    recipient_phone = models.CharField(null=True,max_length=200)
    amount= models.DecimalField(default=0, max_digits=16, decimal_places=6)
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    expiration_date = models.DateTimeField(auto_now_add=False)
    created_at = models.DateTimeField(auto_now_add=True)

class giftcardtransaction(models.Model):
    giftID = models.ForeignKey(giftCard,on_delete=models.CASCADE,null=True)
    redeemedamount= models.DecimalField(default=0, max_digits=16, decimal_places=6)
    purchaseamount= models.DecimalField(default=0, max_digits=16, decimal_places=6)
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class plan(models.Model):
    initial_minimum_user =models.CharField(null=True,max_length=200,unique=True)
    price = models.DecimalField(default=0, max_digits=16, decimal_places=6)
    subsequent_minimum = models.CharField(null=True,max_length=200)
    number_of_days = models.CharField(null=True,max_length=200)
    billing_interval = models.CharField(null=True,max_length=200)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

class contract(models.Model):
    planID = models.ForeignKey(plan,on_delete=models.CASCADE,null=True)
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    contract_start_date = models.DateTimeField(auto_now_add=True)
    contract_end_date =  models.DateTimeField(auto_now_add=True)
    number_of_license =models.CharField(null=True,max_length=200,unique=True)
    active = models.BooleanField(default=0)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

class contracttransaction(models.Model):
    contractID = models.ForeignKey(contract,on_delete=models.CASCADE,null=True) 
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    transaction_amount = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    transaction_date =  models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

class voucher(models.Model):
    ID = models.CharField(null=True,max_length=50)
    CUSTOMERCODE=models.CharField(null=True,max_length=50)
    Amount = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    DateCreated = models.DateTimeField(auto_now_add=True,null=True)
    CreatedBy = models.CharField(null=True,max_length=50)
    OtherInfo=models.CharField(null=True,max_length=50)
    class Meta:
          db_table ='voucher'

class vouchertransactions(models.Model):
    ID = models.CharField(null=True,max_length=50)
    Invoicenumber=models.DecimalField(default=0,max_digits=16,decimal_places=6)
    DateUsed = models.DateTimeField(auto_now_add=True,null=True)
    Credit = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    Debit = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    Particular =  models.CharField(null=True,max_length=50)
    class Meta:
          db_table ='vouchertransactions'

class listvouchertransactions(models.Model):
    ID = models.CharField(null=True,max_length=50)
    Invoicenumber=models.DecimalField(default=0,max_digits=16,decimal_places=6)
    DateUsed = models.DateTimeField(auto_now_add=True,null=True)
    Credit = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    Debit = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    Particular =  models.CharField(null=True,max_length=50)
    recno =  models.IntegerField(null=True)
    class Meta:
          db_table ='vouchertransactions'
    


   
