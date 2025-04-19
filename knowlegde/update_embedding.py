import json
from api.helpers.db_config import get_db
from api.helpers.sentence_embedding import model_embedding 
from api.helpers.common import extract_text_from_docx, extract_text_from_pdf, extract_text_from_pptx
import torch
from api.helpers.gemini import model_extraction
from api.helpers.push_file_to_bucket import  upload_to_s3, delete_file_s3
class UpdateEmbedding:
    def __init__(self):
        self.PROMPT_EXTRACT_FILE = """You are an advanced language model trained to convert unstructured data (pdf, docx, pptx) into structured data in JSON format. Please extract and transform the content from the following document into a JSON record suitable for a database that stores software product marketing materials. Perform the content extraction in Vietnamese. The JSON object should include the following fields:

product_name (TEXT): The name of the product.

short_description (TEXT): A brief description of the product.

key_features (LIST): A list of key features of the product. Example: ["feature A", "feature B", "feature C"]

key_features_description (LIST): A list of descriptions corresponding to each key feature, in the same order and quantity as in key_features. Example: ["feature A description", "feature B description", "feature C description"]

target_audience (TEXT): The target customers or user groups. Example: "audience 1, audience 2"

problem_solved (TEXT): The problems the product solves. Example: "problem A, problem B"

benefits (TEXT): The benefits of using the product. Example: "benefit 1, benefit 2"

industry_applications (TEXT): The industries where the product is applicable. Example: "industry 1, industry 2"

scalability (TEXT): Scalability information of the product.

notable_projects (TEXT): Notable deployments or clients using the product. Example: "notable 1, notable 2"

achievement (TEXT): Achievements or milestones the product has attained. Example: "achievement 1, achievement 2"
"""
        self.model = model_extraction
    def extract_data_from_file(self, file_path: str):
        if file_path.endswith(".pdf"):
            parse_text = extract_text_from_pdf(file_path)
        if file_path.endswith(".pptx"):
            parse_text = extract_text_from_pptx(file_path)
        if file_path.endswith(".docx"):
            parse_text = extract_text_from_docx(file_path)
        content = [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{self.PROMPT_EXTRACT_FILE}\n\n{parse_text}"}
                    ]
                }
        ]
        response = self.model.generate_content(content)
        return response.text.replace("```json", "").replace("```", "")
    def push_data_to_database(self, file_path):
        while True:
            json_data_string = self.extract_data_from_file(file_path)
            try:
                json_data = json.loads(json_data_string)
                if len(json_data["key_features"]) == len(json_data["key_features_description"]):
                    break
            except:
                print(json_data_string)
        product_name = json_data["product_name"]
        short_description = json_data["short_description"]
        target_audience = json_data["target_audience"]
        problem_solved = json_data["problem_solved"]
        key_features = json_data["key_features"]
        key_features_description = json_data["key_features_description"]
        benefits = json_data["benefits"]
        industry_applications = json_data["industry_applications"]
        scalability = json_data["scalability"]
        notable_projects = json_data["notable_projects"]
        achievement = json_data["achievement"]
        document_url = upload_to_s3(file_path, f"company_document/{file_path}")
        license = "Đã được cấp phép"
        price = "Liên hệ"
        conn = get_db()
        cursor = conn.cursor()
        software_sql_query = "INSERT INTO software (product_name, short_description, target_audience, problem_solved, benefits, industry_applications, scalability, notable_projects, source_file, achievement, license, price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        software_params = [product_name, short_description, target_audience, problem_solved, benefits, industry_applications, scalability, notable_projects, document_url, achievement, license, price]
        cursor.execute(software_sql_query, software_params)
        conn.commit()
        query = "SELECT id FROM software WHERE product_name = %s"

        cursor.execute(query, [product_name])
        rows = cursor.fetchall()
        software_id = rows[0][0]
        for feature_name, feature_description in zip(key_features, key_features_description):
            feature_sql_query = "INSERT INTO software_feature (software_id, feature_name, feature_description) VALUES (%s, %s, %s)"
            feature_params = (software_id, feature_name, feature_description)
            cursor.execute(feature_sql_query, feature_params)
        conn.commit()
        cursor.close()
        conn.close()
        return document_url
    def delete_record(self, software_id):
        conn = get_db()
        cursor = conn.cursor()
        sql_query = "SELECT source_file from software WHERE id = %s"
        cursor.execute(sql_query, [software_id])
        rows = cursor.fetchall()
        document_url = rows[0][0]
        try:
            delete_file_s3(document_url)
        except:
            pass
        sofware_sql_query = "DELETE FROM software WHERE id = %s"
        feature_sql_query = "DELETE FROM software_feature WHERE software_id = %s"
        
        cursor.execute(sofware_sql_query, [software_id])
        cursor.execute(feature_sql_query, [software_id])

        

        conn.commit()
        cursor.close()
        conn.close()
    def get_all(self,):
        software_sql_query = "SELECT id, product_name, short_description, source_file FROM software"
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(software_sql_query)
        rows = cursor.fetchall()
        data = []
        for row in rows:
            id, software_name, short_description, source_file = row
            item = {
                "id": id,
                "product_name": software_name,
                "short_description": short_description,
                "source_file": source_file
            }
            data.append(item)
        return data
    def embedding_file(self, file_path):
        document_url = self.push_data_to_database(file_path)
        sql_query = "SELECT id, short_description, target_audience, problem_solved, benefits, industry_applications, scalability FROM software WHERE ai_processed = false"
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        for row in rows:
            id, short_description, target_audience, problem_solved, benefits, industry_applications, scalability = row
            if short_description is None:
                short_description_embedding = None
            else:
                short_description_embedding = model_embedding.encode(short_description).tolist()
            if target_audience is None:
                target_audience_embedding = None
            else:
                target_audience_embedding = model_embedding.encode(target_audience).tolist()
            if problem_solved is None:
                problem_solved_embedding = None
            else:
                problem_solved_embedding = model_embedding.encode(problem_solved).tolist()
            if benefits is None:
                benefits_embedding = None
            else:
                benefits_embedding = model_embedding.encode(benefits).tolist()
            if industry_applications is None:
                industry_applications_embedding = None
            else:
                industry_applications_embedding = model_embedding.encode(industry_applications).tolist()
            if scalability is None:
                scalability_embedding = None
            else:
                scalability_embedding = model_embedding.encode(scalability).tolist()
           

            software_sql_query = "UPDATE software SET short_description_embedding = %s, target_audience_embedding = %s, problem_solved_embedding = %s, benefits_embedding = %s, industry_applications_embedding = %s, scalability_embedding = %s, ai_processed = %s WHERE id = %s"
            software_params = (short_description_embedding , target_audience_embedding , problem_solved_embedding , benefits_embedding , industry_applications_embedding , scalability_embedding, True, id)
            cursor.execute(software_sql_query,software_params)
        conn.commit()
        cursor.close()
        conn.close()
        sql_query = "SELECT id, feature_name,  feature_description FROM software_feature WHERE ai_processed = false"
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        for row in rows:
            id, feature_name,  feature_description = row
            feature_name_embedding = model_embedding.encode(feature_name).tolist()
            feature_description_embedding = model_embedding.encode(feature_description).tolist()
            
            feature_sql_query = "UPDATE software_feature SET feature_name_embedding = %s, feature_description_embedding = %s, ai_processed = %s WHERE id = %s"
            feature_params = (feature_name_embedding , feature_description_embedding, True, id)
            cursor.execute(feature_sql_query, feature_params)
        conn.commit()
        cursor.close()
        conn.close()
        return document_url













        
    





