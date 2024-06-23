from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member
import re

@receiver(post_save, sender=Member)
def generate_membership_number(sender, instance, created, **kwargs):
    if created and not instance.membership_number:
        # Get the last member by membership_number
        last_member = Member.objects.filter(membership_number__regex=r'^MIT-\d+$').order_by('-membership_number').first()
        if not last_member:
            new_number = '00001'
        else:
            last_number = re.search(r'\d+$', last_member.membership_number).group()
            new_number = f'{int(last_number) + 1:05}'

        instance.membership_number = f'MIT-{new_number}'
        
        # Avoid recursive saving by using update instead of save
        Member.objects.filter(id=instance.id).update(membership_number=instance.membership_number)