# Create a file named create_groups.py in your app's management/commands directory
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from members.models import Member
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create 'Administrator' group if it doesn't exist
        admin_group, admin_created = Group.objects.get_or_create(name='Administrator')
        if admin_created:
            self.stdout.write(self.style.SUCCESS("Group 'Administrator' created successfully"))
            self.assign_permissions(admin_group, ['add_member', 'change_member'])
        else:
            self.stdout.write(self.style.WARNING("Group 'Administrator' already exists"))

        # Create 'Ordinary User' group if it doesn't exist
        user_group, user_created = Group.objects.get_or_create(name='Ordinary User')
        if user_created:
            self.stdout.write(self.style.SUCCESS("Group 'Ordinary User' created successfully"))
            self.assign_permissions(user_group, ['add_member'])
        else:
            self.stdout.write(self.style.WARNING("Group 'Ordinary User' already exists"))
    
    def assign_permissions(self, group, permission_codenames):
        # Fetch content type for your Member model
        content_type = ContentType.objects.get_for_model(Member)
        
        # Assign permissions to the group
        permissions = Permission.objects.filter(content_type=content_type, codename__in=permission_codenames)
        group.permissions.add(*permissions)
