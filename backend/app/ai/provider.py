
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
import os
from backend.app.core.logger import logger
from backend.app.core.logging_utils import log_execution_time


MODEL = os.getenv("AI_MODEL", "gemma4:31b-cloud")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


@log_execution_time
def generate_response(message: list[dict]) -> str:
    """ The process of sending a message"""
    logger.debug("Отправка запроса к Ollama: %d сообщений", len(message))
    try:

        # Защита от несериализуемых объектов: превращаем всё в строки
        safe_messages = []
        for msg in message:
            safe_msg = {
                'role': str(msg.get('role', 'user')),
                'content': str(msg.get('content', ''))
            }
            safe_messages.append(safe_msg)

        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": MODEL,
                "messages": safe_messages,
                "stream": False,
                'options': {
                    'num_predict': 4096
                }
            },  timeout=120
        )
        # for debugging , print status and raw response
        # print("STATUS:", response.status_code)
        # print("TEXT:", response.text)
        response.raise_for_status()

        data = response.json()
        answer = data['message']['content']
        logger.info('Ответ получен (длина %d символов)', len(answer))
        return answer
    except requests.RequestException as e:
        logger.error("Ошибка при обращении к Ollama: %s", e)
        return "Извините, произошла ошибка при обращении к языковой модели."
    except (KeyError, ValueError)as e:
        logger.error("Ошибка парсинга ответа от Ollama: %s", e)
        return "Извините, ответ модели был в неожиданном формате."
