import boto3
import os
import uuid
from django.utils.text import get_valid_filename
from rest_framework.pagination import PageNumberPagination

class MembersModulePagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

ALLOWED_EXTENSIONS = {'png','jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_secure_filename(filename):
    valid_filename = get_valid_filename(filename)
    extension = valid_filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    return unique_filename


def upload_file_to_s3(file, acl="public-read"):
    filename = get_secure_filename(file.name)
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv('AWS_S3_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_S3_SECRET_ACCESS_KEY')
    )
    try:
        s3.upload_fileobj(
            file,
            os.getenv("AWS_S3_BUCKET_NAME"),
            f"members/{filename}",
            ExtraArgs={
                "ContentType": file.content_type
            }
        )
    except Exception as e:
        # This is a catch all exception, edit this part to fit your needs.
        print("Something Happened: ", e)
        raise e
    
    return filename


def upload_and_get_url(file):
    if file:
        if allowed_file(file.name):
            output = upload_file_to_s3(file)
            if output:
                bucket = os.getenv("AWS_S3_BUCKET_NAME")
                BASE_URL = 'members/'
                return f'https://{bucket}.s3.amazonaws.com/{BASE_URL}{output}'
        else:
            raise ValueError(f"Incorrect File Type")
    # Return None if the file is not provided or is of incorrect type
    return None

def get_members_corrected_data(data):
    address = {
        "permanent_country" : data.pop("permanent_country"),
        "permanent_state" : data.pop("permanent_state"),
        "permanent_city" : data.pop("permanent_city"),
        "permanent_halqa" : data.pop("permanent_halqa"),
        "permanent_address" : data.pop("permanent_address"),
        "current_country" : data.pop("current_country"),
        "current_state" : data.pop("current_state"),
        "current_city" : data.pop("current_city"),
        "current_halqa" : data.pop("current_halqa"),
        "current_address" : data.pop("current_address"),
    }
    data["address"] = address
    return data

def get_membership_fee_details(result_page):
    results = []
    for membership_fee in result_page:
        results.append({
            "amount": membership_fee.amount,
            "reference_number": membership_fee.reference_number,
            "year": membership_fee.year,
            "fee_status": membership_fee.fee_status,
            "created_at": membership_fee.created_at,
            "created_by": membership_fee.created_by.full_name,
            "updated_at": membership_fee.updated_at,
            "updated_by": membership_fee.updated_by.full_name,
        })
    return results