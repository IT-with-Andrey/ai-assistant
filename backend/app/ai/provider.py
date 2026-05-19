
# from openai import OpenAI
# from backend.app.core.config import API_KEY , MODEL


# client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=API_KEY,
#     default_headers={
#         "HTTP-Referer": "http://localhost",
#         "X-Title": "AI Assistant"
#     }
# )

# def generate_response(message):
#     response = client.chat.completions.create(
#         model=MODEL,
#         messages=message
          
#     )
    

   

#     return response.choices[0].message.content
# ============================================================
# ВАРИАНТ 2: Локальная модель через Ollama (активен сейчас)
# ============================================================
import requests

MODEL = "qwen2.5-coder:7b"


def generate_response(message):
    """ The process of sending a message"""
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": MODEL,
            "messages": message,
            "stream": False,
            'options': {
                'num_predict' : 2048
            }
        }
    )
    # for debugging , print status and raw response
    # print("STATUS:", response.status_code)
    # print("TEXT:", response.text)

    data = response.json() # json.loads(response.text).
    return data["message"]["content"]   # extract the response text 