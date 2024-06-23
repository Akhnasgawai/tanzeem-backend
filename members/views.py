# rest api imports
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

# django imports
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

# app imports
from .models import Member, User, MembershipFee
from .serializers import UserSerializer, MemberSerializer, ChangePasswordSerializer, CustomLoginSerializer, UserUpdateSerializer, MembershipFeeSerializer, ViewMembershipFeeSerializer
from .decorators import admin_required
from .schema import get_members_corrected_data, get_membership_fee_details, MembersModulePagination

# utility imports
import xlsxwriter
from datetime import datetime

@api_view(['POST'])
def login(request):
    serializer = CustomLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        group = serializer.validated_data.get('group')
        user = authenticate(request=request, username=email, password=password)
        if user is None:
            try:
                user_exists = User.objects.get(email=email)
                if not user_exists.is_active:
                    return Response({"errors":"Account is Disabled, Contact Administrator"}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({"errors": "Incorrect Email"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"errors":"Incorrect Password"}, status=status.HTTP_400_BAD_REQUEST)
        if group not in user.groups.values_list('name', flat=True):
            return Response({"errors": "Invalid Access"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=email)
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        access_token['role'] = group
        access_token['name'] = user.full_name
        access_token['email'] = user.email
        access_token['mobile'] = user.mobile_number

        tokens = {
            'refresh': str(refresh),
            'access': str(access_token),
        }
        return Response(tokens, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        group_name = request.data.get('group_name')
        if group_name:
            # Assign the user to the provided group
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_registered_users(request):
    paginator = MembersModulePagination()
    users = User.objects.all()
    result_page = paginator.paginate_queryset(users, request)
    serializer = UserSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@admin_required
def update_user_status(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'errors': 'User Not Found'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = UserUpdateSerializer(user, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        user = request.user
        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'errors': 'Incorrect current password'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_member(request):
    data_dict = request.data.dict()
    image = data_dict.get("image_file")
    valid_data = get_members_corrected_data(data_dict)
    member_serializer = MemberSerializer(data=valid_data, context={'request': request, 'image': image})
    if member_serializer.is_valid():
        member_data = member_serializer.save()
        payment_details = []
        for year in range(member_data.joining_date.year, datetime.now().year):
            payment_data = {
                'member': member_data.id,
                'year': year,
                'reference_number': '-' if member_data.member_type in ['Lifetime Member', 'Sarparast'] else None,
                'fee_status': 'paid' if member_data.member_type in ['Lifetime Member', 'Sarparast'] else 'due',
                'created_by': request.user.id,
                'updated_by': request.user.id,
            }
            payment_details.append(payment_data)
        serializer = MembershipFeeSerializer(data=payment_details, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(member_serializer.data, status=status.HTTP_201_CREATED)
        return Response({"errors": "Internal Server Error"}, status=status.HTTP_206_PARTIAL_CONTENT)
    return Response({"errors" : member_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_member(request, member_id):
    try:
        member = Member.objects.get(pk=member_id)
    except Member.DoesNotExist:
        return Response({"errors" : "Member Not Found"}, status=status.HTTP_404_NOT_FOUND)
    
    if 'status' in request.data and not request.user.groups.filter(name='Administrator').exists():
        return Response({"errors": "Permission denied to update 'status'"}, status=status.HTTP_403_FORBIDDEN)

    serializer = MemberSerializer(member, data=request.data, partial=True, context={'request_user': request.user})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_member(request, member_id):
    member = Member.objects.get(id=member_id, soft_delete=False)
    serializer = MemberSerializer(member, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def members(request):
    members = Member.objects.filter(soft_delete=False)
    country = request.GET.get("country", None)
    state = request.GET.get("state", None)
    city = request.GET.get("city", None)
    halqa = request.GET.get("halqa", None)
    query = request.GET.get("query", None)
    member_status = request.GET.get("status", None)
    mobile_number = request.GET.get("mobile_number", None)
    member_id = request.GET.get("meber_id", None)

    paginator = MembersModulePagination()

    if country is not None:
        members = members.filter(Q(address__current_country__icontains=country))

    if state is not None:
        members = members.filter(Q(address__current_state__icontains=state))

    if city is not None:
        members = members.filter(Q(address__current_city__icontains=city))

    if halqa is not None:
        members = members.filter(Q(address__current_halqa__icontains=halqa))

    if query is not None:
        members = members.filter(Q(name__icontains=query) | Q(surname__icontains=query) | Q(father_name__icontains=query))

    if member_status is not None:
        members = members.filter(status = member_status)
    
    if mobile_number is not None:
        members = members.filter(Q(mobile_number__icontains=mobile_number.strip()))

    if member_id is not None:
        members = members.filter(Q(membership_number__icontains=member_id))

    if len(members) == 0:
        return Response({"errors":"No Member Found"}, status=status.HTTP_200_OK)
    else:  # Serialize many instances
        members = members.order_by('-created_at')
        result_page = paginator.paginate_queryset(members, request)
        serializer = MemberSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_member_by_mobile(request, mobile_number):
    try:
        member = Member.objects.get(mobile_number=mobile_number.strip(), soft_delete=False)
        result = MemberSerializer(member, many=False)
        return Response({"result":result.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error":"Member Not Found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_member_by_membership_id(request, member_id):
    try:
        member = Member.objects.get(membership_number=member_id, soft_delete=False)
        result = MemberSerializer(member, many=False)
        return Response({"result":result.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error":"Member Not Found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def download_member_list(request):
    members = Member.objects.filter(soft_delete=False)
    workbook = xlsxwriter.Workbook('members.xlsx')
    worksheet = workbook.add_worksheet()
    member_fields = ['name', 'surname','father_name','date_of_birth','email', 'mobile_number','qualification','profession','whatsapp_number','is_executive','is_office_bearer','member_type', 'address']
    address_fields = ['permanent_country', 'permanent_state','permanent_city','permanent_address','permanent_halqa','current_country', 'current_state','current_city','current_address','current_halqa']
    headers = member_fields + address_fields
    for col_num, header in enumerate(headers):
        print(f"col_num {col_num} and header {header}")
        if col_num == 12:
            continue
        worksheet.write(0, col_num, header)
    for row_num, member in enumerate(members, start=1):
        for col_num, field in enumerate(headers):
            if field == 'date_of_birth':
                date_value = getattr(member, field)
                formatted_date = date_value.strftime('%Y-%m-%d') if date_value else ''
                worksheet.write(row_num, col_num, formatted_date)
            if field == 'address':
                address_data = getattr(member, field, None)

                if address_data:
                    for address_col, address_field in enumerate(address_fields):
                        content = getattr(address_data, address_field, '')
                        worksheet.write(row_num, col_num+address_col+1, content)
                    break
                else:
                    for address_field in address_fields:
                        worksheet.write(row_num, col_num, '')
            else:
                # For other fields, handle encoding to UTF-8
                data = str(getattr(member, field, '')).encode('utf-8', errors='ignore').decode('utf-8')
                worksheet.write(row_num, col_num, data)
            
    workbook.close()
    with open('members.xlsx', 'rb') as excel_file:
        response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=members.xlsx'
    return response

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@admin_required
def delete_member(request):
    id = request.data.get("member_id")
    try:
        member = Member.objects.get(pk=id)
    except Member.DoesNotExist:
        return Response({"errors" : "Member Not Found"}, status=status.HTTP_404_NOT_FOUND)
    data = {'soft_delete': True}
    serializer = MemberSerializer(member, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message":"Member Deleted Successfully"}, status=status.HTTP_200_OK)
    return Response({"errors" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_membership_fee(request):
    mobile_number = request.data.get("mobile_number").strip()
    from_year = int(request.data.get('from_year'))
    to_year = int(request.data.get('to_year'))
    reference_number = request.data.get('reference_number')
    amount = float(request.data.get('amount'))
    user = Member.objects.filter(mobile_number=mobile_number, soft_delete=False).first()
    if user is None:
        return Response({"message":"Invalid Mobile Number Or Member Does'nt Exist"}, status=status.HTTP_200_OK)
    payments = []
    for year in range(from_year, to_year):
        membership_fee = MembershipFee.objects.filter(member=user, year=year).first()
        if membership_fee is None:
            payment_data = {
                'member': user.id,
                'year': year,
                'reference_number': reference_number,
                'amount': amount,
                'fee_status': 'paid',
                'created_by': request.user.id,
                'updated_by': request.user.id,
            }
            payments.append(payment_data)
        else:
            payment_data = {
                'fee_status': 'paid', 
                'amount': amount, 
                'reference_number': reference_number,
                'updated_by': request.user.id,
            }
            serializer = MembershipFeeSerializer(membership_fee, data=payment_data, partial=True)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response({"errors" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    # return Response({'message': "Fetched Successfully"})
    if payments:
        serializer = MembershipFeeSerializer(data=payments, many=True)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response({"errors" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": "Membership fees updated successfully."}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_membership_details(request):
    year = request.GET.get("year", None)
    paginator = MembersModulePagination()
    membership_fees = MembershipFee.objects.filter(member__soft_delete=False).order_by("-created_at")
    if year:
        membership_fees = membership_fees.filter(year=year)
    if len(membership_fees) == 0:
        return Response({"errors":"No Member Found"}, status=status.HTTP_200_OK)
    else:  # Serialize many instances
        result_page = paginator.paginate_queryset(membership_fees, request)
        serializer = ViewMembershipFeeSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_membership_fees_history(request, member_id):
    try:
        member = Member.objects.get(id=member_id)
        print("HEY MEMBER: ", member)
        membership_fees = member.membership_fee.all().order_by('-year')
        paginator = MembersModulePagination()
        result_page = paginator.paginate_queryset(membership_fees, request)
        results = get_membership_fee_details(result_page)
        return paginator.get_paginated_response(results)
    except ObjectDoesNotExist:
        return Response({"errors": "No Member Found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def suspend_member(request):
    try:
        member = Member.objects.get(id=request.data.get('member_id'))
    except Exception as e:
        return Response({"errors" : 'Member Not Found'}, status=status.HTTP_404_NOT_FOUND)
    suspended_till = request.data.get('end_date')
    suspension_reason = request.data.get('reason')
    member.suspend(suspended_till, suspension_reason, request.user)
    return Response({"message": f"{member.get_full_name} suspended till {suspended_till}."}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suspended_members(request):
    paginator = MembersModulePagination()
    current_time = datetime.now()
    suspended_members = Member.objects.filter(
        suspensions__end_date__gte=current_time
    ).distinct().order_by('-created_at')
    result_page = paginator.paginate_queryset(suspended_members, request)
    serializer = MemberSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suspension_history(request, member_id):
    try:
        member = Member.objects.get(pk=member_id)
    except Exception as e:
        return Response({"errors" : 'Member Not Found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = MemberSerializer(member, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get("refresh_token")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Log out Successful!"},status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"errors" : str(e)}, status=status.HTTP_400_BAD_REQUEST)