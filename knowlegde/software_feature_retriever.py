from api.helpers.db_config import get_db
from api.helpers.gemini import convert_text_to_json
from api.helpers.prompt import PROMPT_CONVERT_QUESTION_TO_JSON_QUERY_SOFTWARE
from api.helpers.sentence_embedding import model_embedding 
#TODO

class FeatureRetriever:
    def __init__(self):
        self.PGDB_QUERY_SOFTWARE = {
    "feature_name": {
        "similarity": "(1 - (feature_name_embedding <=> %(feature_name_embedding)s::public.vector))",
        "weight": 1/2
    },
    "feature_description": {
        "similarity": "(1 - (feature_description_embedding <=> %(feature_description_embedding)s::public.vector))",
        "weight": 1/2
    },
}
        self.history = "Here is the content of the previous conversation."
    def query_feature(self, json_data):
        embed_params = {}
        query = """
            SELECT id, software_id, feature_name, feature_image_url, feature_description
        """
        total_similarity_element = []

        for key, val in json_data.items():
            if key in self.PGDB_QUERY_SOFTWARE:
                embed_key = f"{key}_embedding"
                embed_params[embed_key] = model_embedding.encode(val).tolist()
                similarity_sql = self.PGDB_QUERY_SOFTWARE[key]["similarity"]

                query += f", {similarity_sql} AS {key}_similarity"
                total_similarity_element.append(f"{similarity_sql} * {self.PGDB_QUERY_SOFTWARE[key]['weight']}")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, embed_params)
        rows = cursor.fetchall()
        if len(rows) > 0:
            document = "Here are the features that the software can offer. Please respond accordingly.\n"
        else:

            document = ""
        for row in rows:
            idx, software_id, feature_name, feature_image_url, feature_description = row
            document += f"FEATURE ID: {idx} \
                    \nFEATURE NAME: {feature_name} \
                    \nFEATURE IMAGE URL: {feature_image_url} \
                    \nFEATURE DESCRIPTION: {feature_description} \
                    \n\n-------------------------\n\n"
    def convert_user_question_to_data(self, question):
        json_data = convert_text_to_json(PROMPT_CONVERT_QUESTION_TO_JSON_QUERY_SOFTWARE, question, self.history)
        return json_data
    def query_feature_by_software(self, software_id):
        query = """
            SELECT id, feature_name, feature_image_url, feature_description FROM software_feature WHERE software_id = %s
        """
        conn = get_db()
        cursor = conn.cursor()
        params = [software_id]
        cursor.execute(query, params)
        rows = cursor.fetchall()
        document = ""
        for row in rows:
            idx, feature_name, feature_image_url, feature_description = row
            document += f"FEATURE ID: {idx} \
                    \nFEATURE NAME: {feature_name} \
                    \nFEATURE IMAGE URL: {feature_image_url} \
                    \nFEATURE DESCRIPTION: {feature_description} \
                    \n\n-------------------------\n\n"
        return document
    def query(self, question):

        pass
    