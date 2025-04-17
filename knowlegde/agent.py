from knowlegde.software_retriever import SoftwareRetriever
from fastapi import  WebSocket
from api.helpers.gemini import model_generation
software_retriever = SoftwareRetriever()

class Chat:
    def __init__(self, customer_name):
        self.PROMPT_GENERATION = f"""System: You are an advanced language model trained to provide software product consultation in the field of surveillance and security for the company "Biển Bạc Joint Stock Company." You must refer to yourself as "em" and address the customer as "anh/chị." Use the provided document to answer the customer's questions in the most friendly and appropriate manner.\nThe customer's name is {customer_name}.
        """
        self.software_retriever = SoftwareRetriever()
        self.model_generation = model_generation


    async def chat(self, question, websocket: WebSocket):
        document = self.software_retriever.query(question)
        self.PROMPT_GENERATION += document
        self.PROMPT_GENERATION += f"User: {question}\n"

        content = [
            {
                "role": "user",
                "parts": [
                    {"text": f"{self.PROMPT_GENERATION}"}
                ]
            }
        ]

        response = self.model_generation.generate_content(content, stream=True)

        for chunk in response:
            # Gửi từng chunk về client qua WebSocket
            await websocket.send_text(chunk.text)

        # Thông báo kết thúc
        await websocket.send_text("__end__")


