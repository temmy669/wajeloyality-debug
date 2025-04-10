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

class merchantUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.name', read_only=True)
    merchID = merchantBasicSerializer(read_only=True)
    branchID = branchSerializer(read_only=True)

    # Write-only fields for creation
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), write_only=True)
    merchID_id = serializers.PrimaryKeyRelatedField(queryset=merchant.objects.all(), write_only=True)
    branchID_id = serializers.PrimaryKeyRelatedField(queryset=branch.objects.all(), write_only=True)

    class Meta:
        model = user
        fields = (
            'username', 'name', 'branchID', 'merchID', 'role',
            'role_id', 'merchID_id', 'branchID_id'
        )
        read_only_fields = ('branchID', 'merchID', 'role')

    def create(self, validated_data):
        role = validated_data.pop('role_id')
        merchID = validated_data.pop('merchID_id')
        branchID = validated_data.pop('branchID_id')

        # Optionally, hash the password here if you’re including it
        return user.objects.create(
            **validated_data,
            role=role,
            merchID=merchID,
            branchID=branchID
        )


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

class AccountantDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountantData
        fields = "__all__"

class AuditorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountantData
        fields = ('amount', 'cardName', 'confirmationCode', 'dateConfirmed', 'customer', 'datePayment')
        read_only_fields = ('amount', 'cardName', 'confirmationCode', 'dateConfirmed', 'customer', 'datePayment')
    