from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from .managers import CustomUserManager
import uuid
from django.conf import settings
from django.utils import timezone
from datetime import date

# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255, default='John')
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    mobile_number = models.CharField(max_length=255)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

class Address(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    permanent_country = models.CharField(max_length=40)
    permanent_state = models.CharField(max_length=50)
    permanent_city = models.CharField(max_length=40)
    permanent_address = models.CharField(max_length=70)
    permanent_halqa = models.CharField(max_length=40)
    current_country = models.CharField(max_length=40)
    current_state = models.CharField(max_length=50)
    current_city = models.CharField(max_length=40)
    current_address = models.CharField(max_length=70)
    current_halqa = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self) -> str:
        return self.id

class Member(models.Model):

    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    LIFETIME = 'Lifetime Member'
    ORDINARY = 'Ordinary Member'
    SARPARAST = 'Sarparast'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    MEMBER_TYPE_CHOICES = [
        (LIFETIME, 'Lifetime Member'),
        (ORDINARY, 'Ordinary Member'),
        (SARPARAST, 'Sarparast'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=40)
    surname = models.CharField(max_length=20, null=True, blank=True)
    father_name = models.CharField(max_length=50, null=True, blank=True)
    membership_number = models.CharField(max_length=10, unique=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=100, null=True, blank=True)
    image_url = models.URLField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    qualification = models.CharField(max_length=30, null=True, blank=True)
    profession = models.CharField(max_length=30, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, null=True, blank=True)
    soft_delete = models.BooleanField(default=False, null=True, blank=True)
    is_executive = models.BooleanField(default=False)
    is_office_bearer = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    member_type = models.CharField(max_length=20, choices=MEMBER_TYPE_CHOICES, default=ORDINARY)
    joining_date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='members_created')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='members_approved')

    def __str__(self) -> str:
        return self.name + " " + self.surname
    
    @property
    def get_full_name(self):
        return self.name + " " + self.surname
    
    # @property
    def is_currently_suspended(self):
        current_suspensions = self.suspensions.filter(end_date__gte=timezone.now())
        return current_suspensions.exists()
    
    def suspend(self, end_date, reason, user):
        Suspension.objects.create(member=self, start_date=timezone.now(), end_date=end_date, reason=reason, created_by=user, updated_by=user)
        self.save()

    def lift_suspension(self):
        current_suspensions = self.suspensions.filter(end_date__gte=timezone.now())
        for suspension in current_suspensions:
            suspension.end_date = timezone.now()
            suspension.save()

class MembershipFee(models.Model):
    DUE = 'due'
    PAID = 'paid'
    FEE_STATUS_CHOICES = [
        (DUE, 'Due'),
        (PAID, 'Paid'),
    ]
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    reference_number = models.CharField(max_length=50, null=True)
    year = models.CharField(max_length=10)
    fee_status = models.CharField(max_length=20, choices=FEE_STATUS_CHOICES, default=DUE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='membership_fee')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membership_fee_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membership_fee_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.reference_number
    

class Suspension(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    member = models.ForeignKey(Member, related_name='suspensions', on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    reason = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='suspension_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='suspension_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.member.name} suspended from {self.start_date} to {self.end_date}"