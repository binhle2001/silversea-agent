import psycopg2
from .settings import *

def get_db():
# Kết nối tới database
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

# # Bật extension pgvector (chỉ cần 1 lần)
# cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

# # Tạo bảng
# cur.execute("""
#     CREATE TABLE IF NOT EXISTS software (
#         id SERIAL PRIMARY KEY,
#         software_name TEXT,
#         software_name_embedding VECTOR(768),
#         software_description TEXT,
#         software_description_embedding VECTOR(768),
#         software_domain TEXT,
#         software_domain_embedding VECTOR(768),
#         partner TEXT,
#         document_url TEXT,
#         achievement TEXT,
#     );
# """)
# cur.execute("""
#     CREATE TABLE IF NOT EXISTS software_feature (
#         id SERIAL PRIMARY KEY,
#         software_id INT,
#         feature_name TEXT,
#         feature_name_embedding VECTOR(768),
#         feature_image_url TEXT,
#         feature_description TEXT,
#         feature_description_embedding VECTOR(768)
#     );
# """)
# conn.commit()
# cur.close()
# conn.close()
