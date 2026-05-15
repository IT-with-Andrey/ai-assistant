
from backend.app.services.assistant_service import chat


while True:

    user_input = input('You: ')


    if user_input == 'exit':
        break

    answer = chat(user_input)

    print(f'AI: {answer}')
    