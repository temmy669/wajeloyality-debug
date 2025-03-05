from .models import *
from rest_framework import generics, permissions, serializers


class merchantSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = merchant
        fields = ('serviceID','businessname','businessdescription','country','merchantphonenumber', 'businessaddress','merchantemailaddress','merchantpassword','active','contactpersonfirstname','contactpersonlastname','contactpersonphone','currency','country_state','country_city')


class merchantUserSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = user
        fields = ('username', 'name', 'branchID', 'merchID', 'role')

class branchSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = branch
        fields = ('branchname','branchaddress','branchstate','branchcity','branchofficeline','merchID')

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


class AccountantDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountantData
        fields = ('customer','amount','cardName', 'dateConfirmed', 'confirmationCode', 'transactionRef')