from .models import *
from rest_framework import generics, permissions, serializers



class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id','name']


class merchantSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = merchant
        fields = ('serviceID','businessname','businessdescription','country','merchantphonenumber', 'businessaddress','merchantemailaddress','merchantpassword','active','contactpersonfirstname','contactpersonlastname','contactpersonphone','currency','country_state','country_city', 'businessname', 'businesslogo', 'themecolor', 'settingsactivated')
# class branchManagerSerilaizer(serializers.ModelSerializer):
#     """Serializer t omao"""
class branchSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = branch
        fields = ('branchname','branchaddress','branchstate','branchcity','branchofficeline','merchID')

class merchantBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = merchant
        fields = ('businessname', 'businesslogo', 'themecolor', 'settingsactivated')

    def to_representation(self, instance):
        # Get the original representation (i.e., all the data)
        representation = super().to_representation(instance)
        
        # Strip out '%20' from the businesslogo field
        if 'businesslogo' in representation:
            representation['businesslogo'] = representation['businesslogo'].replace('%20', ' ')
        
        return representation

from django.contrib.auth.hashers import make_password
class merchantUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.name', read_only=True)
    merchID = merchantBasicSerializer(read_only=True)
    branchID = branchSerializer(read_only=True)

    # Write-only fields for creation
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), write_only=True)
    merchID_id = serializers.PrimaryKeyRelatedField(queryset=merchant.objects.all(), write_only=True)
    branchID_id = serializers.PrimaryKeyRelatedField(queryset=branch.objects.all(), write_only=True)
    userpassword = serializers.CharField(write_only=True)  # ✅ ensure password is write-only

    class Meta:
        model = user
        fields = (
            'id', 'username', 'name', 'branchID', 'merchID', 'role',
            'role_id', 'merchID_id', 'branchID_id', 'userpassword'
        )
        read_only_fields = ('branchID', 'merchID', 'role')

    def create(self, validated_data):
        role = validated_data.pop('role_id')
        merchID = validated_data.pop('merchID_id')
        branchID = validated_data.pop('branchID_id')
        raw_password = validated_data.pop('userpassword')  #plain password from input

        # Create user instance without saving yet
        user_obj = user(
            **validated_data,
            role=role,
            merchID=merchID,
            branchID=branchID,
            userpassword=make_password(raw_password)
        )  
        user_obj.save()
        return user_obj
    

class themeColorSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = merchant
        fields = ('id','themecolor','themecolorlight','themetextcolor','themetitlecolor','themebordercolor')

class campaignTemplates(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = campaigntemplate
        fields = ('title', 'active','merchID')

class createCampaigns(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = campaigns
        fields = ('title','campaigntype', 'merchID','interval','tempateID','enddate','startdate')
        
    

class merachantLoginSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:    
        """Meta class to map serializer's fields with the model fields."""
        model = merchant

        fields = ('id','serviceID','merchantphonenumber', 'businessaddress','merchantemailaddress','active','contactpersonfirstname','contactpersonlastname')

class merchantCustomerSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:    
        """Meta class to map serializer's fields with the model fields."""
        model = customer
        fields = ('firstname','lastname','customerIdentifier', 'DOB','merchID','facebooklink','twitterlink','instagramlink','emailaddress','gender')

class merchantLoyaltyRuleSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:    
        """Meta class to map serializer's fields with the model fields."""
        model = loyaltyrule
        fields = ('loyaltyrule','rewardpoint','amountspent', 'startdate','endate','status','merchID')

class merchantCrossCampaignRuleSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:    
        """Meta class to map serializer's fields with the model fields."""
        model = crosscampaignrule
        fields = ('campaignrulename','amountspent', 'startdate','endate','status','merchID')

class merchantGiftCardSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:    
        """Meta class to map serializer's fields with the model fields."""
        model = giftCard
        fields = ('serialnumber','cardname', 'amount','merchID','expiration_date','created_at')

class planSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:    
        """Meta class to map serializer's fields with the model fields."""
        model = plan
        fields = ('id','initial_minimum_user','price', 'subsequent_minimum','number_of_days','billing_interval','created_at')


class GiftCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = giftCard
        fields = ("id","serialnumber", "cardname", "recipient_phone", "recipient_email", "createdby", "amount", "merchID", "active", "expiration_date", "createddate")


# User serializer to represent the manager (creator of the gift card)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = user  # Assuming 'user' is the model for the user
        fields = ['username']

# Branch serializer to represent the branch related to the merchant
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = branch
        fields = ['branchname']

# GiftCard serializer to represent the gift card information
# class GiftCardSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = giftCard
#         fields = ['cardname']

# AccountantData serializer for the transaction data
class AccountantDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccountantData
        fields = [
            'confirmationCode', 'customer', 'cardName', 'amount',
            'dateConfirmed', 'datePayment', 'transactionRef']
        
    def create(self, validated_data, **kwargs):
        merchID = kwargs.get("merchID")
        userID =  kwargs.get("userID")
        return AccountantData.objects.create(**validated_data, merchID=merchID, userID=userID)


class AccountantGetSerializer(serializers.ModelSerializer):
    confirmationCode = serializers.CharField()
    customer = serializers.CharField()
    cardName = serializers.CharField()
    amount = serializers.DecimalField(max_digits=16, decimal_places=2)
    transactionRef = serializers.CharField()
    dateConfirmed = serializers.DateField()
    datePayment = serializers.DateField()

    def to_representation(self, instance):
        accountant_data = instance

        return {
            'confirmationCode': accountant_data.confirmationCode,
            'customer': accountant_data.customer,
            'cardName': accountant_data.cardName,
            'amount': accountant_data.amount,
            'transactionRef': accountant_data.transactionRef,
            'dateConfirmed': accountant_data.dateConfirmed,
            'datePayment': accountant_data.datePayment
        }



# AuditorSerializer to combine the related models
class AuditorSerializer(serializers.Serializer):
    confirmationCode = serializers.CharField()
    customer = serializers.CharField()
    cardName = serializers.CharField()
    amount = serializers.DecimalField(max_digits=16, decimal_places=2)
    transactionRef = serializers.CharField()
    dateConfirmed = serializers.DateField()
    datePayment = serializers.DateField()
    manager = serializers.CharField()
    branch = BranchSerializer(many=True)

    def to_representation(self, instance):
        accountant_data = instance

        # Find giftCard using confirmationCode
        gift_card = giftCard.objects.filter(confirmationCode=accountant_data.confirmationCode).first()

        if gift_card:
            user_obj = gift_card.createdby  # This is the manager (User instance)
            branch_obj = getattr(user_obj, 'branchID', None)

            return {
                'confirmationCode': accountant_data.confirmationCode,
                'customer': accountant_data.customer,
                'cardName': gift_card.cardname,
                'amount': accountant_data.amount,
                'transactionRef': accountant_data.transactionRef,
                'dateConfirmed': accountant_data.dateConfirmed,
                'datePayment': accountant_data.datePayment,
                'manager': getattr(user_obj, 'name', 'Nill'),
                'branch': BranchSerializer([branch_obj], many=True).data if branch_obj else [],
            }
