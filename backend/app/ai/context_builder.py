

from backend.app.ai.prompts import SYSTEM_PROMPT

def build_context(history, user_input):
    message = [
        {
            'role': 'system',
            'content': SYSTEM_PROMPT
        }
    ]


    message.extend(history)


    message.append({
        'role': 'user',
        'content': user_input
    })

    return message