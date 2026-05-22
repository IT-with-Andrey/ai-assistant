import requests
from backend.app.core.logger import logger
from backend.app.core.logging_utils import log_execution_time


MODEL = "gemma4:31b-cloud"

@log_execution_time
def generate_response(message: list[dict]) -> str:
    """ The process of sending a message"""
    logger.debug("Отправка запроса к Ollama: %d сообщений", len(message))
    try:

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": MODEL,
                "messages": message,
                "stream": False,
                'options': {
                    'num_predict' : 4096
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
        logger.error ("Ошибка при обращении к Ollama: %s", e)
        return "Извините, произошла ошибка при обращении к языковой модели."
    except (KeyError,ValueError)as e :
        logger.error ("Ошибка парсинга ответа от Ollama: %s", e)
        return "Извините, ответ модели был в неожиданном формате."