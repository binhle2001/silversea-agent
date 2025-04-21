from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2 import service_account
from .common import get_env_var

# Load credentials
credentials = service_account.Credentials.from_service_account_file(get_env_var("GCP", "CREDENTIAL_PATH"))

# Khởi tạo BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)
project_id = get_env_var("GCP", "PROJECT_ID")
dataset_billing_name = get_env_var("GCP", "DATASET_BILLING")
billing_account = get_env_var("GCP", "BILLING_ACCOUNT")
# Viết query
def get_billing(time_start: str):
    query =  f"SELECT service.description, SUM(cost) AS total_cost FROM `{project_id}.{dataset_billing_name}.gcp_billing_export_resource_v1_{billing_account}` WHERE usage_start_time >= '{time_start}' GROUP BY service.description"

    # Tạo job config với location đúng
    job_config = bigquery.QueryJobConfig()
    # Thực thi query với location asia-southeast1
    query_job = client.query(query, job_config=job_config, location="asia-southeast1")

    # Lấy kết quả
    results = query_job.result()
    data = []
    # In kết quả
    for row in results:
        service_description, cost = row
        data.append({"service_description": service_description, "cost": cost})




def get_project_id(credentials_path):
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    project_id = credentials.project_id
    return credentials, project_id


def list_sql_instances(project_id, credentials):
    service = build('sqladmin', 'v1beta4', credentials=credentials)
    request = service.instances().list(project=project_id)
    response = request.execute()
    instances = response.get("items", [])
    result = []
    for inst in instances:
        result.append({
            "name": inst["name"],
            "createTime": inst.get("createTime", "N/A"),
        })
    return result


def list_compute_instances(project_id, credentials):
    service = build('compute', 'v1', credentials=credentials)
    request = service.instances().aggregatedList(project=project_id)
    response = request.execute()
    vms = []
    for zone_data in response.get('items', {}).values():
        for inst in zone_data.get('instances', []):
            vms.append({
                "name": inst["name"],
                "creationTimestamp": inst.get("creationTimestamp", "N/A"),
                
            })
    return vms


def list_cloud_run_services(project_id, credentials, region='asia-southeast1'):
    service = build('run', 'v1', credentials=credentials)
    parent = f"projects/{project_id}/locations/{region}"
    try:
        request = service.projects().locations().services().list(parent=parent)
        response = request.execute()
        result = []
        for svc in response.get('items', []):
            metadata = svc.get("metadata", {})
            result.append({
                "name": metadata.get("name"),
                "createTime": metadata.get("creationTimestamp", "N/A"),
                
            })
        return result
    except Exception as e:
        return [{"error": str(e)}]
    
def get_services_in_use():
    credentials_path = get_env_var("GCP", "CREDENTIAL_PATH")  # 🔁 Thay bằng đường dẫn thật
    credentials, project_id = get_project_id(credentials_path)
    sql_services = []
    for sql in list_sql_instances(project_id, credentials):
        sql_services.append(sql)
    compute_instances = []
    for vm in list_compute_instances(project_id, credentials):
        compute_instances.append(vm)
    cloud_runs = []
    for svc in list_cloud_run_services(project_id, credentials):
        cloud_runs.append(svc)
    return {"project_id": project_id, "sql_service": sql_services, "compute_instance": compute_instances, "cloud_run": cloud_runs}