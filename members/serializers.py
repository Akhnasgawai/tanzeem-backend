from rest_framework import serializers
from .models import User, Member, Address, MembershipFee, Suspension
from .schema import upload_and_get_url
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
import pycountry

class CustomLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    group = serializers.CharField()  # Additional parameter

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    groups = GroupSerializer(many=True, read_only=True)
    is_active = serializers.CharField(read_only = True)

    class Meta:
        model = User
        fields = ('id', 'full_name', 'password', 'email', 'groups', 'is_active', 'mobile_number')

    def create(self, validated_data):
        user = User.objects.create_user(
            full_name = validated_data['full_name'],
            email=validated_data['email'],
            password=validated_data['password'],
            mobile_number=validated_data['mobile_number'],
        )
        return user
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_active']
        
class CreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'full_name']

class AddressSerializer(serializers.ModelSerializer):
    permanent_country_code = serializers.SerializerMethodField(read_only=True)
    current_country_code = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Address
        fields = "__all__"

    def get_country_code(self, country_name):
        country = pycountry.countries.get(name=country_name)
        return country.alpha_2 if country else None

    def get_permanent_country_code(self, obj):
        return self.get_country_code(obj.permanent_country)

    def get_current_country_code(self, obj):
        return self.get_country_code(obj.current_country)
    
class SuspensionSerializer(serializers.ModelSerializer):
    created_by = CreatorSerializer(read_only=True)
    class Meta:
        model = Suspension
        fields = '__all__'
        # fields = ['start_date', 'end_date', 'reason','created_by','created_at']

class MemberSerializer(serializers.ModelSerializer):
    created_by = CreatorSerializer(read_only=True)
    approved_by = CreatorSerializer(read_only=True)
    address = AddressSerializer()
    is_suspended = serializers.SerializerMethodField()
    # suspension_history = SuspensionSerializer(many=True, read_only=True)
    # suspension_history = SuspensionSerializer(source='suspensions', many=True, read_only=True)
    current_suspension_history = serializers.SerializerMethodField()

    def validate_unique_field(self, display_name, value):
        field_name = display_name.replace(" ", "_")
        instance = self.instance

        # Check if there is another soft-deleted member with the same field value
        filter_kwargs = {field_name: value, 'soft_delete': False}
        if instance and instance.pk:
            existing_member = Member.objects.filter(**filter_kwargs).exclude(pk=instance.pk).first()
        else:
            existing_member = Member.objects.filter(**filter_kwargs).first()

        if existing_member:
            raise serializers.ValidationError(f"Member with this {display_name} already exists.")

        return value
    
    def get_is_suspended(self, obj):
        return obj.is_currently_suspended()
    
    def get_current_suspension_history(self, obj):
        current_suspensions = obj.suspensions.filter(end_date__gte=timezone.now())
        return SuspensionSerializer(current_suspensions, many=True).data

    def validate_mobile_number(self, value):
        return self.validate_unique_field('mobile number', value)
    
    def validate_email(self, value):
        return self.validate_unique_field('email', value)

    class Meta:
        model = Member
        # fields = "__all__"
        fields = ['id','name','surname','father_name','date_of_birth','membership_number','place_of_birth','email','mobile_number','address','qualification','profession','is_suspended','current_suspension_history','whatsapp_number','address','soft_delete','is_executive','is_office_bearer','status','member_type','joining_date','created_at','updated_at','created_by','approved_at','approved_by','image_url']
    
    def create(self, validated_data):
        # print("VALIDATED DATA: ", validated_data)
        address_data = validated_data.pop('address')
        address = Address.objects.create(**address_data)
        validated_data['address'] = address
        # image = validated_data.pop('image_file')
        if self.context['image']:
            image = self.context['image']
            validated_data['image_url'] = upload_and_get_url(image)
        else:
            validated_data['image_url'] = None
        # Assuming the authenticated user is available in the context

        authenticated_user = self.context['request'].user

        # Assign the authenticated user as the creator while creating the Member object
        validated_data['created_by'] = authenticated_user

        # Create the Member instance with the assigned creator
        return Member.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Only allow users in 'admin_group' to update is_verified
        if 'status' in validated_data and self.context.get('request_user').groups.filter(name='Administrator').exists():
            instance.is_verified = validated_data['status']
            instance.approved_by = self.context.get('request_user')  # Set updated_by to request.user
            if validated_data['status'] and instance.status != validated_data['status']:
                instance.approved_at = timezone.now()
        
        address_data = validated_data.pop('address', None)
        if address_data:
            if instance.address:
                # If address already exists, update it
                Address.objects.update_or_create(pk=instance.address.pk, defaults=address_data)
            else:
                # If address doesn't exist, create a new one
                address = Address.objects.create(**address_data)
                instance.address = address
    
        return super().update(instance, validated_data)

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class MembershipFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipFee
        fields = '__all__'

class ViewMembershipFeeSerializer(serializers.ModelSerializer):
    created_by = CreatorSerializer(read_only=True)
    updated_by = CreatorSerializer(read_only=True)
    member = MemberSerializer(read_only=True)
    class Meta:
        model = MembershipFee
        fields = '__all__'