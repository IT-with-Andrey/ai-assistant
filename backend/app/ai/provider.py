
from openai import OpenAI
from backend.app.core.config import API_KEY , MODEL


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    default_headers={
        "HTTP-Referer": "http://localhost",
        "X-Title": "AI Assistant"
    }
)

def generate_response(message):
    response = client.chat.completions.create(
        model=MODEL,
        messages=message
          
    )
    

   

    return response.choices[0].message.content

