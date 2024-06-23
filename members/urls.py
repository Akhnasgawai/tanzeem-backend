from django.urls import path
from . import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    # authentication api's
    path('register/', views.register, name='register'),
    path('login/', views.login, name ='login'), 
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name ='token_refresh'), 
    path('get_users/', views.get_registered_users, name='get_users'),
    path('update_user_status/<uuid:user_id>/', views.update_user_status, name='update_user'),
    path('change_password/', views.change_password, name='change_password'),
    path('logout/', views.logout, name='logout'),

    # Member CRUD Operations
    path('add_member/', views.add_member, name='members'),
    path('update_member/<uuid:member_id>/', views.update_member, name='update_member'),
    path('delete_member/', views.delete_member, name='delete_member'),
    path('get_member/<uuid:member_id>/', views.get_member, name='get_member'),
    path('member-list/', views.members, name='member-list'),
    path('get-member-by-mobile/<str:mobile_number>/', views.get_member_by_mobile, name='member_by_mobile'),
    path('get-member-by-member-id/<str:member_id>/', views.get_member_by_membership_id, name='member_by_member_id'),
    path('download_member_list/', views.download_member_list, name='download_member_list'),

    # Member Suspension CRUD Operations
    path('suspend/', views.suspend_member, name='suspend_member'),
    path('suspended-member-list/', views.get_suspended_members, name='suspended-member-list'),
    path('suspension-history/<uuid:member_id>/', views.get_suspension_history, name="suspension-history"),

    # Memberhip Fee Crud Operations
    path('add_membership_fee/', views.add_membership_fee, name='add_fee'),
    path('view_membership_fee/', views.get_membership_details, name='get_membership_details'),
    path('get_membership_fees_history/<uuid:member_id>/', views.get_membership_fees_history, name='get_membership_fees_history'),
]