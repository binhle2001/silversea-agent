from datetime import datetime
import boto3
from .push_file_to_bucket import s3
from .common import get_env_var

aws_access_key_id = get_env_var("aws", "CLIEND_ID")
aws_secret_access_key = get_env_var("aws", "CLIEND_SECRET")
bucket_name = get_env_var("aws", "BUCKET_NAME")
region = get_env_var("aws", "REGION")

client = boto3.client('ce',
                  aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key,
                  region_name=region)

def get_s3_bucket():
    response = s3.list_buckets()
    print(response['Buckets'])
    data = []
    for bucket in response['Buckets']:
        bucket_name = bucket["Name"]
        bucket_created_at = bucket["CreationDate"].strftime("%Y-%m-%d")
        item = {"bucket_name": bucket_name, "CreationDate": bucket_created_at}
        data.append(item)
    return data

def get_aws_billing(time: str):
    # Gọi API lấy billing từ đầu tháng đến nay
    print(time)
    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': time,
            'End': datetime.today().strftime('%Y-%m-%d')
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    return response['ResultsByTime']

