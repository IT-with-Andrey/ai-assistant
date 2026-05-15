
from backend.app.ai.provider import generate_response

from backend.app.ai.context_builder import build_context



history = []


def chat(user_input):
    message = build_context(history, user_input)

    answer = generate_response(message)

    history.append({
            'role': 'user',
            'content': user_input
    })

    history.append({
        'role': 'assistant',
        'content': answer
    })


    return answer