from .models import *
from rest_framework import generics, permissions, serializers

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name')
        extra_kwargs={'id':{'read_only':True}}

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

    def to_representation(self, obj):
        """Add the merchant details to the user's information. """
        instance = super().to_representation(obj)
        merchant = merchant.objects.get(pk=instance['merchID'])\
            .values('businessname', 'businesslogo', 'settingsactivated', 'themecolor')
        instance['merchant'] = merchant
        return instance
        


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
        fields = "__all__"

    def to_representation(self, obj):
        """Add merchant and branch name to the accountant data instance. """
        instance = super().to_representation(obj)
        gc_trans = giftcardtransaction(reference=instance.transactionRef)
        instance['merchant'] = gc_trans.merchID.businessname
        instance['branch'] = gc_trans.branch.branchname
        return instance