

from backend.app.ai.prompts import SYSTEM_PROMPT

def build_context(history, user_input,summary: str = None , user_facts:list =None):

    """
    Builds the full context for sending to the LLM
    Acceptc:
            history - list of dicts with keys 'role' and 'content' (from DB or other source)

            user_input - string with  the user's new message 

            message = list of dicts ready to be passed to genetate_response()

                    """
    # statr with the System message - Instruction for the model
     #Если есть факты о пользователе, добавляем их как системную информацию
    message = [
        {
            'role': 'system',
            'content': SYSTEM_PROMPT or 'You are assistant'
        }
    ]
    if user_facts:
        facts_text = ' Факты о пользователе: \n' + '\n'.join(
    [f'- {str(f.key)}: {str(f.value)}' for f in user_facts]
)
        message.append({
            'role': 'system',
            'content': facts_text
        })
    if summary:
        message.append({
            'role': 'system',
            'content': f"Контекст предыдущего диалога (НЕ обсуждай его, если не спросят, просто используй для понимания):\n{str(summary)}"})


    # Clean the history 
    #Keep only messages that have both 'role' and 'content ' (Not None and not empty)
    # Rebuild each  element  as a new dict (just in case , to avoid mutating the original objects)
    clean_history = [
    {'role': m['role'], 'content': str(m['content'])}
    for m in history
    if m.get('role') and m.get('content')
]
    
    

    # add the cleaned history to out final list 
    message.extend(clean_history)

    # Finally , add the current user query
    message.append({
    'role': 'user',
    'content': str(user_input)
})
    # return the full context
    return message 