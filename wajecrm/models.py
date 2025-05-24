# Create your models here.
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from enum import Enum

from datetime import datetime
from django.utils import timezone
#from django.core.exceptions import FieldDoesNotExist 

from safedelete.models import SafeDeleteModel
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


# Create your models here.

role_choices =(
     ('admin', 'Admin'), 
     ('accountant', 'Accountant'),
     ('auditor', 'Auditor'),
     ('manager', 'Manager'))

class Role(models.Model):
    #id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, 
                            choices=role_choices, 
                            default='admin')
    

    def __str__(self):
         return self.name
    

class merchant(models.Model):
    serviceID =  models.CharField(max_length=255,null=True)
    businessname = models.CharField(max_length=45,null=True)
    merchantphonenumber = models.CharField(max_length=45,null=True)
    businessaddress = models.CharField(max_length=45,null=True)
    merchantemailaddress = models.CharField(max_length=45,null=True)
    merchantpassword= models.CharField(max_length=255,null=True)
    contactpersonfirstname = models.CharField(max_length=255,null=True)
    country = models.CharField(max_length=255,null=True)
    country_state = models.CharField(max_length=255,null=True)
    country_city = models.CharField(max_length=255,null=True)
    currency = models.CharField(max_length=255,null=True)
    contactpersonlastname = models.CharField(max_length=255,null=True)
    contactpersonphone= models.CharField(max_length=255,null=True)
    themecolor = models.CharField(max_length=255,default="default")
    themecolorlight = models.CharField(max_length=255,null=True)
    themetextcolor = models.CharField(max_length=255,null=True)
    themetitlecolor = models.CharField(max_length=255,null=True)
    themebordercolor = models.CharField(max_length=255,null=True)
    businesslogo = models.ImageField(upload_to="merchantlogo/")
    active = models.BooleanField(default=0)
    rate = models.DecimalField(max_digits=10,decimal_places=2,null=False,default=1)
    settingsactivated = models.BooleanField(default=1)
    businessdescription = models.CharField(max_length=255,null=True)
    businessfacebook = models.CharField(max_length=45,null=True)
    businesstwitter = models.CharField(max_length=45,null=True)
    bankname= models.CharField(max_length=255,null=False)
    pointname= models.CharField(max_length=255,null=True,default='point')
    accountnumber = models.CharField(max_length=255,null=False)
    accountname =models.CharField(max_length=255,null=False)
    createddate = models.DateField(auto_now_add=True)
    updateddate = models.DateField('updateddate',null=True)
    class Meta:
          ordering = ['serviceID']

    def __str__(self):
         return self.businessname

class branch(models.Model):
    branchcode= models.CharField(max_length=45,null=True)
    branchname= models.CharField(max_length=45,null=True)
    branchaddress= models.CharField(max_length=45,null=True)
    branchstate = models.CharField(max_length=45,null=True)
    branchcity = models.CharField(max_length=45,null=True)
    branchofficeline = models.CharField(max_length=45,null=True)
    merchID = models.ForeignKey(merchant, on_delete=models.CASCADE, related_name='branches')
    createddate = models.DateField('createddate',auto_now_add=True)
    updateddate = models.DateField('updateddate',null=True)

    def __str__(self):
         return self.branchname

class customer(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=45,null=True)
    firstname = models.CharField(max_length=45,null=True)
    lastname = models.CharField(max_length=45,null=True)
    emailaddress = models.CharField(max_length=45,null=True)
    gender = models.CharField(max_length=45)
    password = models.CharField(max_length=225,null=True)
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

    def __str__(self):
         return self.firstname

class attachment(models.Model):
    body= models.CharField(max_length=45)
    name = models.CharField(max_length=45, null=True)
    merchID = models.ForeignKey(merchant, on_delete=models.CASCADE)
    createddate = models.DateField('createddate',auto_now_add=True)
    updateddate = models.DateField('updateddate',null=True)

class user(models.Model):
    username= models.CharField(max_length=45)
    name= models.CharField(max_length=45,null=True)
    userpassword= models.CharField(max_length=255,null=True)
    branchID = models.ForeignKey(branch, on_delete=models.CASCADE)
    merchID = models.ForeignKey(merchant, on_delete=models.CASCADE)
    createddate = models.DateField('createddate',auto_now_add=True)
    updateddate = models.DateField('updateddate',null=True)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)

    
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

class crosscampaignrule(models.Model):
    campaignrulename= models.CharField(max_length=45)
    item = models.ImageField(upload_to="crosspromotion/",null=True)
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
    receiptno = models.CharField(max_length=100,null=True)
    description = models.TextField(max_length=400,null=True)
    transactionamount=models.DecimalField(default=0,max_digits=60,decimal_places=2,null=True)
    assignedpoint=models.DecimalField(default=0,max_digits=10,decimal_places=4)
    redeemedpoint=models.DecimalField(default=0,max_digits=10,decimal_places=2)
    transactiondate = models.DateField('transctiondate',null=True)
    createddate = models.DateField('createddate',auto_now_add=True) 
    updateddate = models.DateField('updateddate',null=True)
    campaignstatus = models.BooleanField(default=0)

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
    campaign_channel = models.CharField(max_length=255,null=True)
    templatename=models.CharField(max_length=45,null=True)
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    subject=models.CharField(max_length=45,null=True)
    createddate = models.DateField('createddate',auto_now_add=True,null= True)
    updateddate = models.DateField('updateddate',null=True)

class giftCard(models.Model):
    serialnumber =models.CharField(null=True,max_length=200)
    cardname = models.CharField(null=True,max_length=200)
    recipient_phone = models.CharField(null=True,max_length=200)
    recipient_email = models.CharField(null=True,max_length=200)
    amount= models.DecimalField(default=0, max_digits=16, decimal_places=6)
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    active = models.BooleanField(default=1)
    # deleted = models.DateField('deleted',null=True)
    expiration_date = models.DateField(auto_now_add=False)
    createddate = models.DateTimeField(auto_now_add=True)
    createdby = models.ForeignKey('user', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.cardname
    
class giftcardtransaction(models.Model):
    giftID = models.ForeignKey(giftCard,on_delete=models.CASCADE,null=True)
    redeemedamount= models.DecimalField(default=0, max_digits=16, decimal_places=6)
    purchaseamount= models.DecimalField(default=0, max_digits=16, decimal_places=6)
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    branch = models.ForeignKey(branch, on_delete=models.DO_NOTHING, blank=True, null=True)
    reference =models.CharField(null=True,max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    createdby = models.CharField(null=True, max_length=200)
    
    def __str__(self):
         return self.reference

class AccountantData(models.Model):
    amount = models.DecimalField(max_digits=16, decimal_places=2)  
    cardName = models.CharField(max_length=200) 
    confirmationCode = models.CharField(max_length=20, unique=True)  
    transactionRef = models.CharField(max_length=255, unique=True)  
    dateConfirmed = models.DateField(default=timezone.now,null=False)
    customer = models.CharField(max_length=200, null=False)
    datePayment = models.DateField(default=timezone.now,null=False)
    
    def __str__(self):
        return f"Transaction: {self.transactionRef} - {self.cardName}"


class plan(models.Model):
    initial_minimum_user =models.CharField(null=True,max_length=200)
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
    number_of_license =models.CharField(null=True,max_length=200)
    active = models.BooleanField(default=0)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

class contracttransaction(models.Model):
    contractID = models.ForeignKey(contract,on_delete=models.CASCADE,null=True) 
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    transaction_amount = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    transaction_date =  models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

class tier(models.Model):
    tiername = models.ForeignKey(plan,on_delete=models.CASCADE,null=True)
    merchID = models.ForeignKey(merchant,on_delete=models.CASCADE,null=True)
    tiermerchantname =models.CharField(null=True,max_length=200)
    numberofpoints = models.CharField(null=True,max_length=200)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

class loyaltyCustomer(models.Model):
    CardNumber = models.CharField(null=False,primary_key=True,max_length=50)
    Loyaltycode = models.CharField(null=True, max_length=50)
    Customername = models.CharField(null=True, max_length=50)
    branch = models.CharField(null=True, max_length=50)
    Address = models.CharField(null=True, max_length=50)
    Tel = models.CharField(null=True, max_length=50)
    class Meta:
          db_table ='loyaltyCustomer'
          app_label = 'mpos0'

class pointtable(models.Model):
    CardNumber = models.IntegerField(null=False, primary_key=True, max_length=50)
    Invoicenumber = models.IntegerField(null=True)
    date = models.DateField(auto_now_add=True, null=True)
    reg = models.IntegerField(null=False, max_length=50)
    InvValue = models.DecimalField(default=0, max_digits=16, decimal_places=6)
    Amount = models.DecimalField(default=0, max_digits=16, decimal_places=6)
    class Meta:
          db_table = 'pointtable'
          app_label = 'mpos0'

class Branch(models.Model):
    BranchCode = models.IntegerField(null=False, primary_key=True, max_length=50)
    BranchNickName =models.CharField(null=True, max_length=50)
    BRANCHID = models.IntegerField(null=False, max_length=50)
    class Meta:
          db_table = 'branch'
          app_label = 'mpos0'

class voucher(models.Model):
    ID = models.CharField(null=True,max_length=50)
    CUSTOMERCODE=models.CharField(null=True,max_length=50)
    Amount = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    DateCreated = models.DateTimeField(auto_now_add=True,null=True)
    CreatedBy = models.CharField(null=True,max_length=50)
    SOLDOUT = models.BooleanField(default=1)
    Status = models.BigIntegerField()
    OtherInfo=models.CharField(null=True,max_length=50)
    vouchertype=models.CharField(null=True,max_length=50)
    InvoiceNo=models.DecimalField(default=0,max_digits=16,decimal_places=6)
    branch=models.CharField(null=True,max_length=50)
    remarks=models.CharField(null=True,max_length=50)
    class Meta:
          db_table ='voucher'
          app_label = 'mpos0'

class vouchertransactions(models.Model):
    ID = models.CharField(null=True,max_length=50)
    Invoicenumber=models.DecimalField(default=0,max_digits=16,decimal_places=6)
    DateUsed = models.DateTimeField(auto_now_add=True,null=True)
    Credit = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    Debit = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    Particular =  models.CharField(null=True,max_length=50)
    ref=models.CharField(null=True,max_length=50)
    class Meta:
          db_table ='vouchertransactions'
          app_label = 'mpos0'

class listvouchertransactions(models.Model):
    ID = models.CharField(null=True,max_length=50)
    Invoicenumber=models.DecimalField(default=0,max_digits=16,decimal_places=6)
    DateUsed = models.DateTimeField(auto_now_add=True,null=True)
    Credit = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    Debit = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    Particular =  models.CharField(null=True,max_length=50)
    recno =  models.IntegerField(null=True)
    ref = models.CharField(null=True,max_length=50)
    class Meta:
          db_table ='vouchertransactions'
          app_label = 'mpos0'

class tblCustomer(models.Model):
    CustomerAccNo =models.CharField(max_length=45,primary_key=True)
    Forename = models.CharField(max_length=45)
    Surname = models.CharField(max_length=45)
    EMail = models.CharField(max_length=45)
    Title=models.CharField(max_length=45) 
    class Meta:
          db_table ='tblCustomer'
          app_label = 'DST'

class tblTicket(models.Model):
    TicketID =models.CharField(max_length=45,primary_key=True)
    TicketDate =models.DateField('TicketDate',null=True)
    CustomerAccNo = models.CharField(max_length=45)
    TicketTotal = models.DecimalField(default=0,max_digits=16,decimal_places=6)
    class Meta:
          db_table ='tblTicket'
          app_label = 'DST'

    
    

   
