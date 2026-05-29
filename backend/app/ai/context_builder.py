from backend.app.ai.persona_manager import PersonaManager

from backend.app.ai.memory_orchestrator import memory_orchestrator


def build_context(history , user_input , summary: str=None , user_facts: str = None , user_id: str = 'default_user'):
    facts = memory_orchestrator.get_user_fact(user_id)
    role = 'default'
    for fact in facts:
        if isinstance(fact,str) and fact.startswith('assistant_role:'):
            role = fact.split(':',1)[1].strip()
            break

    system_prompt = PersonaManager.get_system_prompt(role)

    message = [{"role": "system", "content": system_prompt}]

    if user_facts:
        message.append({"role": "system", "content": f"Факты о пользователе:\n{user_facts}"})

    if summary:
        message.append({"role": "system", "content": f"Контекст предыдущего диалога:\n{summary}"})

    clean_history = []
    for m in history:
        if hasattr(m, 'role'):
            role = m.role
            content = m.content
        else:
            role = m['role']
            content = m['content']
        clean_history.append({'role': role, 'content': str(content)})

    message.extend(clean_history)
    message.append({"role": "user", "content": str(user_input)})
    return message