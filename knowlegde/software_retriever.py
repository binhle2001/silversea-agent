import json
from api.helpers.db_config import get_db
from api.helpers.gemini import convert_text_to_json
from api.helpers.prompt import PROMPT_CONVERT_QUESTION_TO_JSON_QUERY_SOFTWARE
from .software_feature_retriever import FeatureRetriever
from api.helpers.sentence_embedding import model_embedding 
import json
# Giả sử bạn đã import các module cần thiết:
# - get_db: hàm kết nối tới PostgreSQL.
# - model_embedding: đối tượng dùng để mã hóa văn bản thành vector.
# - convert_text_to_json, PROMPT_CONVERT_QUESTION_TO_JSON_QUERY_SOFTWARE: dùng để chuyển đổi câu hỏi người dùng thành JSON.
# - FeatureRetriever: class hỗ trợ truy vấn key features cho từng sản phẩm.

class SoftwareRetriever:
    def __init__(self):
        self.PGDB_QUERY_SOFTWARE = {
            "short_description": {
                "similarity": "(1 - (short_description_embedding <=> %(short_description_embedding)s::public.vector))",
                "weight": 1/6
            },
            "target_audience": {
                "similarity": "(1 - (target_audience_embedding <=> %(target_audience_embedding)s::public.vector))",
                "weight": 1/6
            },
            "problem_solved": {
                "similarity": "(1 - (problem_solved_embedding <=> %(problem_solved_embedding)s::public.vector))",
                "weight": 1/6
            },
            "benefits": {
                "similarity": "(1 - (benefits_embedding <=> %(benefits_embedding)s::public.vector))",
                "weight": 1/6
            },
            "industry_applications": {
                "similarity": "(1 - (industry_applications_embedding <=> %(industry_applications_embedding)s::public.vector))",
                "weight": 1/6
            },
            "scalability": {
                "similarity": "(1 - (scalability_embedding <=> %(scalability_embedding)s::public.vector))",
                "weight": 1/6
            }
        }
        self.feature_retriever = FeatureRetriever()

    def query_software(self, json_data):
        embed_params = {}
        # 1) Các cột SELECT gốc
        query = """
        SELECT
            s.id,
            s.product_name,
            s.short_description,
            s.target_audience,
            s.problem_solved,
            s.benefits,
            s.industry_applications,
            s.license,
            s.price,
            s.scalability,
            s.notable_projects,
            s.source_file,
            s.achievement
        """
        total_similarity_element = []
        similarity_fields = []

        # 2) Xử lý key_features nếu có và không rỗng
        key_texts = json_data.get("key_features") or []
        if key_texts:
            key_embs = [model_embedding.encode(t).tolist() for t in key_texts]

            # build VALUES clause: (%(key_feat_vec_0)s::vector), (%(key_feat_vec_1)s::vector), …
            values_parts = []
            for i, emb in enumerate(key_embs):
                p = f"key_feat_vec_{i}"
                embed_params[p] = emb
                values_parts.append(f"(%({p})s::vector)")

            # thành: (VALUES (...), (...)) AS v(embedding)
            values_clause = f"(VALUES {', '.join(values_parts)}) AS v(embedding)"

            # thêm key_features_similarity vào SELECT
            query += f""",
            COALESCE(
                (
                SELECT AVG(1 - (sf.feature_name_embedding <=> v.embedding))
                FROM software_feature sf,
                    {values_clause}
                WHERE sf.software_id = s.id
                ), 0
            ) AS key_features_similarity
            """

            total_similarity_element.append(f"""\n        COALESCE((
                SELECT AVG(1 - (sf.feature_name_embedding <=> v.embedding))
                FROM software_feature sf,
                    {values_clause}
                WHERE sf.software_id = s.id
                ), 0) * 1.0\n        """)
            similarity_fields.append("key_features_similarity")

        # 3) Xử lý các field embedding khác
        for key, val in json_data.items():
            if val is not None:
                if key in self.PGDB_QUERY_SOFTWARE and len(val) > 5:
                    emb_param = f"{key}_embedding"
                    embed_params[emb_param] = model_embedding.encode(val).tolist()
                    sim_expr = self.PGDB_QUERY_SOFTWARE[key]["similarity"]
                    weight   = self.PGDB_QUERY_SOFTWARE[key]["weight"]
                    query += f", {sim_expr} AS {key}_similarity"
                    total_similarity_element.append(f"{sim_expr} * {weight}")
                    similarity_fields.append(f"{key}_similarity")

        # 4) Tổng hợp total_similarity & thêm LIMIT
        if total_similarity_element:
            query += ", " + " + ".join(total_similarity_element) + " AS total_similarity"
            query += " FROM software s ORDER BY total_similarity DESC LIMIT 2"
        else:
            query += " FROM software s LIMIT 2"
        # Thực hiện query
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, embed_params)
        rows = cursor.fetchall()

        # Xây dựng output, bao gồm các thông tin sản phẩm và chi tiết similarity
        document = ""
        
        for row in rows:
            # Lấy 13 cột đầu: thông tin sản phẩm
            product = {
                "PRODUCT ID": row[0],
                "PRODUCT NAME": row[1],
                "SHORT DESCRIPTION": row[2],
                "TARGET AUDIENCE": row[3],
                "PROBLEMS SOLVED": row[4],
                "BENEFITS": row[5],
                "INDUSTRY APPLICATION": row[6],
                "LICENSE": row[7],
                "PRICE": row[8],
                "SCALABILITY": row[9],
                "NOTABLE PROJECT": row[10],
                "DOCUMENT URL": row[11],
                "ACHIEVEMENT": row[12]
            }
            # Các cột similarity được thêm vào sau 13 cột chính
            # Giả sử thứ tự các trường similarity trong SELECT được lưu theo similarity_fields, và cột cuối cùng là total_similarity
            num_base_cols = 13
            similarity_values = row[num_base_cols:]
            # Nếu có nhiều cột similarity, cột cuối cùng là total_similarity
            total_similarity = similarity_values[-1] if similarity_values else 0.0
            field_similarities = similarity_values[:-1] if len(similarity_values) > 1 else []

            similarity_details = "SIMILARITY DETAILS:\n"
            for field_name, sim_val in zip(similarity_fields, field_similarities):
                # Nếu giá trị similarity là None, chuyển về 0.0
                if sim_val is None:
                    sim_val = 0.0
                similarity_details += f"  {field_name}: {sim_val:.4f}\n"
            similarity_details += f"  TOTAL SIMILARITY: {total_similarity:.4f}\n"

            # Lấy key features từ bảng khác qua feature_retriever (đảm bảo hàm này trả về chuỗi đã được format)
            key_features = self.feature_retriever.query_feature_by_software(product["PRODUCT ID"])

            # document += f"PRODUCT ID: {product['PRODUCT ID']}\n" \
            #             f"PRODUCT NAME: {product['PRODUCT NAME']}\n" \
            #             f"SHORT DESCRIPTION: {product['SHORT DESCRIPTION']}\n" \
            #             f"KEY FEATURES: \n{key_features}\n" \
            #             f"TARGET AUDIENCE: {product['TARGET AUDIENCE']}\n" \
            #             f"PROBLEMS SOLVED: {product['PROBLEMS SOLVED']}\n" \
            #             f"BENEFITS: {product['BENEFITS']}\n" \
            #             f"INDUSTRY APPLICATION: {product['INDUSTRY APPLICATION']}\n" \
            #             f"LICENSE: {product['LICENSE']}\n" \
            #             f"PRICE: {product['PRICE']}\n" \
            #             f"SCALABILITY: {product['SCALABILITY']}\n" \
            #             f"NOTABLE PROJECT: {product['NOTABLE PROJECT']}\n" \
            #             f"DOCUMENT URL: {product['DOCUMENT URL']}\n" \
            #             f"ACHIEVEMENT: {product['ACHIEVEMENT']}\n" \
            #             f"{similarity_details}\n" \
            #             "\n-------------------------\n\n"
            document += f"PRODUCT ID: {product['PRODUCT ID']}\n" \
                        f"PRODUCT NAME: {product['PRODUCT NAME']}\n" \
                        f"SHORT DESCRIPTION: {product['SHORT DESCRIPTION']}\n" \
                        f"KEY FEATURES: \n{key_features}\n" \
                        f"BENEFITS: {product['BENEFITS']}\n" \
                        f"PRICE: {product['PRICE']}\n" \
                        f"SCALABILITY: {product['SCALABILITY']}\n" \
                        f"NOTABLE PROJECT: {product['NOTABLE PROJECT']}\n" \
                        f"DOCUMENT URL: {product['DOCUMENT URL']}\n" \
                        f"ACHIEVEMENT: {product['ACHIEVEMENT']}\n" \
                        f"{similarity_details}\n" \
                        "\n-------------------------\n\n"
        return f"Here are the product details that might match your search preferences: \n{document}\nPlease review the list above to remove any product that are irrelevant or do not meet user requirements."

    def convert_user_question_to_data(self, question, history):
        json_data_str = convert_text_to_json(PROMPT_CONVERT_QUESTION_TO_JSON_QUERY_SOFTWARE, question, history)
        json_data = json.loads(json_data_str)
        return json_data

    def query(self, question):
        json_data = self.convert_user_question_to_data(question, "")
        document = self.query_software(json_data)
        return document
