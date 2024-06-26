# Generated by Django 5.0.1 on 2024-06-23 08:08

import datetime
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Address",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("permanent_country", models.CharField(max_length=40)),
                ("permanent_state", models.CharField(max_length=50)),
                ("permanent_city", models.CharField(max_length=40)),
                ("permanent_address", models.CharField(max_length=70)),
                ("permanent_halqa", models.CharField(max_length=40)),
                ("current_country", models.CharField(max_length=40)),
                ("current_state", models.CharField(max_length=50)),
                ("current_city", models.CharField(max_length=40)),
                ("current_address", models.CharField(max_length=70)),
                (
                    "current_halqa",
                    models.CharField(blank=True, max_length=40, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("full_name", models.CharField(default="John", max_length=255)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("mobile_number", models.CharField(max_length=255)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Member",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=40)),
                ("surname", models.CharField(blank=True, max_length=20, null=True)),
                ("father_name", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "membership_number",
                    models.CharField(blank=True, max_length=10, unique=True),
                ),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                (
                    "place_of_birth",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("image_url", models.URLField(blank=True, null=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                (
                    "mobile_number",
                    models.CharField(blank=True, max_length=15, null=True),
                ),
                (
                    "qualification",
                    models.CharField(blank=True, max_length=30, null=True),
                ),
                ("profession", models.CharField(blank=True, max_length=30, null=True)),
                (
                    "whatsapp_number",
                    models.CharField(blank=True, max_length=15, null=True),
                ),
                (
                    "soft_delete",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                ("is_executive", models.BooleanField(default=False)),
                ("is_office_bearer", models.BooleanField(default=False)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "member_type",
                    models.CharField(
                        choices=[
                            ("Lifetime Member", "Lifetime Member"),
                            ("Ordinary Member", "Ordinary Member"),
                            ("Sarparast", "Sarparast"),
                        ],
                        default="Ordinary Member",
                        max_length=20,
                    ),
                ),
                ("joining_date", models.DateField(default=datetime.date.today)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                (
                    "address",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="members.address",
                    ),
                ),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="members_approved",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="members_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MembershipFee",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(decimal_places=2, max_digits=10, null=True),
                ),
                ("reference_number", models.CharField(max_length=50, null=True)),
                ("year", models.CharField(max_length=10)),
                (
                    "fee_status",
                    models.CharField(
                        choices=[("due", "Due"), ("paid", "Paid")],
                        default="due",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="membership_fee_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="membership_fee",
                        to="members.member",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="membership_fee_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Suspension",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("start_date", models.DateTimeField(auto_now_add=True)),
                ("end_date", models.DateTimeField()),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suspension_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suspensions",
                        to="members.member",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suspension_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
