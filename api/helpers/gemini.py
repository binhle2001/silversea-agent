generation_json_config = {
  "temperature": 0.7,
  "stop_sequences": ['<|im_end|>'],
  "top_p": 0.98,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}
generation_config = {
  "temperature": 0.7,
  "stop_sequences": ['<|im_end|>'],
  "top_p": 0.98,
  "top_k": 24,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
]

import os
import google.generativeai as genai
from .common import get_env_var
from .prompt import *
os.environ["GEMINI_API_KEY"] = get_env_var("gemini", "GEMINI_API_KEY")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model_extraction = genai.GenerativeModel(
  model_name="gemini-2.0-flash",
  safety_settings=safety_settings,
  generation_config=generation_json_config,
)

model_generation = genai.GenerativeModel(
  model_name="gemini-2.0-flash",
  safety_settings=safety_settings,
  generation_config=generation_config,
)
def convert_text_to_json(promt, question, history):
    prompt_text = promt.format(question = question, history = history)

    chat_session = model_extraction.start_chat(
            history=[
            ]
        )
    output = chat_session.send_message(prompt_text).text
    return output.replace("```json", "").replace("```", "")


