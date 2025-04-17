import boto3
from botocore.exceptions import NoCredentialsError
from api.helpers.common import get_env_var

aws_access_key_id = get_env_var("aws", "CLIEND_ID")
aws_secret_access_key = get_env_var("aws", "CLIEND_SECRET")
bucket_name = get_env_var("aws", "BUCKET_NAME")
region = get_env_var("aws", "REGION")

# Khởi tạo client S3
s3 = boto3.client('s3',
                  aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key,
                  region_name=region)

def upload_to_s3(file_path, s3_key):
    try:
        s3.upload_file(file_path, bucket_name, s3_key)
        print(f"✅ Uploaded {file_path} → s3://{bucket_name}/{s3_key}")
        return f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    except FileNotFoundError:
        print("❌ File not found!")
        return None
    except NoCredentialsError:
        print("❌ Credentials are invalid!")
        return None

def delete_file_s3(url):
    s3_key = url.split("amazonaws.com")[1][1:]
    s3.delete_object(Bucket=bucket_name, Key=s3_key)